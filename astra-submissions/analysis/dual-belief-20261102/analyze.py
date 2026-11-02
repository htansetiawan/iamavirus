"""Independent truth joins and frozen-gate arithmetic. Never reruns a policy."""
from collections import Counter,defaultdict
import gzip,hashlib,importlib.util,json,math,statistics,sys
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];KIT=Path.home()/'git/fow-starter'
sys.path.insert(0,str(KIT));sys.path.insert(0,str(ROOT))
import chess,referee
from learning import rules,ingest

spec=importlib.util.spec_from_file_location('hash_reference',ROOT/'astra-submissions/analysis/history-mixture-20261102/analyze.py');hash_reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(hash_reference)
spec=importlib.util.spec_from_file_location('collector',ROOT/'astra-submissions/experiments/dual-belief-20261102/run.py');collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def normalized(logs):
 values=np.exp(np.asarray(logs,dtype=np.float64));return values/values.sum()
def mask(r):
 flat=np.array(r['king_flat'])+.9*np.array(r['queen_flat']);sharp=np.array(r['king_sharp'])+.9*np.array(r['queen_sharp'])
 out=(flat>flat.min()+.02)|(sharp>sharp.min()+.02)
 if out.all():out=sharp>sharp.min()+.02
 return out
def main():
 plan=json.loads((OUT/'plan.json').read_text());receipt=json.loads((OUT/'receipt.json').read_text())
 assert receipt['state']=='completed' and len(receipt['games'])==24
 assert receipt['plan_sha256']==sha(OUT/'plan.json')
 assert [r['game'] for r in receipt['games']]==[r['game'] for r in plan['games']]
 for path,digest in plan['sources'].items():assert sha(ROOT/path)==digest,path
 totals=Counter();records=[];bygame=defaultdict(list);times={n:0. for n in ('base','candidate')};retained={n:0. for n in times}
 for case,rec in zip(plan['games'],receipt['games']):
  assert not rec['error'] and rec['returncode']==0
  assert sha(case['path'])==case['sha256'];r=json.loads(Path(case['path']).read_text())
  a=collector.actor(r,case['side']);assert hashlib.sha256(json.dumps(a).encode()).hexdigest()==rec['actor_sha256']
  path=OUT/'games'/f"{case['game']}.json.gz";assert sha(path)==rec['output_sha256']
  with gzip.open(path,'rt') as f:data=json.load(f)
  native,errors=ingest.validate_replay(r);assert not errors,errors
  b=referee.FowBoard();states=[];repetitions=Counter({referee.position_key(b):1})
  for ply,frame in enumerate(r['frames']):
   if ply:
    assert referee.outcome(b,repetitions) is None
    move=chess.Move.from_uci(frame['move']);assert move in referee.fow_moves(b);b.push(move);repetitions[referee.position_key(b)]+=1
   assert ''.join(b.piece_at(s).symbol() if b.piece_at(s) else '-' for s in range(64))==frame['board']
   assert referee.observation(b,chess.WHITE)==frame['white'] and referee.observation(b,chess.BLACK)==frame['black']
   states.append(b.copy(stack=False));totals['referee_frames']+=1
  for name in times:
   times[name]+=data['cpu'][name]
   retained[name]+=data['rows'][-1]['cpu'][name] if data['rows'] else 0
  for k,row in enumerate(data['rows']):
   ply=row['ply'];assert ply==case['side']+2*k;b=states[ply];worlds=row['worlds'];n=len(worlds['keys'])
   assert 0<n<=4096
   for field in ('hist','sharp','flat','half','boards'):assert len(worlds[field])==n
   assert len(row['flat_approx'])==n
   assert all(x==y/2 for x,y in zip(row['flat_approx'],worlds['sharp']))
   approx=normalized(row['flat_approx']);exact=normalized(worlds['flat']);sharp=normalized(worlds['sharp']);key=hash_reference.state_key(b)
   truth=np.array([s==key for s in worlds['keys']]);assert truth.any()
   own=lambda text:tuple((i,c) for i,c in enumerate(text) if c not in '-?' and c.isupper()==(case['side']==0))
   truth_own=own(r['frames'][ply]['board'])
   assert all(own(s)==truth_own for s in worlds['boards'])
   base=row['risks']['base'];cand=row['risks']['candidate'];moves=base['moves'];assert moves==cand['moves'] and moves
   legal={m.uci() for m in referee.fow_moves(b)};fatal=[]
   for m in moves:
    assert m in legal
    q=b.copy(stack=False);q.push(chess.Move.from_uci(m));king=q.king(not q.turn)
    lost=king is None or q.is_attacked_by(q.turn,king)
    # Winning king captures take priority in the game's terminal rule. The
    # v37 immediate guard predicate is compared as implemented; these prefix
    # choices have both kings after any non-winning candidate.
    assert lost==native[ply].board.move_loses_king(m),(case['game'],ply,m)
    fatal.append(lost);totals['candidate_truth_labels']+=1
   y=np.asarray(fatal);bm=mask(base);cm=mask(cand)
   safe=~y;new_all_safe=bool(safe.any() and not bm[safe].all() and cm[safe].all())
   metrics={}
   for name,dist,risk,exclusions in [('approx',approx,base,bm),('dual',exact,cand,cm),('sharp',sharp,base,bm)]:
    risk_key='king_sharp' if name=='sharp' else 'king_flat';p=np.array(risk[risk_key]);assert np.all(np.isfinite(p)) and np.all((p>=-1e-12)&(p<=1+1e-12))
    pc=np.clip(p,1e-12,1-1e-12)
    metrics[name]=dict(truth_probability=float(dist[truth].sum()),nll=-math.log(max(float(dist[truth].sum()),1e-12)),king_brier=float(np.mean((p-y)**2)),king_logloss=float(np.mean(-(y*np.log(pc)+(1-y)*np.log(1-pc)))),fatal_excluded=int((y&exclusions).sum()),safe_excluded=int((safe&exclusions).sum()))
   item=dict(game=case['game'],ply=ply,states=n,moves=moves,fatal=fatal,baseline_excluded=bm.tolist(),dual_excluded=cm.tolist(),changed_mask=bool(np.any(bm!=cm)),new_all_safe_veto=new_all_safe,metrics=metrics,total_variation=float(np.abs(approx-exact).sum()/2))
   records.append(item);bygame[case['game']].append(item);totals['states']+=n;totals['fatal_actions']+=int(y.sum());totals['decisions']+=1
   totals['changed_masks']+=item['changed_mask'];totals['new_all_safe_veto']+=new_all_safe
  print(json.dumps(dict(audited=case['game'],decisions=len(data['rows']))),flush=True)
 pergame=[]
 for gid,rows in bygame.items():
  pergame.append(dict(game=gid,decisions=len(rows),nll_gain=statistics.mean(r['metrics']['approx']['nll']-r['metrics']['dual']['nll'] for r in rows)))
 values=np.array([g['nll_gain'] for g in pergame]);rng=np.random.default_rng(252)
 ci=np.quantile(values[rng.integers(0,len(values),(5000,len(values)))].mean(1),[.025,.975]).tolist()
 metrics={name:{metric:statistics.mean(r['metrics'][name][metric] for r in records) for metric in ('king_brier','king_logloss')} for name in ('approx','dual','sharp')}
 for name in metrics:
  metrics[name]['equal_game_nll']=statistics.mean(statistics.mean(r['metrics'][name]['nll'] for r in rows) for rows in bygame.values())
  for metric in ('fatal_excluded','safe_excluded'):metrics[name][metric]=sum(r['metrics'][name][metric] for r in records)
 gate=dict(nll_gain_at_least_005=float(values.mean())>=.05,king_brier_not_worse=metrics['dual']['king_brier']<=metrics['approx']['king_brier'],at_least_five_mask_changes=totals['changed_masks']>=5,no_new_all_safe_veto=not totals['new_all_safe_veto'])
 result=dict(passed_integrity=True,games=len(bygame),totals=dict(totals),metrics=metrics,equal_game_nll_gain=float(values.mean()),descriptive_game_bootstrap95=ci,better_games=int((values>1e-6).sum()),worse_games=int((values<-1e-6).sum()),mean_tv=statistics.mean(r['total_variation'] for r in records),max_tv=max(r['total_variation'] for r in records),cpu_seconds_retained=retained,cpu_seconds_including_stopped_update=times,collection_seconds=receipt['seconds'],gate=gate,advance=all(gate.values()),source_sha256=sha(Path(__file__)),plan_sha256=sha(OUT/'plan.json'),receipt_sha256=sha(OUT/'receipt.json'),referee_sha256=sha(KIT/'referee.py'),limitations=['Reused selected development prefixes; no capped midgame strength claim','Guards exclude based on both measures; sharp branch unchanged','Queen predicate intentionally unchanged and not independently corrected here','Original masks before repetition avoidance, not actual chosen search moves','Labels cover all view-legal actions, not the deployed policy distribution','Independent truth/referee checks do not independently recompute every hypothesis risk'])
 write(OUT/'cases.json',dict(records=records,pergame=pergame));write(OUT/'summary.json',result);print(json.dumps(result))
if __name__=='__main__':main()
