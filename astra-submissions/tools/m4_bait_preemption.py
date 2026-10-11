#!/usr/bin/env python3
"""Rule-check the king-preemption branch around public game 4bkwxxng.

This is a retrospective, full-board tactical audit of a public replay. It is
not a belief policy or playing-strength test. The referee and game are explicit
inputs so the saved result can be independently regenerated.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


def read_square(board, side, square, referee, chess):
    return referee.observation(board, side)[chess.parse_square(square)]


def winner(outcome):
    if outcome is None or outcome[0] == '1/2-1/2':
        return None
    return 'white' if outcome[0] == '1-0' else 'black'


def advance(board, repetitions, uci, referee, chess):
    move = chess.Move.from_uci(uci)
    assert move in referee.fow_moves(board), (uci, board.fen())
    side = 'white' if board.turn else 'black'
    observed_to = read_square(board, board.turn, chess.square_name(move.to_square), referee, chess)
    assert observed_to != '?', (uci, side, 'destination not visible')
    board.push(move)
    key = referee.position_key(board)
    repetitions[key] += 1
    outcome = referee.outcome(board, repetitions)
    return {'move': uci, 'mover': side, 'destination_seen': observed_to,
            'after': outcome, 'winner': winner(outcome)}


def replies(board, repetitions, referee):
    """Exhaustively record one side's legal replies and the exact rule outcome."""
    items = []
    for move in referee.fow_moves(board):
        board.push(move)
        key = referee.position_key(board)
        repetitions[key] += 1
        result = referee.outcome(board, repetitions)
        items.append({'move': move.uci(), 'outcome': result,
                      'winner': winner(result)})
        repetitions[key] -= 1
        if not repetitions[key]:
            del repetitions[key]
        board.pop()
    return items


def replay_to(game, ply, referee):
    board = referee.FowBoard()
    repetitions = Counter({referee.position_key(board): 1})
    for frame in game['frames'][1:ply + 1]:
        board.push_uci(frame['move'])
        repetitions[referee.position_key(board)] += 1
    encoded = ''.join(board.piece_at(sq).symbol() if board.piece_at(sq) else '-'
                      for sq in range(64))
    assert encoded == game['frames'][ply]['board']
    return board, repetitions


