#!/usr/bin/env python3
"""Independent referee check of every completed paired-screen choice."""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys
from run import OUT,ROOT,sha

spec=importlib.util.spec_from_file_location('backport_oracle',ROOT/'astra-submissions/experiments/persistent-response-20261101/review.py')
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle);ref=oracle.ref

if __name__=='__main__':
    phase=sys.argv[1];assert phase in ('queen','broad')
    plan=json.loads((OUT/'plan.json').read_text());cases=[c for c in plan['cases'] if c['phase']==phase]
    labels=json.loads((OUT/(phase+'-labels.json')).read_text());cache={};frames=transitions=choices=0
    for c in cases:
        if c['game'] in cache:continue
        p=ROOT/'data/raw/games'/c['game']/'replay.json';assert sha(p)==c['replay_sha256'];rp=json.loads(p.read_text())
        board=ref.FowBoard();history=Counter({ref.position_key(board):1});sequence=[]
        for i,frame in enumerate(rp['frames']):
            if i:board.push_uci(frame['move']);history[ref.position_key(board)]+=1
            actual=ref.make_frame(board,frame['clocks']);assert all(actual[k]==frame[k] for k in ('board','white','black'))
            sequence.append((board.copy(),history.copy()));frames+=1
        cache[c['game']]=sequence
    for c in cases:
        rb,hist=cache[c['game']][c['ply']];answers={}
        for r in labels:
            if r['name']!=c['name']:continue
            if r['move'] not in answers:
                answer,n=oracle.probe(rb,hist,r['move'],c['side']);answers[r['move']]=answer;transitions+=n;choices+=1
            for k in ('legal','fatal','terminal','exchange_loss','queen_exchange_loss','forced_king_loss_after_capture'):
                assert answers[r['move']][k]==r[k],(c['name'],r['arm'],k)
    result=dict(phase=phase,frames_checked=frames,unique_choices_checked=choices,transitions_checked=transitions,
                referee_sha256=sha(oracle.REFPATH),oracle_sha256=sha(Path(spec.origin)),script_sha256=sha(Path(__file__)),
                labels_sha256=sha(OUT/(phase+'-labels.json')),scope='Independent bounded tactical labels, not a strength estimate.')
    with (OUT/(phase+'-referee-review.json')).open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
