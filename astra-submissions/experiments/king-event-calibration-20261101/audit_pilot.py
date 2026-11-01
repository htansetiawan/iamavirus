#!/usr/bin/env python3
"""Cross-check collected pilot candidate labels directly with the course referee."""
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(Path.home()/'git/fow-starter'))
import chess
import referee

OUT=ROOT/'astra-submissions/analysis/king-event-calibration-20261101'
plan=json.loads((OUT/'plan.json').read_text())
pilot=json.loads((OUT/'receipt-pilot.json').read_text());assert pilot['state']=='complete'
count=0;frames=0
for game in plan['games'][:pilot['limit']]:
    replay=json.loads(Path(game['replay_path']).read_text());board=referee.FowBoard()
    repetitions=Counter({referee.position_key(board):1})
    by_ply=defaultdict(list)
    for line in (OUT/'games'/f"{game['game']}.jsonl").read_text().splitlines():
        row=json.loads(line);by_ply[row['ply']].append(row)
    for ply,frame in enumerate(replay['frames']):
        if ply:
            board.push(chess.Move.from_uci(frame['move']));repetitions[referee.position_key(board)]+=1
        text=''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64))
        assert text==frame['board']
        assert referee.observation(board,chess.WHITE)==frame['white']
        assert referee.observation(board,chess.BLACK)==frame['black'];frames+=1
        for row in by_ply[ply]:
            move=chess.Move.from_uci(row['move']);assert move in referee.fow_moves(board)
            child=board.copy();child.push(move);rep=repetitions.copy();rep[referee.position_key(child)]+=1
            result=referee.outcome(child,rep)
            lost=bool(result and result[0]==('0-1','1-0')[row['side']])
            assert lost==bool(row['fatal']),(game['game'],ply,row['move'],result,row['fatal'])
            count+=1
report={'games':pilot['limit'],'frames':frames,'candidate_labels':count,'mismatches':0,
        'referee_sha256':hashlib.sha256(Path(referee.__file__).read_bytes()).hexdigest()}
(OUT/'pilot-referee-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
