from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,math,os,resource,signal,subprocess,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];OUT=ROOT/'astra-submissions/analysis/sparse-cfr-20261102';OLD=ROOT/'astra-submissions/analysis/solver-workspace-20261102';BUILD=HERE/'build'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def clean_env():return {k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_','OMP_','OPENBLAS_','MKL_'))}
def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def preflight():
 env=clean_env();env.update(ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1');records=[]
 for name in ('check-opt','check-san','check-negative'):
  p=BUILD/name;r=subprocess.run([str(p)],capture_output=True,text=True,timeout=120,env=env,preexec_fn=no_core)
  row=dict(command=str(p),binary_sha256=sha(p),exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr);records.append(row)
  if name=='check-negative':assert r.returncode!=0 and 'mismatch slot=' in r.stderr,'negative control did not expose omitted prediction clearing'
  elif r.returncode:
   write(OUT/'native-failure.json',records);raise RuntimeError(row)
  else:assert 'stale predictions cleared:' in r.stderr and int(r.stderr.split('stale predictions cleared:')[1].split()[0])>0
 write(OUT/'native-checks.json',dict(passed=True,negative_control_detected=True,records=records));print(json.dumps(dict(passed=True,negative_control_detected=True,positive_results=[json.loads(r['stdout']) for r in records[:2]])))
def prepare():
 assert json.loads((OUT/'native-checks.json').read_text())['passed']
 old=json.loads((OLD/'receipt.json').read_text());assert old['state']=='completed'
 trees=[j for j in old['jobs'] if j['stage']=='benchmark'];assert len(trees)==8
 for row in trees:assert sha(row['tree'])==row['raw_sha256']
 sources=[*HERE.glob('*.py'),*HERE.glob('*.c'),*HERE.glob('*.h'),HERE/'README.md',OUT/'build.json',OUT/'native-checks.json',BUILD/'check-opt',BUILD/'check-san',OLD/'receipt.json',OLD/'tree-review.json']
 write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),trees=trees,sources={str(p):sha(p) for p in sources},build=json.loads((OUT/'build.json').read_text())['pins'],iterations=200,per_tree_seconds=120,total_seconds=1200,cores=[0,1],min_speedup=1.2,scope='Reuse exact 253 trees; no fresh capture or policy outcomes; optimized solver vs original v37'))
 print(json.dumps(dict(prepared=True,trees=len(trees))))
def collect():
 os.sched_setaffinity(0,{0,1});plan=json.loads((OUT/'plan.json').read_text())
 for p,h in plan['sources'].items():assert sha(p)==h,p
 for p,h in plan['build'].items():assert sha(ROOT/p)==h,p
 started=time.monotonic();receipt=dict(state='running',started_at=datetime.now(timezone.utc).isoformat(),plan_sha256=sha(OUT/'plan.json'),jobs=[]);write(OUT/'receipt.json',receipt)
 try:
  for index,tree in enumerate(plan['trees']):
   assert sha(tree['tree'])==tree['raw_sha256']
   names=['check-opt']+(['check-san'] if index==0 else [])
   for name in names:
    left=plan['total_seconds']-(time.monotonic()-started);assert left>0
    steps=plan['iterations'] if name=='check-opt' else 5;env=clean_env();env.update(ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
    p=subprocess.Popen([str(BUILD/name),'trace',tree['tree'],str(steps)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,start_new_session=True,preexec_fn=no_core);error=None
    try:stdout,stderr=p.communicate(timeout=min(left,plan['per_tree_seconds']))
    except BaseException as e:error=repr(e);os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate()
    rec=dict(case=tree['case'],binary=name,exit_code=p.returncode,error=error,stdout=stdout,stderr=stderr,tree_sha256=tree['raw_sha256']);write(OUT/(tree['case']+'-'+name+'.json'),rec);receipt['jobs'].append({k:rec[k] for k in ('case','binary','exit_code','error','tree_sha256')})
    assert p.returncode==0 and not error,rec
    result=json.loads(stdout);assert result['identical'];print(json.dumps(dict(case=tree['case'],binary=name,**result)),flush=True)
  receipt['state']='completed'
 except BaseException as e:receipt['state']='failed';receipt['error']=repr(e);raise
 finally:
  receipt['seconds']=time.monotonic()-started;receipt['ended_at']=datetime.now(timezone.utc).isoformat();(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':globals()[sys.argv[1]]()
