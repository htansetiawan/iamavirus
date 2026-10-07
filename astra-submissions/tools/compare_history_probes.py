#!/usr/bin/env python3
"""Paired whole-game analysis of a completed history-port experiment.

Intervals describe this retrospective corpus and one training/prior setup.
They are not Elo estimates, and they do not include variation across RNG seeds
when the experiment used only one seed.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=253)
    args = parser.parse_args()
    if args.bootstrap < 1:
        parser.error("bootstrap draws must be positive")
    state = json.loads(args.state.read_text())
    if state["state"] != "complete" or not state["inputs_unchanged"]:
        parser.error("experiment must be complete with unchanged inputs")
    runs = state["runs"]
    if len(runs) != state["job_count"] or not all(r["complete"] for r in runs):
        parser.error("missing or failed runs")
    by = {(r["game"], r["side"], r["seed"], r["prior"], r["mode"]): r for r in runs}
    if len(by) != len(runs):
        parser.error("duplicate run identity")
    groups = defaultdict(dict)
    for r in runs:
        groups[(r["prior"], r["mode"])][(r["game"], r["side"], r["seed"])] = r
    identities = set(next(iter(groups.values())))
    if not all(set(g) == identities for g in groups.values()):
        parser.error("arms must contain identical complete game seats and seeds")
    for key in identities:
        if len({(g[key]["updates"], g[key]["hidden_squares"]) for g in groups.values()}) != 1:
            parser.error("arms did not observe identical histories")

    # In mode 2, unsuccessful recovery is transactional. Without a rescue,
    # all population-derived diagnostics must equal the strict-only arm.
    coupling_checks, coupling_failures = 0, []
    same_fields = ("updates", "collapsed_updates", "random_rebuilds", "truth_held_updates",
                   "view_mismatch_updates", "continuation_invalid_updates", "evidence_conflicts",
                   "hidden_brier_sum", "hidden_log_loss_sum")
    for (prior, mode), group in groups.items():
        if mode != 2 or (prior, 1) not in groups:
            continue
        for key, h in group.items():
            if h["history_rescues"]:
                continue
            coupling_checks += 1
            different = [f for f in same_fields if h[f] != groups[(prior, 1)][key][f]]
            if different:
                coupling_failures.append({"game": key[0], "side": key[1], "seed": key[2],
                                          "prior": prior, "different": different})

    # Cluster by whole game, including all colors/seeds if present. Ratios use
    # micro denominators inside each bootstrap draw; long histories are not
    # mistakenly counted as independent samples.
    games = sorted({r["game"] for r in runs})
    game_at = {game: i for i, game in enumerate(games)}
    columns = ("updates", "truth_held_updates", "hidden_squares", "hidden_brier_sum",
               "hidden_log_loss_sum", "random_rebuilds")
    arrays = {}
    for arm, group in groups.items():
        a = np.zeros((len(games), len(columns)), dtype=np.float64)
        for r in group.values():
            a[game_at[r["game"]]] += [r[c] for c in columns]
        arrays[arm] = a
    sample = np.random.default_rng(args.seed).integers(0, len(games), (args.bootstrap, len(games)))
    metrics = {"truth_held_fraction": (1, 0), "hidden_brier": (3, 2),
               "hidden_log_loss": (4, 2), "random_rebuilds_per_update": (5, 0)}
    boot = {arm: a[sample].sum(axis=1) for arm, a in arrays.items()}
    comparisons = []
    requested = []
    for prior in sorted({p for p, _ in groups}):
        requested += [((prior, 0), (prior, 1)), ((prior, 1), (prior, 2))]
    requested += [((1, mode), (2, mode)) for mode in (0, 1, 2)]
    for before, after in requested:
        if before not in groups or after not in groups:
            continue
        result = {"before": {"prior": before[0], "mode": before[1]},
                  "after": {"prior": after[0], "mode": after[1]}, "metrics": {}}
        a, b = arrays[before].sum(axis=0), arrays[after].sum(axis=0)
        for name, (num, den) in metrics.items():
            delta = boot[after][:, num] / boot[after][:, den] - boot[before][:, num] / boot[before][:, den]
            result["metrics"][name] = {"before": a[num] / a[den], "after": b[num] / b[den],
                                      "delta": b[num] / b[den] - a[num] / a[den],
                                      "paired_game_95_interval": np.quantile(delta, [.025, .975]).tolist()}
        recognition = {"fatal_recorded_moves": 0, "before_zero_risk": 0, "after_zero_risk": 0,
                       "newly_recognized": [], "newly_missed": []}
        for key in sorted(identities):
            x, y = groups[before][key]["final_actor"], groups[after][key]["final_actor"]
            if not x or not x["true_attackers_after_actual"]:
                continue
            if x["ply"] != y["ply"] or x["actual_move"] != y["actual_move"]:
                raise ValueError("mismatched terminal labels")
            recognition["fatal_recorded_moves"] += 1
            z0, z1 = x["actual_move_king_loss_particles"] == 0, y["actual_move_king_loss_particles"] == 0
            recognition["before_zero_risk"] += z0
            recognition["after_zero_risk"] += z1
            if z0 != z1:
                recognition["newly_recognized" if z0 else "newly_missed"].append({
                    "game": key[0], "side": key[1], "seed": key[2], "ply": x["ply"],
                    "move": x["actual_move"],
                    "before_risk": x["actual_move_king_loss_particles"] / x["particles"],
                    "after_risk": y["actual_move_king_loss_particles"] / y["particles"],
                    "before_illegal_mass": x["actual_move_illegal_particles"] / x["particles"],
                    "after_illegal_mass": y["actual_move_illegal_particles"] / y["particles"]})
        result["fatal_move_recognition"] = recognition
        comparisons.append(result)
    by_opponent = {}
    for r in runs:
        key = f"prior{r['prior']}-mode{r['mode']}"
        group = by_opponent.setdefault(r["opponent"], {}).setdefault(key, {
            "runs": 0, "updates": 0, "truth_held_updates": 0, "hidden_squares": 0,
            "hidden_brier_sum": 0.0, "random_rebuilds": 0, "history_rescues": 0,
            "evidence_conflicts": 0, "fatal_recorded_moves": 0, "fatal_moves_given_zero_risk": 0})
        group["runs"] += 1
        for name in ("updates", "truth_held_updates", "hidden_squares", "hidden_brier_sum",
                     "random_rebuilds", "history_rescues", "evidence_conflicts"):
            group[name] += r[name]
        final = r["final_actor"]
        if final and final["true_attackers_after_actual"]:
            group["fatal_recorded_moves"] += 1
            group["fatal_moves_given_zero_risk"] += final["actual_move_king_loss_particles"] == 0
    for groups_for_opponent in by_opponent.values():
        for group in groups_for_opponent.values():
            group["truth_held_fraction"] = group["truth_held_updates"] / group["updates"]
            group["hidden_brier"] = group["hidden_brier_sum"] / max(1, group["hidden_squares"])
    report = {"status": "complete" if not coupling_failures else "failed coupling invariant",
              "source_state": str(args.state),
              "state_sha256": hashlib.sha256(args.state.read_bytes()).hexdigest(),
              "probe_sha256": state["binary_sha256"], "corpus_sha256": state["corpus_sha256"],
              "unique_games": len(games), "runs": len(runs), "bootstrap_draws": args.bootstrap,
              "bootstrap_seed": args.seed, "aggregates": state["aggregates"],
              "zero_rescue_coupling_checks": coupling_checks,
              "zero_rescue_coupling_failures": coupling_failures, "comparisons": comparisons,
              "by_opponent": by_opponent,
              "limitations": ["Retrospective selected losing seats, not an all-outcome sample or Elo test.",
                              "Whole-game intervals do not cover independent training or filter seed variation.",
                              "Recognizing risk in a recorded fatal action is not choosing a safer action.",
                              "A zero-risk action with illegal-particle mass is not certified safe.",
                              "Multiple exploratory contrasts; no multiplicity-adjusted promotion claim.",
                              "Timing was collected on shared host CPU resources, not isolated arena hardware."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        parser.error("output exists; preserve prior results")
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "games": len(games), "runs": len(runs),
                      "coupling_checks": coupling_checks, "coupling_failures": len(coupling_failures)}))
    if coupling_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
