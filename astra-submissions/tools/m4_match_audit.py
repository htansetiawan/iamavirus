#!/usr/bin/env python3
"""Independently reconstruct frozen local matches and label tactical failures.

Truth boards are used only by this retrospective audit, never sent to a bot.
One-move survival labels do not imply a winning continuation or actor-known safety.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

import chess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def material(board, side):
    values = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
              chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}
    return sum(values[p.piece_type] * (1 if p.color == side else -1)
               for p in board.piece_map().values())


def attackers(board, side, view):
    king = board.king(side)
    if king is None:
        return []
    return [{'piece': board.piece_at(sq).symbol(), 'square': chess.square_name(sq),
             'visible': view[sq] != '?'} for sq in board.attackers(not side, king)]


def audit(game, side, referee):
    own = side == 'white'
    board = referee.FowBoard()
    repetitions = Counter()
    decisions = []
    for index, frame in enumerate(game['frames']):
        assert frame['ply'] == index
        if index:
            assert referee.outcome(board, repetitions) is None, (game['id'], index, 'after terminal')
            before = board.copy(stack=False)
            move = before.parse_uci(frame['move'])
            assert move in referee.fow_moves(before)
            if board.turn == own:
                safe = []
                for candidate in referee.fow_moves(board):
                    child = board.copy(stack=False)
                    child.push(candidate)
                    counts = repetitions.copy()
                    counts[referee.position_key(child)] += 1
                    terminal = referee.outcome(child, counts)
                    if not terminal or terminal[0] != ('0-1' if own else '1-0'):
                        safe.append(candidate.uci())
                view = game['frames'][index-1][side]
                decisions.append({'ply': index-1, 'move': move.uci(), 'fen': before.fen(),
                    'safe_moves': safe, 'immediate_loss': move.uci() not in safe,
                    'material_cp': material(before, own), 'attackers_before': attackers(before, own, view),
                    'opponent_move_changed_view': index < 3 or game['frames'][index-3][side] != view})
            board.push(move)
        encoded = ''.join(board.piece_at(sq).symbol() if board.piece_at(sq) else '-' for sq in range(64))
        assert encoded == frame['board'], (game['id'], index, 'board')
        for color, key in [(True, 'white'), (False, 'black')]:
            assert referee.observation(board, color) == frame[key], (game['id'], index, key)
        repetitions[referee.position_key(board)] += 1
    assert referee.outcome(board, repetitions) == (game['result'], game['reason'])
    last_view = game['frames'][-2][side]
    return {'id': game['id'], 'side': side, 'result': game['result'], 'reason': game['reason'],
        'frames_validated': len(game['frames']), 'plies': len(game['frames'])-1,
        'terminal_attackers': attackers(board, own, last_view),
        'terminal_material_cp': material(board, own), 'decisions': decisions,
        'final_clocks': game['frames'][-1]['clocks']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.run/'manifest.json').read_text())
    referee_path = args.run/'referee.py'
    assert sha(referee_path) == manifest['artifacts']['referee.py']['sha256']
    spec = importlib.util.spec_from_file_location('frozen_referee', referee_path)
    referee = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(referee)
    rows = []
    for job in manifest['jobs']:
        path = args.run/'jobs'/job['id']/'game.json'
        if not path.exists():
            continue
        row = audit(json.loads(path.read_text()), job['side'], referee)
        row['source'] = str(path.resolve())
        row['sha256'] = sha(path)
        rows.append(row)
    report = {'classification': 'retrospective rules and one-move safety audit, not Elo evidence',
        'run': str(args.run.resolve()), 'manifest_sha256': sha(args.run/'manifest.json'),
        'referee_sha256': sha(referee_path), 'tool_sha256': sha(Path(__file__)),
        'games': rows, 'complete': len(rows) == len(manifest['jobs'])}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    for row in rows:
        print(json.dumps({k: row[k] for k in ['id','side','plies','frames_validated','terminal_material_cp','terminal_attackers']} | {'last_decision': row['decisions'][-1]}))


if __name__ == '__main__':
    main()
