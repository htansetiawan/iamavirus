#!/usr/bin/env python3
"""Differential test of the C++ rules against referee.py.

referee.py is the arena's own rule implementation, so agreement with it is the
only definition of correctness that matters. Positions are reached by random
legal play, which covers castling, en passant, promotions and positions where a
king is already capturable far more thoroughly than hand-written cases.

Four things are compared at every position:
  * the Fog of War move list,
  * perft, which additionally exercises make/unmake,
  * each side's observation, i.e. the visibility rule,
  * the exact legal moves derivable from an observation alone.
"""
import argparse
import os
import random
import subprocess
import sys

# referee.py and vision.py come from the course starter kit. Point FOW_KIT at a
# directory containing them (the Python bot's directory works).
KIT = os.environ.get(
    'FOW_KIT',
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'bot'))
sys.path.insert(0, KIT)

sys.path.insert(0, os.path.join(KIT, 'starters', 'python'))

import chess  # noqa: E402
from referee import FowBoard, fow_moves, observation  # noqa: E402
from uniform_random import candidates, infer_en_passant  # noqa: E402


def legal_moves(view, side, rights, previous, ep):
    # The current kit folds en passant inference into candidates(); it is
    # recomputed there from the same two observations.
    del ep
    return candidates(view, side, rights, previous)

HARNESS = os.environ.get('FOW_CONFORMANCE_BINARY', '/tmp/conformance')


def raw_fen(board):
    """A FEN carrying the board's *raw* en passant square.

    board.fen() emits the en passant field only when an orthodox-legal capture
    exists, but Fog of War visibility depends on the raw square: a pawn
    capturable en passant is visible even when the capture would be pinned in
    ordinary chess. Round-tripping through board.fen() therefore loses
    information that the visibility rule needs.
    """
    rights = board.clean_castling_rights()
    castling = ''
    for mask, flag in ((chess.BB_H1, 'K'), (chess.BB_A1, 'Q'),
                       (chess.BB_H8, 'k'), (chess.BB_A8, 'q')):
        if rights & mask:
            castling += flag
    target = (chess.square_name(board.ep_square)
              if board.ep_square is not None else '-')
    return (f'{board.board_fen()} {"w" if board.turn else "b"} '
            f'{castling or "-"} {target} 0 1')


def reached_positions(games, seed):
    """Positions from random legal play, plus the observations around each move."""
    rng = random.Random(seed)
    samples = []
    for _ in range(games):
        board = FowBoard()
        previous = {chess.WHITE: None, chess.BLACK: None}
        for _ in range(rng.randint(1, 80)):
            moves = fow_moves(board)
            if not moves:
                break
            views = {side: observation(board, side) for side in (chess.WHITE, chess.BLACK)}
            samples.append((raw_fen(board), views, dict(previous),
                            board.turn, int(board.clean_castling_rights())))
            previous = views
            board.push(rng.choice(moves))
            if board.king(chess.WHITE) is None or board.king(chess.BLACK) is None:
                break
    return samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--games', type=int, default=250)
    parser.add_argument('--seed', type=int, default=20261006)
    args = parser.parse_args()

    samples = reached_positions(args.games, args.seed)
    requests, expected, labels = [], [], []

    def ask(request, want, label):
        requests.append(request)
        expected.append(str(want))
        labels.append(label)

    for fen, views, previous, turn, rights in samples:
        board = FowBoard(fen)
        ask(f'moves;{fen}',
            ' '.join(sorted(m.uci() for m in fow_moves(board))), f'moves {fen}')
        for side, name in ((chess.WHITE, '0'), (chess.BLACK, '1')):
            ask(f'visible;{fen};{name}', views[side], f'visible[{name}] {fen}')
            # Exact legal moves from the observation alone, for the side to move.
            if side != turn:
                continue
            own_rights = rights & board.occupied_co[side]
            ep = infer_en_passant(previous[side], views[side], side)
            _, moves = legal_moves(views[side], side, own_rights,
                                   previous[side], ep)
            ask(f'legal;{views[side]};{name};{own_rights};'
                f'{-1 if ep is None else ep}',
                ' '.join(sorted(m.uci() for m in moves)),
                f'legal[{name}] {fen}')
            if previous[side] is not None:
                ask(f'ep;{previous[side]};{views[side]};{name}',
                    -1 if ep is None else ep, f'ep[{name}] {fen}')

    # Perft on a sample, since it is the expensive check.
    rng = random.Random(args.seed + 1)
    for fen, _, _, _, _ in rng.sample(samples, min(40, len(samples))):
        board = FowBoard(fen)

        def perft(b, d):
            moves = fow_moves(b)
            if d <= 1:
                return len(moves)
            total = 0
            for move in moves:
                b.push(move)
                total += perft(b, d - 1)
                b.pop()
            return total

        ask(f'perft;{fen};3', perft(board, 3), f'perft3 {fen}')

    result = subprocess.run([HARNESS], input='\n'.join(requests),
                            capture_output=True, text=True)
    actual = result.stdout.splitlines()
    if len(actual) != len(requests):
        print(f'harness returned {len(actual)} answers for {len(requests)} '
              f'requests; stderr: {result.stderr[:300]}')
        return 1

    failures = 0
    by_kind = {}
    for label, want, got in zip(labels, expected, actual):
        kind = label.split()[0]
        counts = by_kind.setdefault(kind, [0, 0])
        counts[0] += 1
        if want != got:
            counts[1] += 1
            failures += 1
            if failures <= 5:
                print(f'MISMATCH {label}\n  expected: {want[:120]}\n  actual:   {got[:120]}')
    for kind in sorted(by_kind):
        total, bad = by_kind[kind]
        print(f'  {kind:10} {total - bad}/{total} match')
    print(f'{len(requests) - failures}/{len(requests)} checks agree with referee.py'
          + ('' if failures else '  -- C++ rules conform exactly'))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
