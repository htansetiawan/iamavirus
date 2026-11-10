"""Independent course prefix and own-input verification; no online sources."""
from collections import Counter
import importlib.util,json,sys
from pathlib import Path
from common import ROOT,OUT,sha,save,now
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref


def validate(plan,case):
 path=Path(case['source']);assert sha(path)==case['source_sha256'];replay=json.loads(path.read_text())
 assert replay['id']==case['game'] and replay.get('rulesVersion')=='fow-v1'
 side=case['side'];key=('white','black')[side];control=replay['timeControl']
 expected=['fow',f"{'w' if side==0 else 'b'} {control['baseSeconds']} {control['incrementSeconds']}"]
 forced=[];board=ref.FowBoard();history=Counter({ref.position_key(board):1})
 for ply,frame in enumerate(replay['frames'][:case['ply']+1]):
  assert frame['ply']==ply
  if ply:
   move=ref.chess.Move.from_uci(frame['move']);assert move in ref.fow_moves(board);board.push(move);history[ref.position_key(board)]+=1
  actual=ref.make_frame(board,frame['clocks']);assert all(actual[k]==frame[k] for k in ('board','white','black'))
  expected.append(frame[key])
  if ply%2==side:
   expected.append(str(frame['clocks'][side]))
   if ply<case['ply']:forced.append(replay['frames'][ply+1]['move'])
 assert board.turn==(side==0) and not ref.outcome(board,history)
 feed=Path(plan['feeds'])/(case['name']+'.input.txt');assert sha(feed)==case['input_sha256']
 actual=feed.read_text().splitlines();assert len(actual)==len(expected) and forced==case['forced']
 for a,b in zip(actual,expected):
  if a!=b:
   if a.startswith(('w ','b ')):
    aa,bb=a.split(),b.split();assert aa[0]==bb[0] and list(map(float,aa[1:]))==list(map(float,bb[1:]))
   else:assert float(a)==float(b)
 return board,history,case['ply']+1


def main():
 plan=json.loads((OUT/'plan.json').read_text());frames=0
 for case in plan['cases']:frames+=validate(plan,case)[2]
 save(OUT/'source-review.json',dict(at=now(),passed=True,cases=8,frames=frames,actor_inputs='Exact own observations, own clocks and forced own prefix moves only. No replay truth/opponent input passed to the executable.',no_api=True))
 print(json.dumps(dict(source_review=True,cases=8,frames=frames)))

if __name__=='__main__':main()
