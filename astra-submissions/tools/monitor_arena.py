#!/usr/bin/env python3
"""Paced, read-only arena monitoring; immutable snapshots and new-game cache.

No credentials, uploads, GPU work, Git commands or engine mutations. A watch is
bounded by --hours. Ctrl-C stops it. Large output belongs on the Seagate drive.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://6s890.lids.mit.edu"
TEAM = "a2c35173659545c99752376a70418438"
DUCK = "8d775e234808489c815a4a9f6bbabfe4"


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


class Deferred(RuntimeError):
    def __init__(self, wait, message):
        super().__init__(message)
        self.wait = wait


class Client:
    def __init__(self):
        self.last = 0.0

    def get(self, path, params=None):
        url = BASE + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        for attempt in range(5):
            time.sleep(max(0, self.last + 1.0 - time.monotonic()))
            self.last = time.monotonic()
            request = urllib.request.Request(url, headers={"Accept": "application/json",
                "User-Agent": "iamavirus-astra-readonly-monitor/1.0"})
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    body = response.read()
                return json.loads(body), dict(url=url, fetched_at=now(),
                                             sha256=hashlib.sha256(body).hexdigest())
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 502, 503, 504):
                    raise
                wait = 2 ** attempt + random.random()
                retry = exc.headers.get("Retry-After")
                if retry:
                    try:
                        wait = max(wait, float(retry))
                    except ValueError:
                        try:
                            wait = max(wait, parsedate_to_datetime(retry).timestamp() - time.time())
                        except (ValueError, TypeError):
                            pass
                if wait > 30 or attempt == 4:
                    raise Deferred(wait, f"HTTP {exc.code}; deferred public read") from exc
                time.sleep(wait)
        raise AssertionError("unreachable")


def result_for_team(game):
    side = "white" if game["whitePlayerId"] == TEAM else "black"
    assert game[side + "PlayerId"] == TEAM
    other = "black" if side == "white" else "white"
    result = "D" if game["result"] == "1/2-1/2" else (
        "W" if game["result"] == ("1-0" if side == "white" else "0-1") else "L")
    return dict(game=game["id"], arena_version=game[side + "Version"], side=side,
                opponent=game[other], opponent_id=game[other + "PlayerId"],
                opponent_version=game[other + "Version"], result=result,
                reason=game["reason"], plies=game["plies"], completed_at=game["createdAt"])


def ledger_event(path, event, snapshot, duck):
    if path is None:
        return
    entry = dict(ts=now(), **{"from": "astra"}, to="all", type="result",
                 subject=f"Arena monitor: v{event['arena_version']} {event['result']} vs {event['opponent']}",
                 body=f"Public completed game {event['game']}: {event['side']}, {event['plies']} plies, "
                      f"{event['reason']}; opponent version {event['opponent_version']}. "
                      f"Duck Elo at this poll: {duck.get('rating')}. This is a result observation, not a causal strength estimate.",
                 refs=[event["game"], str(snapshot), BASE + "/api/games/" + event["game"]])
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        data = (json.dumps(entry) + "\n").encode()
        if os.write(descriptor, data) != len(data):
            raise OSError("short ledger write")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def poll(client, output, state, ledger, cache):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot = output / "snapshots" / stamp
    leaderboard, fetch1 = client.get("/api/leaderboard")
    versions, fetch2 = client.get(f"/api/leaderboard/{TEAM}/versions")
    metadata = [fetch1, fetch2]
    seen = set(state.get("seen", []))
    initial = not state.get("initialized", False)
    games, cursor = [], None
    # On startup, retain a recent snapshot. Subsequently follow sequential pages
    # until a known game appears so a busy interval does not silently skip data.
    while True:
        params = dict(player=TEAM, sort="played", order="desc", limit=100)
        if cursor:
            params["cursor"] = cursor
        page, record = client.get("/api/games", params)
        metadata.append(record)
        games.extend(page["games"])
        cursor = page["nextCursor"]
        if initial or not cursor or any(g["id"] in seen for g in page["games"]):
            break
    players = {p["id"]: p for p in leaderboard["players"]}
    duck = players.get(DUCK, {})
    ours = players.get(TEAM, {})
    fresh = [g for g in games if g["id"] not in seen]
    events = [result_for_team(g) for g in fresh]
    write_json(snapshot / "leaderboard.json", leaderboard)
    write_json(snapshot / "versions.json", versions)
    write_json(snapshot / "games.json", games)
    for game, event in zip(fresh, events):
        # Startup does not redownload a hundred historical games. Cache recent
        # v10-vs-Duck wins, then every newly completed team game after startup.
        notable_initial = (event["arena_version"] == 10 and event["opponent_id"] == DUCK
                           and event["result"] == "W")
        if initial and not notable_initial:
            continue
        destination = output / "replays" / (game["id"] + ".json.gz")
        if not destination.exists():
            existing = cache / game["id"] / "replay.json" if cache else None
            if existing is not None and existing.exists():
                raw = existing.read_bytes()
                replay = json.loads(raw)
                assert replay["id"] == game["id"]
                metadata.append(dict(game=game["id"], cache=str(existing), sha256=hashlib.sha256(raw).hexdigest()))
            else:
                replay, record = client.get("/api/games/" + game["id"])
                metadata.append(record)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(destination, "wt") as handle:
                json.dump(replay, handle)
        if not initial and (event["opponent_id"] == DUCK or event["reason"] not in
                           ("King capturable", "Threefold repetition", "50-move rule", "Move limit reached", "No legal moves")):
            ledger_event(ledger, event, snapshot, duck)
        print(json.dumps(dict(at=now(), event=event)), flush=True)
    write_json(snapshot / "fetch-metadata.json", metadata)
    latest = dict(at=now(), snapshot=str(snapshot), team_rating=ours.get("rating"),
                  active_version=ours.get("activeVersion"), active_record=ours.get("activeRecord"),
                  duck_rating=duck.get("rating"), duck_active_version=duck.get("activeVersion"),
                  duck_active_record=duck.get("activeRecord"), versions=versions["versions"],
                  new_results=[] if initial else events, startup_snapshot=initial)
    write_json(output / "latest.json", latest)
    state.update(initialized=True, seen=sorted(seen | {g["id"] for g in games}), last_success=now())
    write_json(output / "state.json", state)
    print(json.dumps({k: latest[k] for k in ("at", "active_version", "active_record", "duck_rating")}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--hours", type=float, default=0, help="0 means one poll")
    parser.add_argument("--interval", type=float, default=300)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args()
    if args.interval < 30 or args.hours < 0 or args.hours > 48:
        parser.error("interval must be >=30 seconds and hours between 0 and 48")
    drive = Path("/media/henrytan/seagate")
    if args.output.resolve().is_relative_to(drive) and not drive.is_mount():
        parser.error("Seagate is not mounted; refusing to write into its empty mountpoint")
    args.output.mkdir(parents=True, exist_ok=True)
    # Prevent accidentally starting two monitors against the same state/cache.
    with (args.output / ".monitor.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state_path = args.output / "state.json"
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        client = Client()
        end = time.monotonic() + args.hours * 3600
        write_json(args.output / "run.json", dict(started=now(), hours=args.hours,
                   interval=args.interval, pid=os.getpid(), team=TEAM, public_get_only=True,
                   source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
        while True:
            wait = args.interval
            try:
                poll(client, args.output, state, args.ledger, args.cache)
            except (urllib.error.URLError, TimeoutError, OSError, ValueError, Deferred) as exc:
                if isinstance(exc, Deferred):
                    wait = max(wait, exc.wait)
                print(json.dumps(dict(at=now(), error=str(exc), retry_after_seconds=wait)), flush=True)
                if args.hours == 0:
                    raise
            if args.hours == 0 or time.monotonic() + wait >= end:
                break
            time.sleep(wait)


if __name__ == "__main__":
    main()
