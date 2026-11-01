#!/usr/bin/env python3
"""Validate every mined forcing branch against the course referee."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/conditional-exchange-20261101'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest
from fresh_taxonomy_gate import material

path=ROOT.parent/'fow-starter/referee.py';sys.path.insert(0,str(path.parent))
spec=importlib.util.spec_from_file_location('astra_clearance_referee',path)
ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
corpus=json.loads((OUT/'clearance-corpus.json').read_text())
checks=0;events=[]

def compare(n,r,reps):
    global checks
    assert n.board.board_string()==ref.make_frame(r,[0,0])['board']
    assert n.outcome()==ref.outcome(r,reps)
    legal={m.uci() for m in ref.fow_moves(r)};assert legal==set(n.board.legal_moves())
    for m in legal:
        child=r.copy();child.push_uci(m);k=child.king(not child.turn)
        fatal=k is None or child.is_attacked_by(child.turn,k)
        assert fatal==n.board.move_loses_king(m);checks+=1

def step(n,r,reps,m):
    nn=n.copy();rr=r.copy();cc=reps.copy();nn.push(m);rr.push_uci(m);cc[ref.position_key(rr)]+=1
    compare(nn,rr,cc);return nn,rr,cc

for event in corpus['hits']:
    data=(ROOT/'data/raw/games'/event['game']/'replay.json').read_bytes()
    assert hashlib.sha256(data).hexdigest()==event['replay_sha256']
    replay=json.loads(data);states,errors=ingest.validate_replay(replay);assert not errors
    rb=ref.FowBoard();reps=Counter({ref.position_key(rb):1})
    for f in replay['frames'][1:event['ply']+1]:rb.push_uci(f['move']);reps[ref.position_key(rb)]+=1
    initial=states[event['ply']];side=initial.board.side;lead=material(initial.board.board_string(),side)
    compare(initial,rb,reps)
    n,r,c=step(initial,rb,reps,event['first']);assert n.outcome() is None
    assert r.is_check()
    safe=[m for m in n.board.legal_moves() if not n.board.move_loses_king(m)]
    assert set(safe)=={b['forced_king_reply'] for b in event['branches']}
    gains=[]
    for branch in event['branches']:
        nn,rr,cc=step(n,r,c,branch['forced_king_reply']);nn,rr,cc=step(nn,rr,cc,event['slider_capture'])
        assert nn.outcome() is None
        possibilities=[]
        for m in nn.board.legal_moves():
            end,er,ec=step(nn,rr,cc,m)
            if end.outcome():
                assert end.outcome()[0]==('1-0' if side==0 else '0-1')
                continue
            possibilities.append(material(end.board.board_string(),side)-lead)
        gain=min(possibilities);assert gain==branch['gain'];gains.append(gain)
    assert min(gains)==event['minimum_gain']
    events.append({'game':event['game'],'ply':event['ply'],'minimum_gain':min(gains),'king_reply_branches':len(gains)})
result={'events':events,'independent_legal_survival_checks':checks,'corpus_sha256':hashlib.sha256((OUT/'clearance-corpus.json').read_bytes()).hexdigest(),
        'referee_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'all_pass':True}
(OUT/'clearance-corpus-validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
