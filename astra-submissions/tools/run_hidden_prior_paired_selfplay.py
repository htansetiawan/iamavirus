#!/usr/bin/env python3
"""Run color-swapped, full-clock v35-vs-hidden-prior screening games."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import statistics
import subprocess
import time


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def bot_command(label, runtime, seed):
    runtime = runtime.resolve()
    env = [
        f"FOW_SEED={seed}",
        "MIST_CAP=200000",
        "MIST_MAX_SECONDS=10",
        "MIST_RISK=1",
        "MIST_THREADS=2",
        f"MIST_STOCKFISH={runtime / 'bin/stockfish'}",
        f"MIST_HISTORY_TABLE={runtime / 'data/history.bin'}",
    ]
    return shlex.join(["env", *env, str(runtime / "mist")])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--kit", type=Path, default=Path.home() / "git/fow-starter")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--pairs", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20261025)
    ap.add_argument("--base-seconds", type=float, default=180)
    ap.add_argument("--increment-seconds", type=float, default=2)
    ap.add_argument("--timeout", type=int, default=1800)
    args = ap.parse_args()
    baseline, candidate = args.baseline.resolve(), args.candidate.resolve()
    referee = args.kit.resolve() / "referee.py"
    py = args.kit.resolve() / ".venv/bin/python"
    for path in (baseline / "mist", baseline / "bin/stockfish", baseline / "data/history.bin",
                 candidate / "mist", candidate / "bin/stockfish", candidate / "data/history.bin",
                 referee, py):
        if not path.is_file():
            raise SystemExit(f"missing required file: {path}")
    out = args.output.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "classification": "paired color-swapped local self-play screening; not an Elo estimate",
        "state": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "baseline": str(baseline), "baseline_sha256": sha(baseline / "mist"),
        "candidate": str(candidate), "candidate_sha256": sha(candidate / "mist"),
        "referee_sha256": sha(referee), "pairs_planned": args.pairs,
        "seed": args.seed, "time_control": {"base": args.base_seconds, "increment": args.increment_seconds},
        "games": [], "pair_scores": [],
        "limits": ["Both programs derive from the v35 clean-room engine; inspect their manifests and hashes for exact changes.",
                   "Identical bot-specific RNG seeds are used in each color-swapped pair.",
                   "Local self-play is a screening comparison, not arena strength or Elo evidence."]
    }

    def save():
        tmp = out.with_suffix(out.suffix + ".tmp")
        tmp.write_text(json.dumps(state, indent=2) + "\n")
        tmp.replace(out)

    save()
    try:
        for pair in range(args.pairs):
            candidate_seed = args.seed + 2 * pair
            baseline_seed = args.seed + 2 * pair + 1
            pair_scores = []
            for candidate_white in (True, False):
                white = (candidate, candidate_seed) if candidate_white else (baseline, baseline_seed)
                black = (baseline, baseline_seed) if candidate_white else (candidate, candidate_seed)
                white_name = "hidden-prior" if candidate_white else "v35"
                black_name = "v35" if candidate_white else "hidden-prior"
                output = out.parent / f"{out.stem}-pair{pair}-candidate-{'white' if candidate_white else 'black'}.json"
                command = [str(py), str(referee), "--trusted-local",
                           "--white", bot_command(white_name, white[0], white[1]),
                           "--black", bot_command(black_name, black[0], black[1]),
                           "--white-name", white_name, "--black-name", black_name,
                           "--base-time", str(args.base_seconds), "--increment", str(args.increment_seconds),
                           "--max-plies", "1000", "--output", str(output)]
                started = time.monotonic()
                proc = subprocess.run(command, cwd=args.kit.resolve(), capture_output=True, text=True,
                                      timeout=args.timeout, check=False)
                elapsed = time.monotonic() - started
                if proc.returncode:
                    raise RuntimeError(f"referee failed ({proc.returncode}): {proc.stderr[-1200:]}")
                game = json.loads(output.read_text())
                result = game["result"]
                candidate_result = 0.5 if result == "1/2-1/2" else float(result == ("1-0" if candidate_white else "0-1"))
                row = {"pair": pair, "candidate_color": "white" if candidate_white else "black",
                       "candidate_seed": candidate_seed, "baseline_seed": baseline_seed,
                       "result": result, "candidate_score": candidate_result,
                       "reason": game.get("reason"), "plies": len(game.get("frames", [])) - 1,
                       "final_clocks": game.get("frames", [])[-1].get("clocks") if game.get("frames") else None,
                       "elapsed_seconds": elapsed, "replay": str(output), "replay_sha256": sha(output),
                       "referee_stdout_tail": proc.stdout[-1000:], "referee_stderr_tail": proc.stderr[-1000:]}
                state["games"].append(row)
                pair_scores.append(candidate_result)
                state["pair_scores"] = [statistics.mean([g["candidate_score"] for g in state["games"] if g["pair"] == i])
                                         for i in sorted({g["pair"] for g in state["games"]})]
                save()
                print(json.dumps(row), flush=True)
            if len(pair_scores) != 2:
                raise RuntimeError("incomplete color-swapped pair")
        pairs = state["pair_scores"]
        state.update(state="complete", completed_at=datetime.now(timezone.utc).isoformat(),
                     score=statistics.mean(pairs), games_complete=len(state["games"]))
        save()
        print(json.dumps({"state": state["state"], "score": state["score"],
                          "pair_scores": pairs}), flush=True)
    except BaseException as exc:
        state.update(state="failed", error=repr(exc), failed_at=datetime.now(timezone.utc).isoformat())
        save()
        raise


if __name__ == "__main__":
    main()
