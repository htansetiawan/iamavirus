"""Replay book: recorded wins against a deterministic opponent, keyed by our view.

    python -m learning.replay_book --team "Knight Vision" --version 29 --output replay.txt

A pure (deterministic) strategy is exploitable by copying: if the opponent always
answers the same history the same way, then playing the winner's moves of a game
it lost makes it play its losing moves again. This collects every game the given
team version lost by king capture, and writes, for the winner's side, one entry
per move: colour|view|move:priority|plies|1.000, the view being the 64-character
observation the winner had just before the move (rank 1 first, as the referee
sends it). Where lines share a view, the shortest line's move wins, so following
the book stays on one line for as long as the opponent repeats itself; the
moment the view differs, the bot is off the book and the engine decides.

`--check` measures the premise first: among exact move histories the version
faced more than once, the share it answered identically every time.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os


def load(raw: str, team: str, version: int):
    games = []
    for p in glob.glob(os.path.join(raw, "games", "*", "listing.json")):
        try:
            l = json.load(open(p))
        except Exception:
            continue
        if team not in (l["white"], l["black"]):
            continue
        v = l["whiteVersion"] if l["white"] == team else l["blackVersion"]
        if v != version:
            continue
        try:
            r = json.load(open(p.replace("listing.json", "replay.json")))
        except Exception:
            continue
        games.append((l, r))
    return games


def determinism(games, team):
    replies = collections.defaultdict(collections.Counter)
    for l, r in games:
        col = 0 if l["white"] == team else 1
        mv = tuple(f["move"] for f in r["frames"][1:])
        for k in range(col, len(mv), 2):
            replies[mv[:k]][mv[k]] += 1
    seen = [c for c in replies.values() if sum(c.values()) >= 2]
    return sum(len(c) == 1 for c in seen), len(seen)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--team", default="Knight Vision")
    ap.add_argument("--version", type=int, default=29)
    ap.add_argument("--output", default="replay.txt")
    ap.add_argument("--max-plies", type=int, default=400)
    ap.add_argument("--check", action="store_true", help="print the determinism measurement and stop")
    ap.add_argument("--first-move", action="append", default=[], metavar="COLOUR:UCI",
                    help="keep only lines whose first move for COLOUR (white/black) is UCI, e.g. black:d7d5. In the opening "
                         "our view cannot tell opponents apart (Black sees none of White's quiet first moves), so a book "
                         "move there is played against everyone; it must be the move our own book plays anyway.")
    args = ap.parse_args(argv)
    games = load(args.raw, args.team, args.version)
    same, total = determinism(games, args.team)
    print(f"{args.team} v{args.version}: {len(games)} games; repeated histories answered identically {same}/{total}")
    if args.check:
        return
    lines = []
    for l, r in games:
        team_white = l["white"] == args.team
        if l["result"] != ("0-1" if team_white else "1-0") or r.get("reason") != "King capturable":
            continue
        frames = r["frames"]
        if len(frames) - 1 > args.max_plies:
            continue
        colour = "black" if team_white else "white"
        first = frames[1 if colour == "white" else 2]["move"] if len(frames) > 2 else ""
        if any(rule.split(":")[0] == colour and rule.split(":")[1] != first for rule in args.first_move):
            continue
        lines.append((len(frames) - 1, l["id"], colour, frames))
    lines.sort(key=lambda x: (x[0], x[1]))
    entries = {}
    for plies, gid, colour, frames in lines:
        for k in range(1, len(frames)):
            mover = "white" if frames[k]["ply"] % 2 == 1 else "black"
            if mover != colour:
                continue
            key = (colour, frames[k - 1][colour])
            entries.setdefault(key, (frames[k]["move"], plies, gid))  # shortest line first
    with open(args.output, "w") as f:
        for (colour, view), (move, plies, gid) in sorted(entries.items()):
            f.write(f"{colour}|{view}|{move}:{1000 - min(plies, 999)}|{plies}|1.000\n")
    by_colour = collections.Counter(c for c, _ in entries)
    for colour in ("white", "black"):
        first = next((x for x in lines if x[2] == colour), None)
        if first:
            print(f"  as {colour}: {sum(1 for x in lines if x[2] == colour)} winning lines, {by_colour[colour]} entries; "
                  f"shortest {first[0]} plies ({first[1]})")
    print(f"wrote {len(entries)} entries to {args.output}")


if __name__ == "__main__":
    main()
