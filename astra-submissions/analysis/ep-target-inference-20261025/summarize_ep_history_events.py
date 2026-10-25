#!/usr/bin/env python3
"""Join replay-derived history-proven EP actions to actually played EP events."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", type=Path, default=HERE / "top-opponent-ep-action-coverage.jsonl")
    ap.add_argument("--candidates", type=Path, default=HERE / "ep-history-candidate-actions.jsonl")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    candidates = set()
    for line in args.candidates.read_text().splitlines():
        row = json.loads(line)
        if row["is_true_ep"]:
            candidates.add((row["game"], row["state_ply"], row["move"]))
    totals = Counter()
    by_team: dict[str, Counter] = defaultdict(Counter)
    by_result: dict[str, Counter] = defaultdict(Counter)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as out:
        for line in args.events.read_text().splitlines():
            if not line:
                continue
            row = json.loads(line)
            match = (row["game"], row["ply"] - 1, row["move"]) in candidates
            row["history_candidate_available"] = match
            row["history_recovers_observation_patch_omission"] = match and not row["patched_available"]
            covered = row["patched_available"] or match
            row["history_augmented_available"] = covered
            out.write(json.dumps(row, separators=(",", ":")) + "\n")
            team = row[row["side"]]
            outcome = "draw" if row["result"] == "1/2-1/2" else (
                "won" if ((row["result"] == "1-0") == (row["side"] == "white")) else "lost")
            for target, key in ((totals, "all"), (by_team[team], team), (by_result[outcome], outcome)):
                target["events"] += 1
                target["baseline_omitted"] += not row["baseline_available"]
                target["observation_patch_omitted"] += not row["patched_available"]
                target["history_recovered"] += row["history_recovers_observation_patch_omission"]
                target["history_augmented_omitted"] += not covered
    summary = {
        "events": totals["events"],
        "baseline_omitted": totals["baseline_omitted"],
        "observation_patch_omitted": totals["observation_patch_omitted"],
        "history_recovered_from_patch_residual": totals["history_recovered"],
        "history_augmented_omitted": totals["history_augmented_omitted"],
        "baseline_recovered_total": totals["baseline_omitted"] - totals["history_augmented_omitted"],
        "by_moving_team": {k: dict(v) for k, v in sorted(by_team.items())},
        "by_mover_outcome": {k: dict(v) for k, v in sorted(by_result.items())},
        "events_out": str(args.out),
        "meaning": "Public replay action coverage after joining candidate move availability; no causal outcome or Elo claim."
    }
    args.out.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
