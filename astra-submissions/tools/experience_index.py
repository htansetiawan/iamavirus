#!/usr/bin/env python3
"""Build and query an actor-only, packed index of validated replay episodes.

This is an offline research index, not a deployed policy. No GPU or API access.
The existing learning.dataset manifest supplies immutable whole-game splits.
Privileged targets are deliberately not copied into this database. Matches are
experience references, not permission to copy moves or declare a square safe.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import heapq
import json
from pathlib import Path
import sqlite3
import struct
import time

SYMBOLS = "-PNBRQKpnbrqk?"
CODES = {symbol: index for index, symbol in enumerate(SYMBOLS)}
SCHEMA = "astra-experience-v1"


def pack_view(view: str) -> bytes:
    """a1 through h8; low nibble is the earlier square; unknown is code 13."""
    if len(view) != 64 or any(c not in CODES for c in view):
        raise ValueError("expected 64 board symbols, including distinct '-'/'?'")
    return bytes(CODES[view[i]] | (CODES[view[i + 1]] << 4) for i in range(0, 64, 2))


def unpack_view(packed: bytes) -> str:
    if len(packed) != 32:
        raise ValueError("expected 32 packed bytes")
    codes = [code for byte in packed for code in (byte & 15, byte >> 4)]
    if any(code >= len(SYMBOLS) for code in codes):
        raise ValueError("reserved nibble in packed observation")
    return "".join(SYMBOLS[code] for code in codes)


def pack_move(move: str) -> bytes:
    if (len(move) not in (4, 5) or move[0] not in "abcdefgh" or
            move[2] not in "abcdefgh" or move[1] not in "12345678" or
            move[3] not in "12345678" or (len(move) == 5 and move[4] not in "qrbn")):
        raise ValueError(f"bad UCI move: {move!r}")
    start = ord(move[0]) - 97 + 8 * (int(move[1]) - 1)
    end = ord(move[2]) - 97 + 8 * (int(move[3]) - 1)
    promotion = 0 if len(move) == 4 else "qrbn".index(move[4]) + 1
    return struct.pack("<H", start | (end << 6) | (promotion << 12))


def sha_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def actor_decisions(actor: dict):
    """Streaming permitted prefixes; deliberately accepts no labels/metadata.

    The current demonstrated action enters the fingerprint only AFTER yielding
    its decision. Ages saturate at 254; 255 means never observed. Last seen
    occupancy is memory, not a claim that a hidden piece stayed on that square.
    """
    side = actor["side"]
    if side not in (0, 1):
        raise ValueError("side must be 0 or 1")
    views, phases, plies = (actor[k] for k in ("observations", "phases", "plies"))
    if not (len(views) == len(phases) == len(plies)):
        raise ValueError("misaligned observation events")
    events = actor["decision_event_indices"]
    aligned = ("own_actions", "legal_actions", "inferred_en_passant", "castling_rights")
    if any(len(actor[k]) != len(events) for k in aligned):
        raise ValueError("misaligned decision fields")
    if events != sorted(set(events)) or any(i < 0 or i >= len(views) for i in events):
        raise ValueError("invalid decision event indices")
    decision_by_event = {event: index for index, event in enumerate(events)}
    seen, seen_at = ["?"] * 64, [-1] * 64
    history = hashlib.sha256(SCHEMA.encode() + bytes([side]))
    previous_ply = -1
    for event, (view, phase, ply) in enumerate(zip(views, phases, plies)):
        packed = pack_view(view)
        if phase not in (0, 1, 2) or ply <= previous_ply:
            raise ValueError("invalid phase or non-increasing ply")
        previous_ply = ply
        history.update(b"O" + struct.pack("<IB", ply, phase) + packed)
        for square, symbol in enumerate(view):
            if symbol != "?":
                seen[square], seen_at[square] = symbol, ply
        if event not in decision_by_event:
            continue
        d = decision_by_event[event]
        if ply % 2 != side:
            raise ValueError("decision for wrong side")
        rights, ep = actor["castling_rights"][d], actor["inferred_en_passant"][d]
        if not 0 <= rights < 2**64 or not -1 <= ep < 64:
            raise ValueError("invalid own rights/EP")
        legal = b"".join(pack_move(move) for move in sorted(actor["legal_actions"][d]))
        if actor["own_actions"][d] not in actor["legal_actions"][d]:
            raise ValueError("demonstrated action outside supplied legal set")
        rights_bytes = struct.pack("<Q", rights)
        key = history.copy()
        key.update(b"D" + rights_bytes + struct.pack("<bI", ep, len(legal)) + legal)
        king = "K" if side == 0 else "k"
        if view.count(king) != 1:
            raise ValueError("live decision must contain exactly one own king")
        own_count = sum(c in ("PNBRQK" if side == 0 else "pnbrqk") for c in view)
        yield dict(event=event, ply=ply, phase=phase, side=side,
                   history=key.digest(), observation=packed,
                   memory=pack_view("".join(seen)),
                   ages=bytes(255 if t < 0 else min(254, ply - t) for t in seen_at),
                   rights=rights_bytes, ep=ep, legal=legal,
                   king_square=view.index(king), own_count=own_count)
        history.update(b"A" + pack_move(actor["own_actions"][d]))


DDL = """
CREATE TABLE episodes (
 id INTEGER PRIMARY KEY, game TEXT NOT NULL, side INTEGER NOT NULL,
 split TEXT NOT NULL, player TEXT, opponent TEXT, played_version TEXT,
 opponent_version TEXT, source_sha256 TEXT NOT NULL, trajectory_sha256 TEXT NOT NULL,
 UNIQUE(game, side));
