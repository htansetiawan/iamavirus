#!/usr/bin/env python3
"""Fit/evaluate a held-out conditional-logit opponent move prior.

Input is JSONL from extract_move_model_dataset.py. The chronological split is
by whole game, so candidate moves from one replay cannot leak across splits.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp


THETA_FULL = np.array([
    1.0883, 4.2173, 0.0000, -0.5976, -0.7174, -0.2331, -0.4542, -0.3852,
    0.1103, 2.3662, 1.6652, -0.5344, -0.8673, -0.1008, 0.8894, 1.5612,
    1.4574, 1.1427, 0.7011, 1.0507, -0.1183, -1.2109, -2.5556, -2.4094,
    0.3295, 0.2615, 0.0, 0.0,
])


def load_groups(path):
    groups = defaultdict(list)
    meta = {}
    with Path(path).open() as f:
        for line in f:
            row = json.loads(line)
            key = (row["game"], row["ply"])
            groups[key].append((row["features"], row["label"], row["candidate"]))
            meta[row["game"]] = (row.get("at", ""), row.get("white", ""), row.get("black", ""))
    result = []
    bad = 0
    for key, rows in groups.items():
        ys = [i for i, (_, y, _) in enumerate(rows) if y]
        if len(ys) != 1:
            bad += 1
            continue
        result.append({"key": key, "game": key[0], "rows": rows, "label": ys[0]})
    return result, meta, bad


def split_games(meta):
    # One timestamp per game; order ties deterministically by ID.
    ordered = sorted(meta, key=lambda g: (meta[g][0], g))
    n = len(ordered)
    a, b = max(1, int(n * .60)), max(2, int(n * .80))
    return set(ordered[:a]), set(ordered[a:b]), set(ordered[b:])


def pack(groups, indices):
    matrices = [np.asarray([r[0] for r in g["rows"]], dtype=np.float64)[:, indices] for g in groups]
    counts = np.asarray([len(x) for x in matrices], dtype=np.int64)
    offsets = np.concatenate(([0], np.cumsum(counts[:-1])))
    truth = offsets + np.asarray([g["label"] for g in groups], dtype=np.int64)
    return np.concatenate(matrices, axis=0), counts, offsets, truth


def objective(beta, packed, center, penalty):
    x, counts, offsets, truth = packed
    z = x @ beta
    maxima = np.maximum.reduceat(z, offsets)
    shifted = z - np.repeat(maxima, counts)
    expz = np.exp(shifted)
    sums = np.add.reduceat(expz, offsets)
    logz = np.log(sums) + maxima
    loss = float(np.sum(logz - z[truth]))
    p = expz / np.repeat(sums, counts)
    grad = x.T @ p - np.sum(x[truth], axis=0)
    delta = beta - center
    loss += 0.5 * penalty * float(delta @ delta)
    grad += penalty * delta
    scale = max(1, len(counts))
    return loss / scale, grad / scale


def fit(groups, indices, center, penalty):
    packed = pack(groups, indices)
    def fg(beta):
        return objective(beta, packed, center, penalty)
    return minimize(fg, center.copy(), jac=True, method="L-BFGS-B",
                    options={"maxiter": 500, "ftol": 1e-11, "gtol": 1e-7}).x


def score(groups, beta, indices):
    x, counts, offsets, truth = pack(groups, indices)
    z = x @ beta
    maxima = np.maximum.reduceat(z, offsets)
    expz = np.exp(z - np.repeat(maxima, counts))
    sums = np.add.reduceat(expz, offsets)
    p = expz / np.repeat(sums, counts)
    group_logz = np.log(sums) + maxima
    nll = group_logz - z[truth]
    brier = np.add.reduceat(p * p, offsets) - 2 * p[truth] + 1
    top1 = np.asarray([int(np.argmax(z[o:o+n]) + o == t)
                       for o, n, t in zip(offsets, counts, truth)])
    true_x = np.asarray([g["rows"][g["label"]][0] for g in groups], dtype=np.float64)
    hidden = (true_x[:, 26] != 0) | (true_x[:, 27] != 0)
    hidden_nll, hidden_top1 = nll[hidden], top1[hidden]
    all_y = np.zeros(len(p), dtype=np.int8); all_y[truth] = 1
    def avg(xs): return float(np.mean(xs)) if len(xs) else None
    # Candidate-level reliability: each position is a categorical choice, so
    # probabilities within a row sum to one and exactly one candidate is true.
    ece = 0.0
    if len(p):
        probs, labels = p, all_y
        for lo in np.linspace(0.0, 0.9, 10):
            mask = (probs >= lo) & (probs < lo + 0.1)
            if np.any(mask):
                ece += float(mask.mean()) * abs(float(probs[mask].mean()) - float(labels[mask].mean()))
    return {"positions": len(groups), "nll": avg(nll), "top1": avg(top1),
            "brier": avg(brier), "candidate_ece_10bin": ece,
            "true_hidden_threat_positions": len(hidden_nll),
            "hidden_nll": avg(hidden_nll), "hidden_top1": avg(hidden_top1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    groups, meta, bad = load_groups(args.dataset)
    train_ids, valid_ids, test_ids = split_games(meta)
    tr = [g for g in groups if g["game"] in train_ids]
    va = [g for g in groups if g["game"] in valid_ids]
    te = [g for g in groups if g["game"] in test_ids]
    lambdas = [1e-4, 1e-3, 1e-2, 1e-1, 1.0]
    models = {}
    for name, indices, center in (
        ("hidden_two_only", np.array([26, 27]), np.zeros(2)),
        ("full_refit", np.arange(28), np.zeros(28)),
    ):
        choices = []
        for lam in lambdas:
            beta = fit(tr, indices, center, lam)
            choices.append((score(va, beta, indices)["nll"], lam))
        _, best_lam = min(choices)
        fit_ids = train_ids | valid_ids
        fit_groups = [g for g in groups if g["game"] in fit_ids]
        beta = fit(fit_groups, indices, center, best_lam)
        full_beta = THETA_FULL.copy()
        full_beta[indices] = beta
        models[name] = {"indices": indices, "beta": beta, "theta_full": full_beta,
                        "lambda": best_lam, "validation_grid": choices}
    baseline_indices = np.arange(28)
    report = {"games": len(meta), "positions": len(groups), "invalid_groups": bad,
              "split_games": {"train": len(train_ids), "validation": len(valid_ids), "test": len(test_ids)},
              "split_positions": {"train": len(tr), "validation": len(va), "test": len(te)},
              "models": {"frozen_v35": score(te, THETA_FULL, baseline_indices)}}
    for name, model in models.items():
        report["models"][name] = {"lambda": model["lambda"],
            "validation_grid_mean_nll": model["validation_grid"],
            "heldout": score(te, model["theta_full"], baseline_indices),
            "coefficients": model["theta_full"].tolist()}
    report["caveat"] = "Small cached replay sample; historical opponents, not an arena strength estimate."
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"games": report["games"], "positions": report["positions"],
                      "splits": report["split_positions"], "models": report["models"],
                      "out": args.out}, indent=2))


if __name__ == "__main__":
    main()
