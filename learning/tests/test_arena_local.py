"""The local arena runner's attempt recording and wall-clock cap, with a fake clock and a fake
referee: every started game is recorded (a failed one too), no pair is retried, and no second
game starts once the cap no longer fits a bounded game."""
import json
from pathlib import Path

import learning.arena_local as al


def _setup(tmp_path, monkeypatch, results, game_seconds=700.0):
    clock = {"t": 1_000_000.0}
    calls = []
    monkeypatch.setattr(al.time, "time", lambda: clock["t"])
    monkeypatch.setattr(al.time, "sleep", lambda s: None)
    monkeypatch.setattr(al, "LEDGER", tmp_path / "games.jsonl")
    monkeypatch.setattr(al, "RECEIPTS", tmp_path / "receipts")
    monkeypatch.setattr(al.ca, "build", lambda path, workdir: path)

    def fake_play(white, black, seed, kit, out, slot, wenv, benv, timeout=None):
        calls.append({"seed": seed, "white": white.name, "timeout": timeout, "t": clock["t"]})
        clock["t"] += game_seconds
        result = results[min(len(calls) - 1, len(results) - 1)]
        if result == "*":
            return {"result": "*", "reason": "runner error", "plies": 0, "seconds": game_seconds, "clocks": None}
        return {"result": result, "reason": "King capturable", "plies": 40, "seconds": game_seconds, "clocks": [50.0, 60.0]}
    monkeypatch.setattr(al.ca, "play", fake_play)
    a, b = tmp_path / "a.zip", tmp_path / "b.zip"
    a.write_bytes(b"a"); b.write_bytes(b"b")
    queue = tmp_path / "queue.json"
    queue.write_text(json.dumps({"matchups": [{"id": "t", "a": str(a), "b": str(b), "max_games": 4, "seed": 100,
                                               "sprt": {"elo0": 0, "elo1": 35, "alpha": 1e-12, "beta": 1e-12}}]}))
    return queue, calls, clock


def _rows(tmp_path):
    return [json.loads(l) for l in (tmp_path / "games.jsonl").read_text().splitlines() if l.strip()]


def test_failed_attempt_is_recorded_and_never_retried(tmp_path, monkeypatch):
    queue, calls, _ = _setup(tmp_path, monkeypatch, ["*", "1-0", "0-1", "1-0"])
    al.run(queue, ["0,1"])
    rows = _rows(tmp_path)
    assert len(calls) == 4 and len(rows) == 4
    assert rows[0]["attempt"] == "failed" and rows[0]["a_score"] is None and rows[0]["result"] == "*"
    assert [r["pair"] for r in rows] == [0, 0, 1, 1]            # pair 0 was not played again
    assert [c["seed"] for c in calls] == [100, 100, 102, 102]
    receipt = json.loads((tmp_path / "receipts" / "queue.json").read_text())
    assert receipt["state"] == "complete" and receipt["attempted_jobs"] == 4 and receipt["failed_jobs"] == 1
    assert receipt["finished_at"] is not None and receipt["queue_sha256"]


def test_wall_cap_stops_before_the_second_colour(tmp_path, monkeypatch):
    # 3,000 s of cap: the first game (700 s) fits the 2,450 s bound, the second colour does not
    queue, calls, _ = _setup(tmp_path, monkeypatch, ["*", "1-0"])
    al.run(queue, ["0,1"], wall_hours=3000 / 3600)
    rows = _rows(tmp_path)
    assert len(calls) == 1 and calls[0]["timeout"] == 3000 - al.CLEANUP_RESERVE_SECONDS
    assert len(rows) == 1 and rows[0]["attempt"] == "failed"   # the failed first game is kept
    receipt = json.loads((tmp_path / "receipts" / "queue.json").read_text())
    assert receipt["state"] == "wall_cap" and receipt["attempted_jobs"] == 1 and receipt["failed_jobs"] == 1


def test_game_in_flight_is_bounded_by_the_remaining_time(tmp_path, monkeypatch):
    queue, calls, _ = _setup(tmp_path, monkeypatch, ["1-0"], game_seconds=100.0)
    al.run(queue, ["0,1"], wall_hours=2500 / 3600)   # 2,500 s: the first game fits (2,450 s bound)
    assert calls[0]["timeout"] == 2500 - al.CLEANUP_RESERVE_SECONDS   # the remaining cap, less the reserve
    assert len(calls) == 1                                            # 2,400 s left: no second game


def test_kill_tree_reaches_a_grandchild_in_its_own_session(tmp_path):
    import subprocess, time as _time, os as _os
    import learning.compare_archives as ca
    # a child that starts a grandchild in a new session (as the referee starts its bots) and waits
    proc = subprocess.Popen(["bash", "-c", "setsid sleep 300 & echo $! > " + str(tmp_path / "gc.pid") + "; wait"])
    for _ in range(50):
        if (tmp_path / "gc.pid").exists() and (tmp_path / "gc.pid").read_text().strip():
            break
        _time.sleep(0.1)
    grandchild = int((tmp_path / "gc.pid").read_text().strip())
    assert grandchild in ca.descendants(proc.pid)
    ca.kill_tree(proc.pid)
    proc.wait(timeout=5)
    _time.sleep(0.2)
    gone = False
    try:
        _os.kill(grandchild, 0)
    except ProcessLookupError:
        gone = True
    assert gone, "the grandchild in its own session is killed too"
