#!/usr/bin/env python3
"""Separate hindsight catalogue for analysts; never an actor retrieval feature.

Browse verified terminal examples by role/geometry facets, or attach their
labels AFTER the existing actor query has chosen and ranked its matches.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experience_index as actors

SCHEMA = "astra-analyst-terminal-catalogue-v1"
KINDS = {"king_bait", "king_walk", "ignored_check", "opened_king_line", "castle_into_attack"}
LIMITATION = ("Oracle hindsight terminal examples, not actor features or move advice. "
              "True-board one-ply safe alternatives need not be realizable from fog information. "
              "Terminal examples alone do not measure bait acceptance or strategy success.")
DDL = """
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE seats (
 game TEXT NOT NULL, side INTEGER NOT NULL, source_sha256 TEXT NOT NULL,
 plies INTEGER NOT NULL, PRIMARY KEY(game,side));
CREATE TABLE motifs (
 id INTEGER PRIMARY KEY, game TEXT NOT NULL, side INTEGER NOT NULL,
 ply INTEGER NOT NULL, kind TEXT NOT NULL, forced INTEGER NOT NULL,
 all_hidden INTEGER NOT NULL, material_before INTEGER NOT NULL,
 label_json TEXT NOT NULL, UNIQUE(game,side,ply),
 FOREIGN KEY(game,side) REFERENCES seats(game,side));
CREATE TABLE attackers (
 motif INTEGER NOT NULL REFERENCES motifs(id), piece TEXT NOT NULL,
 square TEXT NOT NULL, hidden_before INTEGER NOT NULL, screen_released INTEGER NOT NULL,
 PRIMARY KEY(motif,square));
