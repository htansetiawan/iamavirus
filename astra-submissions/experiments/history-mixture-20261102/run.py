"""Separate permitted-input native filtering from post-exit truth scoring."""
from collections import defaultdict
import ctypes as C
from datetime import datetime,timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];OUT=ROOT/'astra-submissions/analysis/history-mixture-20261102'
sys.path.insert(0,str(ROOT))
from learning import ingest

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(text):return hashlib.sha256(text.encode()).hexdigest()
def write(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')

def libraries():
 h=C.CDLL(str(HERE/'build/filter.so'));l=C.CDLL(str(HERE/'build/legacy.so'))
 p=C.c_void_p;u=C.c_ulonglong;i=C.c_int;z=C.c_size_t;d=C.c_double;s=C.c_char_p
 specs=[(h,'hm_load',[],None),(h,'hm_new',[i,i],p),(h,'hm_free',[p],None),
        (h,'hm_step',[p,C.c_ushort,i,s],z),(h,'hm_stats',[p,C.POINTER(d)],None),
        (h,'hm_export',[p,C.POINTER(u),C.POINTER(i),C.POINTER(u),C.POINTER(d),z],z),
        (l,'lg_load',[],None),(l,'lg_new',[i],p),(l,'lg_free',[p],None),
        (l,'lg_step',[p,C.c_ushort,i,s],z),(l,'lg_count',[p],z),(l,'lg_capped',[p],i),
        (l,'lg_export',[p,C.POINTER(u),C.POINTER(i),C.POINTER(d)],None),
        (l,'lg_truth_key',[s,i,u,i],u)]
 for lib,name,args,restype in specs:getattr(lib,name).argtypes=args;getattr(lib,name).restype=restype
 h.hm_load();l.lg_load();return h,l

def move_code(m):
 square=lambda s:ord(s[0])-97+8*(int(s[1])-1)
 promo='nbrq'.index(m[4])+1 if len(m)==5 else 6
 return square(m[:2])|(square(m[2:4])<<6)|(promo<<12)

def actor(r,side):
 # The final completed-game frame has no next decision. Do not treat game
 # termination as a continuing-play observation for either filter.
 frames=r['frames'][:-1][:65]
 return dict(side=side,views=[f[('white','black')[side]] for f in frames],
             own_moves={str(p):frames[p]['move'] for p in range(1,len(frames)) if (p-1)%2==side})

def child():
 os.sched_setaffinity(0,{0,1});a=json.load(sys.stdin);h,l=libraries();side=a['side']
 handles={'legacy':l.lg_new(side),'representative':h.hm_new(side,0),'mixture':h.hm_new(side,1)}
 times={name:0. for name in handles};rows=[];stop='end-of-prefix'
 try:
  for ply,view in enumerate(a['views']):
   limit=False
   for name,ptr in handles.items():
    if ply:
     own=str(ply) in a['own_moves'];m=move_code(a['own_moves'][str(ply)]) if own else 0
     start=time.process_time();n=(l.lg_step if name=='legacy' else h.hm_step)(ptr,m,own,view.encode());times[name]+=time.process_time()-start
     if n==C.c_size_t(-1).value:limit=True;stop='candidate-bound'
    if name=='legacy':
     n=l.lg_count(ptr);stats=[n,n,1,0,0,0,0,0]
     if l.lg_capped(ptr):limit=True;stop='legacy-cap'
    else:
     st=(C.c_double*8)();h.hm_stats(ptr,st);stats=list(st)
    if stats[0]>4096 or stats[1]>131072:limit=True;stop='state/history-bound'
   if limit:break
   if ply%2!=side:continue
   snapshot={'ply':ply,'arms':{}}
   for name,ptr in handles.items():
    if name=='legacy':
     n=l.lg_count(ptr);keys=(C.c_ulonglong*n)();halves=(C.c_int*n)();masses=(C.c_double*n)();l.lg_export(ptr,keys,halves,masses);stats=[n,n,1,0,0,0,0,0]
    else:
     st=(C.c_double*8)();h.hm_stats(ptr,st);stats=list(st);n=int(stats[1])
     keys=(C.c_ulonglong*n)();halves=(C.c_int*n)();masses=(C.c_double*n)();hist=(C.c_ulonglong*n)()
     assert h.hm_export(ptr,keys,halves,hist,masses,n)==n
    groups=defaultdict(float)
    for k,half,mass in zip(keys,halves,masses):groups[(k,half)]+=mass
    total=sum(groups.values())
    snapshot['arms'][name]=dict(states=[[str(k),half,v/total] for (k,half),v in sorted(groups.items())] if total else [],stats=stats,cpu_seconds=times[name])
   rows.append(snapshot)
  print(json.dumps(dict(rows=rows,stop=stop,last_attempted_ply=ply,cpu_seconds=times)))
 finally:
  for name,ptr in handles.items():(l.lg_free if name=='legacy' else h.hm_free)(ptr)

def prepare():
 assert json.loads((OUT/'native-checks.json').read_text())['passed']
 src=HERE/'build/src'
 cmd=['gcc','-O2','-std=c11','-shared','-fPIC','-pthread','-D_POSIX_C_SOURCE=199309L','-I',str(src),str(HERE/'legacy.c'),str(src/'board.c'),str(src/'movemodel.c'),'-lm','-o',str(HERE/'build/legacy.so')]
 subprocess.run(cmd,check=True)
 old=json.loads((ROOT/'astra-submissions/analysis/hidden-king-complement-20261102/plan.json').read_text());opponents=old['opponents']
 accepted=(ROOT/'data/raw/accepted.jsonl').read_bytes();byid={r['id']:r for r in map(json.loads,accepted.splitlines())}
 eligible=[]
 for r in byid.values():
  if not '2026-11-02T05:28'<=(r.get('createdAt') or '')<'2026-11-03':continue
  side=next((s for s in (0,1) if r.get(('white','black')[s])=='IAmAVirus' and r.get(('whiteVersion','blackVersion')[s])==37),None)
  if side is not None and r.get(('black','white')[side]) in opponents:eligible.append((r['createdAt'],r['id'],side))
 seen=set();groups={0:[],1:[]}
 for at,gid,side in sorted(eligible):
  p=ROOT/f'data/raw/games/{gid}/replay.json';r=json.loads(p.read_text());signature=digest(' '.join(str(f['move']) for f in r['frames'][1:]))
  if signature in seen:continue
  seen.add(signature);groups[side].append(dict(game=gid,side=side,path=str(p),sha256=sha(p),sequence_sha256=signature))
 chosen=[]
 for side in (0,1):
  assert len(groups[side])>=12;chosen+=sorted(groups[side],key=lambda r:digest('250-history:'+r['game']))[:12]
 pins={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'legacy.c',HERE/'filter.c',HERE/'check.c',HERE/'README.md',OUT/'native-checks.json',HERE/'build/filter.so',HERE/'build/legacy.so',HERE/'build/data/history.bin']}
 write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),games=chosen,sources=pins,archive_sha256=hashlib.sha256(accepted).hexdigest(),selection='12 per colour; salted ID after sequence dedup; no outcome selection',max_seconds=900,game_seconds=60))
 print(json.dumps(dict(prepared=True,games=len(chosen))),flush=True)

