from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];OUT=ROOT/'astra-submissions/analysis/interaction-prior-20261102';BUILD=HERE/'build'
BASE=HERE.parent/'full-prior-cost-20261102/build-r2/sparse/src'
TEAMS=['Greek Gift','Knight Vision','Strongly Invisible','Decent Chess Bot','Crimson Fog','Instructors','Mist Opportunities','duck','HYPOTHERMIA']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def main():
 os.sched_setaffinity(0,{2,3});OUT.mkdir(exist_ok=False);BUILD.mkdir(exist_ok=False)
 accepted=ROOT/'data/raw/accepted.jsonl';index={r['id']:r for r in map(json.loads,accepted.read_text().splitlines())}
 excluded=set()
 for rel,key in [('deployed-prior-comparison-20261102/plan.json','games'),('full-prior-posterior-20261102/plan.json','games'),('fresh-taxonomy-20261101/cases.json','cases')]:
  excluded.update(r['game'] for r in json.loads((ROOT/'astra-submissions/analysis'/rel).read_text())[key])
 seen=set()
 def seq(r):return hashlib.sha256(' '.join(f['move'] for f in r['frames'][1:]).encode()).hexdigest()
 for gid in sorted(excluded):seen.add(seq(json.loads((ROOT/'data/raw/games'/gid/'replay.json').read_text())))
 games=[];exclusions=[]
 windows={'train':('2026-10-20','2026-11-01',4000),'validation':('2026-11-01','2026-11-01T10:00',300),'test':('2026-11-01T20:00','2026-11-02T02:45',300)}
 for split,(low,high,cap) in windows.items():
  choices=[r for r in index.values() if low<=(r.get('createdAt') or '')<high and r['id'] not in excluded and any(r.get(k) in TEAMS for k in ('white','black'))]
  choices.sort(key=lambda r:hashlib.sha256(('interaction228:'+r['id']).encode()).digest());count=0
  for r in choices:
   p=ROOT/'data/raw/games'/r['id']/'replay.json';rp=json.loads(p.read_text());sig=seq(rp)
   if sig in seen or rp.get('rulesVersion')!='fow-v1':exclusions.append({'game':r['id'],'split':split,'reason':'duplicate sequence' if sig in seen else 'rules'});continue
   seen.add(sig)
   candidates=[ply for ply in range(len(rp['frames'])-1) if rp[('white','black')[ply%2]] in TEAMS]
   if split=='train':candidates=sorted(sorted(candidates,key=lambda p:hashlib.sha256(f"interaction228:{r['id']}:{p}".encode()).digest())[:24])
   games.append({'game':r['id'],'split':split,'white':rp['white'],'black':rp['black'],'created_at':rp['createdAt'],'replay_sha256':sha(p),'sequence_sha256':sig,'selected_plies':candidates,'frames':len(rp['frames'])});count+=1
   if count==cap:break
  assert count==cap or (split=='test' and count>=150),(split,count)
 command=['gcc','-std=c11','-O3','-shared','-fPIC','-pthread','-I'+str(BASE),str(HERE/'bridge.c'),str(BASE/'board.c'),str(BASE/'movemodel.c'),'-lm','-o',str(BUILD/'bridge.so')]
 r=subprocess.run(command,capture_output=True,text=True,timeout=60);(OUT/'build.log').write_text(r.stdout+r.stderr);r.check_returncode()
 deps=[HERE/n for n in ['README.md','bridge.c','freeze.py','learn.py']]+[BUILD/'bridge.so',ROOT/'astra-submissions/experiments/deployed-prior-comparison-20261102/prior.c',ROOT/'astra-submissions/experiments/queen-terminal-backport-20261102/build-r2/base/data/history.bin']+list(BASE.glob('*.[ch]'))
 plan={'created':datetime.now(timezone.utc).isoformat(),'games':games,'excluded_panels':sorted(excluded),'sequence_exclusions':exclusions,'accepted_sha256':sha(accepted),'teams':TEAMS,'windows':windows,'dependencies':{str(p):sha(p) for p in deps},'seed':2281102,'epochs':12,'batch':512,'learning_rate':.03,'ridges':{'linear':[.001],'quadratic':[.001,.01]},'bootstrap_draws':2000,'cores':[2,3],'max_seconds':2700,'gate':{'full_gain':.05,'cheap_gain':.03,'matched_linear_gain':.02,'surprise_min':100,'surprise_gain_min':-.02,'all_move_nonregression':True},'scope':'Conditional move-predictor test on true parent boards. No belief/search integration or strength claim.'}
 save(OUT/'plan.json',plan);print(json.dumps({'games':{s:sum(g['split']==s for g in games) for s in windows},'plan_sha256':sha(OUT/'plan.json')}))
if __name__=='__main__':main()
