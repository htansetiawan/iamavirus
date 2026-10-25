#!/usr/bin/env python3
"""Compare frozen v35 and a candidate on held-out fatal hidden-arrival prefixes.

Every target game must be excluded from candidate fitting. This is a fixed
prefix diagnostic; it measures move changes and immediate true-board king
fatality only, not counterfactual game strength.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from learning import ingest, rules
from replay_v35_fatal_choices import run_case


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def board_count(trace: dict) -> int | None:
    row = trace.get("v35_truth_rank_at_target") or {}
    if isinstance(row.get("particles"), int):
        return row["particles"]
    match = re.search(r"\|P\|=(\d+)", row.get("report", ""))
    return int(match.group(1)) if match else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audit", type=Path, default=Path("astra-submissions/analysis/standing-trend-20261024/hidden-arrival-cases-ply70.json"))
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--baseline-dir", type=Path, default=Path("/tmp/iamavirus-v35-exact-trace"))
    ap.add_argument("--candidate-dir", type=Path, required=True)
    ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument("--baseline-king-guard", type=float,
                    help="override MIST_KING_GUARD for the baseline arm")
    ap.add_argument("--candidate-king-guard", type=float,
                    help="override MIST_KING_GUARD for the candidate arm")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    audit = json.loads(args.audit.read_text())
    cases = audit["examples"]
    if len({case["game"] for case in cases}) != len(cases):
        raise SystemExit("target cases must be one per game")
    rows = []
    by_opponent = {}
    started = time.monotonic()
    for index, case in enumerate(cases, 1):
        replay = json.loads((args.raw / "games" / case["game"] / "replay.json").read_text())
        states, problems = ingest.validate_replay(replay)
        if problems:
            raise ValueError(f"{case['game']}: invalid replay: {problems[:2]}")
        side = rules.WHITE if replay["white"] == "IAmAVirus" else rules.BLACK
        results = {}
        for arm, binary_dir, king_guard in (
            ("v35", args.baseline_dir, args.baseline_king_guard),
            ("candidate", args.candidate_dir, args.candidate_king_guard),
        ):
            result = run_case(case, replay, binary_dir, args.seconds, 300.0, king_guard)
            move = result["v35_replayed_choice"]
            fatal = states[case["ply"]].board.move_loses_king(move)
            results[arm] = {
                "move": move,
                "immediate_fatal": fatal,
                "listed_safe_alternative": move in case["safe_alternatives"],
                "truth_rank": result["v35_truth_rank_at_target"],
                "belief_size": board_count(result),
                "risk": result["chosen_move_risk"],
                "runtime_seconds": result.get("runtime_seconds"),
            }
        out = {"game": case["game"], "opponent": case["opponent"], "ply": case["ply"],
               "recorded_fatal_move": case["move"], "safe_alternatives": case["safe_alternatives"],
               "v35": results["v35"], "candidate": results["candidate"],
               "choice_changed": results["v35"]["move"] != results["candidate"]["move"],
               "fatality_changed": results["v35"]["immediate_fatal"] != results["candidate"]["immediate_fatal"]}
        rows.append(out)
        by_opponent.setdefault(case["opponent"], []).append(out)
        if index % 5 == 0 or index == len(cases):
            partial = {"state": "running", "completed": index, "planned": len(cases), "rows": rows}
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(partial, indent=2) + "\n")
            print(json.dumps({"completed": index, "planned": len(cases), "elapsed_seconds": round(time.monotonic()-started, 1)}), flush=True)

    def summary(items):
        base_fatal = sum(x["v35"]["immediate_fatal"] for x in items)
        cand_fatal = sum(x["candidate"]["immediate_fatal"] for x in items)
        return {
            "n": len(items), "changed": sum(x["choice_changed"] for x in items),
            "v35_immediate_fatal": base_fatal, "candidate_immediate_fatal": cand_fatal,
            "fatal_saved": sum(x["v35"]["immediate_fatal"] and not x["candidate"]["immediate_fatal"] for x in items),
            "fatal_introduced": sum(not x["v35"]["immediate_fatal"] and x["candidate"]["immediate_fatal"] for x in items),
            "candidate_listed_safe_alternative": sum(x["candidate"]["listed_safe_alternative"] for x in items),
            "full_model_beliefs_le_10000": sum(x["candidate"]["belief_size"] is not None and x["candidate"]["belief_size"] <= 10000 for x in items),
        }
    report = {
        "classification": "game-excluded fixed-prefix, one-ply safety diagnostic; not Elo or game strength",
        "audit": str(args.audit), "audit_sha256": sha(args.audit),
        "baseline_binary_sha256": sha(args.baseline_dir / "mist"),
        "candidate_binary_sha256": sha(args.candidate_dir / "mist"),
        "target_games": len(cases), "seconds_per_move": args.seconds,
        "king_guard": {"baseline": args.baseline_king_guard,
                       "candidate": args.candidate_king_guard},
        "summary": summary(rows),
        "by_opponent": {name: summary(items) for name, items in sorted(by_opponent.items())},
        "elapsed_seconds": time.monotonic() - started,
        "limits": ["All cases were selected from historical IAmAVirus losses and are not representative of all decisions.",
                   "Only immediate true-board king fatality and a capped list of safe alternatives are measured.",
                   "Changed moves are not branched through opponent strategies; no material, positional, or Elo conclusion follows."],
        "rows": rows,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"summary": report["summary"], "by_opponent": report["by_opponent"],
                      "elapsed_seconds": report["elapsed_seconds"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
