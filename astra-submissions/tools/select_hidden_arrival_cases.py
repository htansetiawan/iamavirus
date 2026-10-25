#!/usr/bin/env python3
"""Select v35 fatal-choice cases where the last unseen move delivered the attacker.

This creates a reproducible targeted subset for exact-binary replay ablations;
it does not label a move policy or estimate strength.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from learning import ingest, rules
from replay_v35_fatal_choices import true_attackers_after


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def select(rows: list[dict], raw: Path, max_ply: int) -> list[dict]:
    selected = []
    for row in rows:
        if row["ply"] == 0 or row["ply"] > max_ply:
            continue
        replay = json.loads((raw / "games" / row["game"] / "replay.json").read_text())
        states, problems = ingest.validate_replay(replay)
        if problems:
            raise ValueError(f"{row['game']}: invalid replay: {problems[:2]}")
        side = rules.WHITE if replay["white"] == "IAmAVirus" else rules.BLACK
        view_key = "white" if side == rules.WHITE else "black"
        ply = row["ply"]
        last_move = replay["frames"][ply].get("move")
        if not last_move:
            continue
        before = replay["frames"][ply - 1][view_key]
        after = replay["frames"][ply][view_key]
        square = lambda s: (int(s[1]) - 1) * 8 + ord(s[0]) - 97
        attackers = true_attackers_after(states[ply].board, row["move"], side)
        arrivals = [a for a in attackers
                    if last_move[2:4] == a["from"]
                    and before[square(last_move[:2])] == "?"
                    and after[square(last_move[2:4])] == "?"]
        if not arrivals:
            continue
        item = dict(row)
        item["hidden_arrival_context"] = {
            "opponent_move": last_move,
            "attacker_squares": [a["from"] for a in arrivals],
            "attacker_pieces": [a["piece"] for a in arrivals],
            "origin_hidden_before": True,
            "destination_hidden_after": True,
        }
        selected.append(item)
    return selected


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audit", type=Path,
                    default=Path("astra-submissions/analysis/standing-trend-20261024/king-choice-audit.json"))
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--max-ply", type=int, default=70)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    source = json.loads(args.audit.read_text())
    rows = select(source["fatal_choices_with_safe_alternatives_examples"], args.raw, args.max_ply)
    result = {
        "classification": "targeted replay subset: fatal choices with an immediately preceding wholly unseen attacker arrival",
        "source_audit": str(args.audit),
        "source_audit_sha256": sha(args.audit),
        "max_ply": args.max_ply,
        "selection_rule": "last opponent move destination equals a true-board attacker square after the recorded fatal action; last-move origin is hidden before it and destination is hidden afterward",
        "count": len(rows),
        "by_opponent": dict(collections.Counter(x["opponent"] for x in rows)),
        "examples": rows,
        "limits": ["Selected from recorded losing decisions with at least one true-board immediate-safe actor-legal alternative.",
                   "This is a targeted failure subset, not a random sample or strength estimate.",
                   "A changed action is only labeled for immediate true-board king fatality; no counterfactual game is played."],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"count": len(rows), "by_opponent": result["by_opponent"],
                      "source_audit_sha256": result["source_audit_sha256"],
                      "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
