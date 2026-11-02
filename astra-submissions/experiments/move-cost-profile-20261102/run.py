#!/usr/bin/env python3
from datetime import datetime, timezone
import difflib, hashlib, json, os, queue, re, resource, shutil, signal, statistics, subprocess, sys, threading, time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/move-cost-profile-20261102';BUILD=HERE/'build'
PRIOR=ROOT/'astra-submissions/analysis/full-prior-posterior-20261102'
COST=HERE.parent/'full-prior-cost-20261102/build-r2'
BASE=HERE.parent/'queen-terminal-backport-20261102/build-r2/base'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest
from learning.compare_archives import kill_tree
from fresh_taxonomy_gate import protocol, exchange_probe
ARMS=('original','optimized')

def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def unique(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def env():
 e={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_','OMP_','OPENBLAS_','MKL_'))}
 e.update(MIST_TIMING='1',MIST_MAX_SECONDS='10',MIST_MODEL_FULL_BELOW='10000',MIST_THREADS='2',MIST_MODEL_TEMP='2',
          MIST_STOCKFISH=str(BASE/'bin/stockfish'),MIST_HISTORY_TABLE=str(BASE/'data/history.bin'),
          FOW_SEED='2271102',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 return e

def build_call(name,cmd,cwd):
 r=subprocess.run(list(map(str,cmd)),cwd=cwd,capture_output=True,text=True,timeout=60,env=env())
 (OUT/(name+'.stdout')).write_text(r.stdout);(OUT/(name+'.stderr')).write_text(r.stderr)
 unique(OUT/(name+'-receipt.json'),dict(command=list(map(str,cmd)),cwd=str(cwd),exit=r.returncode))
 r.check_returncode()

def instrument(src):
 p=src/'main.c';old=p.read_text();s=old
 needle='        SearchResult r; int ok = 0;';assert s.count(needle)==1
 s=s.replace(needle,'        const double profile_guard_seconds = now_seconds() - guards_started;\n        const double profile_search_at = now_seconds();\n'+needle)
 needle='        char uci[6]; move_to_uci(r.move, uci);';assert s.count(needle)==1
 s=s.replace(needle,'        if (getenv("MIST_TIMING")) fprintf(stderr, "astra_profile: guards %.9f search %.9f budget %.9f view_elapsed %.9f\\n", profile_guard_seconds, now_seconds() - profile_search_at, budget, now_seconds() - view_at);\n'+needle)
 p.write_text(s)
 return ''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),'a/src/main.c','b/src/main.c'))

