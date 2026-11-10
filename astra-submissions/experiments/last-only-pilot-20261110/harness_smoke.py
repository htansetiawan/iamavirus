"""Exercise turn control and inspect a known full replay before the real pilot."""
from datetime import datetime,timezone
import json,os,sys
from pathlib import Path
from pilot import HERE,OUT,ROOT,referee,save,inspect_game,cleanup,run_controlled
from learning import ingest


def main():
 os.sched_setaffinity(0,{0,1});directory=HERE/'build/harness-smoke';directory.mkdir(exist_ok=False)
 ref=referee();argv=[sys.executable,str(HERE/'fixture_bot.py')];game=run_controlled(ref,argv,argv,base=180,increment=2,max_plies=1000,match_id='lastonly-harness-fixture',white_name='script fixture',black_name='script fixture',registry_path=directory/'processes.json',retain_stderr=True)
 save(directory/'replay.json',game)
 assert game['result']=='0-1' and game['reason']=='King capturable' and len(game['frames'])==12
 states,errors=ingest.validate_replay(game);assert not errors and len(states)==12
 job=dict(id=game['id'],side='black');inspection=inspect_game({},job,directory)
 # Scripted bots must fail the production SF-initialization requirement.
 assert inspection['faults']==['missing SF startup: white','missing SF startup: black'] and inspection['score'] is None
 assert not cleanup(directory)
 result=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,fixture_only=True,plies=11,course_and_native_frames=12,turn_isolation_checked=True,production_inspector_rejects_nonproduction_bots=True,owned_process_cleanup_verified=True,no_real_pilot_game_started=True,no_strength_claim=True)
 save(OUT/'harness-smoke.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
