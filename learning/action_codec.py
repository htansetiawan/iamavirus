"""Action identifiers and the colour-relative coordinate transform.

    promotion_code: none=0, queen=1, rook=2, bishop=3, knight=4
    action_id = (from_square * 64 + to_square) * 5 + promotion_code

Raw API strings stay in a1..h8 order everywhere outside the model. Inside the
model Black's board is reflected rank-wise (`square ^ 56`) so that both colours
share one set of weights; White uses the identity. Every endpoint, memory map,
target and en passant square is transformed with the same function, and emitted
moves are transformed back.
"""
from __future__ import annotations

PROMOTION_CODES = {"": 0, "q": 1, "r": 2, "b": 3, "n": 4}
PROMOTION_SUFFIX = {code: suffix for suffix, code in PROMOTION_CODES.items()}
NUM_ACTIONS = 64 * 64 * 5
FILES = "abcdefgh"
RANKS = "12345678"


def square_index(name: str) -> int:
    return (ord(name[1]) - ord("1")) * 8 + (ord(name[0]) - ord("a"))


def square_name(square: int) -> str:
    return FILES[square & 7] + RANKS[square >> 3]


def canonical_square(square: int, side: int) -> int:
    """The model's view of a raw square: reflected for Black, identity for White."""
    return square ^ 56 if side == 1 else square


def raw_square(square: int, side: int) -> int:
    """Inverse of canonical_square (it is an involution)."""
    return square ^ 56 if side == 1 else square


def canonical_bitboard(mask: int, side: int) -> int:
    """Rank reflection of a bitboard: swaps rank i with rank 7-i for Black."""
    if side == 0:
        return mask
    out = 0
    for rank in range(8):
        row = (mask >> (8 * rank)) & 0xFF
        out |= row << (8 * (7 - rank))
    return out


def parse_uci(uci: str) -> tuple[int, int, int]:
    """(from_square, to_square, promotion_code) in raw coordinates."""
    if len(uci) not in (4, 5):
        raise ValueError(f"bad UCI move {uci!r}")
    suffix = uci[4:] if len(uci) == 5 else ""
    if suffix not in PROMOTION_CODES:
        raise ValueError(f"bad promotion in {uci!r}")
    return square_index(uci[:2]), square_index(uci[2:4]), PROMOTION_CODES[suffix]


def format_uci(from_square: int, to_square: int, promotion: int) -> str:
    return square_name(from_square) + square_name(to_square) + PROMOTION_SUFFIX[promotion]


def encode_action(uci: str, side: int) -> int:
    """Action id of a raw UCI move, in the side's canonical coordinates."""
    f, t, promotion = parse_uci(uci)
    f, t = canonical_square(f, side), canonical_square(t, side)
    return (f * 64 + t) * 5 + promotion


def decode_action(action_id: int, side: int) -> str:
    """Raw UCI move from a canonical action id."""
    if not 0 <= action_id < NUM_ACTIONS:
        raise ValueError(f"action id {action_id} out of range")
    promotion = action_id % 5
    pair = action_id // 5
    f, t = pair // 64, pair % 64
    return format_uci(raw_square(f, side), raw_square(t, side), promotion)


def split_action(action_id: int) -> tuple[int, int, int]:
    """(canonical from, canonical to, promotion code) of an action id."""
    promotion = action_id % 5
    pair = action_id // 5
    return pair // 64, pair % 64, promotion
