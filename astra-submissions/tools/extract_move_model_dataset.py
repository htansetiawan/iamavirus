#!/usr/bin/env python3
"""Extract rules-exact conditional-logit examples from cached FOW replays.

The C feature probe is deliberately a separate oracle so the trained model's
features match the archived C engine. Games, not plies, define the split.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import subprocess
import sys
from pathlib import Path


def read_json(path: Path):
    op = gzip.open if path.suffix == ".gz" else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def sq(s: str) -> int:
    return ord(s[0]) - 97 + 8 * (ord(s[1]) - 49)


def start_castling(board: str) -> int:
    # A right is available only if both the home king and original rook exist.
    rights = 0
    for king, rook in ((4, 0), (4, 7), (60, 56), (60, 63)):
        color = 0 if king < 8 else 1
        kchar, rchar = ("K", "R") if color == 0 else ("k", "r")
        if board[king] == kchar and board[rook] == rchar:
            rights |= 1 << rook
    return rights


def replay_rows(game):
    frames = game.get("frames")
    if not isinstance(frames, list) or len(frames) < 2:
        return
    if frames[0].get("ply") != 0 or len(frames[0].get("board", "")) != 64:
        return
    rights = start_castling(frames[0]["board"])
    ep = -1
    for i in range(len(frames) - 1):
        before, after = frames[i], frames[i + 1]
        board = before.get("board", "")
        move = after.get("move")
        if len(board) != 64 or not isinstance(move, str) or len(move) not in (4, 5):
            return
        side = int(before["ply"]) & 1
        previous = before.get("move") or "-"
        yield (game.get("id", ""), board, side, rights, ep, previous, move,
               game.get("createdAt") or "", game.get("white", ""),
               game.get("black", ""), int(before["ply"]))

        src, dst = sq(move), sq(move[2:4])
        piece = board[src]
        # Moving a king or original rook permanently removes its rights.
        if piece == "K": rights &= ~((1 << 0) | (1 << 7))
        elif piece == "k": rights &= ~((1 << 56) | (1 << 63))
        if piece.upper() == "R" and src in (0, 7, 56, 63): rights &= ~(1 << src)
        # Capturing a rook on its original square removes that right.
        if board[dst].upper() == "R" and dst in (0, 7, 56, 63): rights &= ~(1 << dst)
        ep = -1
        if piece.upper() == "P" and abs(dst - src) == 16:
            ep = (dst + src) // 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay-root", action="append", required=True,
                    help="directory recursively containing replay JSON/JSON.GZ")
    ap.add_argument("--probe", required=True, help="compiled move_model_features_probe")
    ap.add_argument("--out", required=True, help="output JSONL, one record per candidate move")
    ap.add_argument("--min-ply", type=int, default=0)
    ap.add_argument("--teams", nargs="*", default=[], help="optional opponent/team names to retain")
    ap.add_argument("--exclude-teams", nargs="*", default=[], help="exclude decisions made by these teams")
    args = ap.parse_args()
    paths = set()
    for root in args.replay_root:
        paths.update(Path(root).rglob("*.json"))
        paths.update(Path(root).rglob("*.json.gz"))
    games = {}
    bad = 0
    for path in sorted(paths):
        try:
            obj = read_json(path)
            if isinstance(obj, dict) and isinstance(obj.get("frames"), list) and obj.get("id"):
                games.setdefault(obj["id"], (path, obj))
        except (OSError, ValueError, json.JSONDecodeError):
            bad += 1
    rows = []
    kept_games = 0
    for gid, (_, game) in games.items():
        if args.teams and not ({game.get("white"), game.get("black")} & set(args.teams)):
            continue
        game_rows = list(replay_rows(game) or ())
        game_rows = [r for r in game_rows if r[-1] >= args.min_ply]
        if args.exclude_teams:
            excluded = set(args.exclude_teams)
            game_rows = [r for r in game_rows if (r[8] if r[2] == 0 else r[9]) not in excluded]
        if game_rows:
            kept_games += 1
            rows.extend(game_rows)
    # One probe invocation preserves ordering and amortizes process overhead.
    row_lookup = {f"{r[0]}:{r[10]}": r for r in rows}
    payload = "".join(f"{r[0]}:{r[10]}\t{r[1]}\t{r[2]}\t{r[3]:016x}\t{r[4]}\t{r[5]}\t{r[6]}\n" for r in rows)
    proc = subprocess.Popen([args.probe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    stdout, stderr = proc.communicate(payload)
    if proc.returncode:
        sys.stderr.write(stderr)
        raise SystemExit(f"feature probe failed ({proc.returncode})")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    examples = 0
    with out.open("w", encoding="utf-8") as f:
        for line in stdout.splitlines():
            fields = line.split("\t")
            if fields[0].startswith("@"):
                continue
            # Candidate line: game, true move, candidate move, feature values.
            key, truth, candidate, *features = fields
            source = row_lookup.get(key)
            if source is None:
                raise RuntimeError(f"probe returned unknown position {key}")
            record = {"game": source[0], "at": source[7], "white": source[8], "black": source[9],
                      "ply": source[10], "label": int(candidate == truth),
                      "candidate": candidate, "features": [float(x) for x in features]}
            f.write(json.dumps(record, separators=(",", ":")) + "\n")
            examples += 1
    print(json.dumps({"unique_cached_games": len(games), "games_used": kept_games,
                      "positions": len(rows), "candidate_examples": examples,
                      "unreadable_files": bad, "output": str(out)}))


if __name__ == "__main__":
    main()
