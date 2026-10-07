#!/usr/bin/env python3
"""Validate cached replays with the course referee and label terminal failures.

This is retrospective truth-board analysis, not an engine replay or Elo test.
Run with the starter kit's Python environment (python-chess is required).
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics

import chess

VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
          chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}


def raw_board(board):
    return "".join(board.piece_at(sq).symbol() if board.piece_at(sq) else "-"
                   for sq in range(64))


def material(board, side):
    return sum((1 if piece.color == side else -1) * VALUES[piece.piece_type]
               for piece in board.piece_map().values())


def review(game, replay, diagnostics, referee, team):
    frames = replay["frames"]
    ours = replay["whitePlayerId"] == team
    side = "white" if ours else "black"
    assert replay[side + "PlayerId"] == team
    assert replay[side + "Version"] == game[side + "Version"]
    board = referee.FowBoard()
    states = []
    repetitions = Counter()
    checks = 0
    for index, frame in enumerate(frames):
        assert frame["ply"] == index
        if index:
            assert referee.outcome(board, repetitions) is None, "play after terminal state"
            board.push(board.parse_uci(frame["move"]))
        assert raw_board(board) == frame["board"], (game["id"], index, "board")
        checks += 1
        for color in (chess.WHITE, chess.BLACK):
            view_key = "white" if color else "black"
            assert referee.observation(board, color) == frame[view_key], (game["id"], index, view_key)
            checks += 1
        states.append(board.copy(stack=False))
        repetitions[referee.position_key(board)] += 1
    assert referee.outcome(board, repetitions) == (replay["result"], replay["reason"])
    before = states[-2]
    loser = before.turn
    loser_key = "white" if loser else "black"
    last_move = chess.Move.from_uci(frames[-1]["move"])
    king = board.king(loser)
    before_attackers = [dict(piece=before.piece_at(sq).symbol(), square=chess.square_name(sq),
                            visible_before=frames[-2][loser_key][sq] != "?")
                        for sq in before.attackers(not loser, before.king(loser))]
    attackers = []
    for sq in board.attackers(not loser, king):
        symbol = board.piece_at(sq).symbol()
        seen = [f["ply"] for f in frames[:-1] if f[loser_key][sq] == symbol]
        # Square/symbol evidence only: two identical pieces can visit a square.
        # Never label this as a tracked piece identity.
        last_seen = max(seen) if seen else None
        stayed = (last_seen is not None and
                  all(f["board"][sq] == symbol for f in frames[last_seen:]))
        attackers.append(dict(piece=symbol, square=chess.square_name(sq),
                              visible_before=frames[-2][loser_key][sq] != "?",
                              last_seen_square_symbol_ply=last_seen,
                              square_occupied_continuously_since_seen=stayed))
    safe = []
    legal = referee.fow_moves(before)
    for move in legal:
        after = before.copy(stack=False)
        after.push(move)
        our_king = after.king(loser)
        if our_king is not None and not after.is_attacked_by(not loser, our_king):
            safe.append(move.uci())
    own_index = 0 if ours else 1
    increment = replay.get("timeControl", {}).get("incrementSeconds")
    elapsed = []
    if increment is not None:
        elapsed = [frames[i - 1]["clocks"][own_index] + increment - frames[i]["clocks"][own_index]
                   for i in range(1, len(frames)) if bool(i % 2) == ours]
        assert min(elapsed) > -0.001
    protocol = diagnostics.get("protocol") or {}
    result = "D" if replay["result"] == "1/2-1/2" else (
        "W" if replay["result"] == ("1-0" if ours else "0-1") else "L")
    own_material = [{"ply": f["ply"], "cp": material(state, ours)}
                    for f, state in zip(frames, states)]
    return dict(game=game["id"], arena_version=replay[side + "Version"], side=side,
                opponent=replay["black" if ours else "white"],
                opponent_version=replay[("black" if ours else "white") + "Version"],
                result=result, plies=game["plies"], completed_at=replay["createdAt"],
                reason=replay["reason"], validation_checks=checks,
                final_move=last_move.uci(), final_mover=loser_key,
                final_piece=before.piece_at(last_move.from_square).symbol(),
                final_king_square=chess.square_name(king),
                loser_already_under_attack=before.is_attacked_by(not loser, before.king(loser)),
                attackers_before_final_move=before_attackers,
                opponent_last_move_changed_loser_observation=frames[-3][loser_key] != frames[-2][loser_key],
                attackers=attackers, safe_immediate_alternatives=safe,
                legal_alternatives=len(legal), terminal_pre_move_fen=before.fen(),
                own_clock_at_finish=frames[-1]["clocks"][own_index],
                median_move_seconds=statistics.median(elapsed) if elapsed else None,
                max_move_seconds=max(elapsed) if elapsed else None,
                own_material_cp_before_terminal=material(before, ours),
                material_path=own_material,
                protocol_reports=diagnostics["reports"], protocol_warnings=diagnostics["warnings"],
                protocol_events=len(protocol.get("events", [])),
                protocol_truncated=protocol.get("truncated"),
                replay_url="https://www.mit.edu/~6.7980/fow/?tab=arena&game=" + game["id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--referee", type=Path, required=True)
    parser.add_argument("--team", default="a2c35173659545c99752376a70418438")
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("course_referee", args.referee)
    referee = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(referee)
    listing = json.loads((args.snapshot / "listing.json").read_text())
    rows = []
    for game in listing["games"]:
        replay = json.loads((args.snapshot / "replays" / (game["id"] + ".json")).read_text())
        diagnostics = json.loads((args.snapshot / "diagnostics" / (game["id"] + ".json")).read_text())
        rows.append(review(game, replay, diagnostics, referee, args.team))
    losses = [row for row in rows if row["result"] == "L"]
    breakdown = defaultdict(Counter)
    for row in rows:
        breakdown[row["opponent"]][row["result"]] += 1
    report = dict(
        referee_sha256=hashlib.sha256(args.referee.read_bytes()).hexdigest(),
        tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        listing_sha256=hashlib.sha256((args.snapshot / "listing.json").read_bytes()).hexdigest(),
        record=dict(Counter(row["result"] for row in rows)), opponent_records=dict(breakdown),
        replay_validation_checks=sum(row["validation_checks"] for row in rows),
        losses_with_safe_immediate_alternatives=sum(bool(row["safe_immediate_alternatives"]) for row in losses),
        losses_already_under_hidden_attack=sum(any(not a["visible_before"]
            for a in row["attackers_before_final_move"]) for row in losses),
        losses_with_hidden_final_attackers=sum(all(not a["visible_before"] for a in row["attackers"]) for row in losses),
        losses_after_unchanged_observation=sum(not row["opponent_last_move_changed_loser_observation"] for row in losses),
        protocol_report_count=sum(len(row["protocol_reports"]) for row in rows),
        protocol_warning_count=sum(len(row["protocol_warnings"]) for row in rows),
        games=rows,
        limitations=["Truth-board safe alternatives are retrospective one-move survival labels, not guaranteed wins or actor-known safety.",
                     "Public protocol has no belief population, search rows or internal stderr; it cannot identify the engine's internal cause.",
                     "Material uses fixed 100/320/330/500/900 values and is descriptive, not a Fog-of-War winning-probability estimate.",
                     "Opponent mix and ten selected completed games do not establish a version regression or Elo change."])
    (args.snapshot / "review.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("games", "limitations")}, indent=2))


if __name__ == "__main__":
    main()
