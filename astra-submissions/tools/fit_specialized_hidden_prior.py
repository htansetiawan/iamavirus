#!/usr/bin/env python3
"""Refit only hidden-threat weights around a recent full-prior fit."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp

from fit_conditional_prior import load_groups, score, split_games


def pack(groups):
    matrices = [np.asarray([r[0] for r in g["rows"]], dtype=np.float64) for g in groups]
    counts = np.asarray([len(x) for x in matrices], dtype=np.int64)
    offsets = np.concatenate(([0], np.cumsum(counts[:-1])))
    truth = offsets + np.asarray([g["label"] for g in groups], dtype=np.int64)
    return np.concatenate(matrices), counts, offsets, truth


def fit_delta(groups, full_theta, strength):
    x, counts, offsets, truth = pack(groups)
    center = np.asarray(full_theta[26:28], dtype=np.float64)
    def fg(beta):
        z = x[:, :26] @ full_theta[:26] + x[:, 26:28] @ beta
        mx = np.maximum.reduceat(z, offsets)
        ex = np.exp(z - np.repeat(mx, counts))
        den = np.add.reduceat(ex, offsets)
        p = ex / np.repeat(den, counts)
        loss = np.sum(np.log(den) + mx - z[truth])
        grad = x[:, 26:28].T @ p - np.sum(x[truth, 26:28], axis=0)
        delta = beta - center
        loss += 0.5 * strength * float(delta @ delta)
        grad += strength * delta
        return float(loss / len(counts)), grad / len(counts)
    return minimize(fg, center.copy(), jac=True, method="L-BFGS-B",
                    options={"maxiter": 500, "ftol": 1e-11, "gtol": 1e-7}).x


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset")
    ap.add_argument("full_report")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    groups, meta, bad = load_groups(args.dataset)
    train_ids, valid_ids, test_ids = split_games(meta)
    tr = [g for g in groups if g["game"] in train_ids]
    va = [g for g in groups if g["game"] in valid_ids]
    te = [g for g in groups if g["game"] in test_ids]
    full_theta = np.asarray(json.loads(Path(args.full_report).read_text())[
        "models"]["full_refit"]["coefficients"], dtype=np.float64)
    strengths = [0.01, 0.1, 1.0, 10.0, 100.0]
    grid = []
    for strength in strengths:
        beta = fit_delta(tr, full_theta, strength)
        theta = full_theta.copy(); theta[26:28] = beta
        grid.append((score(va, theta, range(28))["nll"], strength, beta.tolist()))
    _, best, _ = min(grid, key=lambda x: x[0])
    fit_ids = train_ids | valid_ids
    beta = fit_delta([g for g in groups if g["game"] in fit_ids], full_theta, best)
    theta = full_theta.copy(); theta[26:28] = beta
    report = {"games": len(meta), "positions": len(groups), "invalid_groups": bad,
              "split_games": {"train": len(train_ids), "validation": len(valid_ids), "test": len(test_ids)},
              "split_positions": {"train": len(tr), "validation": len(va), "test": len(te)},
              "base_hidden_weights": full_theta[26:28].tolist(),
              "lambda": best, "validation_grid": grid,
              "base_full_refit_heldout": score(te, full_theta, range(28)),
              "specialized_hidden_heldout": score(te, theta, range(28)),
              "theta_full": theta.tolist(),
              "caveat": "Offline predictive ablation; not playing-strength evidence."}
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k:report[k] for k in ("lambda", "validation_grid", "base_full_refit_heldout", "specialized_hidden_heldout")},indent=2))


if __name__ == "__main__": main()
