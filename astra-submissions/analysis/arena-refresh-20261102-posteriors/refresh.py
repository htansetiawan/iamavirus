from pathlib import Path
from datetime import datetime,timezone
import fcntl,hashlib,json,os,subprocess,sys,time
root=Path('/home/henrytan/git/iamavirus');sys.path.insert(0,str(root))
from learning.compare_archives import kill_tree
os.sched_setaffinity(0,{2,3})
out=Path(__file__).resolve().parent;raw=root/'data/raw/accepted.jsonl'
known={json.loads(s)['id'] for s in raw.read_text().splitlines()};start=time.monotonic()
lock=(root/'data/logs/daily/.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
state={'started':datetime.now(timezone.utc).isoformat(),'parent_pid':os.getpid(),'before_ids':len(known),'limit':150,'pace_seconds':1.2,'status':'running'}
with (out/'execution.json').open('x') as f:json.dump(state,f,indent=2)
with (out/'stdout.txt').open('x') as stdout,(out/'stderr.txt').open('x') as stderr:
 p=subprocess.Popen([str(root/'.venv/bin/python'),'-m','learning.ingest','--team','IAmAVirus','--output','data/raw','--limit','150','--pause','1.2'],cwd=root,stdout=stdout,stderr=stderr,start_new_session=True)
 state['child_pid']=p.pid;(out/'execution.json').write_text(json.dumps(state,indent=2)+'\n')
 try:p.wait(timeout=600);state.update(status='complete' if p.returncode==0 else 'failed',exit=p.returncode)
 except BaseException as e:kill_tree(p.pid);p.wait();state.update(status='failed',exit=p.returncode,error=f'{type(e).__name__}: {e}')
new={json.loads(s)['id'] for s in raw.read_text().splitlines()};state.update(ended=datetime.now(timezone.utc).isoformat(),elapsed=time.monotonic()-start,new_ids=sorted(new-known))
(out/'execution.json').write_text(json.dumps(state,indent=2)+'\n');print(json.dumps(state),flush=True)
assert state['status']=='complete',state