def prepare():
 os.sched_setaffinity(0,{2,3});OUT.mkdir(exist_ok=False);BUILD.mkdir(exist_ok=False)
 prior=json.loads((PRIOR/'plan.json').read_text());execution=json.loads((PRIOR/'execution.json').read_text());assert execution['status']=='complete'
 for p,h in prior['dependencies'].items():assert sha(Path(p))==h,p
 sizes=[]
 for g in prior['games']:
  rr=[json.loads(l) for l in (PRIOR/(g['game']+'-original.stdout')).read_text().splitlines()]
  eligible=[r for r in rr if r['decision'] and r['ply']//2>=8];assert eligible
  best=min(eligible,key=lambda r:(-r['parents'],r['ply']))
  sizes.append((best['parents'],g['game'],best['ply'],g))
 heavy=sorted(sizes,key=lambda x:(-x[0],x[1]))[:4];used={x[1] for x in heavy}
 ordinary=sorted([x for x in sizes if x[1] not in used],key=lambda x:(abs(x[0]-1000),x[1]))[:4]
 cases=[]
 for n,(parents,gid,ply,g) in enumerate(heavy+ordinary):
  p=ROOT/'data/raw/games'/gid/'replay.json';assert sha(p)==g['replay_sha256'];rp=json.loads(p.read_text());states,errors=ingest.validate_replay(rp);assert not errors
  feed,forced=protocol(rp,ply,g['us']);name=f'{gid}-{ply}';path=OUT/(name+'.input.txt');path.write_text(feed)
  cases.append(dict(name=name,game=gid,ply=ply,side=g['us'],group='large' if n<4 else 'ordinary',prior_parents=parents,forced=forced,input_sha256=sha(path),replay_sha256=sha(p)))
 binaries={};patches={};sources={}
 for arm,folder in [('original','original'),('optimized','sparse')]:
  d=BUILD/arm;d.mkdir();shutil.copytree(COST/folder/'src',d/'src');shutil.copyfile(BASE/'build.sh',d/'build.sh')
  build_call('build-'+arm,['bash','build.sh'],d)
  if arm=='original':assert sha(d/'mist')==sha(BASE/'mist')=='14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd'
  binaries[arm]={'production':sha(d/'mist')};shutil.copytree(d/'src',d/'profile-src');patch=instrument(d/'profile-src');patchpath=OUT/(arm+'-profile.patch');patchpath.write_text(patch);patches[arm]=sha(patchpath)
  command=['gcc','-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=199309L',*[d/'profile-src'/x for x in ['board.c','belief.c','movemodel.c','cfr.c','eval.c','search.c','gtcfr.c','front.c','sfeval.c','main.c']],'-lm','-o',d/'profile']
  build_call('build-profile-'+arm,command,d);binaries[arm]['profile']=sha(d/'profile')
  r=subprocess.run([str(d/'profile')],input='fow\nw 180 2\n'+__import__('learning.rules',fromlist=['Board']).Board().observation(0)+'\n180\n',env={**env(),'MIST_MAX_SECONDS':'.3'},capture_output=True,text=True,timeout=30)
  unique(OUT/(arm+'-smoke.json'),dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr))
  assert r.returncode==0 and r.stdout.startswith('ready\nmove ') and 'astra_profile: ' in r.stderr
  sources.update({str(p):sha(p) for folder in ['src','profile-src'] for p in (d/folder).glob('*.[ch]')})
 deps=[Path(__file__),HERE/'README.md',PRIOR/'plan.json',PRIOR/'summary.json',BASE/'bin/stockfish',BASE/'data/history.bin',ROOT/'learning/compare_archives.py',ROOT/'learning/ingest.py',ROOT/'learning/rules.py',ROOT/'astra-submissions/tools/fresh_taxonomy_gate.py']
 deps += [BUILD/a/n for a in ARMS for n in ['mist','profile']]+[OUT/(c['name']+'.input.txt') for c in cases]
 plan=dict(created=now(),cases=cases,binaries=binaries,profile_patches=patches,dependencies={**sources,**{str(p):sha(p) for p in deps}},
   jobs=[{'case':c['name'],'arm':a} for i,c in enumerate(cases) for a in ARMS[i%2:]+ARMS[:i%2]],cores=[2,3],per_call_seconds=120,parent_seconds=1200,seed=2271102,
   scope='Selected complete-decision cost profile, not a strength gate. True labels joined after process exit; original forced moves only, no opponent true moves.')
 unique(OUT/'plan.json',plan);print(json.dumps({'cases':len(cases),'calls':len(plan['jobs']),'plan_sha256':sha(OUT/'plan.json')}),flush=True)

def limits():resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))

