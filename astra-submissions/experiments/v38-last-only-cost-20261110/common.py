from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
import signal,subprocess,time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/v38-last-only-cost-20261110'

def now():return datetime.now(timezone.utc).isoformat()
def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,value):
 path=Path(path);temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temporary.replace(path)
def pins(plan):
 for path,value in plan['dependencies'].items():assert sha(path)==value,path

def environment(plan,case,fixed=False):
 e={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
 ship=Path(plan['ship']);e.update(MIST_STOCKFISH=str(ship/'bin/stockfish'),MIST_HISTORY_TABLE=str(ship/'data/history.bin'),ASTRA_SF_ALLCHILDREN='1',MIST_SAMPLES='32',MIST_THREADS='2',MIST_SF_WORKERS='2',MIST_ASYNC='0',MIST_MAX_SECONDS='10',FOW_SEED=str(plan['seed']),MIST_FORCE_MOVES=','.join(case['forced']),ASTRA_COST_BLOCKS='1' if fixed else '6',ASTRA_COST_ROTATE=str(case['index']%6))
 if fixed:e['ASTRA_FIXED_ROUNDS']='4'
 return e

def records(stderr):return [json.loads(line.removeprefix('astra-three ')) for line in stderr.splitlines() if line.startswith('astra-three ')]
def process(plan,case,fixed):
 feed=Path(plan['feeds'])/(case['name']+'.input.txt');assert sha(feed)==case['input_sha256']
 start=time.monotonic();child=subprocess.Popen([plan['binary']],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=environment(plan,case,fixed),cwd=ROOT,start_new_session=True)
 prefix=Path(plan['store'])/f"{'preflight' if fixed else 'measure'}-{case['index']:02d}"
 try:stdout,stderr=child.communicate(feed.read_text(),timeout=plan['per_case_seconds'])
 except BaseException:
  os.killpg(child.pid,signal.SIGKILL);stdout,stderr=child.communicate()
  prefix.with_suffix('.stdout').write_text(stdout);prefix.with_suffix('.stderr').write_text(stderr);raise
 prefix.with_suffix('.stdout').write_text(stdout);prefix.with_suffix('.stderr').write_text(stderr)
 assert child.returncode==0,(case['name'],child.returncode,stderr[-2000:])
 rows=records(stderr);expected=3 if fixed else 18;assert len(rows)==expected
 constant=('budget','seed','population','belief','mask','avoid_count','samples','our_moves')
 assert all(tuple(r[k] for k in constant)==tuple(rows[0][k] for k in constant) for r in rows)
 assert all(r['sf_restarts']==0 and r['sf_calls']>0 and r['nodes']>0 and r['iterations']>0 for r in rows)
 output=[line[5:] for line in stdout.splitlines() if line.startswith('move ')]
 assert stdout.splitlines()[0]=='ready' and len(output)==len(case['forced'])+1
 assert output[:-1]==case['forced'] and output[-1]==next(r['move'] for r in rows if r['arm']==0)
 if fixed:
  keys=('move','raw_move','value','probability','nodes','iterations','samples','our_moves','infosets')
  assert all(tuple(r[k] for k in keys)==tuple(rows[0][k] for k in keys) for r in rows),'fixed-work engine mismatch'
 return stdout,stderr,rows,time.monotonic()-start
