"""Truth-dependent labels. Everything here reads the full board; nothing here
may be imported by the feature builder, the model, or the C++ adapter.
"""
from __future__ import annotations

import numpy as np

from . import rules

NUM_BELIEF_CLASSES = 7  # enemy P N B R Q K, no enemy piece
NO_ENEMY = 6
_SYMBOL_TYPE = {s: i for i, s in enumerate("PNBRQK")}


def hidden_enemy_classes(board: str, observation: str, side: int) -> tuple[np.ndarray, np.ndarray]:
    """Per raw square: enemy class from the true board, and a mask of hidden squares.

    Visible squares get a class too (the adapter enforces visible facts
    directly), but only the hidden ones carry belief loss.
    """
    classes = np.full(64, NO_ENEMY, dtype=np.int8)
    hidden = np.zeros(64, dtype=bool)
    enemy_is_white = side == rules.BLACK
    for square, symbol in enumerate(board):
        if symbol != "-" and symbol.isupper() == enemy_is_white:
            classes[square] = _SYMBOL_TYPE[symbol.upper()]
        hidden[square] = observation[square] == "?"
    return classes, hidden


def king_danger(truth: rules.Board, candidates: list[str]) -> np.ndarray:
    """1 where a candidate leaves the mover's king capturable on the true board.

    A counterfactual one-move label under the official terminal rule, not the
    eventual game result.
    """
    return np.array([int(truth.move_loses_king(uci)) for uci in candidates], dtype=np.int8)


def terminal_return(result: str, side: int) -> float:
    if result == "1-0":
        return 1.0 if side == rules.WHITE else -1.0
    if result == "0-1":
        return -1.0 if side == rules.WHITE else 1.0
    return 0.0
