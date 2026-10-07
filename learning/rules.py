"""Fog of War rules, observations and the C++ engine, through the C interface.

Squares are 0..63 in a1..h8 order, the arena's own convention. Colours are
0 for White and 1 for Black. Castling rights are a bitboard of rook squares
that still carry a right, exactly as referee.py's `clean_castling_rights`.

Termination follows referee.py's `outcome()` in this order after each move:
king capturable, threefold repetition, 100 plies without a capture or pawn
move, no legal move; plus the arena's 1,000-ply draw.
"""
from __future__ import annotations

import ctypes
from collections import Counter
from dataclasses import dataclass, field

from . import _native

WHITE, BLACK = 0, 1
START_BOARD = "RNBQKBNRPPPPPPPP--------------------------------pppppppprnbqkbnr"
OBSERVATION_CHARACTERS = frozenset("?-PNBRQKpnbrqk")
MOVE_BUFFER = 256 * 6 + 8
_MAX_PLIES = 1000

# Reasons the referee reports, by termination class.
NORMAL_REASONS = {
    "King capturable", "Threefold repetition", "50-move rule",
    "No legal moves", "Move limit reached",
}


def square_name(square: int) -> str:
    return "abcdefgh"[square & 7] + "12345678"[square >> 3]


def square_index(name: str) -> int:
    return (ord(name[1]) - ord("1")) * 8 + (ord(name[0]) - ord("a"))


def is_observation(text: str) -> bool:
    return len(text) == 64 and set(text) <= OBSERVATION_CHARACTERS


class Board:
    """A full game state. Mutating methods change it; `copy()` is cheap."""

    __slots__ = ("_handle",)

    def __init__(self, handle: int | None = None):
        lib = _native.library()
        self._handle = handle if handle is not None else lib.fow_position_new()

    def __del__(self):
        if getattr(self, "_handle", None):
            _native.library().fow_position_free(self._handle)
            self._handle = None

    def copy(self) -> "Board":
        return Board(_native.library().fow_position_clone(self._handle))

    @classmethod
    def from_fen(cls, fen: str) -> "Board":
        board = cls()
        if not _native.library().fow_position_set_fen(board._handle, fen.encode()):
            raise ValueError(f"bad FEN: {fen}")
        return board

    @classmethod
    def from_board_string(cls, text: str, side: int, castling: int = 0,
                          en_passant: int = -1) -> "Board":
        board = cls()
        ok = _native.library().fow_position_set_board(
            board._handle, text.encode(), side, castling, en_passant)
        if not ok:
            raise ValueError(f"bad board string: {text}")
        return board

    # -- state -----------------------------------------------------------
    @property
    def side(self) -> int:
        return _native.library().fow_position_side(self._handle)

    @property
    def en_passant(self) -> int:
        return _native.library().fow_position_en_passant(self._handle)

    @property
    def castling(self) -> int:
        return _native.library().fow_position_castling(self._handle)

    @property
    def halfmove_clock(self) -> int:
        return _native.library().fow_position_halfmove(self._handle)

    @halfmove_clock.setter
    def halfmove_clock(self, value: int) -> None:
        _native.library().fow_position_set_halfmove(self._handle, value)

    def repetition_key(self) -> int:
        return _native.library().fow_position_repetition_key(self._handle)

    def board_string(self) -> str:
        buffer = ctypes.create_string_buffer(65)
        _native.library().fow_position_board(self._handle, buffer)
        return buffer.value.decode()

    def observation(self, color: int) -> str:
        buffer = ctypes.create_string_buffer(65)
        _native.library().fow_position_observation(self._handle, color, buffer)
        return buffer.value.decode()

    def visible(self, color: int) -> int:
        return _native.library().fow_position_visible(self._handle, color)

    def king_square(self, color: int) -> int:
        return _native.library().fow_position_king_square(self._handle, color)

    def piece_at(self, square: int) -> int:
        """-1 for empty, else piece type (P N B R Q K = 0..5) + 6 * colour."""
        return _native.library().fow_position_piece_at(self._handle, square)

    def is_attacked(self, square: int, by_color: int) -> bool:
        return bool(_native.library().fow_position_is_attacked(self._handle, square, by_color))

    def own_castling(self, color: int) -> int:
        """Castling rights restricted to `color`'s rooks."""
        rank_mask = 0xFF if color == WHITE else 0xFF << 56
        return self.castling & rank_mask

    # -- moves -----------------------------------------------------------
    def legal_moves(self) -> list[str]:
        buffer = ctypes.create_string_buffer(MOVE_BUFFER)
        count = _native.library().fow_position_legal_moves(self._handle, buffer, MOVE_BUFFER)
        text = buffer.value.decode()
        moves = text.split() if text else []
        assert len(moves) == count, "move buffer overflow"
        return moves

    def push(self, uci: str) -> None:
        if not _native.library().fow_position_push(self._handle, uci.encode()):
            raise ValueError(f"illegal move {uci} in {self.board_string()}")

    def mover_lost(self) -> bool:
        """The side that just moved left its king capturable (or has none)."""
        return bool(_native.library().fow_position_mover_lost(self._handle))

    def move_loses_king(self, uci: str) -> bool:
        result = _native.library().fow_move_loses_king(self._handle, uci.encode())
        if result < 0:
            raise ValueError(f"illegal move {uci}")
        return bool(result)


