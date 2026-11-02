"""Post-hoc taxonomy/visibility description; no branch selection or model input."""
import hashlib
import json
from pathlib import Path
import sys

import chess

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT))
from learning import move_taxonomy


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    review=json.loads((OUT/'review.json').read_text());assert review['passed']
    rows=[]
    for r in review['rows']:
        name=r['job']['id'];path=OUT/name/'replay.json';assert sha(path)==r['replay_sha256']
        game=json.loads(path.read_text());branch=game['continuation']['branch_ply'];side=branch%2
        first=game['frames'][branch+1];opponent=('black','white')[side]
        destination=chess.parse_square(first['move'][2:4])
        tax=move_taxonomy.label_game(game)
        events=[m for m in tax['moves'] if m['ply']>branch]
        attackers=[]
        if game['result'] in ('1-0','0-1') and game['reason']=='King capturable':
            end=game['frames'][-1];previous=game['frames'][-2];board=chess.Board(None)
            for i,c in enumerate(end['board']):
                if c!='-':board.set_piece_at(i,chess.Piece.from_symbol(c))
            loser=chess.WHITE if game['result']=='0-1' else chess.BLACK
            key='white' if loser else 'black';king=board.king(loser)
            assert king is not None
            for square in board.attackers(not loser,king):
                attackers.append(dict(piece=board.piece_at(square).symbol(),square=chess.square_name(square),
                                      visible_after= end[key][square]!='?',
                                      square_visible_before=previous[key][square]!='?'))
        rows.append(dict(job=name,source=game['continuation']['source_game'],root_move=first['move'],
                         root_piece_hidden=first[opponent][destination]=='?',result=r['result'],censored=r['censored'],
                         continuation_events=events,terminal_attackers=attackers,replay_sha256=sha(path)))
    result=dict(post_hoc=True,rows=rows,taxonomy_sha256=sha(ROOT/'learning/move_taxonomy.py'),
                scope='Descriptions of the frozen trajectories after outcomes; neither a strategy rule nor independent strength evidence.')
    with (OUT/'taxonomy.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps([dict(job=r['job'],root_hidden=r['root_piece_hidden'],result=r['result'],terminal_attackers=r['terminal_attackers']) for r in rows]))


if __name__=='__main__':main()
