"""Check exact-prefix parity, history ownership and next-view partitions.

The course referee validates all hypothetical views. It never supplies an
unobserved move to the filter. No truth-based action-quality labels are used.
"""
from collections import Counter,defaultdict
import gzip,hashlib,importlib.util,json,math,random,sys
from pathlib import Path

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
OLD=ROOT/'astra-submissions/analysis/history-mixture-20261102'
KIT=Path.home()/'git/fow-starter';sys.path.insert(0,str(KIT));sys.path.insert(0,str(ROOT))
import chess,referee
from learning.move_taxonomy import fen

spec=importlib.util.spec_from_file_location('prior_audit',OLD/'analyze.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
spec=importlib.util.spec_from_file_location('collector',ROOT/'astra-submissions/experiments/history-partition-20261102/run.py')
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,value):
 with Path(p).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
MASK=(1<<64)-1
def mix(h,value):
 z=(h+0x9E3779B97F4A7C15*(value|1))&MASK
 z=((z^(z>>30))*0xBF58476D1CE4E5B9)&MASK
 z=((z^(z>>27))*0x94D049BB133111EB)&MASK
 return z^(z>>31)
def view_hash(view):
 h=1469598103934665603
 for c in view:h=((h^ord(c))*1099511628211)&MASK
 return h
