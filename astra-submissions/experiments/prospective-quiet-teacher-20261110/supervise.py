"""One original bounded collection, source audit, fixed scoring and review."""
import argparse
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import uuid
from protocol import ROOT,OUT,HERE,now,sha,check_pins,instant,write


def cores(ident,remove=False):
    path=ROOT/'chatroom/cores.json'
    with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);state=json.loads(path.read_text())
        if remove:state['allocation']=[r for r in state['allocation'] if r.get('lease')!=ident]
        elif any(set(r.get('cores',[]))&{2,3} for r in state['allocation']):return False
        else:state['allocation'].append(dict(owner='astra',cores=[2,3],lease=ident,purpose='326 sealed source audit/fixed CPU teacher prediction/independent review; no GPU'))
        state['updated']=now();temp=path.with_name('.cores-'+ident);temp.write_text(json.dumps(state,indent=2)+'\n');os.replace(temp,path)
    return True


def stage(state,name,argv,bound):
    state['phase']=name;write(OUT/'pipeline.json',state);started=time.monotonic()
    with (OUT/(name+'.stdout')).open('x') as stdout,(OUT/(name+'.stderr')).open('x') as stderr:
        child=subprocess.Popen(argv,cwd=ROOT,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'),stdout=stdout,stderr=stderr,start_new_session=True)
        try:code=child.wait(timeout=bound)
        except BaseException:
            if child.poll() is None:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            raise
    record=dict(stage=name,code=code,seconds=time.monotonic()-started);state['stages'].append(record);write(OUT/'pipeline.json',state);print(json.dumps(record),flush=True)
    assert code==0,(name,'failed; no automatic retry')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--publication-commit',required=True);args=parser.parse_args()
    plan=json.loads((OUT/'plan.json').read_text());check_pins(plan)
    assert datetime.now(timezone.utc)<instant(plan['cutoff']) and not (OUT/'pipeline.json').exists()
    assert subprocess.check_output(['git','show',args.publication_commit+':'+str((OUT/'plan.json').relative_to(ROOT))],cwd=ROOT)==(OUT/'plan.json').read_bytes()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('fixed total pipeline deadline')));signal.alarm(plan['pipeline_wall_seconds'])
    state=dict(status='running',started_at=now(),source_publication=args.publication_commit,plan_sha256=sha(OUT/'plan.json'),stages=[],pid=os.getpid(),pid_scope='tool namespace; original execution handle is authoritative')
    write(OUT/'pipeline.json',state,exclusive=True);started=time.monotonic();ident=uuid.uuid4().hex;claimed=False
    python=str(ROOT/'.venv/bin/python')
    try:
        stage(state,'collect',[python,str(HERE/'collect.py'),'--publication-commit',args.publication_commit],plan['wall_seconds']+30)
        collector=json.loads((OUT/'execution.json').read_text())
        if collector['status']!='complete' or collector['phase']!='sealed':
            state.update(status='closed_without_scoring',phase='insufficient complete data');return
        limit=time.monotonic()+plan['core_wait_seconds']
        while not (claimed:=cores(ident)):
            assert time.monotonic()<limit,'core reservation timeout; no duplicate run'
            time.sleep(30)
        for name,bound in [('source_audit',1200),('score',1800),('review',1200)]:
            stage(state,name,['taskset','-c','2,3',python,str(HERE/(name+'.py'))],bound)
        review=json.loads((OUT/'independent-review.json').read_text());assert review['passed']
        state.update(status='complete',phase='reviewed',decision=review['decision'])
    except BaseException as exc:state.update(status='failed',error=repr(exc));raise
    finally:
        if claimed:cores(ident,remove=True)
        state.update(ended_at=now(),seconds=time.monotonic()-started,lease_was_claimed=claimed,own_lease_released=True)
        write(OUT/'pipeline.json',state);print(json.dumps(state),flush=True)


if __name__=='__main__':main()
