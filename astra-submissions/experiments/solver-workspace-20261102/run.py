from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,math,os,signal,subprocess,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];OUT=ROOT/'astra-submissions/analysis/solver-workspace-20261102'
PRIOR=ROOT/'astra-submissions/analysis/move-cost-profile-20261102';BUILD=HERE/'build'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def clean_env():return {k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_','OMP_','OPENBLAS_','MKL_'))}
def preflight():
 env=clean_env();env.update(ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1');records=[]
 for name in ('check-opt','check-san'):
  p=BUILD/name;r=subprocess.run([str(p)],capture_output=True,text=True,timeout=120,env=env)
  row=dict(command=str(p),binary_sha256=sha(p),exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr);records.append(row)
  if r.returncode:write(OUT/'native-failure.json',records);raise RuntimeError(row)
 write(OUT/'native-checks.json',dict(passed=True,records=records));print(json.dumps(dict(passed=True,results=[json.loads(r['stdout']) for r in records])))
def prepare():
 assert json.loads((OUT/'native-checks.json').read_text())['passed']
 old=json.loads((PRIOR/'plan.json').read_text());cases=old['cases']
 sf=ROOT/'astra-submissions/experiments/queen-terminal-backport-20261102/build-r2/base/bin/stockfish';assert sf.is_file()
 store=Path((ROOT/'data/store').read_text().strip());assert store.is_dir()
 dest=store/'astra/solver-workspace-20261102';dest.mkdir(parents=True,exist_ok=False)
 sources=[*HERE.glob('*.py'),*HERE.glob('*.c'),*HERE.glob('*.h'),HERE/'README.md',OUT/'build.json',OUT/'native-checks.json',BUILD/'dump-engine',BUILD/'check-opt',BUILD/'check-san',BUILD/'base/data/history.bin',sf]
 sources+=[PRIOR/(c['name']+'.input.txt') for c in cases]
 sources+=list((BUILD/'diagnostic').glob('*.[ch]'))
 write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),cases=cases,sources={str(p):sha(p) for p in sources},source_build=json.loads((OUT/'build.json').read_text())['pins'],store=str(dest),stockfish=str(sf),search_seconds=2.5,iterations=200,per_case_seconds=120,total_seconds=1200,seed=2531102,cores=[0,1],scope='Eight cost-selected reused decisions; same frozen tree and starting solver arrays; speed measurement only'))
 print(json.dumps(dict(prepared=True,cases=len(cases),store=str(dest))))
def collect():
 os.sched_setaffinity(0,{0,1});plan=json.loads((OUT/'plan.json').read_text())
 for path,digest in plan['sources'].items():assert sha(path)==digest,path
 for path,digest in plan['source_build'].items():assert sha(ROOT/path)==digest,path
 start=time.monotonic();receipt=dict(state='running',started_at=datetime.now(timezone.utc).isoformat(),plan_sha256=sha(OUT/'plan.json'),jobs=[]);write(OUT/'receipt.json',receipt)
 def execute(command,env,stdin):
  left=plan['total_seconds']-(time.monotonic()-start);assert left>0
  p=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,start_new_session=True)
  error=None
  try:out,err=p.communicate(stdin,timeout=min(left,plan['per_case_seconds']))
  except BaseException as e:
   error=repr(e);os.killpg(p.pid,signal.SIGKILL);out,err=p.communicate()
  return dict(exit_code=p.returncode,error=error,stdout=out,stderr=err)
 try:
  for case in plan['cases']:
   name=case['name'];raw=Path(plan['store'])/(name+'.tree');env=clean_env();env.update(MIST_MAX_SECONDS=str(plan['search_seconds']),MIST_FORCE_MOVES=','.join(case['forced']),MIST_STOCKFISH=plan['stockfish'],MIST_HISTORY_TABLE=str(BUILD/'base/data/history.bin'),MIST_THREADS='2',FOW_SEED=str(plan['seed']),ASTRA_SOLVER_TREE=str(raw))
   feed=PRIOR/(name+'.input.txt');assert sha(feed)==case['input_sha256']
   row=execute([str(BUILD/'dump-engine')],env,feed.read_text());write(OUT/(name+'-capture.json'),row);receipt['jobs'].append(dict(case=name,stage='capture',exit_code=row['exit_code'],error=row['error']))
   assert not row['error'] and row['exit_code']==0,row
   assert raw.is_file() and raw.stat().st_size<150_000_000
   moves=[line[5:] for line in row['stdout'].splitlines() if line.startswith('move ')];assert moves[:-1]==case['forced'] and len(moves)==len(case['forced'])+1
   if case==plan['cases'][0]:
    env=clean_env();env.update(ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
    checked=execute([str(BUILD/'check-san'),'trace',str(raw),'5'],env,None);write(OUT/(name+'-load-sanitizer.json'),checked);assert not checked['error'] and checked['exit_code']==0,checked
   row=execute([str(BUILD/'check-opt'),'trace',str(raw),str(plan['iterations'])],clean_env(),None);write(OUT/(name+'-benchmark.json'),row);receipt['jobs'].append(dict(case=name,stage='benchmark',exit_code=row['exit_code'],error=row['error']))
   assert not row['error'] and row['exit_code']==0,row
   data=json.loads(row['stdout']);assert data['identical']
   compressed=raw.with_suffix('.tree.gz');compressed.write_bytes(gzip.compress(raw.read_bytes(),mtime=0));receipt['jobs'][-1].update(raw_sha256=sha(raw),compressed_sha256=sha(compressed),raw_bytes=raw.stat().st_size,compressed_bytes=compressed.stat().st_size,tree=str(raw))
   print(json.dumps(dict(case=name,**data)),flush=True)
  receipt['state']='completed'
 except BaseException as e:receipt['state']='failed';receipt['error']=repr(e);raise
 finally:
  receipt['seconds']=time.monotonic()-start;receipt['ended_at']=datetime.now(timezone.utc).isoformat();(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':globals()[sys.argv[1]]()
