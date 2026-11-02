"""Actor-input-only collector, followed by a separately invoked truth audit."""
import ctypes as C
from datetime import datetime,timezone
import gzip,hashlib,json,math,os,signal,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/dual-belief-20261102'
sys.path.insert(0,str(ROOT))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def library(name):
 l=C.CDLL(str(HERE/'build'/name/'filter.so'));p=C.c_void_p;z=C.c_size_t;i=C.c_int;s=C.c_char_p;u=C.c_ulonglong;d=C.c_double
 for fn,args,restype in [('db_init',[i,i],None),('db_new',[i,z],p),('db_free',[p],None),('db_step',[p,C.c_ushort,i,s],z),('db_count',[p],z),('db_overflowed',[p],i),('db_export',[p,C.POINTER(u),C.POINTER(u),C.POINTER(C.c_float),C.POINTER(C.c_float),C.POINTER(i),s],None),('db_risks',[p,s,C.POINTER(C.c_ushort),C.POINTER(d),C.POINTER(d),C.POINTER(d),C.POINTER(d)],i),('db_key',[s,i,u,i],u)]:
  getattr(l,fn).argtypes=args;getattr(l,fn).restype=restype
 l.db_init(1,2);return l
def move_code(m):
 sq=lambda x:ord(x[0])-97+8*(int(x[1])-1)
 return sq(m[:2])|(sq(m[2:4])<<6)|(('nbrq'.index(m[4])+1 if len(m)==5 else 6)<<12)
def move_text(m):
 sq=lambda n:chr(97+n%8)+str(1+n//8)
 promo=m>>12
 return sq(m&63)+sq((m>>6)&63)+('nbrq'[promo-1] if 1<=promo<=4 else '')
def actor(r,side):
 frames=r['frames'][:-1][:65]
 return dict(side=side,views=[f[('white','black')[side]] for f in frames],own={str(p):frames[p]['move'] for p in range(1,len(frames)) if (p-1)%2==side})
def export(l,b):
 n=l.db_count(b);keys=(C.c_ulonglong*n)();hist=(C.c_ulonglong*n)();sharp=(C.c_float*n)();flat=(C.c_float*n)();half=(C.c_int*n)();boards=C.create_string_buffer(65*n)
 l.db_export(b,keys,hist,sharp,flat,half,boards)
 return dict(keys=list(map(str,keys)),hist=list(map(str,hist)),sharp=list(sharp),flat=list(flat),half=list(half),boards=[boards.raw[65*i:65*i+64].decode() for i in range(n)])
def risks(l,b,view):
 moves=(C.c_ushort*256)();vectors=[(C.c_double*256)() for _ in range(4)]
 n=l.db_risks(b,view.encode(),moves,*vectors)
 return dict(moves=[move_text(moves[i]) for i in range(n)],**{name:list(v)[:n] for name,v in zip(('king_flat','king_sharp','queen_flat','queen_sharp'),vectors)})
def child():
 os.sched_setaffinity(0,{0,1});a=json.load(sys.stdin)
 libs={n:library(n) for n in ('base','candidate')};beliefs={n:l.db_new(a['side'],200000) for n,l in libs.items()};times={n:0. for n in libs};rows=[];reason='end-of-prefix'
 try:
  for ply,view in enumerate(a['views']):
   stop=False
   for name,l in libs.items():
    if ply:
     own=str(ply) in a['own'];start=time.process_time();l.db_step(beliefs[name],move_code(a['own'][str(ply)]) if own else 0,own,view.encode());times[name]+=time.process_time()-start
    n=l.db_count(beliefs[name]);assert n>0 and not l.db_overflowed(beliefs[name]),(name,ply,n)
    if n>4096:stop=True
   if stop:reason='state-bound';break
   snapshots={n:export(l,beliefs[n]) for n,l in libs.items()}
   for k in ('keys','hist','sharp','half','boards'):assert snapshots['base'][k]==snapshots['candidate'][k],(ply,k)
   if ply%2!=a['side']:continue
   r={n:risks(l,beliefs[n],view) for n,l in libs.items()}
   for key in ('moves','king_sharp','queen_sharp'):assert r['base'][key]==r['candidate'][key],(ply,key)
   rows.append(dict(ply=ply,worlds=snapshots['candidate'],flat_approx=snapshots['base']['flat'],risks=r,cpu=times.copy()))
  print(json.dumps(dict(rows=rows,stop=reason,last_attempted_ply=ply,cpu=times)))
 finally:
  for name,l in libs.items():l.db_free(beliefs[name])
def prepare():
 assert json.loads((OUT/'native-checks.json').read_text())['passed']
 previous=json.loads((ROOT/'astra-submissions/analysis/history-mixture-20261102/plan.json').read_text())
 sources=[*HERE.glob('*.py'),*HERE.glob('*.c'),HERE/'README.md',OUT/'native-checks.json',OUT/'build.json']
 pins={str(p.relative_to(ROOT)):sha(p) for p in sources}
 pins.update(json.loads((OUT/'build.json').read_text())['pins'])
 write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),games=previous['games'],sources=pins,seconds_per_game=60,seconds_total=900,selection='24 reused development games from experiment250, no new outcome selection'))
 print(json.dumps(dict(prepared=True,games=len(previous['games']))))
