#!/usr/bin/env python3
"""Extract actual en-passant actions from a prefiltered public replay file list."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

START_CASTLE = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)


def square(text: str) -> int:
    return (ord(text[1]) - 49) * 8 + ord(text[0]) - 97


def castle_before(frames: list[dict], target: int) -> int:
    rights = START_CASTLE
    for ply in range(1, target):
        move = frames[ply].get("move")
        if not move:
            continue
        board = frames[ply - 1]["board"]
        src, dst = square(move[:2]), square(move[2:4])
        piece, captured = board[src], board[dst]
        if piece == "K": rights &= ~((1 << 0) | (1 << 7))
        if piece == "k": rights &= ~((1 << 56) | (1 << 63))
        if src in (0, 7, 56, 63): rights &= ~(1 << src)
        if captured in "Rr" and dst in (0, 7, 56, 63): rights &= ~(1 << dst)
    return rights


def is_ep(frames: list[dict], ply: int) -> bool:
    if ply <= 0:
        return False
    frame, before = frames[ply], frames[ply - 1]["board"]
    move = frame.get("move")
    if not move or len(move) < 4:
        return False
    src, dst = square(move[:2]), square(move[2:4])
    mover = before[src]
    if mover not in "Pp" or before[dst] != "-" or src % 8 == dst % 8:
        return False
    if abs(src // 8 - dst // 8) != 1:
        return False
    captured = (src // 8) * 8 + (dst % 8)
    enemy = "p" if mover == "P" else "P"
    after = frame["board"]
    return before[captured] == enemy and after[captured] == "-" and after[dst] == mover


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", type=Path, required=True, help="newline-separated prefiltered replay JSON paths")
    ap.add_argument("--out", type=Path, required=True, help="output JSONL of true EP replay actions")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    files = args.files.read_text().splitlines()
    events = []
    games_read = 0
    for name in files[:args.limit or None]:
        path = Path(name)
        try:
            replay = json.loads(path.read_text())
            frames = replay["frames"]
            games_read += 1
            for ply in range(1, len(frames)):
                if not is_ep(frames, ply):
                    continue
                side = "white" if ply % 2 else "black"
                event = {
                    "game": replay.get("id", path.parent.name),
                    "white": replay.get("white", ""), "black": replay.get("black", ""),
                    "result": replay.get("result", ""), "reason": replay.get("reason", ""),
                    "ply": ply, "side": side, "move": frames[ply]["move"],
                    "view": frames[ply - 1][side], "castle_rooks": castle_before(frames, ply),
                }
                events.append(event)
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            continue
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as out:
        for event in events:
            out.write(json.dumps(event, separators=(",", ":")) + "\n")
    teams = {}
    for event in events:
        team = event[event["side"]]
        teams[team] = teams.get(team, 0) + 1
    print(json.dumps({"games_read": games_read, "actual_ep_actions": len(events),
                      "teams_that_moved": teams, "output": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()
