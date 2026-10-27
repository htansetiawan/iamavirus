#!/usr/bin/env python3
"""Summarize existing B2 replays; no engine execution or model fitting.

Only jointly scored positions enter centipawn comparisons. Bootstrap units
are games, because ordinary control suites contain several decisions/game.
These are development diagnostics after the B1-informed B2 revision, not
untouched confirmation data and not estimates of playing strength.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import statistics


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(root, kind):
    paths = {label: root / f"{kind}{suffix}.json" for label, suffix in
             [("suite", ""), ("baseline", "-A"), ("candidate", "-B2")]}
    if not all(p.exists() for p in paths.values()):
        return {"status": "pending", "missing": [str(p) for p in paths.values() if not p.exists()]}
    suite = json.loads(paths["suite"].read_text())
    meta = {f"{r['game']}:{r['k']}": r for r in suite}
    rows = {}
    errors = {}
    for side in ("baseline", "candidate"):
        raw = json.loads(paths[side].read_text())["results"]
        errors[side] = sum("error" in r for r in raw)
        rows[side] = {r["id"]: r for r in raw if "error" not in r}
    ids = sorted(set(meta) & rows["baseline"].keys() & rows["candidate"].keys())
    a, b = rows["baseline"], rows["candidate"]
    cp_ids = [i for i in ids if a[i].get("cp_loss") is not None and b[i].get("cp_loss") is not None]
    by_game, by_opponent = defaultdict(list), defaultdict(list)
    for i in cp_ids:
        delta = b[i]["cp_loss"] - a[i]["cp_loss"]
        by_game[meta[i]["game"]].append(delta)
        by_opponent[meta[i]["opponent"]].append(delta)
    clusters = list(by_game.values())
    rng = random.Random(20261026036)
    boots = []
    for _ in range(2000):
        picked = rng.choices(clusters, k=len(clusters))
        boots.append(sum(sum(x) for x in picked) / sum(len(x) for x in picked))
    boots.sort()
    safe = [i for i in ids if a[i].get("safe", True)]
    return {
        "status": "complete",
        "paths": {k: str(v) for k, v in paths.items()},
        "sha256": {k: digest(v) for k, v in paths.items()},
        "planned_decisions": len(meta), "paired_decisions": len(ids),
        "paired_games": len({meta[i]["game"] for i in ids}), "errors": errors,
        "cp_jointly_scored": len(cp_ids),
        "cp_mean_baseline": statistics.mean(a[i]["cp_loss"] for i in cp_ids),
        "cp_mean_candidate": statistics.mean(b[i]["cp_loss"] for i in cp_ids),
        "cp_mean_delta_candidate_minus_baseline": statistics.mean(b[i]["cp_loss"]-a[i]["cp_loss"] for i in cp_ids),
        "cp_delta_game_cluster_bootstrap_95": [boots[49], boots[1949]],
        "bootstrap_replicates": 2000, "bootstrap_seed": 20261026036,
        "cp_delta_by_opponent": {k: {"n": len(v), "mean": statistics.mean(v)} for k, v in sorted(by_opponent.items())},
        "repeat_baseline": sum(bool(a[i].get("repeat")) for i in ids)/len(ids),
        "repeat_candidate": sum(bool(b[i].get("repeat")) for i in ids)/len(ids),
        "safe_decisions": len(safe),
        "fatal_baseline": sum(bool(a[i].get("fatal")) for i in safe),
        "fatal_candidate": sum(bool(b[i].get("fatal")) for i in safe),
        "fatal_fixed": [i for i in safe if a[i].get("fatal") and not b[i].get("fatal")],
        "fatal_broken": [i for i in safe if not a[i].get("fatal") and b[i].get("fatal")],
        "candidate_veto_recorded_rate": sum(bool(b[i].get("pveto_played")) for i in ids)/len(ids),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "classification": "post-revision development diagnostics; not untouched confirmation or Elo evidence",
        "method": "paired CP support only; percentile bootstrap resamples games, retaining their decisions; fixed 2000 replicates",
        "suites": {k: summarize(args.results, k) for k in ("calib", "oos", "control", "control-loss")},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+"\n")
    for k, s in report["suites"].items():
        print(k, s["status"], {x: s[x] for x in ("paired_decisions", "cp_jointly_scored", "cp_mean_delta_candidate_minus_baseline", "cp_delta_game_cluster_bootstrap_95", "fatal_baseline", "fatal_candidate") if x in s})


if __name__ == "__main__":
    main()
