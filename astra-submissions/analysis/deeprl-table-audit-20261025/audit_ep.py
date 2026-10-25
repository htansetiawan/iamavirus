"""Referee-backed EP exposure audit; never infer a pawn from move displacement.

Run with fow-starter/.venv/bin/python. Replays must start at the standard position.
Checks every full board and both observations, then counts only nonterminal
candidate turns. Uses the gate manifest, not a changing directory glob.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--referee-dir', type=Path, required=True)
    args = p.parse_args()
    sys.path.insert(0, str(args.referee_dir.resolve()))
    import chess
    from referee import FowBoard, make_frame, outcome, position_key

    raw = args.manifest.read_bytes()
    manifest = json.loads(raw)
    rows = []
    for record in manifest['games']:
        path = Path(record['replay'])
        data = path.read_bytes()
        replay = json.loads(data)
        side = record['candidate_color']
        candidate = side == 'white'
        board = FowBoard()
        repetitions = Counter({position_key(board): 1})
        actionable, terminal_only, recorded_ep = [], [], []
        ended = None
        for index, frame in enumerate(replay['frames']):
            if index:
                assert ended is None, (path, index, 'moves after terminal')
                move = board.parse_uci(frame['move'])
                if board.turn == candidate and board.is_en_passant(move):
                    recorded_ep.append({'ply': frame['ply'], 'move': frame['move']})
                board.push(move)
                repetitions[position_key(board)] += 1
            expected = make_frame(board, frame['clocks'], frame['move'])
            for key in ('ply', 'board', 'white', 'black'):
                assert frame[key] == expected[key], (path, index, key)
            ended = outcome(board, repetitions)
            if board.turn == candidate:
                moves = [m.uci() for m in board.generate_pseudo_legal_ep()]
                if moves:
                    event = {'ply': frame['ply'], 'preceding_move': frame['move'],
                             'ep_moves': moves}
                    (terminal_only if ended else actionable).append(event)
        if ended:
            assert tuple(ended) == (replay['result'], replay['reason']), path
        rows.append({'replay': str(path), 'sha256': hashlib.sha256(data).hexdigest(),
                     'candidate_color': side, 'frames_checked': len(replay['frames']),
                     'actionable': actionable, 'terminal_only': terminal_only,
                     'selected_ep': recorded_ep})
    print(json.dumps({'manifest_sha256': hashlib.sha256(raw).hexdigest(),
                      'referee_sha256': hashlib.sha256(
                          (args.referee_dir/'referee.py').read_bytes()).hexdigest(),
                      'completed_games': len(rows),
                      'actionable_count': sum(len(r['actionable']) for r in rows),
                      'selected_ep_count': sum(len(r['selected_ep']) for r in rows),
                      'games': rows}, indent=2))


if __name__ == '__main__':
    main()
