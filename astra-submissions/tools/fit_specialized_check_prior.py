#!/usr/bin/env python3
"""Fit a specialized unseen-check move-prior weight with game-disjoint validation."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from fit_conditional_prior import THETA_FULL, load_groups, score, split_games


def pack(groups):
    matrices = [np.asarray([r[0] for r in g["rows"]], dtype=np.float64) for g in groups]
    counts = np.asarray([len(x) for x in matrices], dtype=np.int64)
    offsets = np.concatenate(([0], np.cumsum(counts[:-1])))
    truth = offsets + np.asarray([g["label"] for g in groups], dtype=np.int64)
    return np.concatenate(matrices), counts, offsets, truth


def fit_weight(groups, base, feature, strength):
    x, counts, offsets, truth = pack(groups)
    base = np.asarray(base, dtype=np.float64)
    def fg(delta):
        z = x @ base + delta[0] * x[:, feature]
        maxima = np.maximum.reduceat(z, offsets)
        expz = np.exp(z - np.repeat(maxima, counts))
        sums = np.add.reduceat(expz, offsets)
        p = expz / np.repeat(sums, counts)
        loss = np.sum(np.log(sums) + maxima - z[truth])
        residual = p.copy()
        residual[truth] -= 1.0
        grad = float(x[:, feature] @ residual)
        loss += 0.5 * strength * float(delta[0] * delta[0])
        grad += strength * float(delta[0])
        return float(loss / len(counts)), np.asarray([grad / len(counts)])
    result = minimize(fg, np.zeros(1), jac=True, method="L-BFGS-B",
                      options={"maxiter": 500, "ftol": 1e-11, "gtol": 1e-7})
    return float(result.x[0])


def with_weight(base, feature, weight):
    theta = np.asarray(base, dtype=np.float64).copy()
    theta[feature] = weight
    return theta


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--feature", type=int, default=26,
                    help="26 = unseen check; 27 = broader unseen threat")
    a = ap.parse_args()
    if a.feature not in (26, 27):
        raise SystemExit("feature must be 26 (unseen check) or 27 (unseen threat)")
    groups, meta, bad = load_groups(a.dataset)
    train_ids, valid_ids, test_ids = split_games(meta)
    train = [g for g in groups if g["game"] in train_ids]
    valid = [g for g in groups if g["game"] in valid_ids]
    test = [g for g in groups if g["game"] in test_ids]
    strengths = [0.01, 0.1, 1.0, 10.0, 100.0]
    grid = []
    for strength in strengths:
        weight = fit_weight(train, THETA_FULL, a.feature, strength)
        theta = with_weight(THETA_FULL, a.feature, weight)
        grid.append({"lambda": strength, "weight": weight,
                     "validation": score(valid, theta, np.arange(28))})
    best = min(grid, key=lambda row: row["validation"]["nll"])
    fit_ids = train_ids | valid_ids
    fit_groups = [g for g in groups if g["game"] in fit_ids]
    weight = fit_weight(fit_groups, THETA_FULL, a.feature, best["lambda"])
    theta = with_weight(THETA_FULL, a.feature, weight)
    base = np.asarray(THETA_FULL, dtype=np.float64)

    def subset(predicate):
        return [g for g in test if predicate(np.asarray(g["rows"][g["label"]][0]))]

    by_feature = {}
    for idx, name in ((26, "unseen_check"), (27, "unseen_threat")):
        selected = subset(lambda x, i=idx: x[i] != 0)
        by_feature[name] = {"positions": len(selected),
                            "frozen": score(selected, base, np.arange(28)),
                            "candidate": score(selected, theta, np.arange(28))}
    either = subset(lambda x: x[26] != 0 or x[27] != 0)
    report = {
        "classification": "single-feature specialist fitted on train games, selected on validation games, evaluated once on later held-out games",
        "dataset": str(a.dataset), "games": len(meta), "positions": len(groups),
        "invalid_groups": bad,
        "split_games": {"train": len(train_ids), "validation": len(valid_ids), "test": len(test_ids)},
        "split_positions": {"train": len(train), "validation": len(valid), "test": len(test)},
        "feature": a.feature, "feature_name": "unseen_check" if a.feature == 26 else "unseen_threat",
        "validation_grid": grid, "selected_lambda": best["lambda"],
        "selected_weight": weight,
        "frozen_test": score(test, base, np.arange(28)),
        "candidate_test": score(test, theta, np.arange(28)),
        "hidden_either_test": {"positions": len(either),
                               "frozen": score(either, base, np.arange(28)),
                               "candidate": score(either, theta, np.arange(28))},
        "feature_subgroups_test": by_feature,
        "theta_full": theta.tolist(),
        "caveat": "Predictive metrics are not playing-strength evidence; target games were excluded from fit but the test split is not a pristine project-wide test.",
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("feature_name", "selected_lambda", "selected_weight",
                                              "frozen_test", "candidate_test",
                                              "hidden_either_test", "feature_subgroups_test")}, indent=2))


if __name__ == "__main__":
    main()
