#!/usr/bin/env python3
"""Measure whether the frozen v35 history table covers held-out replay choices.

The table is a cache of action counts keyed by an opponent's own observation
history. This audit replays public observations and moves to rebuild the exact
uint64 key used by mist-c, then measures lookup coverage and whether the held-out
move is among the cached actions. It does not claim playing strength.

Example (store output on a roomy filesystem):
  python3 astra-submissions/tools/audit_history_table.py \
    --table /media/henrytan/seagate1/iamavirus-data/derived/moves/history-train.bin \
    --test-list /media/henrytan/seagate1/iamavirus-data/derived/moves/arena-latest-test.txt \
    --train-list /media/henrytan/seagate1/iamavirus-data/derived/moves/arena-latest-train.txt \
    --raw data/raw --output /tmp/astra-history-table-audit.json
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import struct
from pathlib import Path
from typing import Any

MASK64 = (1 << 64) - 1
FNV_OFFSET = 1469598103934665603
FNV_PRIME = 1099511628211
GOLDEN = 0x9E3779B97F4A7C15
MIX_A = 0xBF58476D1CE4E5B9
MIX_B = 0x94D049BB133111EB
HEADER = struct.Struct("<8sII")
RECORD = struct.Struct("<QII")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def view_hash(view: str) -> int:
    if len(view) != 64:
        raise ValueError(f"observation has length {len(view)}, expected 64")
    h = FNV_OFFSET
    for byte in view.encode("ascii"):
        h = ((h ^ byte) * FNV_PRIME) & MASK64
    return h


def history_mix(h: int, value: int) -> int:
    z = (h + GOLDEN * (value | 1)) & MASK64
    z = ((z ^ (z >> 30)) * MIX_A) & MASK64
    z = ((z ^ (z >> 27)) * MIX_B) & MASK64
    return z ^ (z >> 31)


def move_code(uci: str) -> int:
    fr = (ord(uci[1]) - 49) * 8 + ord(uci[0]) - 97
    to = (ord(uci[3]) - 49) * 8 + ord(uci[2]) - 97
    # mist-c's piece enum is PAWN=0, KNIGHT=1, BISHOP=2, ROOK=3,
    # QUEEN=4, KING=5, NO_PIECE=6. NO_PIECE is stored for non-promotions.
    promo = {"n": 1, "b": 2, "r": 3, "q": 4}.get(uci[4], 6) if len(uci) == 5 else 6
    return fr | (to << 6) | (promo << 12)


def read_table(path: Path) -> dict[int, tuple[int, dict[int, int]]]:
    data = path.read_bytes()
    if len(data) < HEADER.size:
        raise ValueError("history table is shorter than its header")
    magic, version, n = HEADER.unpack_from(data)
    if magic != b"MISTHIST" or version != 1:
        raise ValueError(f"unexpected history table header {magic!r}, version {version}")
    expected = HEADER.size + n * RECORD.size
    if len(data) != expected:
        raise ValueError(f"table length {len(data)} != expected {expected}")
    table: dict[int, tuple[int, dict[int, int]]] = {}
    previous = -1
    for i in range(n):
        h, move, count = RECORD.unpack_from(data, HEADER.size + i * RECORD.size)
        if h < previous:
            raise ValueError("history table records are not sorted by hash")
        previous = h
        if h not in table:
            table[h] = (0, {})
        total, moves = table[h]
        moves[move] = moves.get(move, 0) + count
        table[h] = (total + count, moves)
    return table


def ids_from_move_list(path: Path) -> set[str]:
    ids = set()
    with path.open() as f:
        for line in f:
            fields = line.split(maxsplit=3)
            if len(fields) >= 2 and fields[0] == "game":
                ids.add(fields[1])
    return ids


def empty_stats() -> dict[str, Any]:
    return {"decisions": 0, "table_present": 0, "lookup_eligible_n_ge_3": 0,
            "actual_action_in_table": 0, "top1_correct": 0, "top4_correct": 0,
            "count_sum": 0, "ply_bins": collections.defaultdict(lambda: [0, 0, 0])}


def add_decision(st: dict[str, Any], table: dict[int, tuple[int, dict[int, int]]], h: int,
                 uci: str, ply: int, min_count: int) -> None:
    st["decisions"] += 1
    total, actions = table.get(h, (0, {}))
    if total:
        st["table_present"] += 1
        st["count_sum"] += total
    if total >= min_count:
        st["lookup_eligible_n_ge_3"] += 1
        code = move_code(uci)
        if actions.get(code, 0):
            st["actual_action_in_table"] += 1
        if actions:
            ranked = sorted(actions.items(), key=lambda kv: (-kv[1], kv[0]))
            rank = next((i for i, (m, _) in enumerate(ranked) if m == code), None)
            if rank is not None and rank == 0:
                st["top1_correct"] += 1
            if rank is not None and rank < 4:
                st["top4_correct"] += 1
    bin_name = "0-9" if ply < 10 else "10-19" if ply < 20 else "20-39" if ply < 40 else "40+"
    row = st["ply_bins"][bin_name]
    row[0] += 1
    row[1] += int(total >= min_count)
    row[2] += int(total >= min_count and actions.get(move_code(uci), 0) > 0)


def load_replay(raw: Path, game_id: str) -> dict | None:
    path = raw / "games" / game_id / "replay.json"
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return None


def analyze_game(replay: dict, table: dict[int, tuple[int, dict[int, int]]],
                 stats: dict[str, dict[str, Any]], min_count: int) -> int:
    frames = replay.get("frames") or []
    if len(frames) < 2:
        return 0
    h = {0: history_mix(0, view_hash(frames[0]["white"])),
         1: history_mix(0, view_hash(frames[0]["black"]))}
    processed = 0
    for t in range(len(frames) - 1):
        nxt = frames[t + 1]
        mover = t & 1
        uci = nxt.get("move")
        if not uci:
            continue
        side_name = "white" if mover == 0 else "black"
        add_decision(stats[replay[side_name]], table, h[mover], uci, t, min_count)
        # Other player receives only their new observation after our move.
        other = mover ^ 1
        h[other] = history_mix(h[other], view_hash(nxt["white" if other == 0 else "black"]))
        # The mover conditions future moves on its own action and post-move view.
        h[mover] = history_mix(history_mix(h[mover], move_code(uci)),
                               view_hash(nxt[side_name]))
        processed += 1
    return processed


def finish_stats(st: dict[str, Any]) -> dict[str, Any]:
    n = st["decisions"]
    eligible = st["lookup_eligible_n_ge_3"]
    out = {k: v for k, v in st.items() if k != "ply_bins"}
    out["eligible_rate"] = eligible / n if n else None
    out["action_coverage_given_eligible"] = st["actual_action_in_table"] / eligible if eligible else None
    out["top1_accuracy_given_eligible"] = st["top1_correct"] / eligible if eligible else None
    out["top4_accuracy_given_eligible"] = st["top4_correct"] / eligible if eligible else None
    out["mean_cached_count_when_present"] = st["count_sum"] / st["table_present"] if st["table_present"] else None
    out["ply_bins"] = {}
    for k, (total, eligible_k, action_hit) in st["ply_bins"].items():
        out["ply_bins"][k] = {"decisions": total, "eligible": eligible_k,
                               "eligible_rate": eligible_k / total if total else None,
                               "action_hits": action_hit,
                               "action_coverage_given_eligible": action_hit / eligible_k if eligible_k else None}
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--table", type=Path, required=True)
    ap.add_argument("--test-list", type=Path, required=True)
    ap.add_argument("--train-list", type=Path, required=True)
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--limit-games", type=int, default=0, help="0 processes every test game")
    ap.add_argument("--min-count", type=int, default=3)
    args = ap.parse_args(argv)
    train_ids = ids_from_move_list(args.train_list)
    test_ids = sorted(ids_from_move_list(args.test_list))
    overlap = train_ids.intersection(test_ids)
    if overlap:
        raise SystemExit(f"train/test game ID overlap: {len(overlap)}")
    if args.limit_games:
        test_ids = test_ids[:args.limit_games]
    table = read_table(args.table)
    overall = empty_stats()
    by_team: dict[str, dict[str, Any]] = collections.defaultdict(empty_stats)
    missing = malformed = processed_games = processed_plies = 0
    for game_id in test_ids:
        replay = load_replay(args.raw, game_id)
        if replay is None:
            missing += 1
            continue
        # Aggregate under anonymized side labels only; team names are not needed
        # to assess the held-out table's generalization.
        proxy = dict(replay)
        replay_stats = {"white": empty_stats(), "black": empty_stats()}
        proxy["white"] = "white"
        proxy["black"] = "black"
        try:
            processed_plies += analyze_game(proxy, table, replay_stats, args.min_count)
        except (KeyError, ValueError, IndexError):
            malformed += 1
            continue
        processed_games += 1
        for color in ("white", "black"):
            for key, value in replay_stats[color].items():
                if key == "ply_bins":
                    for bin_name, row in value.items():
                        target = overall["ply_bins"][bin_name]
                        for i in range(3): target[i] += row[i]
                else:
                    overall[key] += value
        # Keep breakdowns by player for inspecting whether the table merely
        # memorizes a few deterministic teams; exact names remain data metadata.
        for color, team in (("white", replay.get("white", "?")), ("black", replay.get("black", "?"))):
            st = by_team[team]
            src = replay_stats[color]
            for key, value in src.items():
                if key == "ply_bins":
                    for bin_name, row in value.items():
                        target = st["ply_bins"][bin_name]
                        for i in range(3): target[i] += row[i]
                else:
                    st[key] += value
    result = {
        "classification": "held-out empirical history-table coverage audit; not a strength estimate",
        "table": {"path": str(args.table), "sha256": sha256(args.table), "history_keys": len(table),
                  "record_count": (args.table.stat().st_size - HEADER.size) // RECORD.size,
                  "min_count": args.min_count},
        "split": {"train_games": len(train_ids), "test_games": len(ids_from_move_list(args.test_list)),
                  "overlap_games": len(overlap), "processed_test_games": processed_games,
                  "missing_replays": missing, "malformed_replays": malformed,
                  "processed_plies": processed_plies, "limit_games": args.limit_games or None},
        "inputs": {"train_list_sha256": sha256(args.train_list), "test_list_sha256": sha256(args.test_list)},
        "overall": finish_stats(overall),
        "teams": {team: finish_stats(st) for team, st in sorted(by_team.items())},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"split": result["split"], "table": result["table"], "overall": result["overall"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
