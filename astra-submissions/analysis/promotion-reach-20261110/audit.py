"""Independent native enumeration of own promotion roots; no policy or fit."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from learning import rules
OUT=Path(__file__).resolve().parent
plan=json.loads((OUT/'plan.json').read_text());result=json.loads((OUT/'result.json').read_text())
source=ROOT/'astra-submissions/analysis/capture-fixed-prior-20261110/plan.json'
games={g['game']:g for g in json.loads(source.read_text())['games']};actual=[];safe=[];frames=0;decisions=0
for game_id in plan['games']:
 g=games[game_id];side=0 if g['white'].casefold()=='iamavirus' else 1;b=rules.Board();frames+=1
 for ply,move in enumerate(g['moves']):
  if b.side==side:
   decisions+=1;promotions=[m for m in b.legal_moves() if len(m)==5]
   if promotions:
    actual.append((game_id,ply,tuple(sorted(promotions))))
    good=[]
    for m in promotions:
     if b.move_loses_king(m):continue
     q=b.copy();q.push(m)
     if q.king_square(1-side)>=0:good.append(m)
    if good:safe.append((game_id,ply,tuple(sorted(good))))
  b.push(move);frames+=1
expected=[(g['game'],r['ply'],tuple(sorted(r['legal']))) for g in result['records'] for r in g['promotion_roots']]
expected_safe=[(g['game'],r['ply'],tuple(sorted(r['king_safe']))) for g in result['records'] for r in g['promotion_roots'] if r['king_safe']]
assert actual==expected and safe==expected_safe
assert frames==result['frames_verified']==27135 and decisions==result['decisions']==13445
native=[json.loads(s) for s in (OUT/'mask.stdout').read_text().splitlines()]
assert native==result['fixed_belief_masks']['rows']
previous=json.loads((ROOT/'astra-submissions/analysis/farsight-root-20261110/audit.json').read_text())
assert set(previous['avoid_moves'])==set(result['fixed_belief_masks']['masks']['old_queen'])
ours={(g['game'],r['ply']) for g in result['records'] for r in g['promotion_roots'] if r['king_safe']}
opp={(g['game'],r['ply']) for g in result['records'] for r in g['opponent_promotion_capture_roots']}
admissible={(g['game'],r['ply']) for g in result['records'] for r in g['opponent_promotion_capture_roots'] if any(not p['reply_self_fatal'] for p in r['paths'])}
unions=ours|opp
from collections import Counter
receipt=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,scope='Native enumeration independent of the course scanner, on every own decision. Opponent-path census relies on the primary course implementation; not independently re-enumerated here.',games=302,frames=frames,decisions=decisions,own_legal_promotion_roots=len(actual),own_safe_promotion_roots=len(safe),own_events_and_moves_match=True,old_native_mask_matches=True,union_opportunity_roots=len(unions),union_opportunity_games=len({g for g,p in unions}),opponent_admissible_capture_promotion_roots=len(admissible),played_versions=dict(Counter(str(g['version']) for g in result['records'])),source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),source,OUT/'result.json',OUT/'mask.stdout',ROOT/'build/librules.so']})
with (OUT/'independent-review.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps(receipt,indent=2))
