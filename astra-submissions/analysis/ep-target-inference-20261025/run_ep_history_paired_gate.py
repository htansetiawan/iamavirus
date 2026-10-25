#!/usr/bin/env python3
"""Run resumable, color-swapped 180+2 v35 vs EP-history candidate matches."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def load_referee(path: Path):
    spec = importlib.util.spec_from_file_location("ep_history_referee", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load referee: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bot_argv(run_dir: Path, seed: int) -> list[str]:
    return ["/usr/bin/env", f"FOW_SEED={seed}", "/bin/bash", str(run_dir / "run.sh")]


def candidate_score(result: str, color: str) -> float:
    if result == "1/2-1/2":
        return 0.5
    candidate_won = (result == "1-0") == (color == "white")
    return 1.0 if candidate_won else 0.0


def run_one(referee, candidate: Path, baseline: Path, pair: int, color: str,
            candidate_seed: int, baseline_seed: int, out_dir: Path) -> dict:
    if color == "white":
        white_argv, black_argv = bot_argv(candidate, candidate_seed), bot_argv(baseline, baseline_seed)
        white_name, black_name = "Astra EP history", "IAmAVirus v35"
    else:
        white_argv, black_argv = bot_argv(baseline, baseline_seed), bot_argv(candidate, candidate_seed)
        white_name, black_name = "IAmAVirus v35", "Astra EP history"
    game_id = f"ep-history-{pair:02d}-candidate-{color}"
    start = time.monotonic()
    replay = referee.run_match(white_argv, black_argv, 180.0, 2.0, game_id,
                               white_name, black_name, 10000)
    elapsed = time.monotonic() - start
    score = candidate_score(replay["result"], color)
    path = out_dir / f"{game_id}.json"
    # Keep replay frames and protocol events; drop only local stderr excerpts.
    stored = {k: v for k, v in replay.items() if k != "privateDiagnostics"}
    atomic_json(path, stored)
    return {
        "pair": pair, "candidate_color": color,
        "candidate_seed": candidate_seed, "baseline_seed": baseline_seed,
        "result": replay["result"], "candidate_score": score,
        "reason": replay["reason"], "plies": len(replay["frames"]) - 1,
        "final_clocks": replay["frames"][-1].get("clocks"), "elapsed_seconds": elapsed,
        "replay": str(path), "replay_sha256": sha(path),
        "failed_side": replay.get("failedSide"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", type=Path, required=True, help="built v35-derived EP-history directory")
    ap.add_argument("--baseline", type=Path, required=True, help="built unchanged v35 directory")
    ap.add_argument("--referee", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True, help="manifest JSON path")
    ap.add_argument("--pairs", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20261080)
    args = ap.parse_args()
    candidate, baseline, referee_path, manifest_path = map(Path.resolve,
        (args.candidate, args.baseline, args.referee, args.out))
    for d in (candidate, baseline):
        if not (d / "run.sh").is_file() or not (d / "mist").is_file():
            raise SystemExit(f"expected built engine and run.sh in {d}")
    out_dir = manifest_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    referee = load_referee(referee_path)
    hashes = {"candidate_binary_sha256": sha(candidate / "mist"),
              "baseline_binary_sha256": sha(baseline / "mist"),
              "referee_sha256": sha(referee_path)}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if (manifest.get("hashes") != hashes or manifest.get("pairs_planned") != args.pairs or
                manifest.get("seed") != args.seed):
            raise SystemExit("existing manifest does not match these binaries/seeds; choose a new output")
        completed = {(g["pair"], g["candidate_color"]) for g in manifest["games"]}
    else:
        manifest = {
            "classification": "paired color-swapped full-clock local gate; not an Elo estimate",
            "state": "running", "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "baseline": str(baseline), "candidate": str(candidate), "referee": str(referee_path),
            "hashes": hashes, "pairs_planned": args.pairs, "seed": args.seed,
            "time_control": {"base": 180, "increment": 2}, "games": [],
        }
        completed = set()
        atomic_json(manifest_path, manifest)
    for pair in range(args.pairs):
        candidate_seed, baseline_seed = args.seed + 2 * pair, args.seed + 2 * pair + 1
        for color in ("white", "black"):
            if (pair, color) in completed:
                continue
            game = run_one(referee, candidate, baseline, pair, color,
                           candidate_seed, baseline_seed, out_dir)
            manifest["games"].append(game)
            pair_scores: dict[str, float] = {}
            for g in manifest["games"]:
                pair_scores[str(g["pair"])] = pair_scores.get(str(g["pair"]), 0.0) + g["candidate_score"]
            manifest["completed_games"] = len(manifest["games"])
            manifest["candidate_score"] = sum(g["candidate_score"] for g in manifest["games"])
            manifest["pair_scores"] = pair_scores
            atomic_json(manifest_path, manifest)
            print(json.dumps(game), flush=True)
    manifest["state"] = "complete"
    manifest["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    atomic_json(manifest_path, manifest)


if __name__ == "__main__":
    main()
