"""Replay collection, validation and quarantine.

    python -m learning.ingest --team IAmAVirus --output data/raw [--limit N]
    python -m learning.ingest --all --output data/raw --limit 2000
    python -m learning.ingest --from-corpus corpus/corpus-all.txt --output data/raw

Raw storage (immutable; one directory per game):

    data/raw/games/<id>/listing.json          the /api/games summary row
    data/raw/games/<id>/replay.json           the /api/games/<id> response
    data/raw/games/<id>/diagnostics.json      optional
    data/raw/games/<id>/fetch_metadata.json   URLs, timestamps, hashes
    data/raw/snapshots/<timestamp>/leaderboard.json
    data/raw/quarantine/<id>.json             exact validation failure
    data/raw/accepted.jsonl                   one line per accepted game

Validation replays every move with the pinned rules and compares each frame's
board and both observations, so an accepted replay is one the engine's own
rules reproduce exactly. Unexplained mismatches are quarantined, never patched.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import copy
import fcntl
import hashlib
import json
import os
import sys
import threading
from pathlib import Path

from . import api_client, rules
from .histories import classify_termination

RULES_FINGERPRINT = "fow-v1/iamavirus-rules-capi"
SUPPORTED_RULES_VERSIONS = {None, "fow-v1"}


def validate_replay(replay: dict, max_plies: int = 1000) -> tuple[list[rules.GameState], list[str]]:
    """Referee states after each frame, plus a list of problems (empty when valid)."""
    problems: list[str] = []
    frames = replay.get("frames")
    if not isinstance(frames, list) or not frames:
        return [], ["no frames"]
    game_id = replay.get("id", "")
    if not isinstance(game_id, str) or len(game_id) < 4:
        problems.append("bad game id")
    if replay.get("rulesVersion") not in SUPPORTED_RULES_VERSIONS:
        problems.append(f"unsupported rulesVersion {replay.get('rulesVersion')!r}")
    result = replay.get("result")
    if result not in ("1-0", "0-1", "1/2-1/2", "*"):
        problems.append(f"bad result {result!r}")
    state = rules.GameState(max_plies=max_plies)
    states: list[rules.GameState] = []
    for t, frame in enumerate(frames):
        if frame.get("ply") != t:
            problems.append(f"frame {t}: ply {frame.get('ply')!r} not contiguous")
            break
        for key in ("board", "white", "black"):
            text = frame.get(key)
            if not isinstance(text, str) or len(text) != 64 or not set(text) <= rules.OBSERVATION_CHARACTERS:
                problems.append(f"frame {t}: bad {key}")
        if problems:
            break
        move = frame.get("move")
        if t == 0:
            if move is not None:
                problems.append("frame 0 carries a move")
            if frame["board"] != rules.START_BOARD:
                problems.append("frame 0 is not the starting position")
        else:
            if not isinstance(move, str) or len(move) not in (4, 5):
                problems.append(f"frame {t}: bad move {move!r}")
                break
            if state.outcome() is not None:
                problems.append(f"frame {t}: game continued past terminal {state.outcome()}")
                break
            if move not in state.board.legal_moves():
                problems.append(f"frame {t}: move {move} is not legal")
                break
            state.push(move)
        if state.board.board_string() != frame["board"]:
            problems.append(f"frame {t}: board mismatch")
            break
        if state.board.observation(0) != frame["white"]:
            problems.append(f"frame {t}: white observation mismatch")
            break
        if state.board.observation(1) != frame["black"]:
            problems.append(f"frame {t}: black observation mismatch")
            break
        states.append(state.copy())
    if problems:
        return states, problems
    termination = classify_termination(replay.get("result", "*"), replay.get("reason", ""))
    verdict = state.outcome()
    if termination == "normal":
        if verdict != (replay.get("result"), replay.get("reason")):
            problems.append(f"final frame outcome {verdict} disagrees with {replay.get('result')} {replay.get('reason')!r}")
    elif verdict is not None:
        problems.append(f"technical termination {replay.get('reason')!r} but position is terminal {verdict}")
    return states, problems


def replay_hash(replay: dict) -> str:
    moves = [f["move"] for f in replay["frames"] if f.get("move")]
    return hashlib.sha256(" ".join(moves).encode()).hexdigest()


class RawStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.games = self.root / "games"
        self.quarantine = self.root / "quarantine"
        self.snapshots = self.root / "snapshots"
        self.accepted = self.root / "accepted.jsonl"
        for directory in (self.games, self.quarantine, self.snapshots):
            directory.mkdir(parents=True, exist_ok=True)
        self._thread_lock = threading.RLock()
        self._writer_depth = 0
        # Read the journal once, then only its appended tail. Existing duplicate
        # rows remain on disk as evidence but cannot duplicate future datasets.
        self._accepted_ids: dict[str, None] = {}
        self._index_identity = None
        self._index_offset = 0
        self._incomplete_tail = False
        self._index_bytes_read = 0

    @contextmanager
    def writer(self):
        """Serialize one game's transaction, never a network request or batch.

        Reentrant for this store, including nested save/append calls. Construct
        a new RawStore in each process; do not carry an active lock across fork.
        Other writers must use this API/the same .writer.lock convention.
        """
        with self._thread_lock:
            if self._writer_depth:
                self._writer_depth += 1
                try:
                    yield
                finally:
                    self._writer_depth -= 1
                return
            with open(self.root / ".writer.lock", "a+b") as handle:
                fcntl.flock(handle, fcntl.LOCK_EX)
                self._writer_depth = 1
                try:
                    yield
                finally:
                    self._writer_depth = 0
                    fcntl.flock(handle, fcntl.LOCK_UN)

    def _refresh_accepted(self) -> None:
        """Read complete new lines under writer(); preserve partial tail bytes."""
        try:
            handle = self.accepted.open("rb")
        except FileNotFoundError:
            self._accepted_ids.clear()
            self._index_identity = None
            self._index_offset = 0
            self._incomplete_tail = False
            return
        with handle:
            stat = os.fstat(handle.fileno())
            identity = (stat.st_dev, stat.st_ino)
            if identity != self._index_identity or stat.st_size < self._index_offset:
                self._accepted_ids.clear()
                self._index_offset = 0
            self._index_identity = identity
            handle.seek(self._index_offset)
            self._incomplete_tail = False
            while line := handle.readline():
                self._index_bytes_read += len(line)
                if not line.endswith(b"\n"):
                    self._incomplete_tail = True
                    break
                if line.strip():
                    self._accepted_ids[json.loads(line)["id"]] = None
                self._index_offset = handle.tell()

    def _accepted_complete(self, game_id: str, listing: bool = False,
                           diagnostics: bool = False) -> bool:
        directory = self.games / game_id
        required = ["replay.json", "fetch_metadata.json"]
        if listing:
            required.append("listing.json")
        if diagnostics:
            required.append("diagnostics.json")
        return game_id in self._accepted_ids and all((directory / name).is_file() for name in required)

    def accepted_ids(self) -> set[str]:
        with self.writer():
            self._refresh_accepted()
            return set(self._accepted_ids)

    def write_json(self, path: Path, payload) -> str:
        with self.writer():
            return api_client.atomic_write(path, json.dumps(payload, indent=1, sort_keys=True).encode())

    def save_game(self, replay: dict, listing: dict | None, fetch: dict, diagnostics: dict | None) -> None:
        with self.writer():
            self._refresh_accepted()
            if self._accepted_complete(replay["id"], listing is not None, diagnostics is not None):
                return
            directory = self.games / replay["id"]
            # Completed accepted sources are immutable. A recovery fills only
            # missing files; it must not replace the original fetched evidence.
            accepted = replay["id"] in self._accepted_ids
            replay_path = directory / "replay.json"
            replay_missing = not replay_path.is_file()
            if not accepted or replay_missing:
                digest = self.write_json(replay_path, replay)
            else:
                digest = api_client.sha256_bytes(replay_path.read_bytes())
            if listing is not None and (not accepted or not (directory / "listing.json").is_file()):
                self.write_json(directory / "listing.json", listing)
            if diagnostics is not None and (not accepted or not (directory / "diagnostics.json").is_file()):
                self.write_json(directory / "diagnostics.json", diagnostics)
            metadata_path = directory / "fetch_metadata.json"
            if not accepted or not metadata_path.is_file() or replay_missing:
                metadata = (json.loads(metadata_path.read_text()) if accepted and metadata_path.is_file()
                            else copy.deepcopy(fetch))
                if isinstance(metadata.get("replay"), dict):
                    record = metadata["replay"]
                    if record.get("sha256") != digest and "sha256" in record:
                        record.setdefault("source_bytes_sha256", record["sha256"])
                    record["sha256"] = digest
                self.write_json(metadata_path, metadata)

    def record_accepted(self, replay: dict, problems_none: bool = True) -> bool:
        """Append at most once per ID, including across independent processes."""
        frames = replay["frames"]
        row = {"id": replay["id"], "white": replay.get("white"), "black": replay.get("black"),
               "whitePlayerId": replay.get("whitePlayerId"), "blackPlayerId": replay.get("blackPlayerId"),
               "whiteVersion": replay.get("whiteVersion"), "blackVersion": replay.get("blackVersion"),
               "result": replay.get("result"), "reason": replay.get("reason"),
               "plies": len(frames) - 1, "createdAt": replay.get("createdAt"),
               "rulesVersion": replay.get("rulesVersion"), "moves_sha256": replay_hash(replay),
               "termination": classify_termination(replay.get("result", "*"), replay.get("reason", ""))}
        with self.writer():
            self._refresh_accepted()
            if replay["id"] in self._accepted_ids:
                return False
            if self._incomplete_tail:
                raise ValueError(f"incomplete journal tail: {self.accepted}; preserve and repair before appending")
            with open(self.accepted, "ab") as handle:
                handle.write((json.dumps(row, sort_keys=True) + "\n").encode())
                handle.flush()
                os.fsync(handle.fileno())
            self._refresh_accepted()
            return True

    def record_quarantine(self, game_id: str, problems: list[str], replay: dict | None) -> None:
        self.write_json(self.quarantine / f"{game_id}.json",
                        {"id": game_id, "problems": problems,
                         "result": replay.get("result") if replay else None,
                         "reason": replay.get("reason") if replay else None,
                         "rulesVersion": replay.get("rulesVersion") if replay else None})

    def accepted_replays(self):
        with self.writer():
            self._refresh_accepted()
            game_ids = list(self._accepted_ids)
        # Do not hold the writer lock while a downstream trainer consumes data.
        for game_id in game_ids:
            path = self.games / game_id / "replay.json"
            if path.exists():
                yield json.loads(path.read_text())


class ReplayProblems(list[str]):
    """Backwards-compatible validation result with per-call ingestion status."""
    def __init__(self, problems=(), *, cached=False, recovered=False):
        super().__init__(problems)
        self.cached = cached
        self.recovered = recovered


def ingest_replay(store: RawStore, replay: dict, listing: dict | None, fetch: dict,
                  diagnostics: dict | None) -> ReplayProblems:
    """Stores a replay, validates it, and files the verdict. Returns the problems."""
    with store.writer():
        store._refresh_accepted()
        game_id = replay["id"]
        if store._accepted_complete(game_id, listing is not None, diagnostics is not None):
            return ReplayProblems(cached=True)
        recovering = game_id in store._accepted_ids
        if recovering:
            # Check the original source too when repairing missing metadata.
            saved = store.games / game_id / "replay.json"
            if saved.is_file():
                replay = json.loads(saved.read_text())
        else:
            store.save_game(replay, listing, fetch, diagnostics)
        _, problems = validate_replay(replay)
        if problems:
            store.record_quarantine(game_id, problems, replay)
        else:
            if recovering:
                store.save_game(replay, listing, fetch, diagnostics)
            store.record_accepted(replay)
        return ReplayProblems(problems, recovered=recovering and not problems)


def resolve_team_id(leaderboard: dict, name: str) -> str | None:
    for player in leaderboard.get("players", []):
        if player.get("name") == name or player.get("id") == name:
            return player.get("id")
    lowered = name.lower()
    for player in leaderboard.get("players", []):
        if lowered in (player.get("name") or "").lower():
            return player.get("id")
    return None


def ingest_from_api(output: Path, team: str | None, player_id: str | None, limit: int | None,
                    outcome: str | None, with_diagnostics: bool, pause: float) -> dict:
    store = RawStore(output)
    client = api_client.ApiClient(min_interval=pause, cache_dir=store.root)
    stamp = api_client.utc_now().replace(":", "").replace("+", "Z")
    leaderboard, lb_record = client.leaderboard()
    store.write_json(store.snapshots / stamp / "leaderboard.json",
                     {"fetched": lb_record.__dict__, "leaderboard": leaderboard})
    params: dict = {"sort": "played", "order": "desc", "limit": 100}
    if player_id is None and team:
        player_id = resolve_team_id(leaderboard, team)
        if player_id is None:
            print(f"team {team!r} not on the leaderboard; using it as a name substring", file=sys.stderr)
    if player_id:
        params["player"] = player_id
    elif team:
        params["white"] = team
        params["colors"] = "any"
    if outcome:
        params["outcome"] = outcome
    print(f"listing games with {params}", file=sys.stderr)
    known = store.accepted_ids()
    counts = {"listed": 0, "fetched": 0, "cached": 0, "accepted": 0, "quarantined": 0, "errors": 0,
              "already_accepted": 0, "recovered": 0}
    for summary, _ in client.iter_games(params, limit):
        counts["listed"] += 1
        game_id = summary["id"]
        if summary.get("result") not in ("1-0", "0-1", "1/2-1/2"):
            continue
        required = ["replay.json", "fetch_metadata.json", "listing.json"]
        if with_diagnostics:
            required.append("diagnostics.json")
        if game_id in known and all((store.games / game_id / name).is_file() for name in required):
            counts["cached"] += 1
            continue
        try:
            replay, record, cached = client.replay(game_id)
        except api_client.ApiError as error:
            counts["errors"] += 1
            print(f"  {game_id}: {error}", file=sys.stderr)
            continue
        counts["cached" if cached else "fetched"] += 1
        fetch = {"replay": record.__dict__, "listing_source": "/api/games"}
        diagnostics = None
        if with_diagnostics:
            try:
                diagnostics, diag_record = client.diagnostics(game_id)
                fetch["diagnostics"] = diag_record.__dict__
            except api_client.ApiError as error:
                fetch["diagnostics_error"] = str(error)
        problems = ingest_replay(store, replay, summary, fetch, diagnostics)
        if problems:
            counts["quarantined"] += 1
        else:
            known.add(game_id)
            counts["already_accepted" if problems.cached else "recovered" if problems.recovered else "accepted"] += 1
        if counts["listed"] % 25 == 0:
            print(f"  {counts}", file=sys.stderr)
    print(f"done: {counts}; {client.requests_made} requests", file=sys.stderr)
    return counts


def ingest_from_corpus(output: Path, corpus: Path) -> dict:
    """Builds replays from the committed move-list corpus (no network)."""
    from .histories import replay_from_moves

    store = RawStore(output)
    counts = {"accepted": 0, "quarantined": 0, "skipped": 0, "recovered": 0}
    seen = store.accepted_ids()
    for line in corpus.read_text().splitlines():
        fields = line.split()
        if len(fields) < 6:
            continue
        game_id, side, result, reason, opponent = fields[:5]
        if game_id in seen and all((store.games / game_id / name).is_file()
                                  for name in ("replay.json", "fetch_metadata.json")):
            counts["skipped"] += 1
            continue
        seen.add(game_id)
        moves = fields[5:]
        reason_text = reason.replace("_", " ")
        white = opponent.replace("_", " ") if side == "b" else "IAmAVirus"
        black = "IAmAVirus" if side == "b" else opponent.replace("_", " ")
        replay = replay_from_moves(game_id, moves, result, reason_text, white, black)
        replay["whitePlayerId"] = white
        replay["blackPlayerId"] = black
        replay["source"] = "corpus"
        fetch = {"replay": {"url": f"corpus:{corpus.name}", "fetched_at": api_client.utc_now(),
                            "sha256": hashlib.sha256(line.encode()).hexdigest(), "status": 0, "attempts": 0}}
        problems = ingest_replay(store, replay, None, fetch, None)
        counts["quarantined" if problems else "skipped" if problems.cached else
               "recovered" if problems.recovered else "accepted"] += 1
        if problems:
            print(f"  {game_id}: {problems[0]}", file=sys.stderr)
    print(f"corpus: {counts}", file=sys.stderr)
    return counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, default=Path("data/raw"))
    parser.add_argument("--team", default=None, help="team name (resolved to an exact id via the leaderboard)")
    parser.add_argument("--player-id", default=None, help="exact team id for the `player` filter")
    parser.add_argument("--outcome", default=None, help="only for analysis: team-won, team-lost, ...")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--diagnostics", action="store_true", help="also archive /diagnostics")
    parser.add_argument("--pause", type=float, default=1.2)
    parser.add_argument("--from-corpus", type=Path, default=None)
    parser.add_argument("--all", action="store_true",
                        help="collect recent public games across every team (no player filter)")
    args = parser.parse_args(argv)
    if args.from_corpus:
        ingest_from_corpus(args.output, args.from_corpus)
        return 0
    if not args.team and not args.player_id and not args.all:
        parser.error("--team, --player-id, --all or --from-corpus is required")
    ingest_from_api(args.output, args.team, args.player_id, args.limit, args.outcome,
                    args.diagnostics, args.pause)
    return 0


if __name__ == "__main__":
    sys.exit(main())
