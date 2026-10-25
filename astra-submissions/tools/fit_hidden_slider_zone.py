#!/usr/bin/env python3
"""Fit one hidden-slider king-zone interaction against the frozen v35 prior.

The input is produced by extract_move_model_dataset.py using the research
feature oracle with MM_HIDDEN_SLIDER_ZONE appended at index 28. This keeps all
v35 logits fixed and fits only the added coefficient. Games are split
chronologically; uncertainty is bootstrapped by whole test game.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fit_conditional_prior import (
    THETA_FULL,
    fit_delta,
    load_groups,
    score,
    split_games,
)

THETA_CHEAP = np.asarray([
    0.7705, 3.6690, 0.0, -0.5296, -0.6920, -0.2792, -0.7406, -0.4606,
    0.1304, 2.3256, 1.3647, -0.6156, -1.4760, -0.1127, 0.7298, 1.5767,
    1.6693, 1.0416, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
], dtype=np.float64)


def per_group_nll(groups, theta):
    result = []
    for group in groups:
        rows = group["rows"]
        logits = np.asarray([np.dot(row[0], theta) for row in rows], dtype=np.float64)
        peak = float(logits.max())
        logz = peak + float(np.log(np.exp(logits - peak).sum()))
        result.append(logz - float(logits[group["label"]]))
    return np.asarray(result)


def bootstrap_game_delta(groups, control, candidate, replicates=5000, seed=734091):
    by_game = {}
    for group, a, b in zip(groups, control, candidate):
        by_game.setdefault(group["game"], []).append(float(b - a))
    game_deltas = np.asarray([np.mean(v) for v in by_game.values()])
    rng = np.random.default_rng(seed)
    n = len(game_deltas)
    samples = rng.integers(0, n, size=(replicates, n))
    means = game_deltas[samples].mean(axis=1)
    return {
        "games": n,
        "mean_delta_candidate_minus_v35": float(game_deltas.mean()),
        "ci95": [float(x) for x in np.quantile(means, [0.025, 0.975])],
        "replicates": replicates,
        "seed": seed,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset", type=Path)
    ap.add_argument("--base", choices=("full", "cheap"), default="full",
                    help="fit against the v35 full or cheap runtime prior")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    if not args.dataset.is_file():
        raise SystemExit(f"dataset not found: {args.dataset}")

    groups, meta, invalid = load_groups(args.dataset)
    if args.base == "cheap":
        # The archived cheap extractor returns after the 18 basic features.
        # Preserve only those and the newly computed index-28 feature.
        for group in groups:
            group["rows"] = [
                (features[:18] + [0.0] * 10 + [features[28]], label, move, actor)
                for features, label, move, actor in group["rows"]
            ]
    train_ids, valid_ids, test_ids = split_games(meta)
    train = [g for g in groups if g["game"] in train_ids]
    valid = [g for g in groups if g["game"] in valid_ids]
    test = [g for g in groups if g["game"] in test_ids]
    frozen = THETA_FULL if args.base == "full" else THETA_CHEAP
    base = np.append(frozen, 0.0)
    index = np.asarray([28], dtype=np.int64)

    grid = []
    for penalty in (1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0):
        weight = float(fit_delta(train, index, base[index], penalty, base=base)[0])
        theta = base.copy(); theta[28] = weight
        grid.append({"penalty": penalty, "weight": weight,
                     "validation_nll": score(valid, theta, np.arange(29))["nll"]})
    chosen = min(grid, key=lambda row: row["validation_nll"])
    fit_ids = train_ids | valid_ids
    fit_groups = [g for g in groups if g["game"] in fit_ids]
    weight = float(fit_delta(fit_groups, index, base[index], chosen["penalty"], base=base)[0])
    candidate = base.copy(); candidate[28] = weight

    base_nll = per_group_nll(test, base)
    candidate_nll = per_group_nll(test, candidate)
    base_metrics = score(test, base, np.arange(29))
    candidate_metrics = score(test, candidate, np.arange(29))
    target = [g for g in test if g["rows"][g["label"]][0][28] > 0]
    target_base = score(target, base, np.arange(29)) if target else None
    target_candidate = score(target, candidate, np.arange(29)) if target else None

    by_actor = {}
    for g in test:
        actor = g["actor"]
        by_actor.setdefault(actor, []).append(g)
    actors = {}
    for actor, subset in sorted(by_actor.items()):
        a = score(subset, base, np.arange(29))
        b = score(subset, candidate, np.arange(29))
        actors[actor] = {"positions": len(subset), "baseline_nll": a["nll"],
                         "candidate_nll": b["nll"],
                         "delta_nll": b["nll"] - a["nll"]}

    report = {
        "experiment": f"single appended MM_HIDDEN_SLIDER_ZONE feature on v35 {args.base} prior",
        "base_prior": args.base,
        "feature_index": 28,
        "feature_definition": "hidden bishop/rook/queen destination; moved piece attacks one or more squares adjacent to the enemy king, but does not necessarily check",
        "dataset": str(args.dataset),
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "positions": len(groups), "games": len(meta), "invalid_groups": invalid,
        "split_games": {"train": len(train_ids), "validation": len(valid_ids), "test": len(test_ids)},
        "split_positions": {"train": len(train), "validation": len(valid), "test": len(test)},
        "validation_grid": grid,
        "selected_penalty": chosen["penalty"],
        "fitted_weight": weight,
        "heldout_v35": base_metrics,
        "heldout_candidate": candidate_metrics,
        "heldout_candidate_minus_v35_nll": candidate_metrics["nll"] - base_metrics["nll"],
        "heldout_game_cluster_bootstrap": bootstrap_game_delta(test, base_nll, candidate_nll),
        "true_move_feature_active_subset": {
            "positions": len(target), "v35": target_base, "candidate": target_candidate,
            "candidate_minus_v35_nll": (target_candidate["nll"] - target_base["nll"] if target else None),
        },
        "actor_slices": actors,
        "coefficients_extended": candidate.tolist(),
        "caveat": "This is held-out prediction of opponents' selected moves, not belief calibration, changed-action quality, or playing strength. The selected feature and all hypotheses were chosen during development; require a sealed sample and referee branches before a strength claim.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in (
        "split_games", "split_positions", "selected_penalty", "fitted_weight",
        "heldout_v35", "heldout_candidate", "heldout_candidate_minus_v35_nll",
        "heldout_game_cluster_bootstrap", "true_move_feature_active_subset")}, indent=2))


if __name__ == "__main__":
    main()
