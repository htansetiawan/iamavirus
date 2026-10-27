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
    # 1,500 s of cap: the first game (700 s) fits (1,200 s bound), the second colour does not
    queue, calls, _ = _setup(tmp_path, monkeypatch, ["*", "1-0"])
    al.run(queue, ["0,1"], wall_hours=1500 / 3600)
    rows = _rows(tmp_path)
    assert len(calls) == 1 and calls[0]["timeout"] == 1200
    assert len(rows) == 1 and rows[0]["attempt"] == "failed"   # the failed first game is kept
    receipt = json.loads((tmp_path / "receipts" / "queue.json").read_text())
    assert receipt["state"] == "wall_cap" and receipt["attempted_jobs"] == 1 and receipt["failed_jobs"] == 1


def test_game_in_flight_is_bounded_by_the_remaining_time(tmp_path, monkeypatch):
    queue, calls, _ = _setup(tmp_path, monkeypatch, ["1-0"], game_seconds=100.0)
    al.run(queue, ["0,1"], wall_hours=1300 / 3600)   # 1,300 s: the first game fits, with 1,300 s left
    assert calls[0]["timeout"] == 1200                            # min(bound, remaining)
