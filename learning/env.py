"""The local simulator and its player adapters.

The simulator owns the true state and delivers to each player only its own
observation events, exactly as the referee does: one view per ply to both
players, no view of a rules-decided terminal frame, and a decision only at the
clock prompt. Wall-clock forfeits are disabled in training (recorded as
`training_mode = "untimed-rules-only"`); timed conformance is a separate test.

Player adapters:
    NeuralPlayer        the recurrent policy, batched across games by the driver
    CaptureGreedyPlayer the course baseline's rule: best capture, random ties
    UniformRandomPlayer uniform over the exact legal list
    CppEnginePlayer     the repaired C++ engine through the C interface
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np

from . import features, labels, rules

TRAINING_MODE = "untimed-rules-only"
PIECE_VALUE = {0: 100, 1: 320, 2: 330, 3: 500, 4: 900, 5: 20000}


class Player:
    """Base adapter. `observe` is called once per real view; `decide` at the clock."""

    neural = False

    def observe(self, view: str, phase: int, ply: int) -> None:
        raise NotImplementedError

    def decide(self, rng: random.Random) -> str | None:
        raise NotImplementedError

    def record(self, uci: str) -> None:
        pass

    def finish(self, result: str) -> None:
        pass


class UniformRandomPlayer(Player):
    def __init__(self, side: int):
        self.tracker = features.FeatureTracker(side)

    def observe(self, view, phase, ply):
        self.tracker.observe(view, phase, ply)

    def decide(self, rng):
        moves = self.tracker.legal_candidates()
        return rng.choice(moves) if moves else None

    def record(self, uci):
        self.tracker.record_own_move(uci)


class CaptureGreedyPlayer(Player):
    """Prefers the most valuable visible capture, random tie-breaking, like baseline.py."""

    def __init__(self, side: int):
        self.side = side
        self.tracker = features.FeatureTracker(side)

    def observe(self, view, phase, ply):
        self.tracker.observe(view, phase, ply)

    def decide(self, rng):
        moves = self.tracker.legal_candidates()
        if not moves:
            return None
        view = self.tracker.current

        def gain(uci):
            target = view[rules.square_index(uci[2:4])]
            if target in "?-":
                return 0
            return PIECE_VALUE["PNBRQK".index(target.upper())]

        best = max(gain(m) for m in moves)
        return rng.choice([m for m in moves if gain(m) == best])

    def record(self, uci):
        self.tracker.record_own_move(uci)


class CppEnginePlayer(Player):
    def __init__(self, side: int, seed: int, node_budget: int = 20000, particles: int = 256):
        self.engine = rules.CppEngine(side, 180.0, 2.0, seed, node_budget, particles)
        self.reflects_own = False

    def observe(self, view, phase, ply):
        self.engine.observe(view, phase == features.PHASE_AFTER_OWN)

    def decide(self, rng):
        return self.engine.choose(60.0)

    def record(self, uci):
        self.engine.notify(uci)


@dataclass
class Transition:
    """One learner decision, measured to the learner's next decision."""
    event: int                     # index of the observation event decided on
    candidates: list[str]
    action_index: int
    log_prob: float
    value: float
    reward: float = 0.0
    terminated: bool = False
    rollout_cut: bool = False
    danger: list[int] = field(default_factory=list)
    board: str = ""


class NeuralPlayer(Player):
    """Holds the tracker and recurrent state; the driver batches the model calls."""

    neural = True

    def __init__(self, side: int, model_key: str, learner: bool = False, temperature: float = 1.0):
        self.side = side
        self.model_key = model_key
        self.learner = learner
        self.temperature = temperature
        self.tracker = features.FeatureTracker(side)
        self.hidden = None              # torch tensor [256] kept by the driver
        self.spatial = None
        self.value = 0.0
        self.observations: list[str] = []
        self.phases: list[int] = []
        self.plies: list[int] = []
        self.transitions: list[Transition] = []
        self.pending_candidates: list[str] = []
        self.last_value = 0.0

    def observe(self, view, phase, ply):
        self.tracker.observe(view, phase, ply)
        self.observations.append(view)
        self.phases.append(phase)
        self.plies.append(ply)

    def observe_inputs(self):
        return self.tracker.planes(), self.tracker.scalars()

    def score_inputs(self):
        self.pending_candidates = self.tracker.legal_candidates()
        ids, froms, tos, promos = features.candidate_arrays(self.pending_candidates, self.side)
        return froms, tos, promos

    def decide(self, rng):
        raise RuntimeError("neural players are decided by the driver")

    def record(self, uci):
        self.tracker.record_own_move(uci)


@dataclass
class GameRecord:
    seed: int
    result: str
    reason: str
    plies: int
    white_kind: str
    black_kind: str


class Game:
    """One simulator game in the lockstep driver."""

    def __init__(self, seed: int, white: Player, black: Player, max_plies: int = 1000,
                 white_kind: str = "", black_kind: str = ""):
        self.seed = seed
        self.rng = random.Random(seed)
        self.state = rules.GameState(max_plies=max_plies)
        self.players = (white, black)
        self.kinds = (white_kind, black_kind)
        self.frame = 0
        self.done = False
        self.outcome: tuple[str, str] | None = None
        self.need_delivery = True
        self.last_mover = -1

    @property
    def side_to_move(self) -> int:
        return self.state.board.side

    def phase_for(self, side: int) -> int:
        if self.frame == 0:
            return features.PHASE_INITIAL
        return features.PHASE_AFTER_OWN if self.last_mover == side else features.PHASE_AFTER_OPPONENT

    def deliver(self) -> None:
        """Both players receive the view of the current frame."""
        for side in (0, 1):
            self.players[side].observe(self.state.board.observation(side), self.phase_for(side), self.frame)
        self.need_delivery = False

    def push(self, uci: str) -> None:
        mover = self.side_to_move
        if uci not in self.state.board.legal_moves():
            # The referee's verdict: an illegal move loses. Recorded, never
            # silently repaired, so a broken adapter is visible in the stats.
            self.forfeit(mover, f"Illegal move: {uci}")
            return
        self.players[mover].record(uci)
        self.state.push(uci)
        self.last_mover = mover
        self.frame += 1
        self.outcome = self.state.outcome()
        if self.outcome is not None:
            self.done = True
            for player in self.players:
                player.finish(self.outcome[0])
        else:
            self.need_delivery = True

    def forfeit(self, side: int, reason: str) -> None:
        self.outcome = ("0-1" if side == 0 else "1-0", reason)
        self.done = True
        for player in self.players:
            player.finish(self.outcome[0])

    def record(self) -> GameRecord:
        return GameRecord(self.seed, self.outcome[0], self.outcome[1], self.frame,
                          self.kinds[0], self.kinds[1])


def danger_labels(game: Game, candidates: list[str]) -> list[int]:
    return [int(x) for x in labels.king_danger(game.state.board, candidates)]
