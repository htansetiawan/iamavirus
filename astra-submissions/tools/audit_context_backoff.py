#!/usr/bin/env python3
"""Measure a color-normalized current-view action table as a history backoff.

This is an offline retrieval experiment, not a policy release. It trains
frequency tables from the game-disjoint train list and evaluates only on the
test list. The key is the actor's current observation in own-piece-relative
orientation; actions are rank-flipped for Black. The exact full-history table
is also scored so that a backoff can be compared on identical held-out moves.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_history_table as exact


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canonical_view(view: str, side: int) -> str:
    if len(view) != 64:
        raise ValueError("observation must contain 64 squares")
    if side == 0:
        return view
    chars = ["-"] * 64
    for sq, piece in enumerate(view):
        dst = sq ^ 56  # rank reflection; files stay in place
        chars[dst] = piece.swapcase() if piece.isalpha() else piece
    return "".join(chars)


def canonical_move(uci: str, side: int) -> str:
    def square(text: str) -> str:
        file_idx = ord(text[0]) - 97
        rank_idx = ord(text[1]) - 49
        if side == 1:
            rank_idx = 7 - rank_idx
        return chr(97 + file_idx) + chr(49 + rank_idx)
    return square(uci[:2]) + square(uci[2:4]) + (uci[4:] if len(uci) > 4 else "")


def update_histories(h: dict[int, int], mover: int, move: str, after: dict,
                     white_key: str = "white", black_key: str = "black") -> None:
    mover_name = white_key if mover == 0 else black_key
    other = mover ^ 1
    other_name = white_key if other == 0 else black_key
    h[other] = exact.history_mix(h[other], exact.view_hash(after[other_name]))
    h[mover] = exact.history_mix(exact.history_mix(h[mover], exact.move_code(move)),
                                 exact.view_hash(after[mover_name]))


def replay_rows(replay: dict):
    frames = replay.get("frames") or []
    if len(frames) < 2:
        return
    h = {0: exact.history_mix(0, exact.view_hash(frames[0]["white"])),
         1: exact.history_mix(0, exact.view_hash(frames[0]["black"]))}
    for t in range(len(frames) - 1):
        mover = t & 1
        uci = frames[t + 1].get("move")
        if not uci:
            continue
        side_name = "white" if mover == 0 else "black"
        view = frames[t][side_name]
        yield mover, t, h[mover], canonical_view(view, mover), canonical_move(uci, mover), uci
        update_histories(h, mover, uci, frames[t + 1])


def load_replay(raw: Path, game_id: str) -> dict | None:
    try:
        return json.loads((raw / "games" / game_id / "replay.json").read_text())
    except FileNotFoundError:
        return None


def add_counts(table: dict[str, collections.Counter], key: str, move: str) -> None:
    table[key][move] += 1


def new_stats() -> dict[str, Any]:
    return {"decisions": 0, "eligible": 0, "action_hit": 0, "top1": 0, "top4": 0,
            "ply_bins": collections.defaultdict(lambda: [0, 0, 0, 0, 0])}


def score(st: dict[str, Any], moves: collections.Counter | None, actual: str,
          ply: int, minimum: int) -> None:
    n = sum(moves.values()) if moves else 0
    eligible = n >= minimum
    hit = bool(moves and moves.get(actual, 0))
    rank = None
    if moves:
        ranked = sorted(moves.items(), key=lambda kv: (-kv[1], kv[0]))
        rank = next((i for i, (m, _) in enumerate(ranked) if m == actual), None)
    st["decisions"] += 1
    st["eligible"] += int(eligible)
    st["action_hit"] += int(eligible and hit)
    st["top1"] += int(eligible and rank == 0)
    st["top4"] += int(eligible and rank is not None and rank < 4)
    bin_name = "0-9" if ply < 10 else "10-19" if ply < 20 else "20-39" if ply < 40 else "40+"
    b = st["ply_bins"][bin_name]
    b[0] += 1
    b[1] += int(eligible)
    b[2] += int(eligible and hit)
    b[3] += int(eligible and rank == 0)
    b[4] += int(eligible and rank is not None and rank < 4)


def finish(st: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in st.items() if k != "ply_bins"}
    n, e = st["decisions"], st["eligible"]
    out["eligible_rate"] = e / n if n else None
    out["action_coverage_given_eligible"] = st["action_hit"] / e if e else None
    out["top1_given_eligible"] = st["top1"] / e if e else None
    out["top4_given_eligible"] = st["top4"] / e if e else None
    out["ply_bins"] = {}
    for name, row in st["ply_bins"].items():
        total, eligible, hit, top1, top4 = row
        out["ply_bins"][name] = {
            "decisions": total, "eligible": eligible,
            "eligible_rate": eligible / total if total else None,
            "action_coverage_given_eligible": hit / eligible if eligible else None,
            "top1_given_eligible": top1 / eligible if eligible else None,
            "top4_given_eligible": top4 / eligible if eligible else None,
        }
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--table", type=Path, required=True, help="the exact v35 history table")
    ap.add_argument("--train-list", type=Path, required=True)
    ap.add_argument("--test-list", type=Path, required=True)
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--limit-train", type=int, default=0)
    ap.add_argument("--limit-test", type=int, default=0)
    ap.add_argument("--thresholds", type=int, nargs="+", default=[3, 10, 25])
    args = ap.parse_args(argv)
    train_ids = sorted(exact.ids_from_move_list(args.train_list))
    test_ids = sorted(exact.ids_from_move_list(args.test_list))
    overlap = set(train_ids) & set(test_ids)
    if overlap:
        raise SystemExit(f"train/test game ID overlap: {len(overlap)}")
    if args.limit_train: train_ids = train_ids[:args.limit_train]
    if args.limit_test: test_ids = test_ids[:args.limit_test]

    view_counts: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    train_missing = train_malformed = train_plies = 0
    for game_id in train_ids:
        replay = load_replay(args.raw, game_id)
        if replay is None:
            train_missing += 1
            continue
        try:
            for _side, _ply, _hist, view, move, _uci in replay_rows(replay):
                add_counts(view_counts, view, move)
                train_plies += 1
        except (KeyError, ValueError, IndexError):
            train_malformed += 1

    exact_table = exact.read_table(args.table)
    thresholds = sorted(set(args.thresholds))
    if not thresholds or thresholds[0] < 1:
        raise SystemExit("thresholds must be positive integers")
    exact_stats = new_stats()
    view_stats = {n: new_stats() for n in thresholds}
    hybrid_stats = {n: new_stats() for n in thresholds}
    per_team = collections.defaultdict(lambda: {
        "exact": new_stats(),
        "view": {n: new_stats() for n in thresholds},
        "hybrid": {n: new_stats() for n in thresholds},
    })
    test_missing = test_malformed = test_plies = 0
    for game_id in test_ids:
        replay = load_replay(args.raw, game_id)
        if replay is None:
            test_missing += 1
            continue
        try:
            for side, ply, hist, view, canonical_action, uci in replay_rows(replay):
                team = replay["white" if side == 0 else "black"]
                htotal, hactions = exact_table.get(hist, (0, {}))
                exact_moves = collections.Counter(hactions) if htotal else None
                # Compare using packed moves for exact keys; use a separate rank
                # statistic since canonical UCI actions are a different key.
                actual_code = exact.move_code(uci)
                score(exact_stats, exact_moves, actual_code, ply, 3)
                score(per_team[team]["exact"], exact_moves, actual_code, ply, 3)
                candidates = view_counts.get(view)
                for threshold in thresholds:
                    score(view_stats[threshold], candidates, canonical_action, ply, threshold)
                    score(per_team[team]["view"][threshold], candidates, canonical_action, ply, threshold)
                    # Exact-key counts take precedence. The coarse table is used
                    # only when the exact key is below its existing default gate.
                    selected = exact_moves if htotal >= 3 else candidates
                    selected_threshold = 3 if htotal >= 3 else threshold
                    score(hybrid_stats[threshold], selected,
                          actual_code if htotal >= 3 else canonical_action,
                          ply, selected_threshold)
                    score(per_team[team]["hybrid"][threshold], selected,
                          actual_code if htotal >= 3 else canonical_action,
                          ply, selected_threshold)
                test_plies += 1
        except (KeyError, ValueError, IndexError):
            test_malformed += 1

    result = {
        "classification": "offline actor-view retrieval backoff probe; not a playing-strength estimate",
        "canonicalization": "Black rank-reflected; own pieces uppercased, opponent pieces lowercased; files unchanged",
        "table": {"sha256": sha256(args.table), "min_exact_count": 3,
                  "view_keys": len(view_counts), "view_action_pairs": sum(len(x) for x in view_counts.values())},
        "split": {"train_games_requested": len(train_ids), "test_games_requested": len(test_ids),
                  "train_test_overlap": 0, "train_missing": train_missing, "train_malformed": train_malformed,
                  "test_missing": test_missing, "test_malformed": test_malformed,
                  "train_decisions": train_plies, "test_decisions": test_plies,
                  "train_list_sha256": sha256(args.train_list), "test_list_sha256": sha256(args.test_list)},
        "exact_history": finish(exact_stats),
        "current_view": {str(k): finish(v) for k, v in view_stats.items()},
        "exact_then_view_backoff": {str(k): finish(v) for k, v in hybrid_stats.items()},
        "teams": {name: {"exact_history": finish(v["exact"]),
                         "current_view": {str(k): finish(x) for k, x in v["view"].items()},
                         "exact_then_view_backoff": {str(k): finish(x) for k, x in v["hybrid"].items()}}
                  for name, v in sorted(per_team.items())},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    def compact(row):
        return {k: row[k] for k in ("decisions", "eligible", "eligible_rate",
                                     "action_coverage_given_eligible", "top1_given_eligible",
                                     "top4_given_eligible")}
    print(json.dumps({"split": result["split"], "table": result["table"],
                      "exact_history": compact(result["exact_history"]),
                      "current_view": {k: compact(v) for k, v in result["current_view"].items()},
                      "exact_then_view_backoff": {k: compact(v) for k, v in result["exact_then_view_backoff"].items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
