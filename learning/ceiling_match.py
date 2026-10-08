"""Asymmetric matches for ceiling experiments: one side may see the whole board
(--a-oracle), get a longer clock, more cores or any FOW_* setting.

    python -m learning.ceiling_match --a-bot build/v15plus/bot --b-bot build/v15plus/bot --a-oracle \
        --pairs 4 --parallel 2 --cores 0-7 --a-threads 2 --b-threads 2 --output data/reports/ceiling/oracle.json
    # more compute for A:  --a-base 1800 --a-env FOW_TIME_CAP=20 FOW_TIME_CAP_HARD=30 FOW_TIME_DIVISOR=30 --a-threads 4

The protocol follows the course referee as our bots experience it: "fow", then
"<w|b> <base> <increment>", "ready" within the startup limit, observations
after every ply (buffered for the side not to move and flushed with the clock
prompt), a clock line, and a "move <uci>" reply; elapsed wall time is charged
against the mover's clock, then the increment added. Rules, legality and the
game outcome come from learning/rules.py (the same C++ rules the engine uses,
ordered as referee.py orders them). An oracle side receives the true board
string in place of its fogged view. Games are written in the replay format
(frames with board, both views, move, clocks) so the taxonomy and gym tools read
them. Offline only; never part of a submission.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import random
import select
import subprocess
import time
from pathlib import Path

from . import rules

ROOT = Path(__file__).resolve().parents[1]


class BotProcess:
    def __init__(self, binary: str, env: dict, cores: str, side: int, base: float, increment: float,
                 startup: float = 15.0):
        self.side = side
        self.proc = subprocess.Popen(["taskset", "-c", cores, binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1, env=env, cwd=str(ROOT))
        self.pending: list[str] = []
        self.send("fow")
        self.send(f"{'w' if side == 0 else 'b'} {base:g} {increment:g}")
        line = self.readline(startup)
        if line is None or line.strip() != "ready":
            raise RuntimeError(f"startup failed: {line!r}")

    def send(self, text: str) -> None:
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()

    def readline(self, timeout: float):
        deadline = time.monotonic() + max(0.0, timeout)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            ready, _, _ = select.select([self.proc.stdout], [], [], remaining)
            if ready:
                line = self.proc.stdout.readline()
                if line == "":
                    return None
                if line.strip():
                    return line

    def observe(self, observation: str) -> None:
        self.pending.append(observation)

    def move(self, clock: float):
        started = time.monotonic()
        for observation in self.pending:
            self.send(observation)
        self.pending.clear()
        self.send(f"{clock:.9f}")
        line = self.readline(clock - (time.monotonic() - started))
        elapsed = time.monotonic() - started
        if line is None or not line.startswith("move "):
            return None, elapsed
        return line.split()[1], elapsed

    def close(self) -> None:
        try:
            self.proc.kill()
        except Exception:
            pass


def play(game_id: str, white: dict, black: dict, max_plies: int = 10000) -> dict:
    state = rules.GameState()
    sides = [white, black]
    clocks = [white["base"], black["base"]]
    bots = []
    frames = []

    def frame(move=None):
        board = state.board
        return {"ply": state.plies, "board": board.board_string(), "white": board.observation(rules.WHITE),
                "black": board.observation(rules.BLACK), "move": move, "clocks": [round(clocks[0], 6), round(clocks[1], 6)]}

    result = {"id": game_id, "white": white["name"], "black": black["name"]}
    try:
        for index, spec in enumerate(sides):
            bots.append(BotProcess(spec["binary"], spec["env"], spec["cores"], index, spec["base"], spec["increment"]))
        frames.append(frame())
        while True:
            outcome = state.outcome()
            if outcome:
                result["result"], result["reason"] = outcome
                break
            if state.plies >= max_plies:
                result["result"], result["reason"] = "1/2-1/2", "Move limit reached"
                break
            board = state.board
            for index, spec in enumerate(sides):
                bots[index].observe(board.board_string() if spec["oracle"] else board.observation(index))
            mover = board.side
            move, elapsed = bots[mover].move(clocks[mover])
            clocks[mover] -= elapsed
            if clocks[mover] < 0 or move is None:
                result["result"] = "0-1" if mover == 0 else "1-0"
                result["reason"] = "Time forfeit" if clocks[mover] < 0 else "No move"
                break
            if move not in board.legal_moves():
                result["result"] = "0-1" if mover == 0 else "1-0"
                result["reason"] = f"Illegal move: {move}"
                break
            clocks[mover] += sides[mover]["increment"]
            state.push(move)
            frames.append(frame(move))
    except Exception as error:
        result["result"], result["reason"] = "*", f"runner error: {error!r}"
    finally:
        for bot in bots:
            bot.close()
    result["frames"] = frames
    result["plies"] = len(frames) - 1
    return result


def parse_cores(text: str) -> list[int]:
    out = []
    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def side_spec(args, which: str, cores: str) -> dict:
    binary = str(Path(getattr(args, f"{which}_bot")).resolve())
    env = dict(os.environ, FOW_MODE="hybrid", FOW_MODEL_DIR=str(Path(getattr(args, f"{which}_model")).resolve()),
               FOW_CELL_THREADS=str(getattr(args, f"{which}_threads")))
    for kv in getattr(args, f"{which}_env") or []:
        k, v = kv.split("=", 1)
        env[k] = v
    return {"name": getattr(args, f"{which}_name"), "binary": binary, "env": env, "cores": cores,
            "base": getattr(args, f"{which}_base"), "increment": getattr(args, f"{which}_increment"),
            "oracle": getattr(args, f"{which}_oracle")}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for which in ("a", "b"):
        ap.add_argument(f"--{which}-bot", required=True)
        ap.add_argument(f"--{which}-model", default="releases/v1")
        ap.add_argument(f"--{which}-name", default=which.upper())
        ap.add_argument(f"--{which}-env", nargs="*")
        ap.add_argument(f"--{which}-threads", type=int, default=2)
        ap.add_argument(f"--{which}-base", type=float, default=180.0)
        ap.add_argument(f"--{which}-increment", type=float, default=2.0)
        ap.add_argument(f"--{which}-oracle", action="store_true")
    ap.add_argument("--pairs", type=int, default=4)
    ap.add_argument("--parallel", type=int, default=2)
    ap.add_argument("--cores", default="0-7")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--max-plies", type=int, default=10000)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    cores = parse_cores(args.cores)
    need = args.a_threads + args.b_threads
    slots = []
    for i in range(args.parallel):
        chunk = cores[i * need:(i + 1) * need]
        if len(chunk) < need:
            raise SystemExit(f"not enough cores for {args.parallel} parallel games of {need} cores")
        slots.append((",".join(map(str, chunk[:args.a_threads])), ",".join(map(str, chunk[args.a_threads:]))))
    jobs = []
    for p in range(args.pairs):
        jobs.append((f"pair{p}-a-white", True, args.seed + 2 * p))
        jobs.append((f"pair{p}-a-black", False, args.seed + 2 * p + 1))
    results = [None] * len(jobs)
    free = list(range(len(slots)))
    with cf.ThreadPoolExecutor(max_workers=len(slots)) as pool:
        futures = {}
        queue = list(enumerate(jobs))

        def submit():
            if not queue or not free:
                return
            i, (gid, a_white, seed) = queue.pop(0)
            slot = free.pop(0)
            a = side_spec(args, "a", slots[slot][0])
            b = side_spec(args, "b", slots[slot][1])
            a["env"]["FOW_SEED"] = str(seed)
            b["env"]["FOW_SEED"] = str(seed + 1000)
            white, black = (a, b) if a_white else (b, a)
            futures[pool.submit(play, gid, white, black, args.max_plies)] = (i, slot)

        for _ in slots:
            submit()
        while futures:
            done, _ = cf.wait(list(futures), return_when=cf.FIRST_COMPLETED)
            for fut in done:
                i, slot = futures.pop(fut)
                results[i] = fut.result()
                r = results[i]
                a_white = jobs[i][1]
                score = {"1-0": 1.0, "0-1": 0.0}.get(r["result"], 0.5)
                a_score = score if a_white else 1 - score
                print(f"{r['id']}: {r['white']} vs {r['black']} {r['result']} ({r['reason']}, {r['plies']} plies) A scores {a_score}", flush=True)
                free.append(slot)
                submit()
    a_total = 0.0
    for (gid, a_white, _), r in zip(jobs, results):
        score = {"1-0": 1.0, "0-1": 0.0}.get(r["result"], 0.5)
        a_total += score if a_white else 1 - score
    summary = {"games": len(jobs), "a_score": a_total, "a_rate": round(a_total / len(jobs), 3),
               "config": {k: v for k, v in vars(args).items()}}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps({"summary": summary, "games": results}))
    print(json.dumps({k: v for k, v in summary.items() if k != "config"}))


if __name__ == "__main__":
    main()
