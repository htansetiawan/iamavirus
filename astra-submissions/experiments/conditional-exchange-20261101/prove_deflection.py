#!/usr/bin/env python3
"""Verify a longer forcing exchange with both the native rules and course referee.

This proves a continuation after a SPECIFIED recapture, not a forced loss from
the original position or the optimality of any root move.
"""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest
from fresh_taxonomy_gate import material

refpath=ROOT.parent/'fow-starter/referee.py'
sys.path.insert(0,str(refpath.parent))
spec=importlib.util.spec_from_file_location('astra_deflection_ref',refpath)
ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
replay=json.loads((ROOT/'data/raw/games/92px495s/replay.json').read_text())
states,errors=ingest.validate_replay(replay);assert not errors
initial=states[26];initial_material=material(initial.board.board_string(),0)
rb=ref.FowBoard()
for f in replay['frames'][1:27]:rb.push_uci(f['move'])
checks=0

def compare(native,other):
    global checks
    frame=ref.make_frame(other,[0,0]);assert frame['board']==native.board.board_string()
    for side,key in [(0,'white'),(1,'black')]:assert frame[key]==native.board.observation(side)
    legal={m.uci() for m in ref.fow_moves(other)};assert legal==set(native.board.legal_moves())
    for move in legal:
        q=other.copy();q.push_uci(move);king=q.king(not q.turn)
        fatal=king is None or q.is_attacked_by(q.turn,king)
        assert fatal==native.board.move_loses_king(move);checks+=1

def step(n,r,move):
    compare(n,r);assert move in n.board.legal_moves()
    nn=n.copy();rr=r.copy();nn.push(move);rr.push_uci(move);compare(nn,rr)
    assert nn.outcome()==ref.outcome(rr,Counter({ref.position_key(rr):1}))
    return nn,rr

rows=[]
for line in [['d1d5','e6d5','f3d5'],['f3d5','e6d5','d1d5']]:
    n,r=initial.copy(),rb.copy()
    for move in line:n,r=step(n,r,move);assert n.outcome() is None
    row={'prefix':line,'net_loss_after_recapture':initial_material-material(n.board.board_string(),0),
         'deflection':'d6h2','branches':[]}
    n,r=step(n,r,'d6h2');assert n.outcome() is None
    safe=[m for m in n.board.legal_moves() if not n.board.move_loses_king(m)]
    row['all_king_surviving_replies']=safe
    assert set(safe)=={'g1h1','g1h2'}
    for move in safe:
        nn,rr=step(n,r,move);nn,rr=step(nn,rr,'d8d5');assert nn.outcome() is None
        responses=[]
        for answer in nn.board.legal_moves():
            if nn.board.move_loses_king(answer):continue
            end,erend=step(nn,rr,answer)
            responses.append({'move':answer,'net_loss':initial_material-material(end.board.board_string(),0),'outcome':end.outcome()})
        assert responses and not any(x['outcome'] and x['outcome'][0]!='0-1' for x in responses)
        best=min(responses,key=lambda x:x['net_loss'])
        row['branches'].append({'king_reply':move,'queen_capture':'d8d5','best_next_response':best,
                                'safe_response_count':len(responses)})
    rows.append(row)
out={'game':'92px495s','ply':26,'rows':rows,'independent_legal_survival_checks':checks,
     'referee_sha256':hashlib.sha256(refpath.read_bytes()).hexdigest(),
     'scope':'Specified recaptures allow a forcing clearance/deflection combination. Not a forced-loss proof for either root move: the player can decline the earlier recapture. Three-ply material labels alone are insufficient.'}
path=ROOT/'astra-submissions/analysis/conditional-exchange-20261101/deflection-proof.json'
path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
