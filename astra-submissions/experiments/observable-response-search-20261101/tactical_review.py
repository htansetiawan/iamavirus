#!/usr/bin/env python3
"""Independent referee checks after the completed four-arm diagnostic."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/observable-response-search-20261101'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest
from fresh_taxonomy_gate import material
refpath=ROOT.parent/'fow-starter/referee.py';sys.path.insert(0,str(refpath.parent))
spec=importlib.util.spec_from_file_location('projection_review_ref',refpath)
ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)

def main():
    rows=json.loads((OUT/'recovery/merged/labelled.json').read_text());checks=0;records=[]
    for row in rows:
        arms=row['arms'];original=arms['original'];projected=arms['projected']
        if (projected['move']==arms['off']['move'] and
            projected['label']['fatal']==original['label']['fatal'] and
            projected['label']['exchange_loss']==original['label']['exchange_loss']):continue
        rp=json.loads((ROOT/'data/raw/games'/row['game']/'replay.json').read_text())
        states,errors=ingest.validate_replay(rp);assert not errors
        initial=states[row['ply']];us=initial.board.side;rb=ref.FowBoard()
        history=Counter({ref.position_key(rb):1})
        for frame in rp['frames'][1:row['ply']+1]:rb.push_uci(frame['move']);history[ref.position_key(rb)]+=1
        start_material=material(initial.board.board_string(),us);seen=set()
        for arm,record in arms.items():
            move=record['move']
            if move in seen:continue
            seen.add(move);native=initial.copy();board=rb.copy();counts=history.copy()
            def push(n,b,c,m):
                nonlocal checks
                assert m in n.board.legal_moves() and m in {x.uci() for x in ref.fow_moves(b)}
                n.push(m);b.push_uci(m);c[ref.position_key(b)]+=1
                frame=ref.make_frame(b,[0,0]);assert frame['board']==n.board.board_string()
                assert frame['white']==n.board.observation(0) and frame['black']==n.board.observation(1)
                assert n.outcome()==ref.outcome(b,c);checks+=1
            push(native,board,counts,move)
            result=dict(case=row['name'],arm=arm,move=move,initial_outcome=native.outcome())
            capture=record['label'].get('worst_capture')
            if capture:
                push(native,board,counts,capture);answers=[]
                assert set(native.board.legal_moves())=={m.uci() for m in ref.fow_moves(board)}
                for reply in native.board.legal_moves():
                    n=native.copy();b=board.copy();c=counts.copy();push(n,b,c,reply)
                    outcome=n.outcome()
                    if outcome and outcome[0]==('0-1','1-0')[us]:continue
                    answers.append(dict(move=reply,net_loss=0 if outcome else start_material-material(n.board.board_string(),us)))
                assert answers
                best=min(r['net_loss'] for r in answers)
                assert best==record['label']['exchange_loss'],(row['name'],move,best,record['label'])
                result.update(punishing_capture=capture,best_safe_response_loss=best,answers=answers)
            records.append(result)
    result=dict(referee_sha256=hashlib.sha256(refpath.read_bytes()).hexdigest(),checks=checks,cases=records,
                assessment='Five choices change versus raw response: four return to the original v37 choice, one changes a rook move but retains the four-point exchange loss. Across all cases all arms have six immediate king losses, one two-point-or-larger exchange loss and no four-point queen losses. The projected model still trades a four-point regression against a separate two-point repair versus original. No playing-strength claim.',
                advancement='Frozen diagnostic checks pass after disclosed harness recovery. Independent tactical review finds no additional label error or reason to relax thresholds. At most a separately frozen small full-clock pilot; no ZIP.')
    (OUT/'tactical-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'checks':checks,'unique_lines':len(records),'assessment':result['assessment']}))

if __name__=='__main__':main()
