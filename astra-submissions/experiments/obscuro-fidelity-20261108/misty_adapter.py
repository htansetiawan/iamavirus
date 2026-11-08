"""Local Brian Liou Misty adapter with course observation-derived actions.

Separate from the frozen 257 adapter. This is not Brian Hu Zhang's Obscuro.
The engine sees only its observations, own moves and clock. Course tracker
source and native package dependencies must be pinned in each future run.
"""
import os
from pathlib import Path
import sys

import chess

COURSE = Path('/home/henrytan/git/fow-starter')
sys.path.insert(0, str(COURSE))
from uniform_random import ObservationTracker
from fow_chess.engine_profile import PROFILES
from fow_chess.observation import Observation
from fow_chess.selfplay import PerspectiveView
from fow_chess import engine_v2


def parse_view(text):
    visible = chess.SquareSet()
    pieces = {}
    for square, symbol in enumerate(text):
        if symbol == '?':
            continue
        visible.add(square)
        if symbol != '-':
            pieces[square] = chess.Piece.from_symbol(symbol)
    return visible, pieces


def own_squares(text, color):
    return {square for square, symbol in enumerate(text)
            if symbol not in '?-' and symbol.isupper() == (color == chess.WHITE)}


def main():
    if sys.stdin.readline().strip() != 'fow':
        return
    side, base, increment = sys.stdin.readline().split()
    color = chess.WHITE if side == 'w' else chess.BLACK
    strategy = PROFILES[os.environ.get('MISTY_PROFILE', 'v1.6')].build_strategy(
        seed=int(os.environ.get('FOW_SEED', '1')),
        time_budget_seconds=float(os.environ.get('MISTY_BUDGET', '0')) or None,
        p_max_size=getattr(engine_v2, '_DEFAULT_P_MAX_SIZE', None))
    strategy.reset(color)
    tracker = ObservationTracker(color)
    previous = None
    pending_own = None
    print('ready', flush=True)
    for raw in sys.stdin:
        text = raw.strip()
        if len(text) == 64 and set(text) <= set('PNBRQKpnbrqk-?'):
            tracker.observe(text)
            visible, pieces = parse_view(text)
            if previous is None:
                pass
            elif pending_own is not None:
                strategy.observe_own_move(pending_own, Observation(
                    visibility_mask=visible, visible_pieces=pieces))
                pending_own = None
            else:
                lost = own_squares(previous, color)-own_squares(text, color)
                captured = next(iter(lost)) if len(lost) == 1 else None
                landing = captured if captured in pieces and pieces[captured].color != color else None
                strategy.observe_opp_move(Observation(visibility_mask=visible,
                    visible_pieces=pieces, own_capture_square=captured,
                    opp_capture_landing_square=landing))
            previous = text
            continue
        try:
            remaining = float(text)
        except ValueError:
            continue
        legal = tracker.legal_moves()
        if not legal:
            raise RuntimeError('Clock prompt with no observation-derived legal move')
        visible, pieces = parse_view(previous)
        view = PerspectiveView(perspective=color, own_legal_moves=legal,
            visible_squares=visible, visible_piece_map=pieces,
            clock_remaining_ms=int(remaining*1000), increment_ms=int(float(increment)*1000))
        move = strategy.pick_move(view)
        if move not in legal:
            print(f'adapter: inadmissible engine move {move}; using legal fallback', file=sys.stderr, flush=True)
            move = legal[0]
        tracker.record_move(move)
        pending_own = move
        print(f'move {move.uci()}', flush=True)


if __name__ == '__main__':
    main()
