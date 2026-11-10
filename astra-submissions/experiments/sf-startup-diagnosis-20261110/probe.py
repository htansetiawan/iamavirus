"""A finite zero-ply startup diagnostic using the same referee as pilot 332."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

from prepare import HERE, ROOT, OUT, SHIP, sha
from test_trace import clean_env
sys.path.insert(0,str(ROOT/'astra-submissions/tools'))
from local_turn_control import run_controlled, cleanup_registry, group_members

OWNER='astra-sf-startup-diagnosis-20261110'
PLAN=OUT/'plan.json'

def now(): return datetime.now(timezone.utc).isoformat()
def save(path,obj):
    temp=path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
    temp.replace(path)

def load():
    plan=json.loads(PLAN.read_text())
    for path,digest in plan['dependencies'].items(): assert sha(path)==digest,path
    return plan

def freeze():
    build=json.loads((OUT/'build.json').read_text())
    mocks=json.loads((OUT/'mock-contracts.json').read_text())
    assert build['passed'] and mocks['passed'] and mocks['calls']==11 and not PLAN.exists()
    evidence=OUT.parent/'last-only-pilot-20261110/backend-failure-evidence.json'
    teacher=OUT.parent/'prospective-quiet-teacher-20261110/plan.json'
    local=[*sorted(HERE.glob('*.py')),OUT/'build.json',OUT/'mock-contracts.json',
        evidence,teacher,ROOT/'chatroom/050-astra-clock-isolation-and-startup.md',
        ROOT/'astra-submissions/tools/local_turn_control.py',SHIP/'run.sh',
        ROOT/'astra-submissions/iamavirus-v38-mist-c-allchildren.zip']
    jobs=[dict(id=f'sf-init-{i:02d}',lane=i%2,diagnostic_side='white' if (i//2+i%2)%2==0 else 'black',seed=3331110+i) for i in range(16)]
    plan=dict(at=now(),scope='Startup only: exact shipped v38 versus observation-only startup-trace copy; no scored game or production change.',
        jobs=jobs,cores={'0':[0,1],'1':[4,5]},supervisor_core=7,base=180,increment=2,max_plies=0,
        job_cap_seconds=38,wall_cap_seconds=330,store_cap_bytes=64*1024*1024,
        store=str(ROOT/'data/astra-spool/sf-startup-diagnosis-20261110'),
        dependencies=build['dependencies']|{str(p):sha(p) for p in local})
    save(PLAN,plan);load();print(json.dumps(dict(pins=len(plan['dependencies']),sha256=sha(PLAN),jobs=len(jobs))))

def referee():
    spec=importlib.util.spec_from_file_location('startup_referee',HERE/'build/referee.py')
    ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    return ref

def directory(plan,job): return Path(plan['store'])/job['id']

def worker(jobid):
    plan=load();job=next(j for j in plan['jobs'] if j['id']==jobid)
    dest=directory(plan,job);ref=referee();args=[]
    for side in ('white','black'):
        diag=side==job['diagnostic_side'];root=HERE/'build/diagnostic' if diag else SHIP
        args.append(['/usr/bin/env',f'FOW_SEED={job["seed"]}','ASTRA_SF_STARTUP_TRACE='+('1' if diag else ''),'/bin/bash',str(root/'run.sh')])
    replay=run_controlled(ref,*args,base=plan['base'],increment=plan['increment'],max_plies=0,
        match_id=jobid,registry_path=dest/'processes.json',retain_stderr=True)
    save(dest/'startup.json',replay)

def lease(plan,take):
    with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);path=ROOT/'chatroom/cores.json';state=json.loads(path.read_text())
        if take:
            wanted={plan['supervisor_core'],*(c for cores in plan['cores'].values() for c in cores)}
            assert wanted<=os.sched_getaffinity(0) and all(not wanted&set(r['cores']) for r in state['allocation'])
            state['allocation'].append(dict(owner=OWNER,cores=sorted(wanted),at=now(),pid=os.getpid(),purpose='16 zero-ply referee startups; no game clock or search, bounded 330s'))
        else: state['allocation']=[r for r in state['allocation'] if r.get('owner')!=OWNER]
        state['updated']=now();save(path,state)

def clean_groups(dest):
    registry=dest/'processes.json'
    if not registry.exists():return ['missing owned startup registry']
    faults=cleanup_registry(registry);deadline=time.monotonic()+5
    rows=json.loads(registry.read_text())
    while True:
        live=[r for row in rows for r in group_members(row['leader']['pgid']) if r['state'] not in ('Z','X')]
        if not live:return faults
        if time.monotonic()>=deadline:return faults+['owned startup groups still live']
        time.sleep(.025)

def run(commit):
    plan=load();assert not (OUT/'execution.json').exists()
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==commit
    published=subprocess.check_output(['git','show',f'{commit}:{PLAN.relative_to(ROOT)}'],cwd=ROOT)
    assert published==PLAN.read_bytes()
    lease(plan,True);root=Path(plan['store']);started=time.monotonic()
    state=dict(started_at=now(),source_publication=commit,plan_sha256=sha(PLAN),status='running',original_attempt=True)
    safe_release=True;stop=threading.Event();terminal=[]
    try:
        root.mkdir(parents=True,exist_ok=False);save(OUT/'execution.json',state)
        os.sched_setaffinity(0,{plan['supervisor_core']})
        def lane(index):
            for job in plan['jobs']:
                if job['lane']!=index or stop.is_set():continue
                try:
                    remaining=plan['wall_cap_seconds']-(time.monotonic()-started)
                    if remaining<=0:raise TimeoutError('batch wall cap')
                    dest=directory(plan,job);dest.mkdir(exist_ok=False)
                    save(dest/'started.json',dict(at=now(),job=job,plan_sha256=sha(PLAN)))
                    begin=time.monotonic();timed_out=False
                    with (dest/'stdout.txt').open('x') as out,(dest/'stderr.txt').open('x') as err:
                        cores=','.join(map(str,plan['cores'][str(index)]))
                        proc=subprocess.Popen(['taskset','-c',cores,sys.executable,str(Path(__file__)),'worker',job['id']],
                            cwd=ROOT,env=clean_env(),stdout=out,stderr=err,start_new_session=True)
                        try:proc.wait(timeout=min(plan['job_cap_seconds'],remaining))
                        except subprocess.TimeoutExpired:
                            timed_out=True
                            try:os.killpg(proc.pid,signal.SIGKILL)
                            except ProcessLookupError:pass
                            proc.wait(timeout=8)
                    cleanup=clean_groups(dest)
                    row=dict(job=job,code=proc.returncode,timed_out=timed_out,cleanup_unverified=cleanup,seconds=time.monotonic()-begin,at=now())
                    save(dest/'terminal.json',row);terminal.append(row)
                    if timed_out or proc.returncode or cleanup:raise RuntimeError('startup worker/cleanup fault')
                    if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>plan['store_cap_bytes']:raise RuntimeError('private storage cap')
                except BaseException:
                    stop.set();raise
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(lane,i) for i in (0,1)]
            for future in futures:future.result()
        assert len(terminal)==len(plan['jobs'])
        state['status']='observed'
    except BaseException as exc:
        state.update(status='technical_failure',error=repr(exc));raise
    finally:
        for dest in root.iterdir() if root.exists() else []:
            if dest.is_dir() and (dest/'started.json').exists():
                cleanup=clean_groups(dest)
                if cleanup:safe_release=False
        state.update(ended_at=now(),seconds=time.monotonic()-started,worker_exits=len(terminal),cleanup_verified=safe_release)
        save(OUT/'execution.json',state)
        if safe_release:lease(plan,False)
    subprocess.run([sys.executable,str(HERE/'review.py')],cwd=ROOT,timeout=60,check=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','worker','run']);parser.add_argument('value',nargs='?');args=parser.parse_args()
    if args.action=='freeze':freeze()
    elif args.action=='worker':worker(args.value)
    else:run(args.value)
