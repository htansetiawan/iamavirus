"""One bounded correctness execution; no synthetic or whole-search timing gate."""
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
OUT=ROOT/'astra-submissions/analysis/last-only-cfr-20261110';OWNER='astra-last-only-cfr-correctness-20261110'
sys.path.insert(0,str(ROOT))
from learning.api_client import atomic_write


def now():return datetime.now(timezone.utc).isoformat()
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,value):atomic_write(path,(json.dumps(value,indent=2,allow_nan=False)+'\n').encode())
def lease(take):
    with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);path=ROOT/'chatroom/cores.json';state=json.loads(path.read_text())
        if take:
            assert all(not(set(r['cores'])&{4,5}) for r in state['allocation'])
            state['allocation'].append(dict(owner=OWNER,cores=[4,5],purpose='bounded correctness tests; no timed strength run',at=now(),pid=os.getpid()))
        else:state['allocation']=[r for r in state['allocation'] if r.get('owner')!=OWNER]
        state['updated']=now();save(path,state)
def child_setup():resource.setrlimit(resource.RLIMIT_CORE,(0,0))


def main():
    plan=json.loads((OUT/'plan.json').read_text())
    for path,value in plan['dependencies'].items():assert sha(path)==value,path
    assert not (OUT/'execution.json').exists();lease(True);os.sched_setaffinity(0,{4,5})
    started=time.monotonic();state=dict(at=now(),pid=os.getpid(),status='running',calls=[],restarted=False)
    save(OUT/'execution.json',state);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('correctness global bound')));signal.alarm(600)
    try:
        jobs=[(f'check-{mode}-{kind}',0) for mode in (0,1) for kind in ('opt','san')]+[('average-api-0',0),('average-api-1',-signal.SIGABRT)]
        for name,expected in jobs:
            environment={k:v for k,v in os.environ.items() if k not in ('LD_PRELOAD','ASAN_OPTIONS','LSAN_OPTIONS','UBSAN_OPTIONS')}
            environment.update(ASAN_OPTIONS='detect_leaks=1:abort_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
            child=subprocess.Popen([str(HERE/'build'/name)],cwd=ROOT,env=environment,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True,preexec_fn=child_setup)
            try:stdout,stderr=child.communicate(timeout=120)
            except BaseException:
                os.killpg(child.pid,signal.SIGKILL);child.communicate();raise
            (OUT/f'{name}.stdout').write_text(stdout);(OUT/f'{name}.stderr').write_text(stderr)
            state['calls'].append(dict(name=name,code=child.returncode,expected=expected,stdout_sha256=sha(OUT/f'{name}.stdout'),stderr_sha256=sha(OUT/f'{name}.stderr')));save(OUT/'execution.json',state)
            assert child.returncode==expected,(name,child.returncode,stderr[-1500:])
        state['status']='complete'
    except BaseException as exc:state.update(status='failed',error=repr(exc));raise
    finally:
        signal.alarm(0);state.update(ended_at=now(),seconds=time.monotonic()-started);save(OUT/'execution.json',state);lease(False)
    subprocess.run([sys.executable,str(HERE/'review.py')],cwd=ROOT,check=True,timeout=120)

if __name__=='__main__':main()
