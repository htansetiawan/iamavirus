"""Exercise the process boundary against original v37, without arena examples."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('experiment',HERE/'run.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
from learning import rules

plan=json.loads((e.OUT/'plan.json').read_text())
old=json.loads((e.OUT/'pre-review-plan.json').read_text())
assert plan['games']==old['games'], 'pre-review selection must be retained'
for p,v in plan['sources'].items():assert e.sha(e.ROOT/p)==v
state=rules.GameState();frames=[]
for move in [None,'g1f3','b8c6','f3g1','c6b8','g1f3','b8c6','b1c3']:
 if move:state.push(move)
 frames.append(dict(board=state.board.board_string(),white=state.board.observation(0),black=state.board.observation(1),move=move))
replay=dict(frames=frames)
receipts=[]
for side in (0,1):
 a=e.actor(replay,side)
 env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_'))}
 env.update(MIST_THREADS='1',MIST_MODEL_TEMP='2') # table deliberately absent
 run=subprocess.run([sys.executable,str(HERE/'run.py'),'child'],input=json.dumps(a),text=True,capture_output=True,env=env,timeout=30)
 assert run.returncode==0,run.stderr
 result=json.loads(run.stdout);maximum=0
 for row in result['rows']:
  marginals={}
  for arm,record in row['arms'].items():
   probabilities={}
   for k,half,mass in record['states']:probabilities[k]=probabilities.get(k,0)+mass
   marginals[arm]=probabilities
  original=marginals['legacy']
  for arm in ('representative','mixture'):
   candidate=marginals[arm]
   assert candidate.keys()==original.keys()
   error=max(abs(candidate[k]-original[k]) for k in original)
   assert error<2e-6,error
   maximum=max(maximum,error)
 receipts.append(dict(side=side,decisions=len(result['rows']),stop=result['stop'],max_board_probability_error=maximum))
assert e.move_code('e7e8q')==52+(60<<6)+(4<<12)
assert e.move_code('e2e4')==12+(28<<6)+(6<<12)
e.write(e.OUT/'process-preflight.json',dict(passed=True,selection_unchanged=True,receipts=receipts,source_sha256=e.sha(Path(__file__))))
print(json.dumps(dict(passed=True,receipts=receipts)))
