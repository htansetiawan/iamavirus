"""Replay a recorded game through the real arena bot, in any mode.

    python -m learning.replay_bot GAME_ID --mode hybrid --seeds 1 2 3 4 --plies 17

Feeds the bot exactly the observations our side received, forces it to play
the recorded moves (FOW_FORCE_MOVES) so the belief follows the real game, and
reports what it *would* have chosen at the requested plies, with its logged
estimates. Node-limited for reproducibility.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from . import ingest

ROOT = Path(__file__).resolve().parents[1]
TEAM = "a2c35173659545c99752376a70418438"


def replay(game_id: str, mode: str, seed: int, nodes: int, model_dir: Path, raw: Path,
           prior: str = "hand", until_ply: int | None = None) -> list[dict]:
    store = ingest.RawStore(raw)
    rep = json.loads((store.games / game_id / "replay.json").read_text())
    frames = rep["frames"]
    side = 1 if rep.get("blackPlayerId") == TEAM else 0
    key = "white" if side == 0 else "black"
    our_moves = [frames[t + 1]["move"] for t in range(len(frames) - 1) if t % 2 == side]
    script = ["fow", f"{'w' if side == 0 else 'b'} 180 2"]
    last = len(frames) - 1 if until_ply is None else min(until_ply, len(frames) - 1)
    for t in range(last + 1):
        script.append(frames[t][key])
        if t % 2 == side and t < len(frames) - 1:
            script.append("170.0")
    env = dict(os.environ, FOW_MODE=mode, FOW_MODEL_DIR=str(model_dir), FOW_SEED=str(seed),
               FOW_NODE_BUDGET=str(nodes), FOW_TIME_RESERVE="0", FOW_OPPONENT_PRIOR=prior,
               FOW_FORCE_MOVES=" ".join(our_moves))
    out = subprocess.run([str(ROOT / "bot")], input="\n".join(script) + "\n", capture_output=True,
                         text=True, env=env, timeout=3600)
    decisions = []
    for line in out.stderr.splitlines():
        if " n=" in line and " mode=" in line:
            fields = dict(re.findall(r"(\w+)=(\S+)", line))
            decisions.append(fields)
    return decisions, side


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game")
    parser.add_argument("--mode", default="hybrid")
    parser.add_argument("--prior", default="hand")
    parser.add_argument("--seeds", nargs="*", type=int, default=[1, 2, 3, 4])
    parser.add_argument("--plies", nargs="*", type=int, required=True, help="our decision plies to report")
    parser.add_argument("--nodes", type=int, default=1500000)
    parser.add_argument("--model-dir", type=Path, default=ROOT / "releases" / "v1")
    parser.add_argument("--raw", type=Path, default=ROOT / "data" / "raw")
    args = parser.parse_args(argv)
    for seed in args.seeds:
        decisions, side = replay(args.game, args.mode, seed, args.nodes, args.model_dir, args.raw,
                                 args.prior, until_ply=max(args.plies))
        for ply in args.plies:
            index = (ply - side) // 2
            if index >= len(decisions):
                print(f"seed {seed} ply {ply}: no decision logged")
                continue
            d = decisions[index]
            chosen = d.get("chose", d.get("move"))
            print(f"seed {seed} ply {ply} [{d.get('mode')}]: would play {chosen} (played {d.get('move')}) "
                  f"risk={d.get('risk')} short={d.get('short')} safe_rows={d.get('safe_rows')} "
                  f"cp={d.get('cp')} cd={d.get('cd')} cands={d.get('cands','')[:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
