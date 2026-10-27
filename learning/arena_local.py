"""The local arena's scheduler: matchups played on the course referee in colour-swapped
pairs across core pairs, every game appended to a ledger, each matchup stopped by a
sequential probability ratio test (SPRT) once its answer is clear (GYM.md 3.1, R3/R4).

    python -m learning.arena_local run queue.json --slots 0,1 2,3 4,5 6,7
    python -m learning.arena_local status queue.json

queue.json: {"matchups": [{"id": "v16d-vs-v15", "a": "path/to/a.zip", "b": "path/to/b.zip",
             "a_env": ["FOW_X=1"], "b_env": [], "max_games": 400,
             "sprt": {"elo0": 0, "elo1": 35, "alpha": 0.05, "beta": 0.05}}]}

Ledger: data/arena_local/games.jsonl, one line per game. A restart resumes from it.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import threading
import time
from pathlib import Path

from . import compare_archives as ca

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "arena_local" / "games.jsonl"
RECEIPTS = ROOT / "data" / "arena_local" / "receipts"
KIT = Path.home() / "git" / "fow-starter"
_lock = threading.Lock()


def elo_to_score(elo: float) -> float:
    return 1.0 / (1.0 + 10 ** (-elo / 400.0))


GAME_BOUND_SECONDS = 2450   # the longest legal 180+2 game (1000 plies: 360 s + 2,000 s of increments) with its
                            # start-up: no game starts unless this fits before the cap, so a legal game is never cut
CLEANUP_RESERVE_SECONDS = 30   # the in-flight game's timeout keeps this much of the cap for recording and cleanup
MIN_GAMES = 20          # no verdict before ten colour-swapped pairs
PRIOR_GAMES = 20        # pseudo-games of variance PRIOR_VAR blended into the sample variance
PRIOR_VAR = 0.22        # per-game score variance of a near-even match with a few draws


def sprt_llr(scores: list[float], elo0: float, elo1: float) -> float:
    """Log-likelihood ratio of H1 (elo1) against H0 (elo0) under the normal approximation used
    by engine-testing frameworks, on per-game scores (1, 0.5, 0) from the candidate's side.
    The variance is shrunk towards PRIOR_VAR so a short run of identical results cannot end
    the test; no verdict before MIN_GAMES (checked by the caller via `sprt_verdict`)."""
    n = len(scores)
    if n < 2:
        return 0.0
    mean = sum(scores) / n
    sample_var = sum((x - mean) ** 2 for x in scores) / n
    var = (n * sample_var + PRIOR_GAMES * PRIOR_VAR) / (n + PRIOR_GAMES)
    s0, s1 = elo_to_score(elo0), elo_to_score(elo1)
    return 0.5 * n * ((mean - s0) ** 2 - (mean - s1) ** 2) / var


def sprt_verdict(scores: list[float], elo0: float, elo1: float, alpha: float, beta: float) -> str:
    lo, hi = sprt_bounds(alpha, beta)
    if len(scores) < MIN_GAMES:
        return "running"
    llr = sprt_llr(scores, elo0, elo1)
    return "H1 (A stronger)" if llr >= hi else ("H0 (A not stronger)" if llr <= lo else "running")


def sprt_bounds(alpha: float, beta: float) -> tuple[float, float]:
    return math.log(beta / (1 - alpha)), math.log((1 - beta) / alpha)


def sha12(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:12]


def ledger_games(matchup_id: str) -> list[dict]:
    if not LEDGER.exists():
        return []
    return [g for g in (json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()) if g["matchup"] == matchup_id]


def summary(m: dict) -> dict:
    """Scores count only valid results; `attempted` counts every recorded attempt (a failed or
    unknown result is recorded with a_score null and attempt "failed"), so a failed pair is
    never played again and the cap counts attempts, not successes."""
    rows = ledger_games(m["id"])
    games = [g for g in rows if g.get("a_score") is not None]
    scores = [g["a_score"] for g in games]
    sp = m.get("sprt", {"elo0": 0, "elo1": 35, "alpha": 0.05, "beta": 0.05})
    llr = sprt_llr(scores, sp["elo0"], sp["elo1"])
    lo, hi = sprt_bounds(sp["alpha"], sp["beta"])
    verdict = sprt_verdict(scores, sp["elo0"], sp["elo1"], sp["alpha"], sp["beta"])
    if len(rows) >= m.get("max_games", 400) and verdict == "running":
        verdict = "max games reached"
    n = len(scores)
    mean = sum(scores) / n if n else 0.0
    w = sum(1 for x in scores if x == 1.0)
    d = sum(1 for x in scores if x == 0.5)
    elo = -400 * math.log10(1 / mean - 1) if 0 < mean < 1 else float("nan")
    return {"id": m["id"], "games": n, "attempted": len(rows), "failed": len(rows) - n,
            "w-d-l": f"{w}-{d}-{n - w - d}", "score": round(mean, 3),
            "elo_diff": round(elo, 1) if elo == elo else None, "llr": round(llr, 2), "bounds": [round(lo, 2), round(hi, 2)],
            "verdict": verdict}


def run(queue_path: Path, slots: list[str], linger_hours: float = 0.0, wall_hours: float | None = None) -> None:
    queue = json.loads(queue_path.read_text())
    state = {"mtime": queue_path.stat().st_mtime}
    linger_until = time.time() + 3600 * linger_hours
    # the run receipt (for an audit): attempted_jobs counts STARTED games, failed_jobs the recorded
    # failed or unknown results; state running -> complete | wall_cap (no new job after --wall-hours)
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    receipt_path = RECEIPTS / f"{queue_path.stem}.json"
    receipt = {"queue": str(queue_path), "queue_sha256": hashlib.sha256(queue_path.read_bytes()).hexdigest(),
               "ledger": str(LEDGER.relative_to(ROOT)) if LEDGER.is_relative_to(ROOT) else str(LEDGER), "state": "running",
               "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "finished_at": None,
               "wall_hours": wall_hours, "attempted_jobs": 0, "failed_jobs": 0, "slots": slots}
    started = time.time()
    deadline = started + 3600 * wall_hours if wall_hours is not None else None

    def write_receipt():   # caller holds _lock
        tmp = receipt_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(receipt, indent=1))
        tmp.replace(receipt_path)

    with _lock:
        write_receipt()
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    workdir = ROOT / "data" / "arena_local" / "builds"
    built = {}
    for m in queue["matchups"]:
        for side in ("a", "b"):
            path = Path(m[side])
            if path not in built:
                built[path] = ca.build(path, workdir)
    stop = threading.Event()

    def reload_queue():
        """Pick up matchups added to or changed in the queue file (caller holds _lock).

        A matchup that stays keeps its dict, so the workers' in-flight counts stay
        right; one removed from the file gets no new games."""
        try:
            mtime = queue_path.stat().st_mtime
        except OSError:
            return
        if mtime == state["mtime"]:
            return
        try:
            fresh = json.loads(queue_path.read_text())
        except (OSError, ValueError):
            return  # caught mid-write; the next job looks again
        state["mtime"] = mtime
        old = {m["id"]: m for m in queue["matchups"]}
        merged = []
        for m in fresh["matchups"]:
            for side in ("a", "b"):
                path = Path(m[side])
                if path not in built:
                    built[path] = ca.build(path, workdir)
            if m["id"] in old:
                kept = old[m["id"]]
                inflight = kept.get("_inflight", 0)
                kept.clear()
                kept.update(m)
                kept["_inflight"] = inflight
                merged.append(kept)
            else:
                merged.append(m)
        queue["matchups"] = merged
        print(f"queue reloaded: {[m['id'] for m in merged]}", flush=True)

    def next_job():
        """The matchup with the fewest games that is still running; its next pair index."""
        with _lock:
            if deadline is not None and time.time() + GAME_BOUND_SECONDS > deadline:
                if receipt["state"] == "running":
                    receipt["state"] = "wall_cap"; write_receipt()
                return None   # the cap: no new pair; a game in flight is bounded by its timeout
            reload_queue()
            best = None
            for m in queue["matchups"]:
                s = summary(m)
                if s["verdict"] != "running":
                    continue
                inflight = m.setdefault("_inflight", 0)
                n = s["attempted"] + 2 * inflight   # attempts, so a failed pair is not retried
                if n >= m.get("max_games", 400):
                    continue
                if best is None or n < best[1]:
                    best = (m, n)
            if best is None:
                return None
            m, n = best
            m["_inflight"] += 1
            pair = n // 2
            return m, pair

    def worker(slot: str):
        while not stop.is_set():
            job = next_job()
            if job is None:
                if time.time() < linger_until:
                    time.sleep(60)  # idle: wait for matchups to be added to the queue file
                    continue
                return
            m, pair = job
            seed = int(m.get("seed", 20000)) + 2 * pair
            a, b = built[Path(m["a"])], built[Path(m["b"])]
            a_env, b_env = " ".join(m.get("a_env", [])), " ".join(m.get("b_env", []))
            for a_white in (True, False):
                out = workdir / f"{m['id']}-p{pair}-{'a' if a_white else 'b'}-white.json"
                white, black = (a, b) if a_white else (b, a)
                wenv, benv = (a_env, b_env) if a_white else (b_env, a_env)
                with _lock:
                    # the cap is checked before EACH game: the second colour of a pair does not start
                    # either, and a game in flight is killed at the deadline (recorded as failed)
                    if deadline is not None and time.time() + GAME_BOUND_SECONDS > deadline:
                        if receipt["state"] == "running":
                            receipt["state"] = "wall_cap"; write_receipt()
                        break
                    receipt["attempted_jobs"] += 1; write_receipt()   # a started game, scored or not
                    # a hung game is killed at the cap (minus the reserve); a legal game always fits
                    timeout = max(1.0, deadline - time.time() - CLEANUP_RESERVE_SECONDS) if deadline is not None else None
                try:
                    g = ca.play(white, black, seed, KIT, out, slot, wenv, benv, timeout=timeout)
                except Exception as error:  # keep the arena running; record the failure
                    g = {"result": "*", "reason": f"runner error {error!r}", "plies": 0, "seconds": 0, "clocks": None}
                score = {"1-0": 1.0, "0-1": 0.0, "1/2-1/2": 0.5}.get(g["result"])
                # every attempt is recorded: a failed or unknown result keeps its row (a_score null,
                # attempt "failed") so the audit sees it and the pair is never played again
                a_score = (score if a_white else 1 - score) if score is not None else None
                rec = {"matchup": m["id"], "pair": pair, "seed": seed, "a_colour": "white" if a_white else "black",
                       "a_score": a_score, "attempt": "ok" if score is not None else "failed",
                       "result": g["result"], "reason": g["reason"], "plies": g["plies"],
                       "seconds": round(g["seconds"], 1), "clocks": g["clocks"], "slot": slot,
                       "a": str(m["a"]), "b": str(m["b"]), "a_sha": sha12(Path(m["a"])), "b_sha": sha12(Path(m["b"])),
                       "a_env": m.get("a_env", []), "b_env": m.get("b_env", []), "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "replay": str(out.relative_to(ROOT))}
                with _lock:
                    if rec["attempt"] == "failed":
                        receipt["failed_jobs"] += 1
                    write_receipt()
                    with LEDGER.open("a") as f:
                        f.write(json.dumps(rec) + "\n")
            with _lock:
                m["_inflight"] -= 1
                s = summary(m)
            print(f"[{slot}] {s['id']}: {s['games']} games {s['w-d-l']} score {s['score']} llr {s['llr']} {s['verdict']}", flush=True)

    with cf.ThreadPoolExecutor(max_workers=len(slots)) as pool:
        list(pool.map(worker, slots))
    with _lock:
        if receipt["state"] == "running":
            receipt["state"] = "complete"
        receipt["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_receipt()
    print(f"run receipt: {receipt_path} state {receipt['state']} attempted {receipt['attempted_jobs']} failed {receipt['failed_jobs']}", flush=True)
    for m in queue["matchups"]:
        print(json.dumps(summary(m)))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["run", "status"])
    ap.add_argument("queue", type=Path)
    ap.add_argument("--slots", nargs="*", default=["0,1", "2,3", "4,5", "6,7"])
    ap.add_argument("--wall-hours", type=float, default=None, help="no new game after this many hours; the receipt says wall_cap")
    ap.add_argument("--linger-hours", type=float, default=0.0,
                    help="when nothing is left to play, keep watching the queue file this long")
    args = ap.parse_args()
    if args.command == "run":
        run(args.queue, args.slots, args.linger_hours, args.wall_hours)
    else:
        for m in json.loads(args.queue.read_text())["matchups"]:
            print(json.dumps(summary(m)))


if __name__ == "__main__":
    main()
