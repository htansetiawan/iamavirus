"""Observation-history features for the recurrent policy. Pure: no truth here.

The tracker consumes exactly the events a bot receives -- its own colour, the
ordered 64-character observations, and the moves it chose -- and nothing else.
`model.forward` and the C++ adapter accept only what this module produces, so
anything that is not derivable from that history cannot leak into the policy.
`neural_observation.cc` mirrors this file plane for plane; the parity test in
`tests/test_feature_parity.py` drives both over the same events.

Planes, shape [32, 8, 8], indexed by the side's canonical square (rank-reflected
for Black so one network serves both colours):

    0-13   current observation: own P N B R Q K, enemy P N B R Q K, unknown,
           visible empty -- exactly one active channel per square
    14-26  last directly observed content: twelve relative piece types + empty
    27     ever directly observed
    28     age since direct observation, min(age, 100) / 100; never seen = 1
    29-30  source and destination of our most recent move
    31     en passant target inferred from permitted observations, when actionable

Scalars, shape [8]: original colour, our turn, own kingside and queenside
castling rights, the three observation-phase indicators, min(ply, 1000) / 1000.
"""
from __future__ import annotations

import numpy as np

from . import action_codec, rules

FEATURE_VERSION = "features-v1"
ACTION_VERSION = "actions-v1"
NUM_PLANES = 32
NUM_SCALARS = 8
PHASE_INITIAL, PHASE_AFTER_OWN, PHASE_AFTER_OPPONENT = 0, 1, 2
PHASE_NAMES = ("initial", "after_own_move", "after_opponent_move")
AGE_CAP = 100
PLY_CAP = 1000
CLASS_EMPTY = 12  # last-seen class for a visible empty square
CLASS_NEVER = -1

_SYMBOL_TYPE = {s: i for i, s in enumerate("PNBRQK")}


def _canonical_indices(side: int) -> np.ndarray:
    squares = np.arange(64, dtype=np.int64)
    return squares ^ 56 if side == rules.BLACK else squares


def relative_class(symbol: str, side: int) -> int:
    """0..5 own piece, 6..11 enemy piece, 12 visible empty, -1 unknown."""
    if symbol == "?":
        return CLASS_NEVER
    if symbol == "-":
        return CLASS_EMPTY
    is_white = symbol.isupper()
    own = is_white == (side == rules.WHITE)
    return _SYMBOL_TYPE[symbol.upper()] + (0 if own else 6)


