#!/usr/bin/env python3
"""Independently verify all dumped views and all new guard-action labels."""
from collections import Counter
import gzip
import importlib.util
import json
from pathlib import Path
from run import ROOT,OUT,sha,save

spec=importlib.util.spec_from_file_location('queen_posterior_oracle',ROOT/'astra-submissions/experiments/persistent-response-20261101/review.py')
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle);ref=oracle.ref

if __name__=='__main__':
    plan=json.loads((OUT/'plan.json').read_text());labels=json.loads((OUT/'truth-labelled-guards.json').read_text())
    assert json.loads((OUT/'execution.json').read_text())['status']=='complete'
    cache={};frames=worlds=transitions=actions=0
    for game in plan['games']:
        path=ROOT/game['replay_path'];assert sha(path)==game['replay_sha256'];rp=json.loads(path.read_text())
        board=ref.FowBoard();history=Counter({ref.position_key(board):1});sequence=[]
        for i,frame in enumerate(rp['frames']):
            if i:board.push_uci(frame['move']);history[ref.position_key(board)]+=1
            actual=ref.make_frame(board,frame['clocks']);assert all(actual[k]==frame[k] for k in ('board','white','black'))
            sequence.append((board.copy(),history.copy()));frames+=1
        cache[game['game']]=(rp,sequence)
    for case in plan['cases']:
        rp,sequence=cache[case['game']];expected=rp['frames'][case['ply']][('white','black')[case['side']]]
        with gzip.open(OUT/(case['name']+'.stderr.gz'),'rt') as f:
            for line in f:
                a=line.split()
                if not a or a[0]!='astra_world':continue
                board=ref.FowBoard(None);board.set_piece_map({i:ref.chess.Piece.from_symbol(c) for i,c in enumerate(a[1]) if c!='-'})
                board.turn=case['side']==0;board.castling_rights=int(a[3]);board.ep_square=None if int(a[4])<0 else int(a[4]);board.halfmove_clock=int(a[5])
                assert ref.observation(board,board.turn)==expected,(case['name'],a[1]);worlds+=1
        rb,history=sequence[case['ply']]
        for row in labels:
            if row['name']!=case['name']:continue
            actual,n=oracle.probe(rb,history,row['move'],case['side']);actions+=1;transitions+=n
            for key in ('legal','fatal','terminal','exchange_loss','queen_exchange_loss','forced_king_loss_after_capture'):
                assert actual[key]==row[key],(case['name'],row['move'],key,actual,row)
    result=dict(frames_checked=frames,dumped_world_views_checked=worlds,guard_actions_checked=actions,transitions_checked=transitions,
                referee_sha256=sha(oracle.REFPATH),oracle_sha256=sha(Path(spec.origin)),script_sha256=sha(Path(__file__)),
                labelled_sha256=sha(OUT/'truth-labelled-guards.json'),plan_sha256=sha(OUT/'plan.json'),
                scope='Independent course-referee validation. Matching the final view does not certify each hidden history or prove its probability calibration. Bounded exchange labels do not prove long-term move quality.')
    with (OUT/'referee-audit.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