def collect():
 plan=json.loads((OUT/'plan.json').read_text())
 for p,v in plan['sources'].items():assert sha(ROOT/p)==v,p
 os.sched_setaffinity(0,{0,1});started=time.monotonic();record=dict(state='running',startedAt=datetime.now(timezone.utc).isoformat(),plan_sha256=sha(OUT/'plan.json'),completed=[],failures=[])
 write(OUT/'receipt.json',record);(OUT/'games').mkdir(exist_ok=False)
 def deadline(signum,frame):raise TimeoutError('batch wall bound')
 signal.signal(signal.SIGALRM,deadline);signal.setitimer(signal.ITIMER_REAL,plan['max_seconds'])
 try:
  for case in plan['games']:
   left=plan['max_seconds']-(time.monotonic()-started)
   if left<=0:raise TimeoutError('batch bound')
   assert sha(case['path'])==case['sha256'];r=json.loads(Path(case['path']).read_text());a=actor(r,case['side'])
   # Replay hidden fields are never transmitted to the native child process.
   import copy
   redacted=copy.deepcopy(r)
   for ply,f in enumerate(redacted['frames']):
    f['board']='X'*64;f[('black','white')[case['side']]]='X'*64
    if ply and (ply-1)%2!=case['side']:f['move']='zzzz'
   redacted['result']='unknown';assert actor(redacted,case['side'])==a
   env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_'))}
   env.update(MIST_THREADS='1',MIST_HISTORY_TABLE=str(HERE/'build/data/history.bin'),MIST_MODEL_TEMP='2')
   proc=subprocess.Popen([sys.executable,str(Path(__file__)),'child'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,start_new_session=True)
   try:stdout,stderr=proc.communicate(json.dumps(a),timeout=min(left,plan['game_seconds']))
   except BaseException:
    os.killpg(proc.pid,signal.SIGKILL);stdout,stderr=proc.communicate();(OUT/'games'/f"{case['game']}.stderr").write_text(stderr);raise
   (OUT/'games'/f"{case['game']}.stderr").write_text(stderr)
   assert proc.returncode==0,stderr
   with gzip.open(OUT/'games'/f"{case['game']}-raw.json.gz",'wt') as f:f.write(stdout)
   output=json.loads(stdout)
   # Join true-board labels only after the unlabelled native process exits.
   states,errors=ingest.validate_replay(r);assert not errors,errors
   _,lib=libraries();rows=[]
   for row in output['rows']:
    b=states[row['ply']].board;key=str(lib.lg_truth_key(b.board_string().encode(),b.side,b.castling,b.en_passant))
    labelled=dict(ply=row['ply'],arms={})
    for name,arm in row['arms'].items():
     board_p=sum(v for k,half,v in arm['states'] if k==key);full_p=sum(v for k,half,v in arm['states'] if k==key and half==b.halfmove_clock)
     labelled['arms'][name]=dict(board_probability=board_p,full_probability=full_p,stats=arm['stats'],cpu_seconds=arm['cpu_seconds'])
    rows.append(labelled)
   write(OUT/'games'/f"{case['game']}.json",dict(case=case,rows=rows,stop=output['stop'],last_attempted_ply=output['last_attempted_ply'],cpu_seconds=output['cpu_seconds'],returncode=proc.returncode,actor_sha256=digest(json.dumps(a)),raw_sha256=sha(OUT/'games'/f"{case['game']}-raw.json.gz")))
   record['completed'].append(case['game']);(OUT/'receipt.json').write_text(json.dumps(record,indent=2)+'\n')
   print(json.dumps(dict(game=case['game'],completed=len(record['completed']),decisions=len(rows),stop=output['stop'])),flush=True)
  record['state']='completed'
 except BaseException as e:record.update(state='failed');record['failures'].append(repr(e));raise
 finally:
  signal.setitimer(signal.ITIMER_REAL,0)
  record.update(endedAt=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-started);(OUT/'receipt.json').write_text(json.dumps(record,indent=2)+'\n')

if __name__=='__main__':{'prepare':prepare,'collect':collect,'child':child}[sys.argv[1]]()
