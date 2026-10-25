#!/usr/bin/env python3
"""Add held-out per-actor conditional-prior metrics to a fit report."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from fit_conditional_prior import THETA_FULL, load_groups, score, split_games


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset")
    ap.add_argument("report")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    groups, meta, bad = load_groups(a.dataset)
    train_ids, valid_ids, test_ids = split_games(meta)
    test = [g for g in groups if g["game"] in test_ids]
    actors = defaultdict(list)
    for g in test: actors[g["actor"]].append(g)
    report = json.loads(Path(a.report).read_text())
    models = {"frozen_v35": THETA_FULL}
    for name in ("hidden_two_only", "full_refit"):
        models[name] = report["models"][name]["coefficients"]
    report["heldout_by_actor"] = {
        model: {actor: score(gs, theta, range(28)) for actor, gs in sorted(actors.items())}
        for model, theta in models.items()
    }
    report["test_games_by_date"] = dict(sorted(Counter(meta[g][0][:10] for g in test_ids).items()))
    report["test_actor_positions"] = {actor: len(gs) for actor, gs in sorted(actors.items())}
    report["invalid_groups_in_rescore"] = bad
    Path(a.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"test_games_by_date": report["test_games_by_date"],
                      "test_actor_positions": report["test_actor_positions"],
                      "heldout_by_actor": report["heldout_by_actor"]}, indent=2))


if __name__ == "__main__": main()
