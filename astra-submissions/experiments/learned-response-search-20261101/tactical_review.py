#!/usr/bin/env python3
"""Independent referee review of the changed king/material examples."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/learned-response-search-20261101'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest
from fresh_taxonomy_gate import material
refpath=ROOT.parent/'fow-starter/referee.py';sys.path.insert(0,str(refpath.parent))
spec=importlib.util.spec_from_file_location('response_review_ref',refpath)
ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)

def main():
    checks=0;records=[]
    for game,ply,lines in [('23paw9tn',48,[['c5e6','d6e5'],['d1e1','d6e5']]),
                           ('xrhh3nfx',87,[['g6h6'],['h3h2']])]:
        rp=json.loads((ROOT/'data/raw/games'/game/'replay.json').read_text());states,errors=ingest.validate_replay(rp);assert not errors
        initial=states[ply];us=initial.board.side;rb=ref.FowBoard()
        for f in rp['frames'][1:ply+1]:rb.push_uci(f['move'])
        start_material=material(initial.board.board_string(),us)
        for line in lines:
            n=initial.copy();r=rb.copy()
            for move in line:
                assert move in n.board.legal_moves() and move in {m.uci() for m in ref.fow_moves(r)}
                n.push(move);r.push_uci(move)
                frame=ref.make_frame(r,[0,0]);assert frame['board']==n.board.board_string()
                assert frame['white']==n.board.observation(0) and frame['black']==n.board.observation(1)
                assert n.outcome()==ref.outcome(r,Counter({ref.position_key(r):1}));checks+=1
            row=dict(game=game,ply=ply,line=line,outcome=n.outcome())
            if n.outcome() is None:
                legal=n.board.legal_moves();assert set(legal)=={m.uci() for m in ref.fow_moves(r)}
                responses=[]
                for m in legal:
                    nn=n.copy();rr=r.copy();nn.push(m);rr.push_uci(m)
                    king=rr.king(not rr.turn);fatal=king is None or rr.is_attacked_by(rr.turn,king)
                    assert fatal==n.board.move_loses_king(m);checks+=1
                    if not fatal:responses.append(dict(move=m,net_loss=start_material-material(nn.board.board_string(),us),outcome=nn.outcome()))
                row['safe_responses']=responses
                if game=='23paw9tn':row['best_response_loss']=min(x['net_loss'] for x in responses)
            records.append(row)
    assert records[0]['best_response_loss']==4
    assert records[1]['best_response_loss']<=-4
    assert records[2]['outcome']==('1-0','King capturable') and records[3]['outcome'] is None
    result=dict(referee_sha256=hashlib.sha256(refpath.read_bytes()).hexdigest(),checks=checks,cases=records,
                assessment='One real immediate-survival repair and one real short-exchange regression. No long-term winning claim for the survival repair; no forced-loss claim for the material branch. The predeclared allowance of one extra material label is not changed.',
                advancement='Decision screen passes; proceed only to bounded full-clock pilot, not submission.')
    (OUT/'tactical-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'checks':checks,'material_losses':[records[0]['best_response_loss'],records[1]['best_response_loss']],'king_outcomes':[records[2]['outcome'],records[3]['outcome']]}))

if __name__=='__main__':main()
