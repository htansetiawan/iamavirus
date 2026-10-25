#!/usr/bin/env python3
"""Compare v35 and the EP patch on six exact replay prefixes.

Only prior own moves are forced. At the target EP decision each binary
searches using the same replay history and seed. This is a local decision
probe, not a strength or full-game evaluation.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CASES = [("0izeuvgd", 16, "d4e3"), ("6v4llaz2", 51, "g5h6"),
         ("8wef0oiw", 64, "g4h3"), ("7gylb8nl", 25, "g5f6"),
         ("jpo6pr7m", 24, "g4f3"), ("3cvzfvz5", 17, "c5d6")]


def build(source: Path) -> Path:
    proc = subprocess.run(["bash", "build.sh"], cwd=source, text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError(f"build failed in {source}:\n{proc.stdout}\n{proc.stderr}")
    return source / "mist"


def run_prefix(binary: Path, replay: dict, target_ply: int, seconds: float, seed: int) -> dict:
    frames = replay["frames"]
    side = "white" if target_ply % 2 else "black"
    side_idx = 0 if side == "white" else 1
    prior = [p for p in range(target_ply - 1) if (p % 2 == 0) == (side == "white")]
    forced = [frames[p + 1]["move"] for p in prior]
    lines = ["fow", f"{'w' if side == 'white' else 'b'} 180 2"]
    for p in range(target_ply):
        lines += [frames[p][side], str(frames[p]["clocks"][side_idx])]
        if (p % 2 == 0) != (side == "white"):
            lines.pop()  # the arena sends a clock only on this bot's turn
    env = dict(os.environ)
    env.update({"MIST_FORCE_MOVES": ",".join(forced), "MIST_MAX_SECONDS": str(seconds),
                "MIST_CAP": "200000", "FOW_SEED": str(seed)})
    proc = subprocess.run([str(binary)], input="\n".join(lines) + "\n", text=True,
                          capture_output=True, env=env, timeout=30)
    moves = [line[5:].strip() for line in proc.stdout.splitlines() if line.startswith("move ")]
    target = frames[target_ply]["move"]
    if proc.returncode or len(moves) != len(forced) + 1:
        raise RuntimeError(f"{replay['id']}: expected {len(forced)+1} moves, got {moves}; stderr={proc.stderr[-1500:]}")
    return {"side": side, "target": target, "prior_own_moves": len(forced),
            "selected": moves[-1], "target_selected": moves[-1] == target,
            "stderr_tail": proc.stderr[-1500:]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, default=ROOT / "fable-submissions/iamavirus-v35-mist-c-v14.zip")
    ap.add_argument("--replay-root", type=Path, default=ROOT / "data/raw/games")
    ap.add_argument("--search-seconds", type=float, default=0.25)
    ap.add_argument("--seeds", type=int, nargs="+", default=[20261025])
    ap.add_argument("--game", choices=[case[0] for case in CASES], help="limit to one replay")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="astra-ep-decision-") as td:
        work = Path(td)
        base, patched = work / "v35", work / "patched"
        base.mkdir()
        with zipfile.ZipFile(args.archive) as zf:
            zf.extractall(base)
        shutil.copytree(base, patched)
        subprocess.run(["patch", "-p1", "-i", str(HERE / "belief-ep-observation.patch")],
                       cwd=patched, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        base_bin, patched_bin = build(base), build(patched)
        rows = []
        cases = [case for case in CASES if args.game is None or case[0] == args.game]
        for seed in args.seeds:
            for game, ply, expected in cases:
                replay = json.loads((args.replay_root / game / "replay.json").read_text())
                if replay["frames"][ply]["move"] != expected:
                    raise ValueError(f"unexpected target move in {game} ply {ply}")
                before = run_prefix(base_bin, replay, ply, args.search_seconds, seed)
                after = run_prefix(patched_bin, replay, ply, args.search_seconds, seed)
                rows.append({"seed": seed, "game": game, "ply": ply, "baseline": before, "patched": after,
                             "choice_changed": before["selected"] != after["selected"]})
        result = {"search_seconds": args.search_seconds, "seeds": args.seeds, "cases": rows,
                  "choices_changed": sum(r["choice_changed"] for r in rows)}
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
