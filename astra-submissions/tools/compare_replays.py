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
    parser.add_argument("--baseline-set", action="append", default=[], metavar="FOW_NAME=VALUE")
    parser.add_argument("--candidate-set", action="append", default=[], metavar="FOW_NAME=VALUE")
    args = parser.parse_args()
    if args.workers < 1 or args.nodes < 1:
        parser.error("workers and nodes must be positive")
    overrides = {}
    for name, settings in (("baseline", args.baseline_set), ("candidate", args.candidate_set)):
        overrides[name] = {}
        for setting in settings:
            key, equals, value = setting.partition("=")
            if not equals or not re.fullmatch(r"FOW_[A-Z0-9_]+", key) or not value:
                parser.error("overrides must be FOW_NAME=VALUE")
            if key in ("FOW_MODE", "FOW_MODEL_DIR"):
                parser.error("mode and model must use their dedicated arguments")
            overrides[name][key] = value
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("output directory must be empty; use a new path to preserve run evidence")
    args.output.mkdir(parents=True, exist_ok=True)
    model_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in sorted(args.model.glob("*.onnx"))}
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
                                   env={**env, **overrides[name]}, text=True, capture_output=True, check=True)
        (args.output / f"{name}-{i}.log").write_text(completed.stdout + completed.stderr)
        if completed.stderr.strip():
            raise RuntimeError(f"Unexpected benchmark diagnostic: {completed.stderr[:300]}")
        if "own-decision stride 6" not in completed.stdout:
            raise RuntimeError("Both benchmark binaries must use the corrected per-side sampling")
        labels = {"seats replayed": "seats", "decisions evaluated": "decisions",
                  "immediate king losses": "king_losses", "real losing positions": "terminal_positions",
                  "...the engine survives": "terminal_survived"}
        values = {}
        for label, key in labels.items():
            match = re.search(re.escape(label) + r"\s*:\s*(\d+)", completed.stdout)
            if not match:
                raise RuntimeError(f"Missing {label}")
            values[key] = int(match[1])
        decisions = [json.loads(line.removeprefix("DECISION "))
                     for line in completed.stdout.splitlines() if line.startswith("DECISION ")]
        if decisions:
            assert len(decisions) == values["decisions"]
            assert sum(row["king_loss"] for row in decisions) == values["king_losses"]
            (args.output / f"{name}-{i}-decisions.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in decisions))
            values["avoidable_king_losses"] = sum(row["king_loss"] and row["safe_alternatives"] > 0
                                                  for row in decisions)
            values["safe_alternative_decisions"] = sum(row["safe_alternatives"] > 0 for row in decisions)
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
    paired = {}
    arms = {}
    for name in ("baseline", "candidate"):
        rows = [json.loads(line) for path in sorted(args.output.glob(f"{name}-*-decisions.jsonl"))
                for line in path.read_text().splitlines()]
        arms[name] = {(row["game"], row["side"], row["ply"]): row for row in rows}
    if arms["baseline"] and arms["candidate"]:
        assert arms["baseline"].keys() == arms["candidate"].keys()
        changed = []
        for key, baseline in arms["baseline"].items():
            candidate = arms["candidate"][key]
            assert baseline["safe_alternatives"] == candidate["safe_alternatives"]
            if baseline["move"] != candidate["move"]:
                changed.append(dict(game=key[0], side=key[1], ply=key[2],
                                    baseline=baseline, candidate=candidate))
        paired = dict(changed_moves=len(changed),
                      newly_safe=sum(row["baseline"]["king_loss"] and not row["candidate"]["king_loss"]
                                     for row in changed),
                      newly_fatal=sum(not row["baseline"]["king_loss"] and row["candidate"]["king_loss"]
                                      for row in changed))
        (args.output / "changed-decisions.json").write_text(json.dumps(changed, indent=2) + "\n")
    report = {"mode": args.mode, "node_budget": args.nodes, "seed": 777, "stride": 6,
              "overrides": overrides, "paired": paired,
              "model_sha256": model_hashes,
              "sampling": "each side's own decision index; terminal losses also included",
              "corpus_sha256": hashlib.sha256(args.corpus.read_bytes()).hexdigest(),
              "binaries": {name: hashlib.sha256(path.read_bytes()).hexdigest()
                           for name, path in [("baseline", args.baseline), ("candidate", args.candidate)]},
              "results": summary,
              "limitations": ["Forced public histories, not counterfactual matches or Elo evidence.",
                               "Per-side stride balances colors; terminal positions are an additional selected stratum.",
                               "Only decisions actually queried consume search RNG, identical in both arms."]}
    assert model_hashes == {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in sorted(args.model.glob("*.onnx"))}, "model changed during run"
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
