#!/usr/bin/env python3
"""Audit the fixed Duck snapshot using cached public replays and course rules.

Truth is used ONLY for offline labels. A hidden attacker is not by itself proof
of a belief bug: search, aggregation and unavoidable losses remain alternatives.
No network, training, or submission is performed by this script.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning import rules
from audit_arena import attackers, square

VALUES = dict(P=1, N=3, B=3, R=5, Q=9, K=0)
TEAM = "a2c35173659545c99752376a70418438"


def material(text, side):
    white = sum((1 if c.isupper() else -1) * VALUES[c.upper()]
                for c in text if c != "-")
    return white if side == 0 else -white


def analyze(replay):
    # Older cached exports used display names in their playerId fields.
    seats = [color for color, label in enumerate(("white", "black"))
             if replay.get(label + "PlayerId") == TEAM or replay[label] == "IAmAVirus"]
    assert len(seats) == 1, replay["id"]
    side = seats[0]
    name = "white" if side == 0 else "black"
    other = "black" if side == 0 else "white"
    board = rules.Board()
    decisions = []
    for ply, frame in enumerate(replay["frames"]):
        assert frame["ply"] == ply
        assert board.board_string() == frame["board"], (replay["id"], ply, "board")
        for color, key in enumerate(("white", "black")):
            assert board.observation(color) == frame[key], (replay["id"], ply, key)
        if ply == len(replay["frames"]) - 1:
            break
        move = replay["frames"][ply + 1]["move"]
        if board.side == side:
            legal = board.legal_moves()
            safe = [m for m in legal if not board.move_loses_king(m)]
            after = board.copy()
            after.push(move)
            row = dict(ply=ply, move_number=ply // 2 + 1, move=move,
                       material_before=material(frame["board"], side),
                       legal_moves=legal, immediate_survival_moves=safe,
                       actual_loses_king=after.mover_lost(),
                       visible_enemies={square(i): c for i, c in enumerate(frame[name])
                                        if c.isalpha() and c.isupper() != (side == 0)})
            if after.mover_lost():
                king = after.king_square(side)
                row["fatal_attackers"] = [dict(square=square(s), piece=after.board_string()[s],
                                               hidden_at_decision=frame[name][s] == "?")
                                           for s in attackers(after.board_string(), king, white=side == 1)]
            if ply + 2 < len(replay["frames"]):
                reply = replay["frames"][ply + 2]["move"]
                victim = after.board_string()[rules.square_index(reply[2:4])]
                row.update(opponent_reply=reply, captured_by_reply=victim,
                           reply_source_hidden=frame[name][rules.square_index(reply[:2])] == "?",
                           material_after_reply=material(replay["frames"][ply + 2]["board"], side))
                # The reply's true move is a hindsight label, not a bot input.
            decisions.append(row)
        board.push(move)
    result = "draw" if replay["result"] == "1/2-1/2" else (
        "win" if replay["result"] == ("1-0" if side == 0 else "0-1") else "loss")
    last = decisions[-1]
    return dict(game=replay["id"], arena_version=replay[name + "Version"],
                opponent_version=replay[other + "Version"], side=name,
                result=result, reason=replay["reason"], decisions=decisions,
                terminal_survival_count=len(last["immediate_survival_moves"])
                if last["actual_loses_king"] else None)


def verify_with_referee(replay, path):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("astra_course_referee", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    board = module.FowBoard()
    native = rules.Board()
    moves_checked = 0
    for ply, frame in enumerate(replay["frames"]):
        actual = module.make_frame(board, frame["clocks"], frame["move"])
        assert all(actual[k] == frame[k] for k in ("board", "white", "black", "ply", "move"))
        if ply == len(replay["frames"]) - 1:
            break
        legal = module.fow_moves(board)
        assert {m.uci() for m in legal} == set(native.legal_moves())
        for move in legal:
            next_board = board.copy()
            next_board.push(move)
            king = next_board.king(not next_board.turn)
            loses = king is None or next_board.is_attacked_by(next_board.turn, king)
            assert loses == native.move_loses_king(move.uci()), (ply, move)
            moves_checked += 1
        uci = replay["frames"][ply + 1]["move"]
        board.push_uci(uci)
        native.push(uci)
    return dict(referee_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                frames=len(replay["frames"]), all_legal_move_survival_checks=moves_checked)


def focus_counterfactuals(replay):
    board = rules.Board()
    out = {}
    for ply, frame in enumerate(replay["frames"][:-1]):
        if ply == 52:
            move = "b1b2"
            assert frame["white"][rules.square_index("b2")] == "p"
            assert move in board.legal_moves()
            after = board.copy()
            after.push(move)
            out["27_Rxb2"] = dict(visible_target=True, immediately_fatal=after.mover_lost(),
                                   immediate_recaptures=[m for m in after.legal_moves() if m[2:4] == "b2"])
        if ply == 62:
            out["32_every_surviving_move_allows_Qg2"] = []
            for move in board.legal_moves():
                if board.move_loses_king(move):
                    continue
                after = board.copy()
                after.push(move)
                assert "a2g2" in after.legal_moves()
                after.push("a2g2")
                assert not after.mover_lost()
                safe = [m for m in after.legal_moves() if not after.move_loses_king(m)]
                assert not safe
                out["32_every_surviving_move_allows_Qg2"].append(move)
        board.push(replay["frames"][ply + 1]["move"])
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=ROOT / "astra-submissions/snapshots/2026-10-07-duck")
    parser.add_argument("--cache", type=Path, default=ROOT / "data/raw/games")
    parser.add_argument("--output", type=Path, default=ROOT / "astra-submissions/analysis/duck-bluqrpex")
    parser.add_argument("--referee", type=Path, default=Path("/home/henrytan/git/fow-starter/referee.py"))
    args = parser.parse_args()
    page = json.loads((args.snapshot / "games-page-1.json").read_text())
    assert page["nextCursor"] is None
    rows, sources = [], []
    for game in page["games"]:
        path = args.cache / game["id"] / "replay.json"
        raw = path.read_bytes()
        # Newer public list metadata supplies versions omitted in old caches.
        replay = {**game, **json.loads(raw)}
        assert replay["id"] == game["id"]
        rows.append(analyze(replay))
        sources.append(dict(game=game["id"], sha256=hashlib.sha256(raw).hexdigest()))
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "duck-decisions.json").write_text(json.dumps(rows, indent=2) + "\n")
    focus = json.loads((args.snapshot / "bluqrpex-replay.json").read_text())
    king_losses = [r for r in rows if r["result"] == "loss" and r["reason"] == "King capturable"]
    summary = dict(games=len(rows), record=dict(Counter(r["result"] for r in rows)),
                   king_losses=len(king_losses),
                   terminal_no_immediate_survival=sum(r["terminal_survival_count"] == 0 for r in king_losses),
                   terminal_survival_alternative=sum(r["terminal_survival_count"] > 0 for r in king_losses),
                   versions={str(v): dict(Counter(r["result"] for r in rows if r["arena_version"] == v))
                             for v in sorted({r["arena_version"] for r in rows})},
                   focus_counterfactuals=focus_counterfactuals(focus),
                   referee_verification=verify_with_referee(focus, args.referee), sources=sources,
                   caveats=["Snapshot aggregates different versions and repeated opponents.",
                            "Version metadata missing from old cached replays is taken from the fixed public games page.",
                            "Safe here means survives the immediate adjudication, not strategically safe or winning.",
                            "No exact arena RNG, hidden belief or private decision trace is available.",
                            "Rxb2 is a plausible missed opportunity, not a proven winning alternative."])
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "sources"}, indent=2))


if __name__ == "__main__":
    main()
