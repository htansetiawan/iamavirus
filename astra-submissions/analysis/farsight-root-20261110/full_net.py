"""Exploratory course-only recorded-net census AFTER the actor has exited."""
from datetime import datetime,timezone
import importlib.util,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
p=ROOT/'astra-submissions/experiments/farsight-root-20261110/audit.py'
spec=importlib.util.spec_from_file_location('course_review',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
out=Path(__file__).resolve().parent;plan=m.read(out/'plan.json');folder=Path(plan['spool'])/'actor'
assert m.read(out/'audit.json')['passed']
pop=m.read(folder/'population.json');worlds=pop['worlds'];top=max(w['logw'] for w in worlds)
weights=[math.exp(w['logw']-top) for w in worlds];den=math.fsum(weights)
forced=[];admissible=[];reply_legal=[]
for w in worlds:
 b=m.world_board(w);root=m.ref.chess.Move.from_uci('a2a1r');reply=m.ref.chess.Move.from_uci('f7g8')
 assert root in m.ref.fow_moves(b);b.push(root)
 if m.mover_lost(b) or reply not in m.ref.fow_moves(b):continue
 reply_legal.append(w['index']);b.push(reply)
 if m.mover_lost(b):continue
 admissible.append(w['index']);safe=False
 for move in m.ref.fow_moves(b):
  q=b.copy();q.push(move)
  if not m.mover_lost(q):safe=True;break
 if not safe:forced.append(w['index'])
share=lambda ids:math.fsum(weights[i] for i in ids)/den
result=dict(at=datetime.now(timezone.utc).isoformat(),scope='Exploratory post-actor oracle label of the recorded promotion/Qg8 net across all retained worlds. No new actor or policy/weight change.',worlds=len(worlds),reply_legal_worlds=len(reply_legal),admissible_reply_worlds=len(admissible),forced_net_indices=forced,forced_net_share=share(forced),sampled_forced_net_share=math.fsum(s['weight'] for s in pop['samples'] if s['index'] in forced),source_hashes=dict(population=m.sha(folder/'population.json'),course_review=m.sha(p),script=m.sha(__file__)),limitation='The historical opponent reply is a post-game oracle label. A multi-ply net event is not one-step king risk, and this selected population is not global calibration.')
with (out/'full-net.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result,indent=2))
