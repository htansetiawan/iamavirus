#!/usr/bin/env python3
"""Audit one-ply visible capture exposure after v35/v36 replay choices.

For each fixed replay prefix, apply each logged root choice to the true
referee board, then enumerate the opponent's legal replies that capture a
visible own piece without leaving the opponent's king capturable. This is an
oracle tactical diagnostic, not an opponent policy or strength estimate.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from learning import ingest, rules

VALUES = (1, 3, 3, 5, 9, 100)
NAMES = "PNBRQK"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def position(replay: dict, states: list, row: dict, side: int, move: str) -> dict:
    ply = row["ply"]
    before = states[ply].board
    if before.move_loses_king(move):
        return {"move": move, "immediate_own_king_fatal": True,
                "visible_captures": [], "visible_vulnerable_material": 0}
    after = before.copy()
    after.push(move)
    opponent = 1 - side
    view = after.observation(opponent)
    reply_destinations = collections.defaultdict(list)
    for reply in after.legal_moves():
        dst = rules.square_index(reply[2:4])
        victim = after.piece_at(dst)
        if victim >= 0 and victim // 6 == side and not after.move_loses_king(reply):
            reply_destinations[dst].append(reply)
    captures = []
    for dst, replies in sorted(reply_destinations.items()):
        if view[dst] == "?":
            continue
        victim = after.piece_at(dst)
        captures.append({
            "square": rules.square_name(dst),
            "piece": NAMES[victim % 6].lower() if side == rules.BLACK else NAMES[victim % 6],
            "value": VALUES[victim % 6],
            "reply_moves": sorted(replies),
        })
    return {
        "move": move,
        "immediate_own_king_fatal": False,
        "visible_captures": captures,
        "visible_vulnerable_material": sum(x["value"] for x in captures),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--comparison", type=Path, action="append", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    rows = []
    replay_cache = {}
    for comparison_path in args.comparison:
        comparison = json.loads(comparison_path.read_text())
        for row in comparison["rows"]:
            game = row["game"]
            replay_path = args.raw / "games" / game / "replay.json"
            replay = replay_cache.get(game)
            if replay is None:
                replay = json.loads(replay_path.read_text())
                states, problems = ingest.validate_replay(replay)
                if problems:
                    raise ValueError(f"{game}: invalid replay: {problems[:2]}")
                replay_cache[game] = (replay, states)
            else:
                replay, states = replay
            side = (rules.WHITE if replay["whitePlayerId"] == "a2c35173659545c99752376a70418438"
                    else rules.BLACK)
            base = position(replay, states, row, side, row["v35"]["move"])
            candidate = position(replay, states, row, side, row["candidate"]["move"])
            base_mass = base["visible_vulnerable_material"]
            cand_mass = candidate["visible_vulnerable_material"]
            rows.append({
                "comparison": str(comparison_path), "game": game,
                "opponent": row["opponent"], "ply": row["ply"],
                "choice_changed": row["choice_changed"],
                "v35": base, "candidate": candidate,
                "vulnerable_material_delta": cand_mass - base_mass,
                "candidate_adds_visible_capture_target": cand_mass > base_mass,
            })
    out = {
        "classification": "one-ply true-board visible-capture availability after fixed-prefix choices; tactical diagnostic only",
        "comparisons": [{"path": str(p), "sha256": sha(p)} for p in args.comparison],
        "positions": len(rows),
        "rows": rows,
        "summary": {
            "v35_immediate_king_fatal": sum(r["v35"]["immediate_own_king_fatal"] for r in rows),
            "candidate_immediate_king_fatal": sum(r["candidate"]["immediate_own_king_fatal"] for r in rows),
            "candidate_adds_visible_capture_target": sum(r["candidate_adds_visible_capture_target"] for r in rows),
            "candidate_removes_visible_capture_target": sum(r["vulnerable_material_delta"] < 0 for r in rows),
            "candidate_visible_vulnerable_material_delta": sum(r["vulnerable_material_delta"] for r in rows),
        },
        "limits": [
            "The true board is used only by this offline audit, not as bot input.",
            "Opponent capture availability is a one-ply oracle and does not model whether an opponent notices or chooses the capture.",
            "Visible vulnerable material is the sum of distinct capturable piece values, not an expected loss; multiple targets may not all be capturable in one game continuation.",
            "No game continuation, opponent policy, or Elo estimate is included.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"positions": out["positions"], "summary": out["summary"],
                      "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
