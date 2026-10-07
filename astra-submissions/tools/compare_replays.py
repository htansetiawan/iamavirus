#!/usr/bin/env python3
"""Compare exact baseline/candidate binaries on identical node-limited replays.

The benchmark supplies neural observations only. Full boards are offline labels.
Splitting by complete game seats preserves belief/recurrent state and seed 777.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--nodes", type=int, default=400000)
    parser.add_argument("--mode", choices=["cpp", "hybrid"], default="hybrid")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rows = [r for r in args.corpus.read_text().splitlines() if r.strip()]
    shards = []
    for i in range(args.workers):
        path = args.output / f"seats-{i}.txt"
        path.write_text("\n".join(rows[i::args.workers]) + "\n")
        shards.append(path.resolve())
    env = dict(os.environ, FOW_MODE=args.mode, FOW_MODEL_DIR=str(args.model.resolve()))
    # Avoid inherited tuning knobs silently changing an experiment.
    env = {k: v for k, v in env.items() if not k.startswith("FOW_")}
    env.update(FOW_MODE=args.mode, FOW_MODEL_DIR=str(args.model.resolve()))
    tasks = [(name, binary.resolve(), i, shard)
             for name, binary in [("baseline", args.baseline), ("candidate", args.candidate)]
             for i, shard in enumerate(shards)]

    def run(task):
        name, binary, i, shard = task
        started = time.monotonic()
        completed = subprocess.run([str(binary), str(shard), "6", str(args.nodes), "verbose"],
                                   env=env, text=True, capture_output=True, check=True)
        (args.output / f"{name}-{i}.log").write_text(completed.stdout + completed.stderr)
        if completed.stderr.strip():
            raise RuntimeError(f"Unexpected benchmark diagnostic: {completed.stderr[:300]}")
        labels = {"seats replayed": "seats", "decisions evaluated": "decisions",
                  "immediate king losses": "king_losses", "real losing positions": "terminal_positions",
                  "...the engine survives": "terminal_survived"}
        values = {}
        for label, key in labels.items():
            match = re.search(re.escape(label) + r"\s*:\s*(\d+)", completed.stdout)
            if not match:
                raise RuntimeError(f"Missing {label}")
            values[key] = int(match[1])
        print(name, i, values, flush=True)
        return name, values, time.monotonic() - started

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(run, tasks))
    summary = {}
    for name in ("baseline", "candidate"):
        counts = {}
        for arm, values, elapsed in results:
            if arm != name:
                continue
            for key, value in values.items():
                counts[key] = counts.get(key, 0) + value
        counts["king_loss_rate"] = counts["king_losses"] / counts["decisions"]
        summary[name] = counts
    assert summary["baseline"]["decisions"] == summary["candidate"]["decisions"]
    report = {"mode": args.mode, "node_budget": args.nodes, "seed": 777, "stride": 6,
              "corpus_sha256": hashlib.sha256(args.corpus.read_bytes()).hexdigest(),
              "binaries": {name: hashlib.sha256(path.read_bytes()).hexdigest()
                           for name, path in [("baseline", args.baseline), ("candidate", args.candidate)]},
              "results": summary,
              "limitations": ["Forced public histories, not counterfactual matches or Elo evidence.",
                               "Original stride semantics sample ply multiples of 6 (White) plus both sides' terminal losses.",
                               "Only decisions actually queried consume search RNG, identical in both arms."]}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