CREATE TABLE decisions (
 id INTEGER PRIMARY KEY, episode INTEGER NOT NULL REFERENCES episodes(id),
 split TEXT NOT NULL, side INTEGER NOT NULL, event INTEGER NOT NULL,
 ply INTEGER NOT NULL, phase INTEGER NOT NULL, history BLOB NOT NULL,
 observation BLOB NOT NULL CHECK(length(observation)=32),
 memory BLOB NOT NULL CHECK(length(memory)=32), ages BLOB NOT NULL CHECK(length(ages)=64),
 rights BLOB NOT NULL CHECK(length(rights)=8), ep INTEGER NOT NULL,
 legal BLOB NOT NULL, king_square INTEGER NOT NULL, own_count INTEGER NOT NULL,
 UNIQUE(episode,event));
CREATE INDEX exact_history ON decisions(split,side,history,id);
CREATE INDEX context_lookup ON decisions(split,side,king_square,own_count,id);
"""


def build(manifest_path: Path, accepted: Path, output: Path):
    if output.exists():
        raise ValueError("output already exists; use a fresh directory")
    drive = Path("/media/henrytan/seagate")
    if output.resolve().is_relative_to(drive) and not drive.is_mount():
        raise ValueError("Seagate is not mounted")
    manifest = json.loads(manifest_path.read_text())
    accepted_bytes = accepted.read_bytes()
    inputs = {str(manifest_path.resolve()): sha_file(manifest_path),
              str(accepted.resolve()): hashlib.sha256(accepted_bytes).hexdigest()}
    games = {}
    for line in accepted_bytes.decode().splitlines():
        row = json.loads(line)
        previous = games.setdefault(row["id"], row["moves_sha256"])
        if previous != row["moves_sha256"]:
            raise ValueError("conflicting accepted game trajectories")
    shards = {split: Path(path) for split, path in manifest["shards"].items()}
    for path in shards.values():
        inputs[str(path.resolve())] = sha_file(path)
    output.mkdir(parents=True)
    db = sqlite3.connect(output / "actors.sqlite")
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(DDL)
    counts, split_by_trajectory, split_by_game = Counter(), {}, {}
    started = time.monotonic()
    try:
        for split, path in sorted(shards.items()):
            if split not in ("train", "validation", "test"):
                raise ValueError(f"unknown split: {split}")
            with gzip.open(path, "rt") as source:
                for line in source:
                    episode = json.loads(line)
                    meta, actor = episode["metadata"], episode["actor"]
                    if meta["split"] != split or meta.get("candidate_mismatches"):
                        raise ValueError("split mismatch or unvalidated actor candidates")
                    game = meta["game_id"]
                    trajectory = games[game]
                    if (split_by_game.setdefault(game, split) != split or
                            split_by_trajectory.setdefault(trajectory, split) != split):
                        raise ValueError("game/duplicate trajectory crosses dataset split")
                    cursor = db.execute("INSERT INTO episodes VALUES(NULL,?,?,?,?,?,?,?,?,?)",
                        (game, actor["side"], split, meta.get("player_id"), meta.get("opponent_id"),
                         json.dumps(meta.get("played_version")), json.dumps(meta.get("opponent_version")),
                         meta["source_hash"], trajectory))
                    eid = cursor.lastrowid
                    # Targets are not read; the index's feature builder has no access to them.
                    for row in actor_decisions(actor):
                        db.execute("INSERT INTO decisions VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (eid, split, row["side"], row["event"], row["ply"], row["phase"],
                             row["history"], row["observation"], row["memory"], row["ages"],
                             row["rights"], row["ep"], row["legal"], row["king_square"], row["own_count"]))
                        counts[split + "_decisions"] += 1
                    counts[split + "_episodes"] += 1
                    if sum(counts[k] for k in counts if k.endswith("_episodes")) % 100 == 0:
                        db.commit()
            db.commit()
            print(json.dumps(dict(split=split, counts=dict(counts))), flush=True)
        # Append-only raw acceptance can legitimately grow while this build runs;
        # the snapshot read above is retained. Every actual episode shard is frozen.
        for path in [manifest_path, *shards.values()]:
            if sha_file(path) != inputs[str(path.resolve())]:
                raise ValueError(f"source changed during build: {path}")
        db.execute("ANALYZE")
        db.commit()
        stats = dict(schema=SCHEMA, built_at=datetime.now(timezone.utc).isoformat(),
                     inputs_sha256=inputs, source_manifest=manifest,
                     counts=dict(counts), games=len(split_by_game),
                     distinct_trajectories=len(split_by_trajectory),
                     elapsed_seconds=time.monotonic()-started,
                     actor_payload_bytes=dict(observation=32, last_seen=32, ages=64,
                         rights=8, history_fingerprint=32, legal_move=2),
                     code_sha256=sha_file(Path(__file__)),
                     limitations=["Research index only; no learned embedding or policy yet.",
                         "History fingerprint excludes clocks absent from source actor schema.",
                         "Last-seen memory/age is an approximate feature, not an exact belief.",
                         "No actor feature depends on true boards, hidden moves, or outcomes."])
    finally:
        db.close()
    stats["database_bytes"] = (output / "actors.sqlite").stat().st_size
    stats["database_sha256"] = sha_file(output / "actors.sqlite")
    (output / "game-splits.json").write_text(json.dumps({game: dict(split=split, trajectory_sha256=games[game])
        for game, split in sorted(split_by_game.items())}, indent=2) + "\n")
    (output / "manifest.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps({k: stats[k] for k in ("games", "counts", "database_bytes", "elapsed_seconds")}))


def distance(left: bytes, right: bytes) -> int:
    """Categorical square distance, never bit Hamming over arbitrary piece IDs.

    A hidden/visible mismatch costs one; different visible symbols cost two.
    This is a retrieval baseline, not a calibrated tactical similarity metric.
    """
    return sum(0 if a == b else 1 if "?" in (a, b) else 2
               for a, b in zip(unpack_view(left), unpack_view(right)))


def query(database: Path, view: str, side: int, top: int = 10,
          budget: int = 2048, history: bytes | None = None, exclude_game: str | None = None):
    if side not in (0, 1) or not 1 <= top <= budget <= 100000:
        raise ValueError("require side 0/1 and 1 <= top <= budget <= 100000")
    packed = pack_view(view)
    king = "K" if side == 0 else "k"
    if view.count(king) != 1:
        raise ValueError("query needs exactly one visible own king")
    own_count = sum(c in ("PNBRQK" if side == 0 else "pnbrqk") for c in view)
    db = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    started = time.monotonic()
    try:
        # SQL filters and indexes bound the candidate pool BEFORE distance work.
        # Current-position-only queries explicitly do not claim identical histories.
        conditions = ["d.split='train'", "d.side=?"]
        params: list = [side]
        if history is not None:
            if len(history) != 32:
                raise ValueError("history fingerprint must be 32 bytes")
            conditions.append("d.history=?")
            params.append(history)
            mode = "recorded_history_prefix"
        else:
            conditions += ["d.king_square=?", "d.own_count=?"]
            params += [view.index(king), own_count]
            mode = "bounded_observation_context"
        if exclude_game is not None:
            conditions.append("e.trajectory_sha256 NOT IN (SELECT trajectory_sha256 FROM episodes WHERE game=?)")
            params.append(exclude_game)
        sql = ("SELECT d.*, e.game, e.trajectory_sha256 FROM decisions d JOIN episodes e ON e.id=d.episode WHERE "
               + " AND ".join(conditions) + " ORDER BY d.id LIMIT ?")
        candidates = db.execute(sql, (*params, budget + 1)).fetchall()
        truncated = len(candidates) > budget
        candidates = candidates[:budget]
        # O(M log k), M <= budget; avoids sorting the full candidate set.
        ranked = heapq.nsmallest(top, candidates,
                                key=lambda row: (distance(packed, row["observation"]), row["id"]))
        return dict(mode=mode, candidate_budget=budget, candidates_examined=len(candidates),
                    truncated=truncated, train_only=True,
                    elapsed_ms=(time.monotonic()-started)*1000,
                    matches=[dict(game=r["game"], side=r["side"], ply=r["ply"],
                        decision_id=r["id"], distance=distance(packed, r["observation"])) for r in ranked],
                    limitation="Bounded context retrieval; no global nearest-neighbor recall guarantee. "
                               "Current view similarity does not imply matching hidden-state histories.")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--manifest", type=Path, required=True)
    build_parser.add_argument("--accepted", type=Path, required=True)
    build_parser.add_argument("--output", type=Path, required=True)
    query_parser = sub.add_parser("query")
    query_parser.add_argument("--database", type=Path, required=True)
    query_parser.add_argument("--view", required=True)
    query_parser.add_argument("--side", choices=[0, 1], type=int, required=True)
    query_parser.add_argument("--top", type=int, default=10)
    query_parser.add_argument("--budget", type=int, default=2048)
    query_parser.add_argument("--history-hex")
    query_parser.add_argument("--exclude-game")
    args = parser.parse_args()
    if args.command == "build":
        build(args.manifest, args.accepted, args.output)
    else:
        print(json.dumps(query(args.database, args.view, args.side, args.top, args.budget,
            bytes.fromhex(args.history_hex) if args.history_hex else None, args.exclude_game), indent=2))


if __name__ == "__main__":
    main()
