"""Terminal-only independent source, label and cost/gate regeneration."""
from collections import Counter
import importlib.util,json,math,statistics
from pathlib import Path
from common import ROOT,HERE,OUT,sha,save,now,pins
from source import validate,ref


def main():
 plan=json.loads((OUT/'plan.json').read_text());pins(plan);execution=json.loads((OUT/'execution.json').read_text())
 assert execution['status']=='complete' and execution['restarted'] is False and len(execution['calls'])==16
 source=json.loads((OUT/'source-review.json').read_text());assert source['passed'] and source['frames']==273
 spec=importlib.util.spec_from_file_location('cost_exchange_oracle',ROOT/'astra-submissions/experiments/persistent-response-20261101/review.py')
 oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
 store=Path(plan['store']);case_results=[];frames=choices=transitions=0;totals={a:Counter() for a in range(3)};timing_rows=0;fixed_rows=0
 orders=[[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]]
 for case in plan['cases']:
  board,history,count=validate(plan,case);frames+=count;observed={};case_rows={}
  for phase in ('preflight','measure'):
   prefix=store/f"{phase}-{case['index']:02d}";stdout=prefix.with_suffix('.stdout').read_text();stderr=prefix.with_suffix('.stderr').read_text()
   receipt=next(r for r in execution['calls'] if r['case']==case['name'] and r['phase']==phase)
   for suffix,key in [('.stdout','stdout_sha256'),('.stderr','stderr_sha256'),('.rows.json','rows_sha256')]:assert sha(prefix.with_suffix(suffix))==receipt[key]
   rows=[json.loads(line.split(' ',1)[1]) for line in stderr.splitlines() if line.startswith('astra-three ')]
   assert rows==json.loads(prefix.with_suffix('.rows.json').read_text())
   assert len(rows)==(3 if phase=='preflight' else 18)==receipt['searches']
   fixed_rows+=len(rows) if phase=='preflight' else 0;timing_rows+=len(rows) if phase=='measure' else 0
   keys=('budget','seed','population','belief','mask','avoid_count','samples','our_moves')
   assert all(tuple(r[k] for k in keys)==tuple(rows[0][k] for k in keys) for r in rows)
   actual=[line[5:] for line in stdout.splitlines() if line.startswith('move ')];assert stdout.splitlines()[0]=='ready'
   assert actual[:-1]==case['forced'] and actual[-1]==next(r['move'] for r in rows if r['arm']==0)
   for block in range(1 if phase=='preflight' else 6):
    group=[r for r in rows if r['block']==block];assert [r['step'] for r in group]==[0,1,2]
    assert [r['arm'] for r in group]==orders[(block+case['index'])%6]
   for row in rows:
    assert row['sf_restarts']==0 and row['sf_calls']>0 and row['nodes']>0 and row['iterations']>0
    assert math.isfinite(row['seconds']) and row['seconds']>0 and row['budget']>0 and 0<=row['probability']<=1
    if row['move'] not in observed:
     label,n=oracle.probe(board,history,row['move'],case['side']);observed[row['move']]=label;transitions+=n;choices+=1
    if phase=='measure':
     label=observed[row['move']];totals[row['arm']]['fatal']+=label['fatal'];totals[row['arm']]['material_ge2']+=(label['exchange_loss'] or 0)>=2;totals[row['arm']]['front_replacements']+=row['move']!=row['raw_move']
   if phase=='preflight':
    identity=('move','raw_move','value','probability','nodes','iterations','samples','our_moves','infosets')
    assert all(tuple(r[k] for k in identity)==tuple(rows[0][k] for k in identity) for r in rows)
   case_rows[phase]=rows
  ratios_lb=[];ratios_lc=[];ratios_cb=[]
  for block in range(6):
   group={r['arm']:r for r in case_rows['measure'] if r['block']==block}
   ratios_lb.append(group[2]['nodes']/group[0]['nodes']);ratios_lc.append(group[2]['nodes']/group[1]['nodes']);ratios_cb.append(group[1]['nodes']/group[0]['nodes'])
  case_results.append(dict(case=case['name'],last_vs_original=statistics.median(ratios_lb),last_vs_cached=statistics.median(ratios_lc),cached_vs_original=statistics.median(ratios_cb),search_budget=case_rows['measure'][0]['budget'],node_ratios_by_block=dict(last_original=ratios_lb,last_cached=ratios_lc,cached_original=ratios_cb),population=case_rows['measure'][0]['population']))
 assert frames==273 and fixed_rows==24 and timing_rows==144
 median_lb=statistics.median(row['last_vs_original'] for row in case_results);median_lc=statistics.median(row['last_vs_cached'] for row in case_results)
 positive=sum(row['last_vs_original']>=1 for row in case_results)
 gates=dict(original_gain=median_lb>=plan['gates']['median_last_original'],incremental_gain=median_lc>=plan['gates']['median_last_cached'],case_consistency=positive>=plan['gates']['nonregressing_cases'],king_safeguard=totals[2]['fatal']<=totals[0]['fatal']+1,material_safeguard=totals[2]['material_ge2']<=totals[0]['material_ge2']+2,complete_source_runtime_review=True)
 for name in ('prospective-quiet-teacher-20261110','move-metadata-recovery-20261110'):
  other=json.loads((ROOT/'astra-submissions/analysis'/name/'plan.json').read_text())
  for path,value in other['dependencies'].items():assert sha(path)==value,path
 decision='Separate real-clock playing-pilot design permitted; no strength or release claim.' if all(gates.values()) else 'Close this cost configuration; no control-arm substitution, tuning retry, playing pilot or release.'
 result=dict(at=now(),gate_pass=all(gates.values()),gates=gates,cases=case_results,median_last_original=median_lb,median_last_cached=median_lc,nonregressing_cases=positive,totals={str(k):dict(v) for k,v in totals.items()},source_frames=frames,fixed_work_searches=fixed_rows,measured_searches=timing_rows,distinct_choices=choices,tactical_transitions=transitions,all_effective_choices_course_legal=True,pins_unchanged=len(plan['dependencies']),teacher_and_metadata_pins_unchanged=True,plan_sha256=sha(OUT/'plan.json'),execution_sha256=sha(OUT/'execution.json'),decision=decision,scope='Eight old cost-selected replay roots, shared belief/mask/sampling seed per case, fresh own SF worker pool per call, six within-case orders. Search elapsed excludes SF process startup and fingerprints. Cold-worker diagnostic, not on-policy arena timing or an Elo estimate; repeated choices are not independent games. Cached control is diagnostic only.254old failure stays failed. Raw logs/rows stay private.')
 save(OUT/'result.json',result);print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))

if __name__=='__main__':main()
