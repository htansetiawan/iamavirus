"""Post-hoc attribution only; does not alter selection or rerun filters."""
from pathlib import Path
import gzip,json,math,statistics

out=Path(__file__).resolve().parent
plan=json.loads((out/'plan.json').read_text());rows=[]
for case in plan['games']:
 gid=case['game'];raw=json.load(gzip.open(out/'games'/f'{gid}-raw.json.gz','rt'))
 labelled=json.loads((out/'games'/f'{gid}.json').read_text());gains=[];best=None
 for r,l in zip(raw['rows'],labelled['rows']):
  distributions=[]
  for name in ('representative','mixture'):
   d={}
   for key,half,mass in r['arms'][name]['states']:d[key]=d.get(key,0)+mass
   distributions.append(d)
  a,b=distributions;tv=sum(abs(a.get(k,0)-b.get(k,0)) for k in a.keys()|b.keys())/2
  gain=math.log(max(l['arms']['mixture']['board_probability'],1e-12)/max(l['arms']['representative']['board_probability'],1e-12));gains.append(gain)
  if best is None or tv>best['tv']:
   best=dict(ply=r['ply'],tv=tv,truth_log_gain=gain,histories_per_board=r['arms']['mixture']['stats'][1]/r['arms']['mixture']['stats'][0])
 rows.append(dict(game=gid,mean_truth_log_gain=statistics.mean(gains),largest_distribution_change=best))
with (out/'case-effects.json').open('x') as f:
 json.dump(dict(posthoc=True,not_an_acceptance_rule=True,by_gain=sorted(rows,key=lambda r:r['mean_truth_log_gain'])),f,indent=2);f.write('\n')
