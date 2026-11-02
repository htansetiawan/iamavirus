"""Freeze and collect the structural diagnostic; no search or truth labels."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,os,signal,subprocess,sys,time,zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/history-partition-20261102'
PREV=ROOT/'astra-submissions/analysis/history-mixture-20261102'
SOURCE=HERE.parent/'history-mixture-20261102/build/src'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,value):
 with Path(p).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def code(m):
 square=lambda s:ord(s[0])-97+8*(int(s[1])-1)
 return square(m[:2])|(square(m[2:4])<<6)|(('nbrq'.index(m[4])+1 if len(m)==5 else 6)<<12)
def actor(r,side,ply):
 lines=[f'{side} {ply}',r['frames'][0][('white','black')[side]]]
 for p in range(1,ply+1):
  own=(p-1)%2==side;move=code(r['frames'][p]['move']) if own else 0
  lines.append(f"{int(own)} {move} {r['frames'][p][('white','black')[side]]}")
 return '\n'.join(lines)+'\n'

def prepare():
 os.sched_setaffinity(0,{0,1});(HERE/'build').mkdir(exist_ok=True)
 archive=ROOT/'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
 assert sha(archive)=='41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c'
 with zipfile.ZipFile(archive) as z:
  for p in SOURCE.iterdir():
   if p.is_file():assert p.read_bytes()==z.read('src/'+p.name)
 native=json.loads((PREV/'native-checks.json').read_text())
 for p,s in native['pins'].items():assert sha(ROOT/p)==s
 common=['gcc','-std=c11','-D_POSIX_C_SOURCE=199309L','-pthread','-I',str(SOURCE)]
 compile_records=[]
 for target,inputs in [('dump',[HERE/'dump.c',SOURCE/'board.c',SOURCE/'movemodel.c']),('test',[HERE/'test_equivalence.c',SOURCE/'cfr.c'])]:
  for sanitized in (False,True):
   name=target+('-san' if sanitized else '')
   cmd=common+(['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'] if sanitized else ['-O2'])+[str(p) for p in inputs]+['-lm','-o',str(HERE/'build'/name)]
   result=subprocess.run(cmd,capture_output=True,text=True);compile_records.append(dict(command=cmd,exit_code=result.returncode,stderr=result.stderr));assert result.returncode==0,result.stderr
 test=subprocess.run([str(HERE/'build/test')],capture_output=True,text=True,timeout=60);assert test.returncode==0,test.stderr
 write(OUT/'native-preflight.json',dict(compile=compile_records,test=json.loads(test.stdout)))
 oldplan=json.loads((PREV/'plan.json').read_text());chosen=[]
 for case in oldplan['games']:
  saved=json.loads((PREV/'games'/f"{case['game']}.json").read_text())
  row=max(saved['rows'],key=lambda r:(r['arms']['mixture']['stats'][3],r['ply']))
  chosen.append(dict(**case,ply=row['ply'],nonrepresentative_mass=row['arms']['mixture']['stats'][3],old_case_sha256=sha(PREV/'games'/f"{case['game']}.json")))
 pins={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'dump.c',HERE/'test_equivalence.c',HERE/'README.md',HERE/'build/dump',HERE/'build/test',HERE.parent/'history-mixture-20261102/filter.c',SOURCE/'cfr.c',SOURCE/'belief.c',SOURCE/'board.c',SOURCE/'movemodel.c',SOURCE.parent/'data/history.bin']}
 write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),cases=chosen,sources=pins,seeds=[251,252,253,254],samples=32,seconds=900,case_seconds=60,
   selection='Within each existing 250 game, maximum actor-derived nonrepresentative history mass; later ply breaks ties',
   next_action='If every history identifies one physical root and copies preserve continuation partitions, no search/match integration follows from replication alone.'))
 print(json.dumps(dict(prepared=True,cases=len(chosen),solver_test=json.loads(test.stdout))))

def collect():
 import copy
 plan=json.loads((OUT/'plan.json').read_text())
 for p,s in plan['sources'].items():assert sha(ROOT/p)==s,p
 assert json.loads((OUT/'host-sanitizers.json').read_text())['passed']
 os.sched_setaffinity(0,{0,1});(OUT/'cases').mkdir(exist_ok=False)
 started=time.monotonic();receipt=dict(state='running',startedAt=datetime.now(timezone.utc).isoformat(),plan_sha256=sha(OUT/'plan.json'),completed=[],failures=[])
 write(OUT/'receipt.json',receipt)
 def deadline(signum,frame):raise TimeoutError('batch wall limit')
 signal.signal(signal.SIGALRM,deadline);signal.setitimer(signal.ITIMER_REAL,plan['seconds'])
 try:
  for case in plan['cases']:
   assert sha(case['path'])==case['sha256'];r=json.loads(Path(case['path']).read_text());text=actor(r,case['side'],case['ply']);redacted=copy.deepcopy(r)
   for p,frame in enumerate(redacted['frames']):
    frame['board']='X'*64;frame[('black','white')[case['side']]]='X'*64
    if p and (p-1)%2!=case['side']:frame['move']='zzzz'
   redacted['result']='unknown';assert actor(redacted,case['side'],case['ply'])==text
   env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_'))}
   env.update(MIST_THREADS='1',MIST_MODEL_TEMP='2',MIST_HISTORY_TABLE=str(SOURCE.parent/'data/history.bin'))
   process=subprocess.Popen([str(HERE/'build/dump')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,start_new_session=True)
   try:stdout,stderr=process.communicate(text,timeout=plan['case_seconds'])
   except BaseException:
    os.killpg(process.pid,signal.SIGKILL);stdout,stderr=process.communicate();(OUT/'cases'/f"{case['game']}.stderr").write_text(stderr);raise
   (OUT/'cases'/f"{case['game']}.stderr").write_text(stderr)
   assert process.returncode==0,stderr
   data=json.loads(stdout);assert data['states']
   path=OUT/'cases'/f"{case['game']}.json.gz"
   with gzip.open(path,'wt') as f:f.write(stdout)
   write(OUT/'cases'/f"{case['game']}-receipt.json",dict(case=case,returncode=process.returncode,payload_sha256=hashlib.sha256(text.encode()).hexdigest(),output_sha256=sha(path),stderr_sha256=sha(OUT/'cases'/f"{case['game']}.stderr")))
   receipt['completed'].append(case['game']);(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
   print(json.dumps(dict(game=case['game'],completed=len(receipt['completed']),states=len(data['states']),histories=sum(len(s['histories']) for s in data['states']))),flush=True)
  receipt['state']='completed'
 except BaseException as exc:receipt.update(state='failed');receipt['failures'].append(repr(exc));raise
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);receipt.update(endedAt=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-started);(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__':{'prepare':prepare,'collect':collect}[sys.argv[1]]()
