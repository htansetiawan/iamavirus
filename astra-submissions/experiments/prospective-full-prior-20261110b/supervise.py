"""Review the new SSD-primary confirmation once; never collect, fit or promote."""
from contextlib import contextmanager
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import uuid

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/prospective-review-20261110b'
STUDY=ROOT/'astra-submissions/analysis/prospective-full-prior-20261110b'


def now():return datetime.now(timezone.utc).isoformat()
def instant(s):return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def atomic(p,v):
    p=Path(p)
    fd,temp=tempfile.mkstemp(prefix='.'+p.name+'-',dir=p.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
        os.replace(temp,p)
    finally:
        if os.path.exists(temp):os.unlink(temp)


def process_identity(pid):
    try:s=Path(f'/proc/{pid}/stat').read_text()
    except FileNotFoundError:return None
    fields=s[s.rfind(')')+2:].split()
    return dict(start_ticks=int(fields[19]),state=fields[0])


@contextmanager
def core_lock(path):
    with Path(path).open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        yield


def claim(core_file,lock_file,lease,cores):
    with core_lock(lock_file):
        state=read(core_file)
        if any(set(item.get('cores',[]))&set(cores) for item in state['allocation']):return False
        state['allocation'].append(dict(owner='astra',cores=cores,lease=lease,
            purpose='307 sealed SSD source audit, frozen scoring and independent verification'))
        state['updated']=now();atomic(core_file,state)
    return True


def check_lease(core_file,lease,cores):
    state=read(core_file)
    own=[x for x in state['allocation'] if x.get('lease')==lease]
    assert len(own)==1 and own[0]['cores']==cores,'core lease changed'
    assert not any(set(x.get('cores',[]))&set(cores) for x in state['allocation'] if x.get('lease')!=lease),'overlapping core lease'


def release(core_file,lock_file,lease):
    with core_lock(lock_file):
        state=read(core_file)
        state['allocation']=[x for x in state['allocation'] if x.get('lease')!=lease]
        state['updated']=now();atomic(core_file,state)


def execute_pipeline(out,study,commands,lease_check):
    """First attempt only. Every stage must exit zero and produce its receipt."""
    assert not any((study/name).exists() for name in ('scoring.json','result.json','independent-review.json')),'scoring already attempted; do not duplicate'
    stages=[]
    for label,argv,bound in commands:
        lease_check()
        started=now();tick=time.monotonic()
        with (out/(label+'.stdout')).open('x') as stdout,(out/(label+'.stderr')).open('x') as stderr:
            child=subprocess.Popen(argv,stdout=stdout,stderr=stderr,start_new_session=True)
            try:code=child.wait(timeout=bound)
            except BaseException:
                # Dedicated group contains only this scoring/audit command.
                if child.poll() is None:
                    os.killpg(child.pid,signal.SIGTERM)
                    try:child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid,signal.SIGKILL);child.wait()
                raise
        stage=dict(label=label,argv=argv,started_at=started,ended_at=now(),exit_code=code,seconds=time.monotonic()-tick)
        stages.append(stage);atomic(out/'stages.json',stages)
        assert code==0,f'{label} exited {code}; no retry'
        if label=='source-audit':
            audit=read(out/'sealed-source-audit.json')
            assert audit['passed'] and audit['complete_cohort_verified'] and audit['production_score_absent'],'source audit not ready for scoring'
        elif label=='score':
            assert read(study/'scoring.json')['status']=='complete'
            assert (study/'result.json').is_file()
        elif label=='verify':
            assert read(study/'independent-review.json')['passed']
    return dict(decision=read(study/'result.json')['decision'],stages=stages,
                result_sha256=sha(study/'result.json'),independent_review_sha256=sha(study/'independent-review.json'))


def main():
    contract=read(OUT/'contract.json')
    for p,h in contract['dependencies'].items():assert sha(p)==h,p
    assert sha(STUDY/'plan.json')==contract['study_plan_sha256']
    collector=contract['collector'];ident=process_identity(collector['pid'])
    assert ident and ident['start_ticks']==collector['start_ticks'] and ident['state']!='Z','original collector missing; do not restart'
    lock=(OUT/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (OUT/'execution.json').exists(),'continuation already attempted'
    lease=uuid.uuid4().hex;leased=False
    core_file=ROOT/'chatroom/cores.json';lock_file=Path('/tmp/iamavirus-cores-json.lock')
    state=dict(started_at=now(),status='running',phase='waiting_for_original_collector',pid=os.getpid(),
               collector=collector,contract_sha256=sha(OUT/'contract.json'),collection_restarted=False,models_fitted=False)
    atomic(OUT/'execution.json',state)
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(InterruptedError('supervisor terminated')))
    try:
        while True:
            current=read(STUDY/'execution.json')
            assert current['pid']==collector['pid'] and current['plan_sha256']==contract['study_plan_sha256']
            assert current['publication_commit']==contract['collector_publication'],'collector receipt identity changed'
            state.update(updated_at=now(),collector_status=current['status'],collector_phase=current.get('phase'),collected=current.get('collected'))
            atomic(OUT/'execution.json',state)
            if current['status']=='complete':
                assert current['phase']=='sealed','collector completed without sealed cohort'
                break
            assert current['status']=='running','collector terminated without a cohort'
            ident=process_identity(collector['pid'])
            assert ident and ident['start_ticks']==collector['start_ticks'] and ident['state']!='Z','original collector missing; no restart'
            assert time.time()<instant(contract['monitor_deadline']),'monitor deadline; no extension'
            time.sleep(contract['poll_seconds'])
        for p,h in contract['dependencies'].items():assert sha(p)==h,p
        state.update(phase='waiting_for_cores',updated_at=now());atomic(OUT/'execution.json',state)
        while True:
            assert time.time()<instant(contract['core_deadline']),'cores unavailable by fixed deadline'
            if claim(core_file,lock_file,lease,contract['cores']):break
            time.sleep(contract['poll_seconds'])
        leased=True
        state.update(phase='audit_score_verify',updated_at=now());atomic(OUT/'execution.json',state)
        py=str(ROOT/'.venv/bin/python');base=ROOT/'astra-submissions/experiments'
        commands=[
            ('source-audit',['taskset','-c','0,1',py,str(base/'cohort-integrity-20261110/audit.py'),'--folder',str(STUDY),'--require-sealed','--out',str(OUT/'sealed-source-audit.json')],180),
            ('score',['taskset','-c','0,1',py,str(base/'prospective-full-prior-20261110b/score.py')],1860),
            ('verify',['taskset','-c','0,1',py,str(base/'prospective-full-prior-20261110b/verify.py')],1860)]
        result=execute_pipeline(OUT,STUDY,commands,lambda:check_lease(core_file,lease,contract['cores']))
        state.update(status='complete',phase='reviewed',result=result)
    except BaseException as exc:
        state.update(status='failed',error=repr(exc))
        raise
    finally:
        if leased:release(core_file,lock_file,lease)
        state.update(ended_at=now(),updated_at=now(),core_lease_released=leased)
        atomic(OUT/'execution.json',state)
        entry=dict(ts=now(),**{'from':'astra','to':'fable'},type='prospective-auto-review-terminal',
            subject='307 SSD continuation '+state['status'],
            body='See execution/stages and the SSD confirmation results. No automatic fit, retry, matches, release or promotion. '+state.get('error',''),
            refs=['chatroom/307-astra-ssd-prospective-confirmation.md',str((OUT/'execution.json').relative_to(ROOT))])
        with (ROOT/'chatroom/ledger.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
    print(json.dumps(state,indent=2),flush=True)


if __name__=='__main__':main()
