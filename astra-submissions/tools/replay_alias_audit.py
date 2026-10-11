#!/usr/bin/env python3
"""Audit indistinguishable opponent moves in completed replays.

The referee verifies every recorded frame. At the selected decision, enumerate
legal alternatives to the LAST opponent move from its recorded preceding board.
Keep alternatives that produce the same observation for us, then label all our
legal replies. These are a subset of history-consistent worlds, not the full
belief or an opponent posterior. Truth is used only for offline labels.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(board):
    return ''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('replays', type=Path, nargs='+')
    ap.add_argument('--ply', type=int, required=True, help='Position before our decision, after an opponent move')
    ap.add_argument('--side', choices=['white', 'black'], required=True)
    ap.add_argument('--kit', type=Path, default=Path.home()/'git/fow-starter')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    sys.path.insert(0, str(args.kit))
    import chess
    import referee
    color = args.side == 'white'
    losing_result = '0-1' if color else '1-0'
    rows = []
    for path in args.replays:
        data = path.read_bytes()
        game = json.loads(data)
        if not 1 <= args.ply < len(game['frames'])-1:
            raise ValueError('Need a preceding opponent move and a recorded own reply')
        board = referee.FowBoard()
        counts = Counter({referee.position_key(board): 1})
        before = None
        history = []
        positions = []
        for index, frame in enumerate(game['frames']):
            if frame['ply'] != index:
                raise ValueError('Nonconsecutive replay frames')
            own_move = None
            if index:
                if index == args.ply:
                    before, before_counts = board.copy(), counts.copy()
                move = chess.Move.from_uci(frame['move'])
                if referee.outcome(board, counts) or move not in referee.fow_moves(board):
                    raise ValueError(f'Illegal move or continuation after terminal at ply {index}')
                if board.turn == color:
                    own_move = move.uci()
                board.push(move)
                counts[referee.position_key(board)] += 1
            elif frame['move'] is not None:
                raise ValueError('Initial frame must not have a move')
            if encoded(board) != frame['board']:
                raise ValueError(f'Board mismatch at ply {index}')
            for side, turn in [('white', chess.WHITE), ('black', chess.BLACK)]:
                if referee.observation(board, turn) != frame[side]:
                    raise ValueError(f'Observation mismatch at ply {index}: {side}')
            if index <= args.ply:
                history.append({'ply': index, 'observation': frame[args.side], 'own_move': own_move})
            positions.append(board.copy())
        ending = referee.outcome(board, counts)
        if ending is None or ending[0] != game['result']:
            raise ValueError('Replay outcome not reproduced by the referee')
        target = positions[args.ply]
        if target.turn != color or before is None or before.turn == color:
            raise ValueError('Selected ply is not after an opponent move')
        observation = game['frames'][args.ply][args.side]
        played = game['frames'][args.ply+1]['move']
        actual_opponent = game['frames'][args.ply]['move']
        same_view = []
        for move in referee.fow_moves(before):
            child = before.copy(); child.push(move)
            reps = before_counts.copy(); reps[referee.position_key(child)] += 1
            if referee.outcome(child, reps) or referee.observation(child, color) != observation:
                continue
            legal, safe, labels = [], [], {}
            for reply in referee.fow_moves(child):
                next_board = child.copy(); next_board.push(reply)
                next_reps = reps.copy(); next_reps[referee.position_key(next_board)] += 1
                result = referee.outcome(next_board, next_reps)
                legal.append(reply.uci()); labels[reply.uci()] = result
                if result is None or result[0] != losing_result:
                    safe.append(reply.uci())
            king = child.king(color)
            attackers = [chess.square_name(s) for s in child.attackers(not color, king)]
            same_view.append({'opponent_move': move.uci(), 'is_actual': move.uci() == actual_opponent,
                              'board': encoded(child), 'fen': child.fen(),
                              'attackers_now': attackers,
                              'legal_replies': sorted(legal), 'safe_replies': sorted(safe),
                              'played_outcome': labels.get(played),
                              'played_legal': played in legal,
                              'played_loses': played in labels and bool(labels[played] and labels[played][0] == losing_result)})
        actual = next(r for r in same_view if r['is_actual'])
        shared_legal = set.intersection(*(set(r['legal_replies']) for r in same_view))
        shared_safe = set.intersection(*(set(r['safe_replies']) for r in same_view))
        legal_union = set.union(*(set(r['legal_replies']) for r in same_view))
        counts_by_move = {move: {'legal_worlds': sum(move in r['legal_replies'] for r in same_view),
                                'safe_worlds': sum(move in r['safe_replies'] for r in same_view)}
                          for move in sorted(legal_union)}
        signature = digest(json.dumps({'side':args.side, 'history':history}, sort_keys=True, separators=(',', ':')).encode())
        king = target.king(color)
        rays = []
        for square in target.attackers(not color, king):
            piece = target.piece_at(square)
            rays.append({'attacker':chess.square_name(square), 'piece':piece.symbol(),
                         'visible_to_us':observation[square] != '?',
                         'king':chess.square_name(king),
                         'between': [chess.square_name(s) for s in chess.SquareSet(chess.between(square,king))]})
        rows.append({'game':game['id'], 'replay':str(path), 'replay_sha256':digest(data),
                     'white':game['white'], 'black':game['black'],
                     'whiteVersion':game.get('whiteVersion'), 'blackVersion':game.get('blackVersion'),
                     'ply':args.ply, 'side':args.side, 'played':played, 'actual_opponent_move':actual_opponent,
                     'observable': {'history':history, 'history_sha256':signature,
                                    'last_opponent_changed_observation':history[-1]['observation'] != history[-2]['observation']},
                     'oracle': {'actual_fen':target.fen(), 'actual_attack_rays':rays,
                                'actual_safe_replies':actual['safe_replies'],
                                'same_view_worlds':len(same_view),
                                'same_view_legal_replies': sorted(shared_legal),
                                'same_view_safe_replies': sorted(shared_safe),
                                'same_view_legal_sets_agree': all(set(r['legal_replies']) == shared_legal for r in same_view),
                                'reply_counts':counts_by_move, 'worlds':same_view}})
    result = {'created_at':datetime.now(timezone.utc).isoformat(),
              'classification':'offline counterfactual reply audit; truth labels are not bot inputs or probabilities',
              'scope':'Alternatives to the last opponent move from the recorded preceding board; not exhaustive belief. Identical board-observation/own-action histories are grouped without clocks.',
              'referee_sha256':digest((args.kit/'referee.py').read_bytes()),
              'tool_sha256':digest(Path(__file__).read_bytes()),
              'observation_history_groups':dict(Counter(r['observable']['history_sha256'] for r in rows)),
              'rows':rows}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'games':len(rows), 'unique_histories':len(result['observation_history_groups']),
                      'cases':[{'game':r['game'], 'same_view_worlds':r['oracle']['same_view_worlds'],
                                'actual_safe_replies':r['oracle']['actual_safe_replies'],
                                'same_view_safe_replies':r['oracle']['same_view_safe_replies']} for r in rows]},indent=2))


if __name__ == '__main__':
    main()
