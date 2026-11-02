from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,os
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
root=Path('/home/henrytan/git/iamavirus');out=root/'astra-submissions/analysis/full-prior-posterior-20261102'
plan=json.loads((out/'plan.json').read_text());result=json.loads((out/'summary.json').read_text());execution=json.loads((out/'execution.json').read_text())
assert execution['status']=='complete' and execution['completed']==72
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p,h in plan['dependencies'].items():assert sha(Path(p))==h,p
cells={};manifest={}
for job in plan['jobs']:
 n=job['name'];receipt=json.loads((out/(n+'-receipt.json')).read_text());assert receipt['returncode']==0 and receipt['error'] is None
 for typ in ['stdout','stderr']:
  p=out/(n+'.'+typ);assert sha(p)==receipt[typ+'_sha256'];manifest[str(p.relative_to(root))]=sha(p)
 rr=[json.loads(line) for line in (out/(n+'.stdout')).read_text().splitlines()]
 assert all(r['matches']>0 or r['ever_capped'] for r in rr)
 cells[job['game'],job['arm']]=rr
primary=[];times={a:[] for a in ['original','optimized','full']};large=[];pergame=[]
for game in plan['games']:
 g=game['game'];arms={a:cells[g,a] for a in times}
 for a,rr in arms.items():
  assert len(rr)==game['validated_frames']-2
  assert [r['ply'] for r in rr]==list(range(1,len(rr)+1))
  times[a]+= [r['update_seconds'] for r in rr]
 for x,y in zip(arms['original'],arms['optimized']):assert {k:v for k,v in x.items() if k!='update_seconds'}=={k:v for k,v in y.items() if k!='update_seconds'}
 if any(r['parents']>10000 and r['decision'] for r in arms['original']):large.append(g)
 rr=[{'game':g,'team':game['team'],'original':x,'full':y} for x,y in zip(arms['original'],arms['full']) if x['decision'] and x['ply']//2>=8]
 primary+=rr
 pergame.append({'game':g,'team':game['team'],'decisions':len(rr),'gain':math.fsum(math.log(max(r['full']['truth_share'],1e-12)/max(r['original']['truth_share'],1e-12)) for r in rr), 'support_original':sum(r['original']['matches']>0 for r in rr),'support_full':sum(r['full']['matches']>0 for r in rr)})
computed={'primary_decisions':len(primary),'large_regime_games':len(large),'support':{a:sum(r[a]['matches']>0 for r in primary) for a in ('original','full')},'mean_truth_nll':{a:-math.fsum(math.log(max(r[a]['truth_share'],1e-12)) for r in primary)/len(primary) for a in ('original','full')},'gain_nats':math.fsum(g['gain'] for g in pergame)/len(primary)}
for k in ['primary_decisions','large_regime_games','support']:assert computed[k]==result[k],k
assert math.isclose(computed['gain_nats'],result['gain_nats'],rel_tol=1e-12,abs_tol=1e-12)
for a in ('original','full'):assert math.isclose(computed['mean_truth_nll'][a],result['mean_truth_nll'][a],rel_tol=1e-12)
groups={t:[g for g in pergame if g['team']==t] for t in dict.fromkeys(g['team'] for g in pergame)}
rng=np.random.default_rng(plan['bootstrap_seed']);boot=[]
for _ in range(2000):
 picked=[rows[i] for rows in groups.values() for i in rng.integers(0,len(rows),len(rows))]
 boot.append(math.fsum(g['gain'] for g in picked)/sum(g['decisions'] for g in picked))
assert np.allclose(np.quantile(boot,[.025,.975]),result['interval95'],rtol=1e-12,atol=1e-12)
for a,t in times.items():
 for key,val in [('total',sum(t)),('p95',float(np.quantile(t,.95))),('maximum',max(t))]:assert math.isclose(val,result['update_seconds'][a][key],rel_tol=1e-12), (a,key)
gate=plan['gate'];t=result['update_seconds']
conds={'support':computed['support']['full']>=computed['support']['original'],'gain':computed['gain_nats']>=gate['minimum_gain_nats'],'interval':result['interval95'][0]>gate['lower_ci_above'],'large_regime':len(large)>=gate['minimum_large_regime_games'],'total_time':t['full']['total']<=gate['total_time_ratio_at_most']*t['original']['total'],'p95_time':t['full']['p95']<=max(gate['p95_floor_seconds'],gate['p95_ratio_at_most']*t['original']['p95'])}
assert conds==result['conditions']
assert result['decision']==('timed_decision_design_allowed' if all(conds.values()) else 'close_full_prior_configuration')
r={'at':datetime.now(timezone.utc).isoformat(),'reviewer':'Independent aggregation script, same agent; no new engine calls','validated_jobs':72,'validated_update_rows':sum(map(len,cells.values())),'exact_ordinary_parity':True,'computed':computed,'per_game':pergame,'large_regime_ids':large,'conditions':conds,'decision':result['decision'],'output_manifest':manifest,'scope':'Held-out-by-named-panel capped-posterior development result, no recovery/clock/search. Does not measure king-risk calibration or Elo.'}
with (out/'independent-review.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps({k:r[k] for k in ['validated_jobs','validated_update_rows','computed','conditions','decision']}))
