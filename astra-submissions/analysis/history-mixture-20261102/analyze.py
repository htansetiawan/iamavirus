"""Read-only audit and descriptive report of the frozen three-filter diagnostic.

Truth joins use the independent course referee and a Python state hash; no
filter is rerun and no stored model probability is modified.
"""
from collections import Counter,defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics as S
import sys
import numpy as np

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
KIT=Path.home()/'git/fow-starter';sys.path.insert(0,str(KIT))
import chess
import referee

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')

MASK=(1<<64)-1
seed=20261009
def splitmix():
 global seed
 seed=(seed+0x9E3779B97F4A7C15)&MASK;z=seed
 z=((z^(z>>30))*0xBF58476D1CE4E5B9)&MASK
 z=((z^(z>>27))*0x94D049BB133111EB)&MASK
 return z^(z>>31)
PIECES=[[[splitmix() for _ in range(64)] for _ in range(6)] for _ in range(2)]
SIDE=splitmix();CASTLE=[];EP=[]
for _ in range(64):CASTLE.append(splitmix());EP.append(splitmix())
def state_key(board):
 value=SIDE if board.turn==chess.BLACK else 0
 for sq,p in board.piece_map().items():value^=PIECES[0 if p.color else 1][p.piece_type-1][sq]
 for sq in chess.scan_forward(board.castling_rights):value^=CASTLE[sq]
 if board.ep_square is not None:value^=EP[board.ep_square]
 return str(value|1)

def marginal(states):
 out=defaultdict(float)
 for key,half,mass in states:out[key]+=mass
 return out