class FeatureTracker:
    """Replays a single player's permitted history into model inputs."""

    def __init__(self, side: int):
        self.side = side
        self.canonical = _canonical_indices(side)
        self.last_seen = np.full(64, CLASS_NEVER, dtype=np.int8)  # by canonical square
        self.last_seen_ply = np.full(64, -1, dtype=np.int32)
        self.ever_seen = np.zeros(64, dtype=bool)
        self.kingside = True
        self.queenside = True
        self.last_own_from = -1
        self.last_own_to = -1
        self.current: str | None = None
        self.previous: str | None = None
        self.previous_phase = PHASE_INITIAL
        self.phase = PHASE_INITIAL
        self.ply = 0
        self.events = 0
        home_rank = 0 if side == rules.WHITE else 7
        self.king_home = home_rank * 8 + 4
        self.rook_homes = (home_rank * 8 + 0, home_rank * 8 + 7)  # queenside, kingside
        self.own_king = "K" if side == rules.WHITE else "k"
        self.own_rook = "R" if side == rules.WHITE else "r"

    # -- events --------------------------------------------------------------
    def observe(self, observation: str, phase: int, ply: int) -> None:
        """One real observation event. Called exactly once per delivered view."""
        if not rules.is_observation(observation):
            raise ValueError("expected a 64-character observation")
        self.previous, self.current = self.current, observation
        self.previous_phase, self.phase = self.phase, phase
        self.ply = ply
        self.events += 1
        # Own castling rights are sticky: once the king or a rook has left its
        # home square the right is gone, and a rook returning never restores it.
        if observation[self.king_home] != self.own_king:
            self.kingside = self.queenside = False
        if observation[self.rook_homes[0]] != self.own_rook:
            self.queenside = False
        if observation[self.rook_homes[1]] != self.own_rook:
            self.kingside = False
        for raw, symbol in enumerate(observation):
            if symbol == "?":
                continue
            c = self.canonical[raw]
            self.last_seen[c] = relative_class(symbol, self.side)
            self.last_seen_ply[c] = ply
            self.ever_seen[c] = True

    def record_own_move(self, uci: str) -> None:
        """Our chosen move. Updates known facts; the GRU waits for the real view."""
        f, t, _ = action_codec.parse_uci(uci)
        self.last_own_from = int(self.canonical[f])
        self.last_own_to = int(self.canonical[t])
        if f == self.king_home and self.current and self.current[f] == self.own_king:
            self.kingside = self.queenside = False
        if f == self.rook_homes[0]:
            self.queenside = False
        if f == self.rook_homes[1]:
            self.kingside = False

    # -- derived facts --------------------------------------------------------
    @property
    def our_turn(self) -> bool:
        return self.ply % 2 == self.side

    def castling_bitboard(self) -> int:
        rights = 0
        if self.queenside:
            rights |= 1 << self.rook_homes[0]
        if self.kingside:
            rights |= 1 << self.rook_homes[1]
        return rights

    def en_passant(self) -> int:
        """Raw en passant target square inferred from the bracketing views, or -1.

        Actionable only at our own decision, when the latest view follows the
        opponent's move and the previous one was taken before it.
        """
        if not self.our_turn or self.current is None:
            return -1
        if self.phase != PHASE_AFTER_OPPONENT or self.previous is None:
            return -1
        if self.previous_phase == PHASE_AFTER_OPPONENT:
            return -1  # two opponent views in a row cannot happen in the protocol
        return rules.infer_en_passant(self.previous, self.current, self.side)

    def legal_candidates(self) -> list[str]:
        """Exact legal moves, raw UCI, derived from the observation history only."""
        if self.current is None or not self.our_turn:
            return []
        return rules.legal_from_observation(self.current, self.side,
                                            self.castling_bitboard(), self.en_passant())

    # -- tensors ----------------------------------------------------------------
    def planes(self) -> np.ndarray:
        out = np.zeros((NUM_PLANES, 64), dtype=np.float32)
        if self.current is not None:
            for raw, symbol in enumerate(self.current):
                c = self.canonical[raw]
                klass = relative_class(symbol, self.side)
                out[12 if klass == CLASS_NEVER else klass, c] = 1.0
        seen = self.ever_seen
        classes = self.last_seen
        idx = np.nonzero(seen)[0]
        out[14 + classes[idx].astype(np.int64), idx] = 1.0
        out[27, seen] = 1.0
        age = np.ones(64, dtype=np.float32)
        age[seen] = np.minimum(self.ply - self.last_seen_ply[seen], AGE_CAP) / AGE_CAP
        out[28] = age
        if self.last_own_from >= 0:
            out[29, self.last_own_from] = 1.0
            out[30, self.last_own_to] = 1.0
        ep = self.en_passant()
        if ep >= 0:
            out[31, self.canonical[ep]] = 1.0
        return out.reshape(NUM_PLANES, 8, 8)

    def scalars(self) -> np.ndarray:
        return np.array([
            float(self.side), float(self.our_turn), float(self.kingside),
            float(self.queenside), float(self.phase == PHASE_INITIAL),
            float(self.phase == PHASE_AFTER_OWN),
            float(self.phase == PHASE_AFTER_OPPONENT),
            min(self.ply, PLY_CAP) / PLY_CAP,
        ], dtype=np.float32)


def candidate_arrays(candidates: list[str], side: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """(action ids, canonical from, canonical to, promotion code) for a candidate list."""
    ids = np.array([action_codec.encode_action(u, side) for u in candidates], dtype=np.int64)
    if len(ids) == 0:
        empty = np.zeros(0, dtype=np.int64)
        return ids, empty, empty, empty
    froms, tos, promos = zip(*(action_codec.split_action(int(a)) for a in ids))
    return ids, np.array(froms, dtype=np.int64), np.array(tos, dtype=np.int64), np.array(promos, dtype=np.int64)


def replay_events(side: int, observations: list[str], phases: list[int], plies: list[int],
                  own_moves: dict[int, str]) -> tuple[np.ndarray, np.ndarray]:
    """Planes and scalars for every event of a history, [E,32,8,8] and [E,8].

    `own_moves` maps an event index to the move we played right after it, so
    the tracker records it before the next observation arrives.
    """
    tracker = FeatureTracker(side)
    planes = np.zeros((len(observations), NUM_PLANES, 8, 8), dtype=np.float32)
    scalars = np.zeros((len(observations), NUM_SCALARS), dtype=np.float32)
    for i, (view, phase, ply) in enumerate(zip(observations, phases, plies)):
        tracker.observe(view, phase, ply)
        planes[i] = tracker.planes()
        scalars[i] = tracker.scalars()
        if i in own_moves:
            tracker.record_own_move(own_moves[i])
    return planes, scalars