CREATE INDEX motif_facets ON motifs(kind,forced,all_hidden,id);
CREATE INDEX attacker_facets ON attackers(piece,hidden_before,motif);
"""


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def readonly(path: Path):
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def build(rows_path: Path, raw_games: Path, output: Path):
    """Bind already audited seat labels to the exact replay bytes before import.

    Does not regenerate or prove labels: their native/referee audit is upstream.
    A bad source or row aborts the entire build, leaving no output database.
    """
    if output.exists():
        raise ValueError("output already exists")
    data = rows_path.read_bytes()
    rows = json.loads(data)
    if not isinstance(rows, list):
        raise ValueError("expected a list of audited seat rows")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".catalogue-") as temp:
        staged = Path(temp) / "catalogue.sqlite"
        db = sqlite3.connect(staged)
        verified, seen = {}, set()
        count = 0
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.executescript(DDL)
            for row in rows:
                game, seat, source, plies = (row[k] for k in ("id", "side", "source_sha256", "plies"))
                if not re.fullmatch(r"[a-z0-9]{8}", game) or seat not in ("white", "black"):
                    raise ValueError("invalid game or side")
                side = 0 if seat == "white" else 1
                if (game, side) in seen:
                    raise ValueError("duplicate game seat")
                seen.add((game, side))
                if not re.fullmatch(r"[0-9a-f]{64}", source) or type(plies) is not int or plies < 0:
                    raise ValueError("invalid source hash or ply count")
                if game not in verified:
                    replay_bytes = (raw_games / game / "replay.json").read_bytes()
                    verified[game] = (sha_bytes(replay_bytes), json.loads(replay_bytes))
                source_hash, replay = verified[game]
                if source_hash != source or replay["id"] != game or len(replay["frames"]) != plies + 1:
                    raise ValueError("replay binding mismatch")
                db.execute("INSERT INTO seats VALUES(?,?,?,?)", (game, side, source, plies))
                label = row.get("terminal_motif")
                if label is None:
                    continue
                if (not plies or (plies - 1) % 2 != side or replay["reason"] != "King capturable"
                        or label["move"] != replay["frames"][-1]["move"]):
                    raise ValueError("terminal decision binding mismatch")
                if label["kind"] not in KINDS:
                    raise ValueError("unknown terminal kind")
                for key in ("forced_one_ply_loss", "all_killers_hidden"):
                    if type(label[key]) is not bool:
                        raise ValueError("expected boolean label facet")
                if label["forced_one_ply_loss"] != (not label["safe_moves"]):
                    raise ValueError("forced facet disagrees with safe alternatives")
                killers = label["killers"]
                if not killers or label["all_killers_hidden"] != all(k["hidden_before"] for k in killers):
                    raise ValueError("inconsistent attacker facets")
                cursor = db.execute("INSERT INTO motifs VALUES(NULL,?,?,?,?,?,?,?,?)",
                    (game, side, plies - 1, label["kind"], int(label["forced_one_ply_loss"]),
                     int(label["all_killers_hidden"]), label["material_before"],
                     json.dumps(label, sort_keys=True, allow_nan=False)))
                for killer in killers:
                    if (killer["piece"] not in "PNBRQK" or len(killer["piece"]) != 1
                            or not re.fullmatch(r"[a-h][1-8]", killer["square"])
                            or type(killer["hidden_before"]) is not bool
                            or type(killer["own_screen_released"]) is not bool):
                        raise ValueError("invalid attacker role")
                    db.execute("INSERT INTO attackers VALUES(?,?,?,?,?)", (cursor.lastrowid,
                        killer["piece"], killer["square"], int(killer["hidden_before"]),
                        int(killer["own_screen_released"])))
                count += 1
            metadata = dict(schema=SCHEMA, source_rows_sha256=sha_bytes(data),
                            games=len(verified), seats=len(seen), terminal_examples=count,
                            limitation=LIMITATION)
            db.executemany("INSERT INTO metadata VALUES(?,?)",
                           [(key, json.dumps(value)) for key, value in metadata.items()])
            db.execute("ANALYZE")
            db.commit()
        finally:
            db.close()
        # Atomic no-overwrite publication on the same filesystem.
        os.link(staged, output)
    return metadata


def check_schema(db):
    row = db.execute("SELECT value FROM metadata WHERE key='schema'").fetchone()
    if row is None or json.loads(row[0]) != SCHEMA:
        raise ValueError("unsupported analyst catalogue schema")


def browse(database: Path, *, kind: str | None = None, attacker: str | None = None,
           all_hidden: bool | None = None, forced: bool | None = None, limit: int = 10):
    if not 1 <= limit <= 1000 or (kind is not None and kind not in KINDS):
        raise ValueError("invalid kind or limit")
    if attacker is not None and attacker not in tuple("PNBRQK"):
        raise ValueError("attacker must be an uppercase piece role")
    for value in (all_hidden, forced):
        if value is not None and type(value) is not bool:
            raise ValueError("facet must be boolean or None")
    conditions, params = [], []
    for column, value in (("m.kind", kind), ("m.all_hidden", all_hidden), ("m.forced", forced)):
        if value is not None:
            conditions.append(column + "=?")
            params.append(value)
    if attacker is not None:
        conditions.append("EXISTS(SELECT 1 FROM attackers a WHERE a.motif=m.id AND a.piece=?)")
        params.append(attacker)
    sql = ("SELECT m.*,s.source_sha256 FROM motifs m JOIN seats s ON s.game=m.game AND s.side=m.side"
           + (" WHERE " + " AND ".join(conditions) if conditions else "") + " ORDER BY m.id LIMIT ?")
    db = readonly(database)
    try:
        check_schema(db)
        matches = [dict(game=r["game"], side=r["side"], ply=r["ply"], source_sha256=r["source_sha256"],
                        oracle_label=json.loads(r["label_json"])) for r in db.execute(sql, (*params, limit))]
        return dict(analyst_only=True, matches=matches, limitation=LIMITATION)
    finally:
        db.close()


def query(actor_database: Path, catalogue_database: Path, view: str, side: int, **kwargs):
    # No catalogue connection or label is consulted before actor ranking finishes.
    result = actors.query(actor_database, view, side, **kwargs)
    annotations = {}
    actor_db, catalogue = readonly(actor_database), None
    try:
        catalogue = readonly(catalogue_database)
        check_schema(catalogue)
        for match in result["matches"]:
            binding = actor_db.execute("SELECT e.game,e.source_sha256,d.side,d.ply FROM decisions d "
                "JOIN episodes e ON e.id=d.episode WHERE d.id=?", (match["decision_id"],)).fetchone()
            if binding is None or (binding["game"], binding["side"], binding["ply"]) != (
                    match["game"], match["side"], match["ply"]):
                raise ValueError("actor decision changed during annotation")
            seat = catalogue.execute("SELECT source_sha256 FROM seats WHERE game=? AND side=?",
                                     (binding["game"], binding["side"])).fetchone()
            status, label = "not_in_catalogue", None
            if seat is not None:
                if seat[0] != binding["source_sha256"]:
                    status = "source_mismatch"
                else:
                    row = catalogue.execute("SELECT label_json FROM motifs WHERE game=? AND side=? AND ply=?",
                        (binding["game"], binding["side"], binding["ply"])).fetchone()
                    status = "labelled_terminal" if row else "no_terminal_label_at_this_decision"
                    label = json.loads(row[0]) if row else None
            annotations[str(match["decision_id"])] = dict(status=status, oracle_label=label)
    finally:
        actor_db.close()
        if catalogue is not None:
            catalogue.close()
    return dict(actor_result=result, analyst_only=True, oracle_annotations=annotations,
                limitation=LIMITATION)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--rows", type=Path, required=True)
    build_parser.add_argument("--raw-games", type=Path, required=True)
    build_parser.add_argument("--output", type=Path, required=True)
    browse_parser = sub.add_parser("browse")
    browse_parser.add_argument("--database", type=Path, required=True)
    browse_parser.add_argument("--kind", choices=sorted(KINDS))
    browse_parser.add_argument("--attacker", choices=list("PNBRQK"))
    browse_parser.add_argument("--all-hidden", action=argparse.BooleanOptionalAction, default=None)
    browse_parser.add_argument("--forced", action=argparse.BooleanOptionalAction, default=None)
    browse_parser.add_argument("--limit", type=int, default=10)
    query_parser = sub.add_parser("query")
    query_parser.add_argument("--actor-database", type=Path, required=True)
    query_parser.add_argument("--catalogue-database", type=Path, required=True)
    query_parser.add_argument("--view", required=True)
    query_parser.add_argument("--side", type=int, choices=(0, 1), required=True)
    query_parser.add_argument("--top", type=int, default=10)
    query_parser.add_argument("--budget", type=int, default=2048)
    query_parser.add_argument("--history-hex")
    query_parser.add_argument("--exclude-game")
    args = vars(parser.parse_args())
    command = args.pop("command")
    if command == "build":
        result = build(args["rows"], args["raw_games"], args["output"])
    elif command == "browse":
        result = browse(**args)
    else:
        history = args.pop("history_hex")
        result = query(**args, history=bytes.fromhex(history) if history else None)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
