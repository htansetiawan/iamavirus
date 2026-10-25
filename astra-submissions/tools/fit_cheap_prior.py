#!/usr/bin/env python3
"""Fit and evaluate the v35 cheap (first 18 features) opponent prior."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from fit_conditional_prior import fit, load_groups, score, split_games


THETA_CHEAP = np.array([
    0.7705, 3.6690, 0.0000, -0.5296, -0.6920, -0.2792, -0.7406, -0.4606,
    0.1304, 2.3256, 1.3647, -0.6156, -1.4760, -0.1127, 0.7298, 1.5767,
    1.6693, 1.0416,
])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    groups, meta, bad = load_groups(args.dataset)
    train_ids, valid_ids, test_ids = split_games(meta)
    tr = [g for g in groups if g["game"] in train_ids]
    va = [g for g in groups if g["game"] in valid_ids]
    te = [g for g in groups if g["game"] in test_ids]
    indices = np.arange(18)
    lambdas = [1e-4, 1e-3, 1e-2, 1e-1, 1.0]
    grid = []
    for lam in lambdas:
        beta = fit(tr, indices, np.zeros(18), lam)
        grid.append((score(va, beta, indices)["nll"], lam))
    _, best = min(grid)
    fit_ids = train_ids | valid_ids
    beta = fit([g for g in groups if g["game"] in fit_ids], indices, np.zeros(18), best)
    by_actor = defaultdict(list)
    for group in te: by_actor[group["actor"]].append(group)
    report = {"games": len(meta), "positions": len(groups), "invalid_groups": bad,
              "split_games": {"train": len(train_ids), "validation": len(valid_ids), "test": len(test_ids)},
              "split_positions": {"train": len(tr), "validation": len(va), "test": len(te)},
              "lambda": best, "validation_grid_mean_nll": grid,
              "frozen_v35": score(te, THETA_CHEAP, indices),
              "fitted_cheap": score(te, beta, indices),
              "fitted_cheap_by_actor": {actor: score(rows, beta, indices) for actor, rows in sorted(by_actor.items())},
              "coefficients_18": beta.tolist(),
              "coefficients_28": beta.tolist() + [0.0] * 10,
              "caveat": "Chronological held-out predictive fit; not playing-strength evidence."}
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("split_games", "split_positions", "lambda", "validation_grid_mean_nll", "frozen_v35", "fitted_cheap")}, indent=2))


if __name__ == "__main__": main()
