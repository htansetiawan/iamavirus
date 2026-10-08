#!/usr/bin/env python3
"""Audit frozen whole-replay belief probes, including their terminal blind spots."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(root, draws=10000):
    campaign = json.loads((root / "campaign.json").read_text())
    if campaign["state"] != "complete":
        raise ValueError("campaign is incomplete")
    by_arm, inputs, seats, terminal = {}, {}, None, {}
    for arm in campaign["arms"]:
        directory = root / arm
        state = json.loads((directory / "state.json").read_text())
        if state["state"] != "complete" or not state["inputs_unchanged"]:
            raise ValueError(f"incomplete or changed arm: {arm}")
        inputs[arm] = {"state_sha256": sha(directory / "state.json"),
                       "runs_sha256": sha(directory / "runs.jsonl"),
                       "binary_sha256": state["binary_sha256"],
                       "corpus_sha256": state["corpus_sha256"],
                       "runner_sha256": state["runner_source_sha256"]}
        runs = [json.loads(line) for line in (directory / "runs.jsonl").read_text().splitlines()]
        keys = {(r["game"], r["side"], r["prior"], r["seed"], r["moves_sha256"]) for r in runs}
        if len(keys) != len(runs) or (seats is not None and keys != seats):
            raise ValueError("duplicate or unmatched seats")
        seats = keys
        groups = defaultdict(lambda: defaultdict(Counter))
        terminal[arm] = []
        for run in runs:
            path = Path(run["trace"])
            if not run["complete"] or sha(path) != run["trace_sha256"]:
                raise ValueError(f"failed run or changed trace: {path}")
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            if [r["ply"] for r in rows] != list(range(run["expected_updates"])):
                raise ValueError("missing or duplicated observation plies")
            count = groups[str(run["prior"])][run["game"]]
            for row in rows:
                count.update({"updates": 1, "truth_held": int(row["truth_board_matches"] > 0),
                              "hidden_squares": row["hidden_squares"],
                              "hidden_brier_sum": row["hidden_brier_sum"],
                              "hidden_log_loss_sum": row["hidden_log_loss_sum"],
                              "rebuilds": int(row["collapsed"] and not row.get("history_recovered", False)),
                              "view_mismatches": int(row["exact_observation_matches"] != row["particles"]),
                              "continuation_invalid": int(row["continuation_invalid_particles"] > 0),
                              "prefix_capped": int(row["successor_prefix_capped"]),
                              "expanded_predecessors": row["expanded_predecessors"],
                              "enumerated_transitions": row["enumerated_transitions"],
                              "prediction_constraint_rejected": row["prediction_constraint_rejected"],
                              "observe_ms_sum": row["observe_ms"]})
            # Restrict fatal labels to the arena-recorded terminal losing move.
            # Earlier recorded moves, winners' final turns and draws are excluded.
            lost = run["result"] == ("0-1" if run["side"] == 0 else "1-0")
            if lost and run["reason"] == "King_capturable":
                row = run["final_actor"]
                if row["ply"] != run["expected_updates"] - 1 or row["ply"] % 2 != run["side"]:
                    raise ValueError("terminal losing move does not match final actor")
                attackers = row["true_attackers_after_actual"]
                if not attackers:
                    raise ValueError("recorded king-capturable loss lacks a true attacker")
                zero = row["actual_move_king_loss_particles"] == 0
                count.update({"terminal_losses": 1, "terminal_zero_risk": int(zero),
                              "terminal_attacker_held": int(any(a["held_particles"] > 0 for a in attackers)),
                              "terminal_unsupported_move": int(row["actual_move_illegal_particles"] > 0)})
                terminal[arm].append({"game": run["game"], "side": run["side"], "prior": run["prior"],
                                      "seed": run["seed"], "ply": row["ply"], "move": row["actual_move"],
                                      "zero_risk": zero, "risk_particles": row["actual_move_king_loss_particles"],
                                      "illegal_particles": row["actual_move_illegal_particles"],
                                      "particles": row["particles"], "attackers": attackers})
        by_arm[arm] = {prior: dict(games) for prior, games in groups.items()}
    if len({(v["binary_sha256"], v["corpus_sha256"], v["runner_sha256"]) for v in inputs.values()}) != 1:
        raise ValueError("arms used different binaries, corpora or runners")
    aggregates = {}
    for arm, priors in by_arm.items():
        aggregates[arm] = {}
        for prior, games in priors.items():
            counts = Counter()
            for game in games.values():
                counts.update(game)
            values = dict(counts)
            values.update(truth_held_fraction=counts["truth_held"] / counts["updates"],
                          hidden_brier=counts["hidden_brier_sum"] / counts["hidden_squares"],
                          hidden_log_loss=counts["hidden_log_loss_sum"] / counts["hidden_squares"])
            aggregates[arm][prior] = values
    comparisons = {}
    metrics = {"truth_held_fraction": ("truth_held", "updates"),
               "hidden_brier": ("hidden_brier_sum", "hidden_squares"),
               "terminal_zero_risk_fraction": ("terminal_zero_risk", "terminal_losses")}
    for arm, priors in by_arm.items():
        if arm == "control":
            continue
        comparisons[arm] = {}
        for prior, games in priors.items():
            names = sorted(games)
            control = by_arm["control"][prior]
            if names != sorted(control):
                raise ValueError("unmatched games")
            indices = np.random.default_rng(253).integers(len(names), size=(draws, len(names)))
            results = {}
            for label, (numerator, denominator) in metrics.items():
                a, b = (np.array([source[g][numerator] for g in names]) for source in (control, games))
                n = np.array([control[g][denominator] for g in names])
                np.testing.assert_array_equal(n, [games[g][denominator] for g in names])
                weights = n[indices].sum(1)
                valid = weights > 0
                values = (b - a)[indices].sum(1)[valid] / weights[valid]
                results[label] = {"candidate_minus_control": float((b-a).sum() / n.sum()) if n.sum() else None,
                                  "paired_game_bootstrap_95": np.percentile(values, [2.5, 97.5]).tolist() if len(values) else None}
            comparisons[arm][prior] = results
    return {"recorded_at": datetime.now(timezone.utc).isoformat(), "root": str(root), "inputs": inputs,
            "aggregates": aggregates, "comparisons_to_control": comparisons, "terminal_losses": terminal,
            "limitations": ["Single seed and 24 games; validation of belief diagnostics, not strength or Elo.",
                            "Both seats of a game are clustered together for paired resampling.",
                            "Only arena-labelled terminal king-capturable losses define the fatal tail.",
                            "Unsupported actual moves can yield zero risk; their counts are reported separately.",
                            "Observe timing shares a CPU with compilation and is not an isolated speed comparison."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = summarize(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    for arm, priors in report["aggregates"].items():
        for prior, r in priors.items():
            print(arm, prior, json.dumps({k: r.get(k, 0) for k in ("truth_held", "updates", "hidden_brier", "rebuilds", "terminal_losses", "terminal_zero_risk", "terminal_attacker_held", "prefix_capped", "enumerated_transitions")}))


if __name__ == "__main__":
    main()