def collect():
 plan=json.loads((OUT/'plan.json').read_text())
 for path,digest in plan['sources'].items():assert sha(ROOT/path)==digest,path
 os.sched_setaffinity(0,{0,1});(OUT/'games').mkdir(exist_ok=False);start=time.monotonic()
 receipt=dict(state='running',started_at=datetime.now(timezone.utc).isoformat(),plan_sha256=sha(OUT/'plan.json'),games=[])
 write(OUT/'receipt.json',receipt)
 try:
  for case in plan['games']:
   left=plan['seconds_total']-(time.monotonic()-start);assert left>0
   assert sha(case['path'])==case['sha256'];r=json.loads(Path(case['path']).read_text());a=actor(r,case['side'])
   import copy
   hidden=copy.deepcopy(r);hidden['result']='unknown'
   for p,f in enumerate(hidden['frames']):
    f['board']='X'*64;f[('black','white')[case['side']]]='X'*64
    if p and (p-1)%2!=case['side']:f['move']='zzzz'
   assert actor(hidden,case['side'])==a
   env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_'))}
   env.update(MIST_HISTORY_TABLE=str(HERE/'build/base/data/history.bin'),MIST_MODEL_TEMP='2',MIST_THREADS='2')
   p=subprocess.Popen([sys.executable,str(Path(__file__)),'child'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,start_new_session=True)
   error=None
   try:stdout,stderr=p.communicate(json.dumps(a),timeout=min(left,plan['seconds_per_game']))
   except BaseException as e:
    error=repr(e);os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate()
   prefix=OUT/'games'/case['game'];prefix.with_suffix('.stderr').write_text(stderr)
   with gzip.open(prefix.with_suffix('.json.gz'),'wt') as f:f.write(stdout)
   row=dict(game=case['game'],returncode=p.returncode,error=error,actor_sha256=hashlib.sha256(json.dumps(a).encode()).hexdigest(),output_sha256=sha(prefix.with_suffix('.json.gz')))
   receipt['games'].append(row);assert not error and p.returncode==0,row
   data=json.loads(stdout);print(json.dumps(dict(game=case['game'],decisions=len(data['rows']),stop=data['stop'])),flush=True)
  receipt['state']='completed'
 except BaseException as e:receipt['state']='failed';receipt['error']=repr(e);raise
 finally:
  receipt['seconds']=time.monotonic()-start;receipt['ended_at']=datetime.now(timezone.utc).isoformat()
  (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':globals()[sys.argv[1]]()
