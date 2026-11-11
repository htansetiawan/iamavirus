"""Candidate-level king-capture curriculum from existing audited episodes.

The danger targets already exist in learning.histories. This module selects
all king captures of non-king enemy pieces, preserving ordinary/safe captures
alongside hidden-covered fatal captures. No fit or runtime policy is included.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import chess

spec = importlib.util.spec_from_file_location("curriculum_actor_prefixes",
                                            Path(__file__).with_name("experience_index.py"))
actors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(actors)
SCHEMA = "astra-king-capture-opportunities-v1"


def candidate_inputs(prefix: dict, move: str):
    """Only actor data and the proposed action enter these inputs.

    Return None for moves outside the curriculum. Unknown is never empty.
    History keys exclude the action whose choice is the supervised target.
    """
    view = actors.unpack_view(prefix["observation"])
    own_king = "K" if prefix["side"] == 0 else "k"
    enemy_pieces = "pnbrq" if prefix["side"] == 0 else "PNBRQ"
    actors.pack_move(move)  # validate syntax before indexing its squares
    start, end = chess.parse_square(move[:2]), chess.parse_square(move[2:4])
    if view[start] != own_king or view[end] not in enemy_pieces:
        return None
    if len(move) != 4:
        raise ValueError("a king capture cannot promote")
    return dict(side=prefix["side"], ply=prefix["ply"], phase=prefix["phase"],
        observation=prefix["observation"].hex(),
        last_seen=prefix["memory"].hex(), ages=prefix["ages"].hex(),
        rights=prefix["rights"].hex(), en_passant=prefix["ep"],
        legal=prefix["legal"].hex(), candidate=move, victim=view[end].upper())


def truth_board(position: str, side: int):
    if len(position) != 64 or any(c not in "-PNBRQKpnbrqk" for c in position):
        raise ValueError("invalid complete-board target")
    board = chess.Board(None)
    board.turn = side == 0
    for square, symbol in enumerate(position):
        if symbol != "-":
            board.set_piece_at(square, chess.Piece.from_symbol(symbol))
    return board


def records(episode: dict):
    actor, targets, meta = (episode[k] for k in ("actor", "targets", "metadata"))
    n = len(actor["decision_event_indices"])
    for field in ("boards", "king_loss_by_action", "policy_valid", "danger_valid"):
        if len(targets[field]) != n:
            raise ValueError("misaligned target fields")
    if meta.get("candidate_mismatches"):
        raise ValueError("unvalidated actor candidate list")
    source = meta["source_hash"]
    if len(source) != 64 or any(c not in "0123456789abcdef" for c in source):
        raise ValueError("invalid source hash")
    for d, prefix in enumerate(actors.actor_decisions(actor)):
        legal, losses = actor["legal_actions"][d], targets["king_loss_by_action"][d]
        if len(legal) != len(losses) or any(x not in (0, 1) for x in losses):
            raise ValueError("misaligned candidate danger labels")
        selected = [(i, candidate_inputs(prefix, move)) for i, move in enumerate(legal)]
        selected = [(i, inputs) for i, inputs in selected if inputs is not None]
        if not selected:
            continue
        if not targets["danger_valid"][d]:
            raise ValueError("candidate risk target is invalid")
        board = truth_board(targets["boards"][d], actor["side"])
        view = actors.unpack_view(prefix["observation"])
        safe = sorted(move for move, loss in zip(legal, losses) if not loss)
        for i, inputs in selected:
            move = chess.Move.from_uci(legal[i])
            if (board.piece_at(move.from_square).symbol() != view[move.from_square]
                    or board.piece_at(move.to_square).symbol() != view[move.to_square]):
                raise ValueError("truth/visible capture binding mismatch")
            trial = board.copy(stack=False)
            trial.push(move)
            king = trial.king(board.turn)
            if king is None:
                raise ValueError("capture lost the mover's king object")
            cover = sorted(trial.attackers(not board.turn, king))
            if bool(cover) != bool(losses[i]):
                raise ValueError("stored C risk disagrees with capture geometry")
            danger = bool(losses[i])
            target = dict(king_loss=danger, all_cover_hidden=bool(cover) and all(view[s] == "?" for s in cover),
                cover=[dict(square=chess.square_name(s), piece=trial.piece_at(s).symbol().upper(),
                            hidden_before=view[s] == "?") for s in cover],
                played=actor["own_actions"][d] == legal[i],
                choice_valid=bool(targets["policy_valid"][d]),
                safe_alternatives=safe, avoidable=bool(safe))
            identity = dict(game=meta["game_id"], source_sha256=source, side=actor["side"],
                            ply=prefix["ply"], split=meta["split"], candidate=legal[i],
                            prefix_fingerprint=prefix["history"].hex())
            key = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            yield dict(schema=SCHEMA, sample_id=key, inputs=inputs, targets=target, metadata=identity)
