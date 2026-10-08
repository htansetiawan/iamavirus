#!/usr/bin/env python3
"""Compare the port's control, strict-filter and history modes on whole replays.

No search or gameplay strength is measured. Every run receives only actor
observations and its recorded own actions; truth is used for offline labels.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--particles", type=int, default=2048)
    parser.add_argument("--seeds", type=int, nargs="+", default=[777])
    parser.add_argument("--modes", type=int, choices=[0, 1, 2], nargs="+", default=[0, 1, 2])
    parser.add_argument("--priors", type=int, choices=[0, 1, 2], nargs="+", default=[1])
    parser.add_argument("--prediction-mode", type=int, choices=[0, 1, 2], default=0,
                        help="grouped prediction ablation when supported by the probe")
    parser.add_argument("--limit", type=int, help="First N seats; explicit pilot only")
    args = parser.parse_args()
    if min(args.workers, args.particles) < 1:
        parser.error("workers and particles must be positive")
    args.output.mkdir(parents=True, exist_ok=False)
    moves_dir = args.output / "moves"
    moves_dir.mkdir()
    seats = []
    for line in args.corpus.read_text().splitlines():
        if not line.strip():
            continue
        game, side, result, reason, opponent, *moves = line.split()
        if side not in ("w", "b") or not moves:
            raise ValueError("malformed seat")
        seats.append(dict(game=game, side=0 if side == "w" else 1, opponent=opponent,
                          result=result, reason=reason, moves=moves))
    if args.limit is not None:
        seats = seats[:args.limit]
    if len({(s["game"], s["side"]) for s in seats}) != len(seats):
        raise ValueError("duplicate game seats")
    jobs = []
    for seat in seats:
        moves = moves_dir / (seat["game"] + ".txt")
        content = " ".join(seat["moves"]) + "\n"
        if moves.exists() and moves.read_text() != content:
            raise ValueError("different move histories for one game")
        moves.write_text(content)
        for prior in args.priors:
            for mode in args.modes:
                for seed in args.seeds:
                    jobs.append({**{k: v for k, v in seat.items() if k != "moves"},
                                 "prior": prior, "mode": mode, "prediction_mode": args.prediction_mode, "seed": seed,
                                 "expected_updates": len(seat["moves"]),
                                 "moves_sha256": sha(moves), "moves_path": str(moves.resolve())})
    probe = args.probe.resolve()
    runs = []
    manifest = {"started_at": datetime.now(timezone.utc).isoformat(), "state": "running", "pid": os.getpid(),
                "probe": str(probe), "binary_sha256": sha(probe),
                "corpus_sha256": sha(args.corpus), "particles": args.particles,
                "seats": len(seats), "job_count": len(jobs),
                "results_journal": str(args.output / "runs.jsonl"),
                "runner_source_sha256": sha(Path(__file__)),
                "limit": args.limit, "interpretation": "Forced-history belief diagnostics, not strength evidence."}

    def save(final=False):
        # Append each result once, and keep running state compact. Rewriting all
        # completed traces per job creates quadratic I/O on the large corpus.
        snapshot = {**manifest, "completed_runs": len(runs)}
        if final:
            snapshot["runs"] = runs
        temporary = args.output / "state.tmp"
        temporary.write_text(json.dumps(snapshot, indent=2) + "\n")
        temporary.replace(args.output / "state.json")

    save()

    def run(job):
        stem = f"{job['game']}-{job['side']}-prior{job['prior']}-mode{job['mode']}-seed{job['seed']}"
        trace, errors = args.output / (stem + ".jsonl"), args.output / (stem + ".stderr")
        command = [str(probe), job["moves_path"], str(job["side"]), str(job["seed"]), str(args.particles)]
        env = {k: v for k, v in os.environ.items() if not k.startswith(("FOW_", "ASTRA_"))}
        env.update(ASTRA_HISTORY_MODE=str(job["mode"]), ASTRA_OPPONENT_PRIOR=str(job["prior"]),
                   ASTRA_PREDICTION_MODE=str(job["prediction_mode"]),
                   ASTRA_PROBE_SQUARES="18")
        started = time.monotonic()
        with trace.open("w") as out, errors.open("w") as err:
            process = subprocess.run(command, env=env, stdout=out, stderr=err, timeout=600)
        rows = [json.loads(line) for line in trace.read_text().splitlines()]
        hidden = sum(r["hidden_squares"] for r in rows)
        actor = [r for r in rows if "actual_move" in r]
        return {**job, "trace": str(trace), "trace_sha256": sha(trace),
                "returncode": process.returncode, "elapsed_seconds": time.monotonic()-started,
                "updates": len(rows),
                "complete": process.returncode == 0 and len(rows) == job["expected_updates"],
                "view_mismatch_updates": sum(r["exact_observation_matches"] != r["particles"] for r in rows),
                "continuation_invalid_updates": sum(r["continuation_invalid_particles"] > 0 for r in rows),
                "evidence_conflicts": sum(r.get("history_evidence_conflict", False) for r in rows),
                "collapsed_updates": sum(r["collapsed"] for r in rows),
                "random_rebuilds": sum(r["collapsed"] and not r.get("history_recovered", False) for r in rows),
                "history_rescues": sum(r.get("history_recovered", False) for r in rows),
                "history_budget_exhausted_updates": sum(r.get("history_budget_exhausted", False) for r in rows),
                "history_transitions": sum(r.get("history_transitions", 0) for r in rows),
                "full_certified_updates": sum(r.get("history_full_certified", False) for r in rows),
                "truth_held_updates": sum(r["truth_board_matches"] > 0 for r in rows),
                "hidden_squares": hidden,
                "hidden_brier_sum": sum(r["hidden_brier_sum"] for r in rows),
                "hidden_log_loss_sum": sum(r["hidden_log_loss_sum"] for r in rows),
                "max_observe_ms": max((r["observe_ms"] for r in rows), default=0),
                "final_actor": actor[-1] if actor else None}

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(run, job): job for job in jobs}
        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception as exc:
                result = {**futures[future], "complete": False, "error": repr(exc)}
            runs.append(result)
            with (args.output / "runs.jsonl").open("a") as journal:
                journal.write(json.dumps(result) + "\n")
            save()
            if len(runs) % 20 == 0 or not result["complete"]:
                print(json.dumps({"completed": len(runs), "total": len(jobs),
                                  "last": {k: result.get(k) for k in ("game", "mode", "prior", "complete")}}), flush=True)
    unchanged = sha(probe) == manifest["binary_sha256"] and sha(args.corpus) == manifest["corpus_sha256"]
    manifest["inputs_unchanged"] = unchanged
    manifest["state"] = "complete" if unchanged and all(r["complete"] for r in runs) else "failed"
    manifest["completed_at"] = datetime.now(timezone.utc).isoformat()
    aggregates = {}
    metrics = ("updates", "view_mismatch_updates", "continuation_invalid_updates", "evidence_conflicts",
               "collapsed_updates", "random_rebuilds", "history_rescues", "history_budget_exhausted_updates",
               "history_transitions", "full_certified_updates", "truth_held_updates", "hidden_squares",
               "hidden_brier_sum", "hidden_log_loss_sum")
    for run_result in runs:
        key = f"prior{run_result['prior']}-mode{run_result['mode']}"
        group = aggregates.setdefault(key, {"runs": 0, "failed_runs": 0, **{m: 0 for m in metrics}})
        if not run_result["complete"]:
            group["failed_runs"] += 1
            continue
        group["runs"] += 1
        for metric in metrics:
            group[metric] += run_result[metric]
        group["max_observe_ms"] = max(group.get("max_observe_ms", 0), run_result["max_observe_ms"])
    for group in aggregates.values():
        for metric in ("hidden_brier", "hidden_log_loss"):
            group[metric] = group[metric + "_sum"] / max(1, group["hidden_squares"])
    manifest["aggregates"] = aggregates
    save(final=True)
    print(json.dumps({"state": manifest["state"], "aggregates": aggregates}, indent=2), flush=True)
    if manifest["state"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