def pairs(counts):return sum(n*(n-1)//2 for n in counts.values())
def construct(s,side):
 b=referee.FowBoard(fen(s['board']));b.turn=side==0;b.castling_rights=int(s['castle']);b.ep_square=None if s['ep']<0 else s['ep'];b.halfmove_clock=s['half'];return b

def main():
 plan=json.loads((OUT/'plan.json').read_text());receipt=json.loads((OUT/'receipt.json').read_text())
 assert receipt['state']=='completed' and not receipt['failures'];assert sha(OUT/'plan.json')==receipt['plan_sha256']
 assert receipt['completed']==[c['game'] for c in plan['cases']]
 for p,h in plan['sources'].items():assert sha(ROOT/p)==h
 totals=Counter();cases=[];seed_rows=[];max_error=0
 for case in plan['cases']:
  gid=case['game'];r=json.loads(Path(case['path']).read_text());assert sha(case['path'])==case['sha256']
  saved=json.loads((OUT/'cases'/f'{gid}-receipt.json').read_text());assert saved['case']==case and saved['returncode']==0
  path=OUT/'cases'/f'{gid}.json.gz';assert sha(path)==saved['output_sha256']
  assert sha(OUT/'cases'/f'{gid}.stderr')==saved['stderr_sha256']
  assert hashlib.sha256(collector.actor(r,case['side'],case['ply']).encode()).hexdigest()==saved['payload_sha256']
  with gzip.open(path,'rt') as f:data=json.load(f)
  states=data['states'];view=r['frames'][case['ply']][('white','black')[case['side']]]
  old_case=OLD/'games'/f'{gid}.json';assert sha(old_case)==case['old_case_sha256']
  with gzip.open(OLD/'games'/f'{gid}-raw.json.gz','rt') as f:old=json.load(f)
  earlier=next(row for row in old['rows'] if row['ply']==case['ply'])
  for arm in ('representative','mixture'):
   weights=[s['rep_mass'] if arm=='representative' else sum(v for h,v in s['histories']) for s in states]
   total=sum(weights);now={(s['key'],s['half']):w/total for s,w in zip(states,weights)}
   before={(k,h):v for k,h,v in earlier['arms'][arm]['states']};assert now.keys()==before.keys()
   error=max(abs(now[k]-before[k]) for k in now);max_error=max(max_error,error);assert error<2e-10,error
  owners={};rep_owners={};shared=shared_rep=0;boards=[];legal_sets=[];own_placements=set();own_rights=set()
  for i,s in enumerate(states):
   b=construct(s,case['side']);assert prior.state_key(b)==s['key'];assert referee.observation(b,b.turn)==view
   own_placements.add(tuple((sq,p.symbol()) for sq,p in b.piece_map().items() if p.color==b.turn))
   own_rights.add(b.castling_rights & (chess.BB_RANK_1 if b.turn else chess.BB_RANK_8))
   assert s['rep_history'] in {h for h,v in s['histories']}
   for h,v in s['histories']:
    assert math.isfinite(v) and v>0
    if h in owners and owners[h]!=i:shared+=1
    owners[h]=i
   h=s['rep_history']
   if h in rep_owners and rep_owners[h]!=i:shared_rep+=1
   rep_owners[h]=i;boards.append(b);legal_sets.append(set(m.uci() for m in referee.fow_moves(b)))
  assert len(own_placements)==1 and len(own_rights)==1
  allowed=sorted(set.intersection(*legal_sets));assert allowed
  one=dict(game=gid,ply=case['ply'],states=len(states),histories=sum(len(s['histories']) for s in states),
           distinct_histories=len(owners),cross_state_histories=shared,cross_state_representatives=shared_rep,common_moves=len(allowed))
  cases.append(one);totals.update({k:one[k] for k in ('states','histories','cross_state_histories','cross_state_representatives')})
  cache={}
  for seed in plan['seeds']:
   indices=random.Random(seed).choices(range(len(states)),weights=[s['rep_mass'] for s in states],k=plan['samples'])
   rng=random.Random(seed^0x251251);base_groups=Counter();new_groups=Counter();cross=Counter();group_roots=[defaultdict(set),defaultdict(set)];semantics=[{},{}]
   sample_rows=[];nodes=terminal=0;actions_by_info=[{},{}]
   for i in indices:
    state=states[i];base=int(state['rep_history']);hist=int(rng.choices([h for h,v in state['histories']],weights=[v for h,v in state['histories']],k=1)[0])
    sample_rows.append([i,str(base),str(hist)])
    if i not in cache:
     branches=[]
     for move in allowed:
      b=boards[i].copy(stack=False);b.push(chess.Move.from_uci(move));king=b.king(not b.turn)
      # Only a surviving branch reaches an opponent information set. These
      # early-prefix diagnostics do not reconstruct repetition histories.
      if king is None or b.is_attacked_by(b.turn,king) or b.halfmove_clock>=100:
       branches.append(None);continue
      next_view=referee.observation(b,b.turn);next_actions=tuple(m.uci() for m in referee.fow_moves(b))
      branches.append((move,next_view,next_actions))
     cache[i]=branches
    for branch in cache[i]:
     if branch is None:terminal+=1;continue
     move,obs,actions=branch;keys=[]
     for arm,h in enumerate((base,hist)):
      key=mix(mix(h,view_hash(obs)),0x5eed0001)|1
      signature=(i,h,obs)
      assert key not in semantics[arm] or semantics[arm][key]==signature,'history hash aliases distinct semantics'
      semantics[arm][key]=signature;group_roots[arm][key].add(i)
      assert key not in actions_by_info[arm] or actions_by_info[arm][key]==actions,'inconsistent legal action order'
      actions_by_info[arm][key]=actions;keys.append(key)
     base_groups[keys[0]]+=1;new_groups[keys[1]]+=1;cross[tuple(keys)]+=1;nodes+=1
   old_same=pairs(base_groups);new_same=pairs(new_groups);both_same=pairs(cross)
   cross_root=[sum(len(v)>1 for v in arm.values()) for arm in group_roots]
   item=dict(game=gid,seed=seed,physical_samples=indices,history_samples=sample_rows,opponent_nodes=nodes,terminal_branches=terminal,
             representative_infosets=len(base_groups),mixture_infosets=len(new_groups),cross_root_infosets=cross_root,
             node_pairs_split=old_same-both_same,node_pairs_merged=new_same-both_same,
             all_changes_only_replicate_same_physical_roots=not any(cross_root) and not shared and not shared_rep)
   seed_rows.append(item)
   totals.update({k:item[k] for k in ('opponent_nodes','terminal_branches','representative_infosets','mixture_infosets','node_pairs_split','node_pairs_merged')})
   totals['cross_root_infosets']+=sum(cross_root)
  print(json.dumps(dict(audited=gid,states=len(states),histories=one['histories'],cross_state_histories=shared)),flush=True)
 result=dict(passed=True,cases=24,seeds=len(seed_rows),totals=dict(totals),max_reconstructed_marginal_error=max_error,
    copies_only=all(r['all_changes_only_replicate_same_physical_roots'] for r in seed_rows),
    recommended_action='Do not integrate history replication into search alone' if all(r['all_changes_only_replicate_same_physical_roots'] for r in seed_rows) else 'Inspect cross-root coupling before a separate search proposal',
    source_sha256=sha(Path(__file__)),referee_sha256=sha(KIT/'referee.py'),plan_sha256=sha(OUT/'plan.json'),receipt_sha256=sha(OUT/'receipt.json'),
    native_solver_control=json.loads((OUT/'native-preflight.json').read_text())['test'],
    limitations=['Reused deliberately high-multiplicity development cases; not population inference',
     'No guard or actual search move quality measured','No repeated-history trace or common-knowledge closure reconstructed',
     'Fixed complete continuation equivalence does not imply identical adaptive GT-CFR runtime or expansion',
     'History/state hashes remain finite; ownership checks apply to this panel'])
 write(OUT/'partition-cases.json',dict(cases=cases,seeds=seed_rows));write(OUT/'summary.json',result)
 print(json.dumps(result))

if __name__=='__main__':main()
