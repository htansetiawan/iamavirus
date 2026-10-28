"""Controlled comparison of two submission archives under real clocks.

    python -m learning.compare_archives A.zip B.zip --pairs 3 --cores 0,1

Builds each archive in its own directory (with ORT_HOME for the neural modes),
then plays colour-swapped seed pairs A-vs-B through referee.py at 180+2, both
bots pinned to the given cores one at a time (the arena pauses the opponent on
your turn; locally the two bots share the cores, so this is a conservative
setting). Reports A's score and a paired-bootstrap interval. Uses the archives'
own run.sh, so each plays in the mode it was packaged with.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import numpy as np

from . import labels
from .evaluate import paired_bootstrap

ROOT = Path(__file__).resolve().parents[1]


def build(archive: Path, workdir: Path) -> Path:
    target = workdir / archive.stem
    if target.exists():
        subprocess.run(["rm", "-rf", str(target)], check=True)
    target.mkdir(parents=True)
    with zipfile.ZipFile(archive) as z:
        z.extractall(target)
    env = dict(os.environ)
    env.setdefault("ORT_HOME", str(Path.home() / "git" / "onnxruntime-sdk" / "onnxruntime-linux-x64-1.24.2"))
    subprocess.run(["bash", "build.sh"], cwd=target, check=True, capture_output=True, text=True, env=env)
    return target


def descendants(pid: int) -> list[int]:
    """Every process below pid, deepest first, from /proc (the referee starts its bots in
    their own sessions, so a process-group kill would orphan them)."""
    children: dict[int, list[int]] = {}
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/stat") as f:
                fields = f.read().rsplit(")", 1)[1].split()
            children.setdefault(int(fields[1]), []).append(int(entry))   # fields[1] = ppid
        except (OSError, IndexError, ValueError):
            continue
    found, stack = [], [pid]
    while stack:
        q = stack.pop()
        for c in children.get(q, []):
            found.append(c); stack.append(c)
    return found[::-1]


def kill_tree(pid: int) -> None:
    for q in descendants(pid) + [pid]:
        try:
            os.kill(q, signal.SIGKILL)
        except ProcessLookupError:
            pass


def play(white: Path, black: Path, seed: int, kit: Path, out: Path, cores: str | None,
         white_env: str = "", black_env: str = "", timeout: float | None = None) -> dict:
    """One referee game. With `timeout` (seconds) the game and every process it started are
    killed at the deadline and a RuntimeError says so; the caller records a failed attempt."""
    python = kit / ".venv" / "bin" / "python"
    prefix = ["taskset", "-c", cores] if cores else []
    # FOW_REFEREE: a wrapper around the kit's referee (learning/oracle_referee.py), experiments only
    referee = Path(os.environ["FOW_REFEREE"]) if os.environ.get("FOW_REFEREE") else kit / "referee.py"
    cmd = prefix + [str(python), str(referee), "--trusted-local",
                    "--white", f"env FOW_SEED={seed} {white_env} bash {white / 'run.sh'}".replace("  ", " "),
                    "--black", f"env FOW_SEED={seed + 1} {black_env} bash {black / 'run.sh'}".replace("  ", " "),
                    "--white-name", white.name, "--black-name", black.name,
                    "--base-time", "180", "--increment", "2", "--max-plies", "1000", "--output", str(out)]
    started = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        _, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(proc.pid)
        proc.wait()
        raise RuntimeError(f"wall cap: game killed after {time.time() - started:.0f} s") from None
    if proc.returncode != 0:
        raise RuntimeError(f"referee exit {proc.returncode}: {err[-400:]}")
    replay = json.loads(out.read_text())
    return {"result": replay["result"], "reason": replay["reason"], "plies": len(replay["frames"]) - 1,
            "seconds": time.time() - started, "clocks": replay["frames"][-1]["clocks"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("a", type=Path)
    parser.add_argument("b", type=Path)
    parser.add_argument("--pairs", type=int, default=3)
    parser.add_argument("--seed", type=int, default=100)
    parser.add_argument("--cores", default=None, help="e.g. 0,1 to pin both bots to two cores")
    parser.add_argument("--kit", type=Path, default=Path.home() / "git" / "fow-starter")
    parser.add_argument("--workdir", type=Path, default=ROOT / "data" / "compare")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--a-env", nargs="*", help="FOW_* settings for A, e.g. FOW_STRIKE=0 (offline variants only)")
    parser.add_argument("--b-env", nargs="*", help="FOW_* settings for B")
    args = parser.parse_args(argv)
    args.workdir.mkdir(parents=True, exist_ok=True)
    a = build(args.a, args.workdir)
    b = build(args.b, args.workdir)
    games, pair_scores = [], []
    for p in range(args.pairs):
        s = args.seed + 2 * p
        a_env = " ".join(args.a_env or [])
        b_env = " ".join(args.b_env or [])
        g1 = play(a, b, s, args.kit, args.workdir / f"pair{p}-a-white.json", args.cores, a_env, b_env)
        g2 = play(b, a, s, args.kit, args.workdir / f"pair{p}-b-white.json", args.cores, b_env, a_env)
        a1 = 0.5 + 0.5 * labels.terminal_return(g1["result"], 0)
        a2 = 0.5 + 0.5 * labels.terminal_return(g2["result"], 1)
        pair_scores.append((a1 + a2) / 2)
        games += [dict(g1, a_colour="white", a_score=a1), dict(g2, a_colour="black", a_score=a2)]
        print(f"  pair {p}: A as white {g1['result']} ({g1['reason']}, {g1['plies']} plies); "
              f"A as black {g2['result']} ({g2['reason']}, {g2['plies']} plies)", file=sys.stderr, flush=True)
    report = {"a": str(args.a), "b": str(args.b), "pairs": args.pairs, "cores": args.cores,
              "a_env": args.a_env or [], "b_env": args.b_env or [],
              "a_score_rate": float(np.mean([g["a_score"] for g in games])),
              "paired": paired_bootstrap(pair_scores), "games": games}
    text = json.dumps(report, indent=1)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        print(f"wrote {args.output}")
    print(f"A={args.a.name} score {report['a_score_rate']:.3f} over {2 * args.pairs} games; paired {report['paired']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
