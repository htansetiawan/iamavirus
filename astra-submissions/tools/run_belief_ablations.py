#!/usr/bin/env python3
"""Run a compiled observation-only probe with capture/deduction factors.

All arms replay the same completed game's views and own actions. True boards
label outputs only. This development diagnostic is not a playing-strength gate.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess


ARMS = {"control": (0, 0), "capture": (1, 0),
        "deductions": (0, 1), "combined": (1, 1)}


def summarize(rows):
    captures = [r for r in rows if r["true_capture_landing"] >= 0
                and not r["true_capture_was_ep"]]
    hidden = sum(r["hidden_squares"] for r in rows)
    pieces = sum(r["hidden_pieces"] for r in rows)
    return dict(
        updates=len(rows), collapses=sum(r["collapsed"] for r in rows),
        truth_in_population=sum(r["truth_board_matches"] > 0 for r in rows),
        ordinary_capture_events=len(captures),
        capture_violations=sum(r["true_capture_landing_support"] != r["particles"] for r in captures),
        mean_observation_consistency=sum(r["exact_observation_matches"] / r["particles"]
                                        for r in rows) / len(rows),
        visibility_conflicts=sum(r.get("visibility_evidence_conflict", False) for r in rows),
        mean_hidden_brier=sum(r["hidden_brier_sum"] for r in rows) / max(1, hidden),
        mean_hidden_log_loss=sum(r["hidden_log_loss_sum"] for r in rows) / max(1, hidden),
        mean_hidden_piece_mass=sum(r["hidden_piece_mass_sum"] for r in rows) / max(1, pieces),
        zero_true_mass_fraction=sum(r["zero_true_mass_squares"] for r in rows) / max(1, hidden),
        mean_observe_ms=sum(r["observe_ms"] for r in rows) / len(rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--moves", type=Path, required=True)
    parser.add_argument("--side", type=int, choices=[0, 1], required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3, 777])
    parser.add_argument("--particles", type=int, default=2048)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.workers < 1 or args.particles < 1:
        parser.error("workers and particles must be positive")
    args.output.mkdir(parents=True, exist_ok=True)

    def run(task):
        name, flags, seed = task
        result = subprocess.run([str(args.probe.resolve()), str(args.moves.resolve()),
                                 str(args.side), str(seed), str(args.particles),
                                 *map(str, flags)], check=True, capture_output=True, text=True)
        if result.stderr:
            raise RuntimeError(result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        assert all(row["seed"] == seed for row in rows)
        return name, rows

    tasks = [(name, flags, seed) for name, flags in ARMS.items() for seed in args.seeds]
    arms = {name: [] for name in ARMS}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for name, rows in executor.map(run, tasks):
            arms[name].extend(rows)
    summary = {}
    for name, rows in arms.items():
        (args.output / f"{name}.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in rows))
        summary[name] = summarize(rows)
    report = dict(
        probe_sha256=hashlib.sha256(args.probe.read_bytes()).hexdigest(),
        moves_sha256=hashlib.sha256(args.moves.read_bytes()).hexdigest(),
        side=args.side, seeds=args.seeds, particles=args.particles,
        arms={name: dict(zip(("capture", "deductions"), flags)) for name, flags in ARMS.items()},
        results=summary,
        limits=["Single development trajectory, repeated across seeds; not independent games.",
                "Truth labels never condition the belief update.",
                "Mean probability on true hidden pieces is a placement diagnostic, not calibration by itself.",
                "Categorical Brier/log loss include hidden empty squares; log loss floors mass at 1e-12.",
                "Observe latency includes OS contention; no strength or Elo claim."])
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