def main():
 plan=json.loads((OUT/'plan.json').read_text());receipt=json.loads((OUT/'receipt.json').read_text())
 assert receipt['state']=='completed' and not receipt['failures']
 assert sha(OUT/'plan.json')==receipt['plan_sha256']
 assert receipt['completed']==[c['game'] for c in plan['games']]
 assert Counter(c['side'] for c in plan['games'])=={0:12,1:12}
 assert len({c['sequence_sha256'] for c in plan['games']})==24
 for p,v in plan['sources'].items():assert sha(ROOT/p)==v,p
 names=('legacy','representative','mixture');entries=[];pergame=[];frames_checked=0;raw_states=0
 for case in plan['games']:
  gid=case['game'];r=json.loads(Path(case['path']).read_text());assert sha(case['path'])==case['sha256']
  labelled=json.loads((OUT/'games'/f'{gid}.json').read_text())
  assert labelled['case']==case and labelled['returncode']==0
  rp=OUT/'games'/f'{gid}-raw.json.gz';assert sha(rp)==labelled['raw_sha256']
  with gzip.open(rp,'rt') as f:raw=json.load(f)
  assert len(raw['rows'])==len(labelled['rows'])
  assert raw['stop']==labelled['stop'] and raw['cpu_seconds']==labelled['cpu_seconds']
  actor=dict(side=case['side'],views=[f[('white','black')[case['side']]] for f in r['frames'][:-1][:65]],
             own_moves={str(p):r['frames'][p]['move'] for p in range(1,min(len(r['frames'])-1,65)) if (p-1)%2==case['side']})
  assert hashlib.sha256(json.dumps(actor).encode()).hexdigest()==labelled['actor_sha256']
  board=referee.FowBoard();states=[];repetitions=Counter({referee.position_key(board):1})
  for p,frame in enumerate(r['frames']):
   if p:
    assert referee.outcome(board,repetitions) is None
    move=chess.Move.from_uci(frame['move']);assert move in referee.fow_moves(board)
    board.push(move);repetitions[referee.position_key(board)]+=1
   text=''.join(board.piece_at(sq).symbol() if board.piece_at(sq) else '-' for sq in range(64))
   assert text==frame['board']
   assert referee.observation(board,chess.WHITE)==frame['white']
   assert referee.observation(board,chess.BLACK)==frame['black']
   states.append((state_key(board),board.halfmove_clock));frames_checked+=1
  game_rows=[]
  for i,(row,saved) in enumerate(zip(raw['rows'],labelled['rows'])):
   assert row['ply']==saved['ply']==case['side']+2*i
   key,clock=states[row['ply']];record=dict(game=gid,side=case['side'],ply=row['ply'],arms={})
   distributions={}
   for name in names:
    arm=row['arms'][name];obs=saved['arms'][name];st=arm['stats'];distribution=marginal(arm['states']);distributions[name]=distribution
    assert st==obs['stats'] and arm['cpu_seconds']==obs['cpu_seconds']
    assert 0<=st[0]<=4096 and st[0]<=st[1]<=131072
    assert all(math.isfinite(p) and p>=0 for p in distribution.values())
    assert not distribution or abs(sum(distribution.values())-1)<1e-10
    assert len({(k,h) for k,h,p in arm['states']})==len(arm['states'])
    probability=distribution.get(key,0);full=sum(p for k,h,p in arm['states'] if k==key and h==clock)
    assert abs(probability-obs['board_probability'])<1e-12
    assert abs(full-obs['full_probability'])<1e-12
    record['arms'][name]=dict(nll=-math.log(max(probability,1e-12)),truth_mass=probability,support=probability>0,
       full_support=full>0,full_nll=-math.log(max(full,1e-12)),states=st[0],histories=st[1],max_histories_per_state=st[2],
       nonrepresentative_mass=st[3],allocated_state_bytes=st[4],histories_per_state=st[1]/st[0] if st[0] else 0,
       table_lookups=st[6],table_hits=st[7],cpu_seconds=arm['cpu_seconds'])
    raw_states+=len(arm['states'])
   a=distributions['mixture'];b=distributions['representative'];c=distributions['legacy']
   record['mixture_representative_tv']=sum(abs(a.get(k,0)-b.get(k,0)) for k in a.keys()|b.keys())/2
   record['representative_legacy_tv']=sum(abs(c.get(k,0)-b.get(k,0)) for k in c.keys()|b.keys())/2
   entries.append(record);game_rows.append(record)
  pergame.append(dict(game=gid,side=case['side'],decisions=len(game_rows),last_ply=game_rows[-1]['ply'] if game_rows else None,
      stop=raw['stop'],cpu_seconds_including_stopped_update=raw['cpu_seconds'],
      cpu_seconds_retained_prefix={n:game_rows[-1]['arms'][n]['cpu_seconds'] if game_rows else 0 for n in names}))

 phases={}
 for phase in ('all','noninitial','history_merged','ply20plus'):
  chosen=[r for r in entries if phase=='all' or phase=='noninitial' and r['ply']>0 or
          phase=='history_merged' and r['arms']['mixture']['histories']>r['arms']['mixture']['states'] or
          phase=='ply20plus' and r['ply']>=20]
  groups=defaultdict(list)
  for r in chosen:groups[r['game']].append(r)
  metrics={n:{k:S.mean(S.mean(r['arms'][n][k] for r in rows) for rows in groups.values()) if groups else None
          for k in ('nll','truth_mass','support','full_support','full_nll','nonrepresentative_mass','histories_per_state')}
          for n in names}
  comparisons={}
  for control in ('representative','legacy'):
   deltas=np.array([S.mean(r['arms'][control]['nll']-r['arms']['mixture']['nll'] for r in rows) for rows in groups.values()])
   rng=np.random.default_rng(250)
   ci=np.quantile(deltas[rng.integers(0,len(deltas),(5000,len(deltas)))].mean(1),[.025,.975]).tolist() if len(deltas) else []
   comparisons[control]=dict(mean_nll_gain=float(deltas.mean()) if len(deltas) else None,descriptive_game_bootstrap95=ci,
       better_games=int((deltas>1e-6).sum()),worse_games=int((deltas<-1e-6).sum()))
  phases[phase]=dict(decisions=len(chosen),games=len(groups),metrics=metrics,comparisons=comparisons)
 memory={n:max((r['arms'][n]['allocated_state_bytes'] for r in entries),default=0) for n in names}
 summary=dict(games=24,decisions=len(entries),seconds=receipt['seconds'],stops=dict(Counter(g['stop'] for g in pergame)),
  phases=phases,raw_marginal_rows_checked=raw_states,referee_frames_checked=frames_checked,
  merged_history_decisions=sum(r['arms']['mixture']['histories']>r['arms']['mixture']['states'] for r in entries),
  changed_board_marginal_decisions=sum(r['mixture_representative_tv']>1e-6 for r in entries),
  max_mixture_representative_tv=max(r['mixture_representative_tv'] for r in entries),
  mean_mixture_representative_tv=S.mean(r['mixture_representative_tv'] for r in entries),
  max_nonrepresentative_mass=max(r['arms']['mixture']['nonrepresentative_mass'] for r in entries),
  max_histories_per_state=max(r['arms']['mixture']['max_histories_per_state'] for r in entries),
  max_histories_per_state_average=max(r['arms']['mixture']['histories_per_state'] for r in entries),
  max_stored_allocation_bytes=memory,
  cpu_seconds_retained_prefix={n:sum(g['cpu_seconds_retained_prefix'][n] for g in pergame) for n in names},
  cpu_seconds_including_stopped_update={n:sum(g['cpu_seconds_including_stopped_update'][n] for g in pergame) for n in names},
  lookup_counts_retained_prefix={n:{k:sum(next(r for r in reversed(entries) if r['game']==g['game'])['arms'][n][k] for g in pergame)
     for k in ('table_lookups','table_hits')} for n in ('representative','mixture')},
  per_game=pergame,receipt_sha256=sha(OUT/'receipt.json'),plan_sha256=sha(OUT/'plan.json'),
  caveats=['early/small common prefixes; reused development data','both modified filters include halfmove; original does not',
           'memory counts retained state/history arrays, not transient candidates, libraries or RSS',
           'CPU costs are diagnostic, unoptimized implementation, fixed arm order; not an arena speed claim',
           'no search, decisions, wins, Elo, or promotion tested','NLL uses 1e-12 floor; support separately reported',
           'repetition history omitted; hashes may collide'])
 write(OUT/'summary.json',summary)
 write(OUT/'audit.json',dict(passed=True,games=24,decisions=len(entries),referee_frames=frames_checked,raw_marginal_rows=raw_states,
   own_input_reconstruction=True,independent_python_hash_and_course_referee=True,source_sha256=sha(Path(__file__)),
   referee_sha256=sha(KIT/'referee.py'),summary_sha256=sha(OUT/'summary.json')))
 print(json.dumps({k:v for k,v in summary.items() if k not in ('per_game','phases')}))
 print(json.dumps(summary['phases']['all']))

if __name__=='__main__':main()