def one(case,arm,plan):
 name=case['name']+'-'+arm;feed=(OUT/(case['name']+'.input.txt')).read_text().splitlines();assert sha(OUT/(case['name']+'.input.txt'))==case['input_sha256']
 blocks=[];block=[]
 for line in feed[2:]:
  block.append(line)
  if len(line)!=64:float(line);blocks.append(block);block=[]
 assert not block and len(blocks)==len(case['forced'])+1
 e=env();e['MIST_FORCE_MOVES']=','.join(case['forced']);start=time.monotonic();end=start+plan['per_call_seconds'];stdout=[];stderr=[];messages=queue.Queue()
 p=subprocess.Popen([str(BUILD/arm/'profile')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,env=e,start_new_session=True,preexec_fn=limits)
 def reader(stream,lines,q=None):
  for line in stream:
   lines.append(line)
   if q is not None:q.put((time.monotonic(),line.rstrip('\n')))
  if q is not None:q.put((time.monotonic(),None))
 threads=[threading.Thread(target=reader,args=(p.stdout,stdout,messages),daemon=True),threading.Thread(target=reader,args=(p.stderr,stderr),daemon=True)]
 for t in threads:t.start()
 error=None;chosen=None;turn_seconds=None
 def get():
  remaining=end-time.monotonic();assert remaining>0,'whole-case timeout'
  return messages.get(timeout=remaining)
 try:
  p.stdin.write('\n'.join(feed[:2])+'\n');p.stdin.flush();_,ready=get();assert ready=='ready',ready
  for i,lines in enumerate(blocks):
   before=time.monotonic();p.stdin.write('\n'.join(lines)+'\n');p.stdin.flush();arrived,line=get();assert line and re.fullmatch(r'move [a-h][1-8][a-h][1-8][nbrq]?',line),line
   if i<len(case['forced']):assert line[5:]==case['forced'][i]
   else:chosen=line[5:];turn_seconds=arrived-before
  p.stdin.close();p.wait(timeout=max(.01,min(10,end-time.monotonic())))
 except BaseException as ex:
  error=f'{type(ex).__name__}: {ex}';kill_tree(p.pid);p.wait()
 finally:
  for t in threads:t.join(timeout=2)
 text=''.join(stderr);out=''.join(stdout)
 for suffix,value in [('stdout',out),('stderr',text)]:
  with (OUT/(name+'.'+suffix)).open('x') as f:f.write(value)
 row=dict(case=case['name'],arm=arm,move=chosen,error=error,exit=p.returncode,elapsed=time.monotonic()-start,turn_seconds=turn_seconds,stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(text.encode()).hexdigest())
 unique(OUT/(name+'-receipt.json'),row)
 assert error is None and p.returncode==0 and chosen,row
 line=[x for x in text.splitlines() if x.startswith('astra_profile: ')];assert len(line)==1
 fields=line[0].split()[1:];row['profile']={fields[i]:float(fields[i+1]) for i in range(0,len(fields),2)}
 summary=[x for x in text.splitlines() if x.startswith('mist: n=')];assert len(summary)==1
 row['search_log']=summary[0];m=re.search(r'\|P\|=(\d+).*nodes=(\d+)',summary[0]);assert m;row.update(worlds=int(m[1]),nodes=int(m[2]),thinnings=text.count('before the update'),rebuilds=text.count('belief empty, rebuilt'))
 updates=re.findall(r'mist: timing (own|opp) update ([0-9.]+) s \|P\| (\d+) -> (\d+)',text)
 row['last_updates']=updates[-2:];row['all_update_seconds_rounded']=sum(float(x[1]) for x in updates)
 rp=ROOT/'data/raw/games'/case['game']/'replay.json';assert sha(rp)==case['replay_sha256'];states,errors=ingest.validate_replay(json.loads(rp.read_text()));assert not errors
 row['label']=exchange_probe(states[case['ply']],chosen);assert row['label']['legal']
 unique(OUT/(name+'-result.json'),row);return row

def run():
 plan=json.loads((OUT/'plan.json').read_text());os.sched_setaffinity(0,set(plan['cores']))
 for p,h in plan['dependencies'].items():assert sha(Path(p))==h,p
 state=dict(started=now(),status='running',completed=0,plan_sha256=sha(OUT/'plan.json'));unique(OUT/'execution.json',state)
 def expire(*_):raise TimeoutError('parent wall cap')
 signal.signal(signal.SIGALRM,expire);signal.alarm(plan['parent_seconds']);rows=[]
 try:
  for j in plan['jobs']:
   case=next(c for c in plan['cases'] if c['name']==j['case']);r=one(case,j['arm'],plan);rows.append(r);state['completed']+=1;save(OUT/'execution.json',state)
   print(json.dumps({k:r[k] for k in ['case','arm','turn_seconds','profile','worlds','nodes','move','label']}),flush=True)
  pairs=[]
  for c in plan['cases']:
   a,b=(next(r for r in rows if r['case']==c['name'] and r['arm']==arm) for arm in ARMS)
   pairs.append(dict(case=c['name'],group=c['group'],turn_ratio=b['turn_seconds']/a['turn_seconds'],node_ratio=b['nodes']/a['nodes'] if a['nodes'] else None,guard_ratio=b['profile']['guards']/a['profile']['guards'] if a['profile']['guards'] else None,worlds=[a['worlds'],b['worlds']],fatal=[a['label']['fatal'],b['label']['fatal']]))
  report=dict(cases=8,calls=16,pairs=pairs,median_turn_ratio=statistics.median(p['turn_ratio'] for p in pairs),median_node_ratio=statistics.median(p['node_ratio'] for p in pairs if p['node_ratio'] is not None),
   totals={a:{k:sum(r['profile'][k] for r in rows if r['arm']==a) for k in ['guards','search','budget']} for a in ARMS},
   king_losses={a:sum(r['label']['fatal'] for r in rows if r['arm']==a) for a in ARMS},scope=plan['scope'],decision='cost_profile_complete_no_promotion')
  unique(OUT/'summary.json',report);print(json.dumps(report,indent=2));state['status']='complete'
 except BaseException as ex:state.update(status='failed',error=f'{type(ex).__name__}: {ex}');raise
 finally:signal.alarm(0);state['ended']=now();save(OUT/'execution.json',state)

if __name__=='__main__':
 assert len(sys.argv)==2 and sys.argv[1] in ('prepare','run');globals()[sys.argv[1]]()
