"""Bounded original preflight then one six-order whole-search measurement."""
import fcntl,json,os,signal,subprocess,sys,time
from pathlib import Path
from common import ROOT,HERE,OUT,now,sha,save,pins,process
OWNER='astra-v38-last-only-cost-20261110'

def lease(take):
 with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);path=ROOT/'chatroom/cores.json';value=json.loads(path.read_text())
  if take:
   assert all(not(set(row['cores'])&{4,5}) for row in value['allocation'])
   value['allocation'].append(dict(owner=OWNER,cores=[4,5],pid=os.getpid(),at=now(),purpose='finite three-arm current-v38 cost study, max30min'))
  else:value['allocation']=[row for row in value['allocation'] if row.get('owner')!=OWNER]
  value['updated']=now();save(path,value)


def main():
 plan=json.loads((OUT/'plan.json').read_text());pins(plan);assert not (OUT/'execution.json').exists()
 lease(True);os.sched_setaffinity(0,{4,5});start=time.monotonic();store=Path(plan['store']);store.mkdir(exist_ok=False)
 state=dict(at=now(),status='running',phase='source-review',calls=[],restarted=False,pid=os.getpid());save(OUT/'execution.json',state)
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('30-minute whole-search bound')));signal.alarm(plan['total_seconds'])
 try:
  subprocess.run([sys.executable,str(HERE/'source.py')],cwd=ROOT,check=True,timeout=120)
  for phase,fixed in [('preflight',True),('measure',False)]:
   state['phase']=phase;save(OUT/'execution.json',state)
   for case in plan['cases']:
    pins(plan);stdout,stderr,rows,elapsed=process(plan,case,fixed)
    prefix=store/f"{phase}-{case['index']:02d}"
    for suffix,text in [('.stdout',stdout),('.stderr',stderr),('.rows.json',json.dumps(rows,indent=2)+'\n')]:prefix.with_suffix(suffix).write_text(text)
    item=dict(phase=phase,case=case['name'],index=case['index'],seconds=elapsed,searches=len(rows),stdout_sha256=sha(prefix.with_suffix('.stdout')),stderr_sha256=sha(prefix.with_suffix('.stderr')),rows_sha256=sha(prefix.with_suffix('.rows.json')))
    state['calls'].append(item);save(OUT/'execution.json',state);print(json.dumps(item),flush=True)
    assert sum(p.stat().st_size for p in store.iterdir())<=plan['store_max_bytes']
  state['status']='complete'
 except BaseException as exc:state.update(status='failed',error=repr(exc));raise
 finally:
  signal.alarm(0);state.update(ended_at=now(),seconds=time.monotonic()-start);save(OUT/'execution.json',state);lease(False)
 subprocess.run([sys.executable,str(HERE/'review.py')],cwd=ROOT,check=True,timeout=300)

if __name__=='__main__':main()