def legal_from_observation(observation: str, side: int, rights: int,
                           en_passant: int = -1) -> list[str]:
    """The exact legal moves derivable from one observation."""
    buffer = ctypes.create_string_buffer(MOVE_BUFFER)
    count = _native.library().fow_legal_from_observation(
        observation.encode(), side, rights, en_passant, buffer, MOVE_BUFFER)
    if count < 0:
        raise ValueError(f"bad observation: {observation}")
    text = buffer.value.decode()
    return text.split() if text else []


def infer_en_passant(previous: str | None, current: str, side: int) -> int:
    """En passant target inferred from the views bracketing the opponent's move, or -1."""
    prev = previous.encode() if previous else None
    return _native.library().fow_infer_en_passant(prev, current.encode(), side)


@dataclass
class GameState:
    """The referee loop's state: a board plus what a board cannot carry."""

    board: Board = field(default_factory=Board)
    repetitions: Counter = field(default_factory=Counter)
    plies: int = 0
    max_plies: int = _MAX_PLIES
    moves: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.repetitions:
            self.repetitions[self.board.repetition_key()] = 1

    def copy(self) -> "GameState":
        return GameState(self.board.copy(), Counter(self.repetitions), self.plies,
                         self.max_plies, list(self.moves))

    def push(self, uci: str) -> None:
        self.board.push(uci)
        self.plies += 1
        self.moves.append(uci)
        self.repetitions[self.board.repetition_key()] += 1

    def outcome(self) -> tuple[str, str] | None:
        """(result, reason) with referee.py's ordering, or None if the game goes on."""
        board = self.board
        side = board.side
        if board.mover_lost():
            return ("1-0" if side == WHITE else "0-1", "King capturable")
        if self.repetitions[board.repetition_key()] >= 3:
            return ("1/2-1/2", "Threefold repetition")
        if board.halfmove_clock >= 100:
            return ("1/2-1/2", "50-move rule")
        if not board.legal_moves():
            return ("0-1" if side == WHITE else "1-0", "No legal moves")
        if self.plies >= self.max_plies:
            return ("1/2-1/2", "Move limit reached")
        return None


class CppEngine:
    """The C++ decision procedure, driven exactly as the protocol drives it."""

    def __init__(self, side: int, base: float = 180.0, increment: float = 2.0,
                 seed: int = 1, node_budget: int = 0, particles: int = 0):
        self._lib = _native.library()
        self._handle = self._lib.fow_engine_new(side, base, increment, seed, node_budget, particles)
        self.side = side
        self._last_view: str | None = None

    def __del__(self):
        if getattr(self, "_handle", None):
            self._lib.fow_engine_free(self._handle)
            self._handle = None

    def observe(self, observation: str, reflects_own_move: bool) -> None:
        self._last_view = observation
        self._lib.fow_engine_observe(self._handle, observation.encode(), int(reflects_own_move))

    def choose(self, remaining_seconds: float) -> str | None:
        buffer = ctypes.create_string_buffer(8)
        ok = self._lib.fow_engine_choose(self._handle, self._last_view.encode(),
                                         remaining_seconds, buffer)
        return buffer.value.decode() if ok else None

    def notify(self, uci: str) -> None:
        self._lib.fow_engine_notify(self._handle, uci.encode())
