from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,statistics,sys
root=Path('/home/henrytan/git/iamavirus');out=root/'astra-submissions/analysis/move-cost-profile-20261102';plan=json.loads((out/'plan.json').read_text());summary=json.loads((out/'summary.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((out/'execution.json').read_text())['status']=='complete'
for p,h in plan['dependencies'].items():assert sha(Path(p))==h,p
refpath=root.parent/'fow-starter/referee.py';assert sha(refpath)=='2f82ac292bfad29bcb2d701b73c060d1ca8281378b4598f08a620fe5c97255be'
spec=importlib.util.spec_from_file_location('review227ref',refpath);ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
manifest={};pairs=[];rows=[];frames=0
for c in plan['cases']:
 rp=json.loads((root/'data/raw/games'/c['game']/'replay.json').read_text());b=ref.FowBoard()
 for ply,f in enumerate(rp['frames'][:c['ply']+1]):
  if ply:
   m=ref.chess.Move.from_uci(f['move']);assert m in ref.fow_moves(b);b.push(m)
  actual=ref.make_frame(b,f['clocks']);assert all(actual[k]==f[k] for k in ('board','white','black'));frames+=1
 pair=[]
 for a in ('original','optimized'):
  n=c['name']+'-'+a;r=json.loads((out/(n+'-result.json')).read_text());receipt=json.loads((out/(n+'-receipt.json')).read_text())
  assert r['error'] is None and r['exit']==0 and receipt['move']==r['move']
  for suffix in ('stdout','stderr'):
   p=out/(n+'.'+suffix);assert sha(p)==r[suffix+'_sha256'];manifest[str(p.relative_to(root))]=sha(p)
  bb=b.copy();m=ref.chess.Move.from_uci(r['move']);assert m in ref.fow_moves(bb);us=bb.turn;bb.push(m);king=bb.king(us);fatal=king is None or bb.is_attacked_by(not us,king);assert fatal==r['label']['fatal']
  assert r['turn_seconds']>=r['profile']['guards']+r['profile']['search']-.002
  rows.append(r);pair.append(r)
 pairs.append({'case':c['name'],'turn_ratio':pair[1]['turn_seconds']/pair[0]['turn_seconds'],'node_ratio':pair[1]['nodes']/pair[0]['nodes'],'same_move':pair[0]['move']==pair[1]['move']})
assert statistics.median(p['turn_ratio'] for p in pairs)==summary['median_turn_ratio']
assert statistics.median(p['node_ratio'] for p in pairs)==summary['median_node_ratio']
r={'at':datetime.now(timezone.utc).isoformat(),'calls':16,'independent_referee_frames':frames,'independent_fatal_labels':16,'same_moves':sum(p['same_move'] for p in pairs),'manifest':manifest,'pairs':pairs,'scope':'Independent aggregation and course-referee labels, same agent. No further policy calls.'}
with (out/'independent-review.json').open('x') as f:json.dump(r,f,indent=2)
print(json.dumps({k:r[k] for k in ('calls','independent_referee_frames','independent_fatal_labels','same_moves')}))