def branch(game, ply, line, referee, chess):
    board, repetitions = replay_to(game, ply, referee)
    steps = []
    for move in line:
        steps.append(advance(board, repetitions, move, referee, chess))
        if steps[-1]['winner']:
            break
    return board, repetitions, steps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--kit', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.kit))
    import referee
    import chess

    game_bytes = args.game.read_bytes()
    game = json.loads(game_bytes)
    ply = 53  # after White's Nd5, before Black's ...Qg6
    root, initial_repetitions = replay_to(game, ply, referee)
    assert game['id'] == '4bkwxxng'
    assert game['frames'][ply + 1]['move'] == 'f6g6'
    assert root.turn == chess.BLACK

    queen_fork, history, queen_steps = branch(
        game, ply, ['f6g6', 'e3e7'], referee, chess)
    assert [step['winner'] for step in queen_steps] == [None, None]
    actual_responses = replies(queen_fork, history, referee)
    actual_safe = [x for x in actual_responses if x['winner'] != 'white']
    assert len(actual_responses) == 37
    assert [x['move'] for x in actual_safe] == ['f8g8']
    _, _, played_loss = branch(
        game, ply, ['f6g6', 'e3e7', 'f8e7'], referee, chess)
    assert played_loss[-1]['winner'] == 'white'

    # From the forced immediate survival, enumerate the remaining tactic.
    after_king_escape, hist2, line2 = branch(
        game, ply, ['f6g6', 'e3e7', 'f8g8', 'e7d8'], referee, chess)
    assert all(step['winner'] is None for step in line2)
    after_queen_capture_responses = replies(after_king_escape, hist2, referee)
    black_survivors = [x for x in after_queen_capture_responses
                       if x['winner'] != 'white']
    assert len(after_queen_capture_responses) == 31
    assert [x['move'] for x in black_survivors] == ['d6e8']

    after_knight_interposition, hist3, line3 = branch(
        game, ply, ['f6g6', 'e3e7', 'f8g8', 'e7d8', 'd6e8', 'd8e8'],
        referee, chess)
    assert all(step['winner'] is None for step in line3)
    post_recapture = replies(after_knight_interposition, hist3, referee)
    assert post_recapture
    assert all(x['winner'] == 'white' for x in post_recapture)

    # Moving the king one decision earlier changes the same queen entry into
    # an ordinary queen exchange, which the rules referee marks nonterminal.
    preventive, hist4, preventive_steps = branch(
        game, ply, ['f8g8', 'e3e7'], referee, chess)
    assert all(step['winner'] is None for step in preventive_steps)
    preventive_responses = replies(preventive, hist4, referee)
    preventive_safe = [x for x in preventive_responses if x['winner'] != 'white']
    assert len(preventive_responses) == 41
    assert len(preventive_safe) == 40
    exchange, hist5, exchange_steps = branch(
        game, ply, ['f8g8', 'e3e7', 'f6e7', 'e1e7'], referee, chess)
    assert all(step['winner'] is None for step in exchange_steps)

    result = {
        'game': game['id'], 'white_version': game['whiteVersion'],
        'black_version': game['blackVersion'], 'decision_ply': ply,
        'classification': 'retrospective full-information rule audit; not an arena-strength test',
        'fen_before_black_move': root.fen(),
        'actual_black_move': game['frames'][ply + 1]['move'],
        'information': {
            'white_queen_e3_in_black_observation': read_square(root, chess.BLACK, 'e3', referee, chess),
            'black_king_f8_in_white_observation': read_square(root, chess.WHITE, 'f8', referee, chess),
            'black_queen_f6_in_black_observation': read_square(root, chess.BLACK, 'f6', referee, chess),
            'e7_in_black_observation': read_square(root, chess.BLACK, 'e7', referee, chess),
        },
        'actual_bait_branch': {
            'line': queen_steps,
            'actual_played_capture': played_loss,
            'black_reply_count_after_white_Qe7': len(actual_responses),
            'black_replies_not_losing_immediately': actual_safe,
            'forced_continuation_after_Kg8': line2 + [
                {'black_replies_after_Qxd8': len(after_queen_capture_responses),
                 'only_reply_not_losing_immediately': black_survivors},
                {'white_line_after_Ne8': line3[-1]},
                {'black_replies_after_Qxe8': len(post_recapture),
                 'all_lose_to_white': True,
                 'moves': [x['move'] for x in post_recapture]},
            ],
        },
        'earlier_king_preemption': {
            'line': preventive_steps,
            'black_reply_count_after_white_Qe7': len(preventive_responses),
            'black_replies_not_losing_immediately': len(preventive_safe),
            'queen_exchange': exchange_steps,
            'position_after_exchange': exchange.fen(),
            'outcome_after_exchange': referee.outcome(exchange, hist5),
        },
        'scope': [
            'The exhaustive reply counts use the exact Fog of War pseudo-legal move generator and terminal rules.',
            'A full-information tactical line does not alone establish a policy over a multi-board belief.',
            'At the earlier decision, the opponent queen square e3 is hidden in Black’s current observation; history/belief is needed to infer this threat.',
            'The preemptive king line establishes survival of this immediate fork, not a winning game or Elo gain.',
        ],
        'game_sha256': hashlib.sha256(game_bytes).hexdigest(),
        'referee_sha256': hashlib.sha256((args.kit / 'referee.py').read_bytes()).hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('game','decision_ply','fen_before_black_move',
        'actual_black_move','information','actual_bait_branch','earlier_king_preemption','scope')},
        indent=2))


if __name__ == '__main__':
    main()
