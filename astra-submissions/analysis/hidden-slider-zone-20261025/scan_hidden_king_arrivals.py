#!/usr/bin/env python3
"""Scan cached public replays for newly created, fully hidden king attacks.

This is an event census, not a strength estimate.  It uses only recorded true
boards to label outcomes; the victim's observation is used to classify whether
the attacking piece(s) were visible after the move.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
from pathlib import Path


def sq(file: int, rank: int) -> int:
    return rank * 8 + file


def attackers(board: str, king_side: str) -> list[int]:
    """Return indices of enemy pieces attacking the specified king."""
    king = "K" if king_side == "white" else "k"
    attacker_white = king_side == "black"
    ksq = board.find(king)
    if ksq < 0:
        return []
    kf, kr = ksq % 8, ksq // 8
    found = []
    for origin, piece in enumerate(board):
        if piece == "-" or piece == "?":
            continue
        is_white = piece.isupper()
        if is_white != attacker_white:
            continue
        kind = piece.upper()
        f, r = origin % 8, origin // 8
        df, dr = kf - f, kr - r
        if kind == "P":
            hit = abs(df) == 1 and dr == (1 if is_white else -1)
        elif kind == "N":
            hit = (abs(df), abs(dr)) in ((1, 2), (2, 1))
        elif kind == "K":
            hit = max(abs(df), abs(dr)) == 1
        else:
            diagonal = abs(df) == abs(dr) and df != 0
            straight = (df == 0) != (dr == 0)
            hit = (kind == "B" and diagonal) or (kind == "R" and straight) or (kind == "Q" and (diagonal or straight))
            if hit:
                step_f = (df > 0) - (df < 0)
                step_r = (dr > 0) - (dr < 0)
                x, y = f + step_f, r + step_r
                while (x, y) != (kf, kr):
                    if board[sq(x, y)] != "-":
                        hit = False
                        break
                    x += step_f
                    y += step_r
        if hit:
            found.append(origin)
    return found


def analyze(path: Path) -> list[dict]:
    try:
        game = json.loads(path.read_text())
        frames = game["frames"]
    except (OSError, ValueError, KeyError, TypeError):
        return []
    events = []
    for after_i in range(1, len(frames)):
        before, after = frames[after_i - 1], frames[after_i]
        mover = "white" if (after_i - 1) % 2 == 0 else "black"
        victim = "black" if mover == "white" else "white"
        before_attacks = attackers(before["board"], victim)
        after_attacks = attackers(after["board"], victim)
        if before_attacks or not after_attacks:
            continue
        victim_view = after[victim]
        hidden = [i for i in after_attacks if victim_view[i] == "?"]
        visible = [i for i in after_attacks if victim_view[i] != "?"]
        # Only count moves by the opposing team that newly expose its king to
        # attack. Their own king must still exist; terminal state is handled by
        # the response classification below.
        if not hidden:
            visibility = "visible"
        elif not visible:
            visibility = "fully_hidden"
        else:
            visibility = "mixed"
        response_i = after_i + 1
        if response_i >= len(frames):
            response = "no_recorded_reply"
            response_move = None
            remaining = None
        else:
            response_frame = frames[response_i]
            response_move = response_frame.get("move")
            remaining = attackers(response_frame["board"], victim)
            response = "attack_survived_reply" if remaining else "defender_escaped"
        events.append({
            "game": game.get("id", path.parent.name),
            "white": game.get("white", ""), "black": game.get("black", ""),
            "result": game.get("result", ""), "reason": game.get("reason", ""),
            "attacker": game.get(mover), "victim": game.get(victim),
            "attacker_side": mover, "victim_side": victim,
            "ply": after.get("ply", after_i), "move": after.get("move"),
            "visibility": visibility,
            "attacking_squares": after_attacks,
            "hidden_attacking_squares": hidden,
            "visible_attacking_squares": visible,
            "response": response, "response_move": response_move,
            "attackers_after_response": remaining,
        })
    return events


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", type=Path, default=Path(__file__).with_name("hidden-king-arrivals.jsonl.gz"))
    ap.add_argument("--summary", type=Path, default=Path(__file__).with_name("hidden-king-arrivals-summary.json"))
    ap.add_argument("--source", type=Path, default=Path("astra-submissions/analysis/ep-target-inference-20261025/top-opponent-ep-action-coverage.jsonl"))
    ap.add_argument("--path-list", type=Path, help="newline-delimited replay.json paths; overrides --source")
    ap.add_argument("--games-root", type=Path, default=Path("data/raw/games"))
    args = ap.parse_args()
    paths = set()
    if args.path_list:
        with args.path_list.open() as f:
            paths = {Path(line.strip()) for line in f if line.strip()}
    else:
        ids = set()
        with args.source.open() as f:
            for line in f:
                try:
                    ids.add(json.loads(line)["game"])
                except (ValueError, KeyError):
                    pass
        paths = {args.games_root / game_id / "replay.json" for game_id in ids}
    by_visibility = collections.defaultdict(collections.Counter)
    by_attacker = collections.defaultdict(collections.Counter)
    total_games = 0
    total_events = 0
    args.events.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.events, "wt") as out:
        for p in sorted(paths):
            rows = analyze(p)
            if not p.exists():
                continue
            total_games += 1
            for e in rows:
                total_events += 1
                by_visibility[e["visibility"]][e["response"]] += 1
                by_attacker[e["attacker"]][e["visibility"] + ":" + e["response"]] += 1
                out.write(json.dumps(e, separators=(",", ":")) + "\n")
    summary = {
        "classification": "public-replay event census; not a strength estimate",
        "games_scanned": total_games, "new_direct_king_attacks": total_events,
        "by_visibility": {k: dict(v) for k, v in by_visibility.items()},
        "by_attacker": {k: dict(v) for k, v in sorted(by_attacker.items())},
        "event_file": str(args.events),
        "source_path_list": str(args.path_list) if args.path_list else str(args.source),
        "selection_note": "With --path-list, this scans cached games whose replay text matched the requested top-team names, not only games containing en passant. Without --path-list, the default source is the EP-event-conditioned 7,827-game subset.",
        "definition": "Before position has no attack on victim king; after attacker move it is attacked. Visibility is victim observation at that frame. Response checks whether the same victim king remains attacked after its recorded reply.",
        "limitations": [
            "Labels use true replay boards and are for offline analysis only.",
            "The census is conditioned on the existing top-opponent replay selection.",
            "Attack persistence after one reply is not causal value or Elo.",
            "No-recorded-reply events are not treated as surviving or successful.",
        ],
    }
    args.summary.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
