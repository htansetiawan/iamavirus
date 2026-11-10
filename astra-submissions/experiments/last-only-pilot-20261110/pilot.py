"""Finite paired 180+2 pilot using the existing audited turn-isolation helper."""
from collections import Counter
from datetime import datetime,timezone
import argparse,fcntl,hashlib,importlib.util,json,math,os
from pathlib import Path
import signal,subprocess,sys,time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/last-only-pilot-20261110'
OWNER='astra-last-only-pilot-20261110'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from local_turn_control import run_controlled,cleanup_registry,group_members
from learning.api_client import atomic_write


def now():return datetime.now(timezone.utc).isoformat()
def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,value):atomic_write(Path(path),(json.dumps(value,indent=2,allow_nan=False)+'\n').encode())
def load():
 plan=json.loads((OUT/'plan.json').read_text())
 for path,value in plan['dependencies'].items():assert sha(path)==value,path
 return plan

def referee():
 spec=importlib.util.spec_from_file_location('last_only_pilot_ref',HERE/'build/referee.py');ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref);return ref

def clean_env():
 env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_','OMP_','MKL_','OPENBLAS_'))}
 env.update(OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1');return env

def command(arm,seed):
 assert arm in ('base','candidate')
 return ['/usr/bin/env',f'FOW_SEED={seed}','/bin/bash',str(HERE/'build'/arm/'run.sh')]

def score(result,color):
 assert result in ('1-0','0-1','1/2-1/2') and color in ('white','black')
 return .5 if result=='1/2-1/2' else float((result=='1-0')==(color=='white'))

def futile(rows,planned=16,minimum=10):
 assert len(rows)<=planned and all(row['score'] in (0.,.5,1.) and not row['faults'] for row in rows)
 return sum(row['score'] for row in rows)+(planned-len(rows))<minimum

def job_dir(plan,job):return Path(plan['store'])/'jobs'/job['id']
def worker(job_id):
 plan=load();job=next(j for j in plan['jobs'] if j['id']==job_id);directory=job_dir(plan,job);ref=referee()
 ours=command('candidate',job['engine_seed']);theirs=command('base',job['opponent_seed'])
 white,black=(ours,theirs) if job['side']=='white' else (theirs,ours)
 game=run_controlled(ref,white,black,base=180,increment=2,max_plies=1000,match_id=job_id,
  white_name='last-only' if job['side']=='white' else 'exact-v38',black_name='last-only' if job['side']=='black' else 'exact-v38',registry_path=directory/'processes.json',retain_stderr=True)
 save(directory/'replay.json',game)

def inspect_game(plan,job,directory):
 game=json.loads((directory/'replay.json').read_text());faults=[];ref=referee();board=ref.FowBoard();hist=Counter({ref.position_key(board):1})
 assert game['id']==job['id'] and game['timeControl']==dict(baseSeconds=180,incrementSeconds=2)
 frames=game['frames'];assert 1<=len(frames)<=1001
 for ply,frame in enumerate(frames):
  assert frame['ply']==ply and len(frame['clocks'])==2 and all(math.isfinite(c) for c in frame['clocks'])
  if ply:
   move=ref.chess.Move.from_uci(frame['move']);assert move in ref.fow_moves(board);board.push(move);hist[ref.position_key(board)]+=1
  actual=ref.make_frame(board,frame['clocks']);assert all(actual[k]==frame[k] for k in ('board','white','black'))
  if ply<len(frames)-1:assert ref.outcome(board,hist) is None,'continued after a terminal position'
 if game.get('failedSide'):faults.append('bot failure: '+game['failedSide']+' '+game['reason'])
 if game.get('warnings'):faults.append('capture warning')
 if game['result'] not in ('1-0','0-1','1/2-1/2'):faults.append('non-game result')
 if not faults:
  terminal=ref.outcome(board,hist)
  if terminal:assert list(terminal)==[game['result'],game['reason']]
  else:assert len(frames)==1001 and game['result']=='1/2-1/2' and game['reason']=='Move limit reached'
  assert all(c>=0 for frame in frames for c in frame['clocks'])
 for side in ('white','black'):
  text=game.get('privateDiagnostics',{}).get(side,'')
  if 'mist: stockfish ready' not in text:faults.append('missing SF startup: '+side)
  if any(marker in text for marker in ('astra-three','astra-solver-pair','astra-teacher','astra-visible')):faults.append('diagnostic binary: '+side)
 controls=game.get('localTurnControl',{}).get('controls',[])
 if len(controls)!=2 or any(not any(e['op']=='freeze' and e.get('members',0)>0 for e in c['events']) or not any(e['op']=='resume' for e in c['events']) for c in controls):faults.append('missing verified turn isolation')
 return dict(job=job,result=game['result'],reason=game['reason'],score=None if faults else score(game['result'],job['side']),faults=faults,plies=len(frames)-1,validated_frames=len(frames),final_clocks=frames[-1]['clocks'],replay_sha256=sha(directory/'replay.json'))

def cleanup(directory):
 registry=directory/'processes.json';unverified=cleanup_registry(registry)
 if not registry.exists():return ['process registry unavailable; descendant cleanup not proven']
 deadline=time.monotonic()+5
 while registry.exists():
  records=json.loads(registry.read_text());live=[p for record in records for p in group_members(record['leader']['pgid']) if p['state'] not in ('Z','X')]
  if not live:return unverified
  if time.monotonic()>deadline:return unverified+['live groups remain after owned cleanup']
  time.sleep(.05)
 return unverified

def lease(take):
 with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);path=ROOT/'chatroom/cores.json';value=json.loads(path.read_text())
  if take:
   wanted={0,1,4,5,7};assert all(not(wanted&set(row['cores'])) for row in value['allocation'])
   value['allocation'].append(dict(owner=OWNER,cores=sorted(wanted),at=now(),pid=os.getpid(),purpose='two full-clock lanes0-1/4-5; supervisor/audit7; bounded2h30'))
  else:value['allocation']=[row for row in value['allocation'] if row.get('owner')!=OWNER]
  value['updated']=now();save(path,value)

