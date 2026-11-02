"""Audit frozen tree serialization, receipts, permitted inputs and timing arithmetic."""
from collections import Counter
import gzip,hashlib,json,math,struct,sys
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];KIT=Path.home()/'git/fow-starter'
sys.path[:0]=[str(ROOT),str(KIT),str(ROOT/'astra-submissions/tools')]
import chess,referee
from fresh_taxonomy_gate import protocol
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def parse(path):
 raw=Path(path).read_bytes();assert raw[:8]==b'ASTRA253';nn,ne,ni,ns,root=struct.unpack_from('=5i',raw,8);assert nn>0 and 0<=root<nn
 at=28;nodes=[]
 for _ in range(nn):
  fields=struct.unpack_from('=5id',raw,at);at+=28;nodes.append(fields)
 def read(dtype,count):
  nonlocal at
  x=np.frombuffer(raw,dtype=dtype,count=count,offset=at);at+=x.nbytes;return x
 child=read('=i4',ne);prob=read('=f8',ne);player=read('=i4',ni);actions=read('=i4',ni);offset=read('=i4',ni)
 arrays=[read('=f8',ns) for _ in range(3)];assert at==len(raw)
 assert np.all((child>=0)&(child<nn));assert np.all((player==0)|(player==1))
 assert sum(actions)==ns and np.array_equal(offset,np.cumsum(actions)-actions)
 for t,p,I,first,count,value in nodes:
  assert t in (0,1,2) and math.isfinite(value) and 0<=first<=first+count<=ne
  if t==1:assert 0<=I<ni and player[I]==p and actions[I]==count
  if t==0:
   values=prob[first:first+count];assert np.all(values>=0) and abs(sum(values)-1)<1e-8
 assert all(np.all(np.isfinite(x)) for x in arrays)
 assert np.all(arrays[0]>=0)
 # Establish the active topology independently of the native loader. Extra
 # disconnected allocations are reported, not silently assumed absent.
 reached=set();todo=[root]
 while todo:
  i=todo.pop()
  if i in reached:continue
  reached.add(i);t,p,I,first,count,v=nodes[i]
  if t!=2:todo.extend(int(c) for c in child[first:first+count])
 return dict(nodes=nn,edges=ne,infosets=ni,slots=ns,reachable_nodes=len(reached),raw_bytes=len(raw))
def main():
 plan=json.loads((OUT/'plan.json').read_text());receipt=json.loads((OUT/'receipt.json').read_text())
 assert receipt['state']=='completed' and receipt['plan_sha256']==sha(OUT/'plan.json')
 for p,h in plan['sources'].items():assert sha(p)==h,p
 for p,h in plan['source_build'].items():assert sha(ROOT/p)==h,p
 assert len(receipt['jobs'])==16 and all(j['exit_code']==0 and not j['error'] for j in receipt['jobs'])
 rows=[];frames=0;labels=0
 for case in plan['cases']:
  name=case['name'];capture=json.loads((OUT/(name+'-capture.json')).read_text());bench=json.loads((OUT/(name+'-benchmark.json')).read_text());assert not capture['error'] and not bench['error'] and capture['exit_code']==bench['exit_code']==0
  rp=ROOT/'data/raw/games'/case['game']/'replay.json';assert sha(rp)==case['replay_sha256'];r=json.loads(rp.read_text());feed,forced=protocol(r,case['ply'],case['side'])
  assert hashlib.sha256(feed.encode()).hexdigest()==case['input_sha256'] and forced==case['forced']
  import copy
  redacted=copy.deepcopy(r);redacted['result']='unknown'
  for ply,f in enumerate(redacted['frames']):
   f['board']='X'*64;f[('black','white')[case['side']]]='X'*64
   if ply and (ply-1)%2!=case['side']:f['move']='zzzz'
  assert protocol(redacted,case['ply'],case['side'])==(feed,forced)
  b=referee.FowBoard();repetitions=Counter({referee.position_key(b):1})
  for ply,f in enumerate(r['frames'][:case['ply']+1]):
   if ply:
    assert referee.outcome(b,repetitions) is None;m=chess.Move.from_uci(f['move']);assert m in referee.fow_moves(b);b.push(m);repetitions[referee.position_key(b)]+=1
   assert ''.join(b.piece_at(sq).symbol() if b.piece_at(sq) else '-' for sq in range(64))==f['board']
   assert referee.observation(b,chess.WHITE)==f['white'] and referee.observation(b,chess.BLACK)==f['black'];frames+=1
  moves=[line[5:] for line in capture['stdout'].splitlines() if line.startswith('move ')];assert moves[:-1]==forced and len(moves)==len(forced)+1
  chosen=chess.Move.from_uci(moves[-1]);assert chosen in referee.fow_moves(b);labels+=1
  rec=next(j for j in receipt['jobs'] if j['case']==name and j['stage']=='benchmark');path=Path(rec['tree']);compressed=path.with_suffix('.tree.gz')
  assert sha(path)==rec['raw_sha256'] and sha(compressed)==rec['compressed_sha256'];assert gzip.decompress(compressed.read_bytes())==path.read_bytes()
  tree=parse(path);assert tree['raw_bytes']==rec['raw_bytes']
  measured=json.loads(bench['stdout']);assert measured['identical'] and measured['steps']==200 and measured['timed_repeats']==5
  ratio=measured['base_seconds']/measured['fast_seconds'];assert abs(ratio-measured['speedup'])<1e-6
  # Base storage counts four persistent arrays; its two temporary vectors
  # are allocated during iteration. Fast storage already includes scratch.
  row=dict(case=name,tree=tree,**measured,base_iteration_solver_bytes=measured['base_storage']+2*tree['slots']*8,fast_iteration_solver_bytes=measured['fast_storage'],tree_sha256=rec['raw_sha256'],compressed_sha256=rec['compressed_sha256'],capture_sha256=sha(OUT/(name+'-capture.json')),benchmark_sha256=sha(OUT/(name+'-benchmark.json')))
  rows.append(row)
 san=json.loads((OUT/(plan['cases'][0]['name']+'-load-sanitizer.json')).read_text());assert san['exit_code']==0 and not san['error'] and json.loads(san['stdout'])['identical']
 geomean=math.exp(sum(math.log(r['base_seconds']/r['fast_seconds']) for r in rows)/len(rows))
 result=dict(passed_integrity=True,cases=len(rows),geometric_mean_solver_speedup=geomean,min_speedup=min(r['speedup'] for r in rows),max_speedup=max(r['speedup'] for r in rows),base_seconds=sum(r['base_seconds'] for r in rows),fast_seconds=sum(r['fast_seconds'] for r in rows),all_bit_identical=True,referee_frames=frames,chosen_legal=labels,privacy_checks=len(rows),advance_equal_clock=geomean>=1.2,collection_seconds=receipt['seconds'],raw_tree_bytes=sum(r['tree']['raw_bytes'] for r in rows),compressed_tree_bytes=sum(j.get('compressed_bytes',0) for j in receipt['jobs']),plan_sha256=sha(OUT/'plan.json'),receipt_sha256=sha(OUT/'receipt.json'),audit_source_sha256=sha(Path(__file__)),referee_sha256=sha(KIT/'referee.py'),limitations=['Eight reused cost-selected cases, not a population performance estimate','Fixed-tree timing excludes growth, Stockfish and belief work','Same operation traces preserve semantics; equal-clock playing strength untested','Only existing v37 callers audited for direct array mutation; not a generic M4 compatibility claim'])
 write(OUT/'tree-review.json',dict(rows=rows));write(OUT/'summary.json',result);print(json.dumps(result))
if __name__=='__main__':main()
