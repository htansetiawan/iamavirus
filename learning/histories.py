"""Per-player information histories from a validated replay.

Frame `t` is the position after `t` half-moves; `frames[t].move` produced it.
A decision at frame `t` pairs that player's history through frame `t` with the
move recorded in `frames[t+1]`. Terminal frames supply labels only: the referee
sends no observation once the game is decided.

Actor fields and labels live in separate records. Only `ActorRecord` reaches
the feature builder; `TargetRecord` is for losses, audits and evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

import numpy as np

from . import features, labels, rules

TERMINATION_NORMAL = "normal"
TERMINATION_TIME = "time"
TERMINATION_ILLEGAL = "illegal"
TERMINATION_CRASH = "crash"
TERMINATION_INFRA = "infrastructure"
TERMINATION_UNKNOWN = "unknown"


def classify_termination(result: str, reason: str) -> str:
    text = (reason or "").lower()
    if reason in rules.NORMAL_REASONS:
        return TERMINATION_NORMAL
    if "time" in text and "forfeit" in text:
        return TERMINATION_TIME
    if "illegal" in text:
        return TERMINATION_ILLEGAL
    if "infrastructure" in text or result == "*":
        return TERMINATION_INFRA
    if any(word in text for word in ("crash", "stopped", "exit", "protocol", "stdout",
                                     "malformed", "startup", "ready", "respond", "memory")):
        return TERMINATION_CRASH
    return TERMINATION_UNKNOWN


@dataclass
class ActorRecord:
    side: int
    observations: list[str]
    phases: list[int]
    plies: list[int]
    decision_event_indices: list[int]
    own_actions: list[str]              # aligned with decisions
    legal_actions: list[list[str]]      # aligned with decisions, raw UCI
    inferred_en_passant: list[int]      # aligned with decisions, raw square or -1
    castling_rights: list[int]          # aligned with decisions, bitboard


@dataclass
class TargetRecord:
    boards: list[str]                   # true board at each decision frame
    king_loss_by_action: list[list[int]]  # aligned with legal_actions
    demonstrated_actions: list[str]     # == own_actions; kept separate on purpose
    terminal_return: float
    policy_valid: list[bool]
    value_valid: list[bool]
    belief_valid: list[bool]
    danger_valid: list[bool]


@dataclass
class EpisodeMetadata:
    game_id: str
    player_id: str
    opponent_id: str
    played_version: Any
    opponent_version: Any
    submission_id: Any
    result: str
    reason: str
    termination: str
    rules_fingerprint: str
    feature_version: str = features.FEATURE_VERSION
    action_version: str = features.ACTION_VERSION
    source_hash: str = ""
    split: str = ""
    candidate_mismatches: list[dict] = field(default_factory=list)


@dataclass
class PlayerEpisode:
    actor: ActorRecord
    targets: TargetRecord
    metadata: EpisodeMetadata

    def to_dict(self) -> dict:
        return {"actor": asdict(self.actor), "targets": asdict(self.targets),
                "metadata": asdict(self.metadata)}

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerEpisode":
        return cls(ActorRecord(**data["actor"]), TargetRecord(**data["targets"]),
                   EpisodeMetadata(**data["metadata"]))

    @property
    def num_decisions(self) -> int:
        return len(self.actor.decision_event_indices)


def phase_of_frame(frame_index: int, frames: list[dict], side: int) -> int:
    if frame_index == 0:
        return features.PHASE_INITIAL
    mover = (frame_index - 1) % 2  # side that produced this frame
    return features.PHASE_AFTER_OWN if mover == side else features.PHASE_AFTER_OPPONENT


def build_episode(replay: dict, states: list[rules.GameState], side: int,
                  rules_fingerprint: str, source_hash: str = "") -> PlayerEpisode:
    """One player's history from a replay whose frames have been validated.

    `states` holds the referee state after each frame, as produced by
    `ingest.validate_replay`; it carries castling, en passant and repetition
    facts that a board string cannot.
    """
    frames = replay["frames"]
    termination = classify_termination(replay.get("result", "*"), replay.get("reason", ""))
    last = len(frames) - 1
    # A rules-decided final frame is never shown to the bots; after a bot
    # failure the final frame's view was delivered and the failed decision has
    # no recorded move, so it never becomes a demonstration either.
    delivered_through = last - 1 if termination == TERMINATION_NORMAL else last
    delivered_through = max(delivered_through, 0)

    tracker = features.FeatureTracker(side)
    observations, phases, plies = [], [], []
    decision_indices, own_actions, legal_lists, eps, rights = [], [], [], [], []
    boards, danger, mismatches = [], [], []
    key = "white" if side == rules.WHITE else "black"
    for t in range(delivered_through + 1):
        view = frames[t][key]
        phase = phase_of_frame(t, frames, side)
        tracker.observe(view, phase, t)
        observations.append(view)
        phases.append(phase)
        plies.append(t)
        if t % 2 != side or t + 1 > last:
            continue
        demonstrated = frames[t + 1].get("move")
        if not demonstrated:
            continue
        truth = states[t].board
        legal_truth = sorted(truth.legal_moves())
        legal_seen = sorted(tracker.legal_candidates())
        if legal_truth != legal_seen:
            mismatches.append({"ply": t, "observation": view, "board": frames[t]["board"],
                               "truth": legal_truth, "derived": legal_seen})
            # The sample is blocked, but the tracker still records the move so
            # later events remain faithful to the real history.
            tracker.record_own_move(demonstrated)
            continue
        decision_indices.append(t)
        own_actions.append(demonstrated)
        legal_lists.append(legal_seen)
        eps.append(tracker.en_passant())
        rights.append(tracker.castling_bitboard())
        boards.append(frames[t]["board"])
        danger.append([int(x) for x in labels.king_danger(truth, legal_seen)])
        tracker.record_own_move(demonstrated)

    normal = termination == TERMINATION_NORMAL
    n = len(decision_indices)
    actor = ActorRecord(side, observations, phases, plies, decision_indices, own_actions,
                        legal_lists, eps, rights)
    targets = TargetRecord(boards, danger, list(own_actions),
                           labels.terminal_return(replay.get("result", "*"), side) if normal else 0.0,
                           [normal] * n, [normal] * n, [True] * n, [True] * n)
    player_key = f"{key}PlayerId"
    other = "black" if side == rules.WHITE else "white"
    metadata = EpisodeMetadata(
        game_id=replay.get("id", ""),
        player_id=replay.get(player_key, replay.get(key, "")),
        opponent_id=replay.get(f"{other}PlayerId", replay.get(other, "")),
        played_version=replay.get(f"{key}Version"),
        opponent_version=replay.get(f"{other}Version"),
        submission_id=replay.get(f"{key}SubmissionId"),
        result=replay.get("result", "*"), reason=replay.get("reason", ""),
        termination=termination, rules_fingerprint=rules_fingerprint,
        source_hash=source_hash, candidate_mismatches=mismatches)
    return PlayerEpisode(actor, targets, metadata)


def replay_from_moves(game_id: str, moves: list[str], result: str, reason: str,
                      white: str = "", black: str = "") -> dict:
    """A replay dict reconstructed from a move list, for corpus files and tests."""
    state = rules.GameState()
    frames = [{"ply": 0, "board": state.board.board_string(),
               "white": state.board.observation(0), "black": state.board.observation(1),
               "move": None}]
    for uci in moves:
        state.push(uci)
        frames.append({"ply": state.plies, "board": state.board.board_string(),
                       "white": state.board.observation(0),
                       "black": state.board.observation(1), "move": uci})
    return {"id": game_id, "white": white, "black": black, "result": result,
            "reason": reason, "frames": frames, "rulesVersion": None}


def event_counts(episode: PlayerEpisode) -> dict:
    return {"events": len(episode.actor.observations),
            "decisions": episode.num_decisions,
            "phases": np.bincount(np.array(episode.actor.phases, dtype=np.int64), minlength=3).tolist()}