def terminate(active):
 proc=active['process'];directory=active['directory']
 if proc.poll() is None:
  os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=10)
 return cleanup(directory)

def run():
 plan=load();assert not (OUT/'execution.json').exists();store=Path(plan['store']);store.mkdir(exist_ok=False)
 lease(True);os.sched_setaffinity(0,{7});started=time.monotonic();active={};completed=[];queues={lane:[job for job in plan['jobs'] if job['lane']==lane] for lane in (0,1)}
 state=dict(at=now(),status='running',pid=os.getpid(),original_attempt=True,completed=0,active=[],points=0.,futility=False)
 def report():
  state.update(updated_at=now(),completed=len(completed),points=sum(row['score'] for row in completed if row['score'] is not None),active=[a['job']['id'] for a in active.values()],seconds=time.monotonic()-started);save(OUT/'execution.json',state)
 report();stop_new=False;technical=False;unverified_cleanup=[]
 try:
  while active or any(queues.values()):
   if sum(p.stat().st_size for p in store.rglob('*') if p.is_file())>plan['store_max_bytes']:technical=True;state['error']='private working-storage bound';break
   if time.monotonic()-started>=plan['batch_wall_cap']:technical=True;state['error']='batch wall bound';break
   for lane in (0,1):
    if lane not in active and queues[lane] and not stop_new:
     load();job=queues[lane].pop(0);directory=job_dir(plan,job);directory.mkdir(parents=True,exist_ok=False)
     save(directory/'started.json',dict(at=now(),job=job,plan_sha256=sha(OUT/'plan.json')))
     stdout=(directory/'stdout.txt').open('x');stderr=(directory/'stderr.txt').open('x')
     proc=subprocess.Popen(['taskset','-c',plan['lanes'][str(lane)],sys.executable,str(Path(__file__)),'worker','--job',job['id']],cwd=ROOT,env=clean_env(),stdout=stdout,stderr=stderr,start_new_session=True)
     active[lane]=dict(job=job,directory=directory,process=proc,stdout=stdout,stderr=stderr,started=time.monotonic())
     save(directory/'handle.json',dict(pid=proc.pid,at=now(),scope='worker in original tool namespace; not host-PID authorization'))
     report()
    if lane not in active:continue
    running=active[lane];proc=running['process']
    if proc.poll() is None and time.monotonic()-running['started']<=plan['game_wall_cap']:continue
    timed_out=proc.poll() is None
    leftover=terminate(running);unverified_cleanup.extend(leftover);running['stdout'].close();running['stderr'].close();job=running['job'];directory=running['directory']
    if proc.returncode or timed_out or leftover or not (directory/'replay.json').exists():
     result=dict(job=job,score=None,faults=[f'worker exit={proc.returncode}; timeout={timed_out}; cleanup={leftover}'])
    else:
     try:result=inspect_game(plan,job,directory)
     except BaseException as exc:result=dict(job=job,score=None,faults=['replay/clock/protocol inspection: '+repr(exc)])
    result.update(exit_code=proc.returncode,seconds=time.monotonic()-running['started'],ended_at=now());save(directory/'result.json',result);completed.append(result);del active[lane]
    print(json.dumps({k:v for k,v in result.items() if k!='job'}|dict(job=job['id'])),flush=True)
    if result['faults']:technical=True;state['error']='technical/source fault';break
    if futile(completed,16,10):stop_new=True;state['futility']=True
    report()
   if technical:break
   if stop_new and not active:break
   time.sleep(1)
  state['status']='technical_failure' if technical else 'closed_futility' if state['futility'] else 'complete'
 except BaseException as exc:state.update(status='failed',error=repr(exc));raise
 finally:
  try:
   for lane,running in list(active.items()):
    try:leftover=terminate(running)
    except BaseException as exc:leftover=['cleanup exception: '+repr(exc)]
    unverified_cleanup.extend(leftover);running['stdout'].close();running['stderr'].close()
    save(running['directory']/'aborted.json',dict(at=now(),reason='original batch stopped; started attempt is not repeatable',cleanup_unverified=leftover));del active[lane]
   state.update(ended_at=now(),cleanup_unverified=unverified_cleanup);report()
   # Keep all reservations through the independent terminal audit.
   subprocess.run([sys.executable,str(HERE/'review.py')],cwd=ROOT,check=True,timeout=300)
  finally:
   if not unverified_cleanup:lease(False)
 if state['status'] in ('technical_failure','failed'):raise RuntimeError(state.get('error','pilot fault'))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=('run','worker'));parser.add_argument('--job');args=parser.parse_args()
 if args.action=='worker':worker(args.job)
 else:run()
