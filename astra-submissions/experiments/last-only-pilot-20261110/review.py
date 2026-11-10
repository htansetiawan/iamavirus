"""Independent terminal C++ replay check, score regeneration and owned cleanup."""
from collections import defaultdict
from datetime import datetime,timezone
import json,sys
from pathlib import Path
from pilot import ROOT,HERE,OUT,load,sha,job_dir,score,futile,referee,save
sys.path.insert(0,str(ROOT))
from learning import ingest,_native
from local_turn_control import group_members


def main():
 plan=load();execution=json.loads((OUT/'execution.json').read_text());rows=[];started=[];aborted=[];unstarted=[];frames=0;problems=[];pairs=defaultdict(dict)
 # Use an immutable already-tested validator snapshot. Do not rebuild a
 # shared library or depend on another agent's C++ source modification time.
 assert _native._library is None
 _native.ensure_built=lambda verbose=True: HERE/'build/native-validator.so'
 assert execution['status'] in ('complete','closed_futility','technical_failure','failed')
 for job in plan['jobs']:
  directory=job_dir(plan,job)
  if not (directory/'started.json').exists():unstarted.append(job['id']);continue
  start=json.loads((directory/'started.json').read_text());assert start['job']==job and start['plan_sha256']==sha(OUT/'plan.json');started.append(job['id'])
  if (directory/'aborted.json').exists():
   abort=json.loads((directory/'aborted.json').read_text());aborted.append(dict(job=job['id'],record=abort))
   if abort['cleanup_unverified']:problems.append(job['id']+': unverified cleanup')
  if (directory/'result.json').exists():
   row=json.loads((directory/'result.json').read_text());assert row['job']==job;rows.append(row)
   if row['faults']:problems.append(dict(job=job['id'],faults=row['faults']));continue
   assert row['exit_code']==0 and row['score']==score(row['result'],job['side'])
   replay=directory/'replay.json';assert sha(replay)==row['replay_sha256'];game=json.loads(replay.read_text())
   # Independent native C++ rules/observation checker, separate from producer's course walk.
   states,errors=ingest.validate_replay(game);assert not errors,(job['id'],errors);assert len(states)==row['validated_frames']==row['plies']+1;frames+=len(states)
   native=states[-1].outcome()
   if native:assert tuple(native)==(row['result'],row['reason'])
   else:assert row['plies']==1000 and row['result']=='1/2-1/2' and row['reason']=='Move limit reached'
   assert not game.get('failedSide') and not game.get('warnings')
   assert all(t>=0 for frame in game['frames'] for t in frame['clocks'])
   controls=game['localTurnControl']['controls'];assert len(controls)==2
   assert all(any(event['op']=='freeze' and event.get('members',0)>0 for event in control['events']) and any(event['op']=='resume' for event in control['events']) for control in controls)
   pairs[job['pair']][job['side']]=row['score']
  registry=directory/'processes.json'
  if registry.exists():
   for record in json.loads(registry.read_text()):
    alive=[r for r in group_members(record['leader']['pgid']) if r['state'] not in ('Z','X')]
    assert not alive,('recorded group still live',job['id'],alive)
  else:problems.append(job['id']+': missing process registry')
 assert len(rows)==execution['completed'] and sum(r['score'] for r in rows if r['score'] is not None)==execution['points']
 valid=[r for r in rows if not r['faults']];scores=[r['score'] for r in valid];points=sum(scores)
 passed=execution['status']=='complete' and len(valid)==16 and not problems and not aborted and points>=10
 if execution['status']=='closed_futility':assert not problems and futile(valid,16,10)
 if passed:decision='Separate qualified-opponent gate design permitted; no release or Elo claim.'
 elif execution['status'] in ('complete','closed_futility') and not problems:decision='Close fixed playing configuration; no extra seed, game, threshold or candidate promotion.'
 else:decision='Technical/incomplete execution; no promotion or replay of started games.'
 for name in ('prospective-quiet-teacher-20261110','move-metadata-recovery-20261110'):
  other=json.loads((ROOT/'astra-submissions/analysis'/name/'plan.json').read_text())
  for path,value in other['dependencies'].items():assert sha(path)==value,path
 result=dict(at=datetime.now(timezone.utc).isoformat(),gate_pass=passed,status=execution['status'],games=len(valid),planned=16,started=len(started),unstarted=unstarted,aborted=aborted,completed=len(rows),wins=scores.count(1),draws=scores.count(.5),losses=scores.count(0),points=points,remaining_best_possible=points+16-len(valid),faults=problems,native_frames_verified=frames,pair_points={str(k):sum(v.values()) for k,v in pairs.items()},complete_pairs=sum(len(v)==2 for v in pairs.values()),candidate_sha256=plan['candidate_sha256'],baseline_sha256=plan['baseline_sha256'],plan_sha256=sha(OUT/'plan.json'),execution_sha256=sha(OUT/'execution.json'),teacher_and_metadata_pins_unchanged=True,decision=decision,scope='Small paired180+2local development pilot against exact activev38, not the actual duck/Instructors or a causal arena Elo estimate. No release/version claim. Started/aborted attempts remain immutable; raw replays/logs private.')
 save(OUT/'result.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
