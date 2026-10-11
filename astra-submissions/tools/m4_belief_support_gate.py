#!/usr/bin/env python3
"""Replay selected hidden-queen decisions through candidate v12's C++ belief.

This is a retrospective diagnostic, not an Elo test. The C++ harness consumes
only the bot's observations and actual-move notifications. Full replay boards
are used only after the candidate chooses, to label true-board support and
immediate royal safety.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = {
    "69nmui22": {"frame": 38, "role": "Duck hidden-queen fork; immediate response"},
    "4bkwxxng": {"frame": 53, "role": "Instructors hidden-queen fork; prophylaxis"},
    "b4c61fg2": {"frame": 82, "role": "Knight Vision queen-capture positive control"},
}
ENGINE_SOURCES = [
    "astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/belief_support_replay.cc",
    "astra-submissions/candidates/v12/engine.cc",
    "astra-submissions/candidates/v12/belief.cc",
    "astra-submissions/candidates/v12/search.cc",
    "astra-submissions/candidates/v12/evaluation.cc",
    "astra-submissions/candidates/v12/observation.cc",
    "astra-submissions/candidates/v12/transposition.cc",
    "astra-submissions/candidates/v12/regret.cc",
    "astra-submissions/candidates/v12/position.cc",
    "astra-submissions/candidates/v12/move.cc",
    "astra-submissions/candidates/v12/bitboard.cc",
    "astra-submissions/candidates/v12/neural_observation.cc",
    "astra-submissions/candidates/v12/neural_inference.cc",
    "astra-submissions/candidates/v12/opponent_model.cc",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def key_values(line: str) -> dict[str, str]:
    return dict(re.findall(r"([A-Za-z_]+)=([^ ]+)", line))


def run_case(engine: Path, replay_path: Path, game: str, prior: int,
             particles: int, seed: int) -> dict:
    replay = json.loads(replay_path.read_text())
    side = "white" if replay["white"] == "IAmAVirus" else "black"
    moves = [frame["move"] for frame in replay["frames"][1:]
             if frame.get("move")]
    target = CASES[game]["frame"]
    if target >= len(moves) or replay["frames"][target]["ply"] != target:
        raise ValueError(f"{game}: decision frame {target} outside replay")
    payload = side + " " + " ".join(moves) + "\n"
    proc = subprocess.run(
        [str(engine), str(seed), str(prior), str(particles), str(target)],
        input=payload, text=True, capture_output=True, check=True,
    )
    decision_line = next((line for line in proc.stdout.splitlines()
                          if line.startswith("DECISION ")), None)
    support_line = next((line for line in proc.stdout.splitlines()
                         if f"ply={target} " in line), None)
    if decision_line is None or support_line is None:
        raise RuntimeError(f"{game}/{seed}/{prior}: missing decision/support line")
    decision = key_values(decision_line)
    support = key_values(support_line)
    return {
        "seed": seed,
        "opponent_prior": prior,
        "true_board_particles": int(support["support"]),
        "true_board_in_root_sample": int(decision["true_in_search_sample"]),
        "root_sample_size": int(decision["search_sample_size"]),
        "chosen_move": decision["choice"],
        "particle_king_risk_permille": int(decision["particle_risk_permille"]),
        "true_board_king_survives_now": bool(int(decision["king_survives_now"])),
        "recorded_opponent_reply_legal": bool(
            int(decision["recorded_opponent_reply_legal"])),
        "opponent_move_loses_immediately": bool(
            int(decision["opponent_loses_immediately"])),
        "safe_replies_after_recorded_opponent_move": int(
            decision["safe_replies_after_recorded_opponent_move"]),
    }


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    return {
        "seeds": n,
        "true_board_retained": sum(r["true_board_particles"] > 0 for r in rows),
        "true_board_in_root_sample": sum(r["true_board_in_root_sample"] > 0
                                          for r in rows),
        "true_board_king_survived": sum(r["true_board_king_survives_now"]
                                        for r in rows),
        "moves": {m: sum(r["chosen_move"] == m for r in rows)
                  for m in sorted({r["chosen_move"] for r in rows})},
        "reply_safe_counts": {
            str(k): sum(r["safe_replies_after_recorded_opponent_move"] == k
                        for r in rows)
            for k in sorted({r["safe_replies_after_recorded_opponent_move"]
                             for r in rows})
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True,
                        help="compiled belief_support_replay binary")
    parser.add_argument("--data", type=Path, default=ROOT / "data/raw/games")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--particles", type=int, default=2048)
    parser.add_argument("--priors", type=int, nargs="+", default=[1, 2])
    args = parser.parse_args()
    engine = args.engine.resolve()
    if not engine.is_file():
        parser.error(f"engine does not exist: {engine}")

    results = []
    for game, info in CASES.items():
        replay_path = args.data / game / "replay.json"
        if not replay_path.is_file():
            parser.error(f"missing replay: {replay_path}")
        replay = json.loads(replay_path.read_text())
        rows = [run_case(engine, replay_path, game, prior, args.particles, seed)
                for prior in args.priors
                for seed in range(1, args.seeds + 1)]
        by_prior = {
            str(prior): summarize([r for r in rows if r["opponent_prior"] == prior])
            for prior in args.priors
        }
        results.append({
            "game": game,
            "white": replay["white"],
            "black": replay["black"],
            "decision_frame": info["frame"],
            "role": info["role"],
            "side_to_move": "black" if info["frame"] % 2 else "white",
            "replay_sha256": sha256(replay_path),
            "summary_by_prior": by_prior,
            "per_seed": rows,
        })

    out = {
        "classification": "selected retrospective decision/support gate; not Elo",
        "engine": str(engine),
        "engine_binary_sha256": sha256(engine),
        "build": {
            "command": "g++ -O2 -std=c++20 -Wall -Wextra -Werror <listed sources> -o belief_support_replay",
            "source_sha256": {p: sha256(ROOT / p) for p in ENGINE_SOURCES},
        },
        "particles": args.particles,
        "resampling_seeds": args.seeds,
        "priors": args.priors,
        "cases": results,
        "limitations": [
            "Only three preselected tactical episodes; not a held-out broad cohort.",
            "True-board checks are offline labels; the runtime receives only observations.",
            "Changing a prior changes stochastic resampling and therefore the population.",
            "The recorded opponent reply is a counterfactual response probe, not a policy model.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps([
        {"game": c["game"], "frame": c["decision_frame"],
         "summary_by_prior": c["summary_by_prior"]}
        for c in results
    ], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
