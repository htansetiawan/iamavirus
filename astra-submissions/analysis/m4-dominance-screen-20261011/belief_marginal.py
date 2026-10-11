#!/usr/bin/env python3
"""Audit the hidden-check marginal, distinct from full-board posterior mass."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True)
args=ap.parse_args();root=args.run.resolve();out=root/'marginal';out.mkdir()
sys.path.insert(0,str(root));from probe import inputs
sys.path.insert(0,str(root/'kit'));import referee
import chess
game=json.loads((root/'gjlnku86.json').read_text())
side,decision,played,feed=inputs(game,None)
env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','M4SF_'))}
env.update(MIST_FORCE_MOVES=','.join(played[:decision-1]),MIST_REPLAY_WARM='0',
    MIST_MAX_SECONDS='1',MIST_M4_ITERATIONS='100000',FOW_SEED='21',MIST_SEARCH='m4',
    MIST_REPLAY_PARENTS='20000',MIST_SAMPLES='32',MIST_M4_FAST_ROOTS='1',
    MIST_STOCKFISH=str(root/'stockfish'),MIST_REPLAY_BELIEF_DUMP=str(out/'belief.txt'))
(out/'input.txt').write_text(feed)
result=subprocess.run([str(root/'candidate')],input=feed,text=True,capture_output=True,env=env,timeout=60)
(out/'stdout.txt').write_text(result.stdout);(out/'stderr.txt').write_text(result.stderr)
assert result.returncode==0
weights={'king_already_attacked':0.,'queen_on_a4':0.}
moves=['e5d3','e5c6','c7c6'];fatal={m:0. for m in moves};counts={m:0 for m in moves}
total=0.;n=0;view=game['frames'][2*decision-1][side]
for line in (out/'belief.txt').read_text().splitlines():
    board,ep,castle,halfmove,logw=line.split();b=referee.FowBoard();b.clear_board()
    for square,piece in enumerate(board):
        if piece!='-':b.set_piece_at(square,chess.Piece.from_symbol(piece))
    b.turn=side=='white';b.ep_square=int(ep) if int(ep)>=0 else None
    b.castling_rights=int(castle,16);b.halfmove_clock=int(halfmove)
    assert referee.observation(b,b.turn)==view
    weight=math.exp(float(logw));total+=weight;n+=1
    weights['king_already_attacked']+=weight*b.is_attacked_by(not b.turn,b.king(b.turn))
    weights['queen_on_a4']+=weight*(b.piece_at(chess.A4)==chess.Piece(chess.QUEEN,chess.WHITE))
    legal=list(referee.fow_moves(b))
    for uci in moves:
        move=chess.Move.from_uci(uci);assert move in legal
        child=b.copy(stack=False);child.push(move)
        loses=child.is_attacked_by(not b.turn,child.king(b.turn))
        fatal[uci]+=weight*loses;counts[uci]+=loses
report={'game':game['id'],'side':side,'ply':2*decision-1,'belief_worlds':n,
    'all_observations_match':True,'posterior_marginals':{k:v/total for k,v in weights.items()},
    'fatal_move_marginals':{m:fatal[m]/total for m in moves},'fatal_world_counts':counts,
    'method':'Complete observations-derived belief dump after a cold decision; no truth passed to engine',
    'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'belief_sha256':hashlib.sha256((out/'belief.txt').read_bytes()).hexdigest()}
(out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
