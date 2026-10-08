"""Running analysis of one arena version's games from the ingested replays.

    python -m learning.arena_watch 15 [--raw data/raw] [--output data/reports/v15-watch.md]

Reads data/raw/games/*/replay.json (see learning.ingest), keeps the games our
team played with the given version, and writes a phone-readable Markdown report:
record, colour split, record by opponent, game lengths, queen-lost-for-less
events (a capture of our queen that our reply does not answer with a queen,
excluding captures that ended the game as our win), short losses, clock floors,
and openings where White played 1.c4 against us (the book-trap family). Pure
measurement; it changes nothing.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import glob
import json
import os

TEAM_ID = "a2c35173659545c99752376a70418438"
VALUE = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 0}


def material(board: str, colour: int) -> int:
    return sum(VALUE[c.lower()] for c in board if c != "-" and (c.isupper() == (colour == 0)))


def queens(board: str, colour: int) -> int:
    return board.count("Q" if colour == 0 else "q")


def square_index(sq: str) -> int:
    return (ord(sq[0]) - 97) + (int(sq[1]) - 1) * 8


def queen_loss(frames, colour: int, our_win: bool):
    """(ply, capturer piece, capturer unseen when we decided) or None."""
    for k in range(2, len(frames)):
        ply = frames[k]["ply"]
        mover = 0 if ply % 2 == 1 else 1
        if mover == colour:
            continue
        if queens(frames[k]["board"], colour) < queens(frames[k - 1]["board"], colour):
            got = (material(frames[k]["board"], 1 - colour) - material(frames[k + 1]["board"], 1 - colour)
                   if k + 1 < len(frames) else 0)
            took_prev = material(frames[k - 2]["board"], 1 - colour) - material(frames[k - 1]["board"], 1 - colour)
            if got >= 9 or took_prev >= 9:
                return None
            if k == len(frames) - 1 and our_win:
                return None  # their capture exposed their king; we won on the spot
            move = frames[k]["move"]
            src = square_index(move[:2])
            view = frames[k - 2]["white" if colour == 0 else "black"]
            return ply, frames[k - 1]["board"][src].lower(), view[src] == "?"
    return None


def load_games(raw: str, version: int):
    games = []
    for path in glob.glob(os.path.join(raw, "games", "*", "replay.json")):
        try:
            r = json.load(open(path))
        except Exception:
            continue
        if r.get("whitePlayerId") == TEAM_ID:
            colour, ver, opp = 0, r.get("whiteVersion"), r.get("black")
        elif r.get("blackPlayerId") == TEAM_ID:
            colour, ver, opp = 1, r.get("blackVersion"), r.get("white")
        else:
            continue
        if ver != version:
            continue
        frames = r.get("frames") or []
        if len(frames) < 2:
            continue
        result = r["result"]
        score = {"1-0": 1.0, "0-1": 0.0}.get(result, 0.5)
        if colour == 1:
            score = 1 - score
        clocks = [f["clocks"][colour] for f in frames]
        moves = [f["move"] for f in frames[1:]]
        games.append({
            "id": r["id"], "created": r.get("createdAt", "")[:16].replace("T", " "),
            "colour": "W" if colour == 0 else "B", "opponent": opp, "plies": len(frames) - 1,
            "score": score, "reason": r.get("reason", ""), "min_clock": min(clocks),
            "queen_loss": queen_loss(frames, colour, score == 1.0),
            "opening": " ".join(m for m in moves[:6] if m),
            "material_end": (material(frames[-1]["board"], colour), material(frames[-1]["board"], 1 - colour)),
        })
    games.sort(key=lambda g: g["created"])
    return games


def report(version: int, games) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out = [f"# Arena v{version} watch", "", f"Updated {now}. Measurement only; newest games at the bottom of the table.", ""]
    if not games:
        out.append("No games ingested yet for this version.")
        return "\n".join(out) + "\n"
    w = sum(g["score"] == 1 for g in games)
    d = sum(g["score"] == 0.5 for g in games)
    l = sum(g["score"] == 0 for g in games)
    out.append(f"**Record: {w}W-{d}D-{l}L over {len(games)} games** ({100 * (w + d / 2) / len(games):.0f}%).")
    for c in "WB":
        sub = [g for g in games if g["colour"] == c]
        if sub:
            out.append(f"As {'White' if c == 'W' else 'Black'}: {sum(g['score'] for g in sub):.1f}/{len(sub)}.")
    losses = [g for g in games if g["score"] == 0]
    ql = [g for g in games if g["queen_loss"]]
    out += ["",
            f"Queen lost for less: {len(ql)} games ({len([g for g in ql if g['queen_loss'][2]])} to a capturer unseen when we moved, "
            f"{len([g for g in ql if g['queen_loss'][0] < 30])} before ply 30); losses with the queen lost: "
            f"{len([g for g in losses if g['queen_loss']])} of {len(losses)}.",
            f"Short losses (12 plies or fewer): {len([g for g in losses if g['plies'] <= 12])}. "
            f"Games with a clock at 15 s or less: {len([g for g in games if g['min_clock'] <= 15])}. "
            f"Mean length {sum(g['plies'] for g in games) / len(games):.0f} plies.",
            f"Games as Black where White opened 1.c4: {len([g for g in games if g['colour'] == 'B' and g['opening'].startswith('c2c4')])} "
            f"(the book-trap family; the v15 gate refuses the booked recapture).", ""]
    by = collections.defaultdict(lambda: [0, 0, 0])
    for g in games:
        by[g["opponent"]][0 if g["score"] == 1 else (1 if g["score"] == 0.5 else 2)] += 1
    out += ["| opponent | W-D-L |", "| --- | --- |"]
    for opp, (ww, dd, ll) in sorted(by.items(), key=lambda kv: -sum(kv[1])):
        out.append(f"| {opp} | {ww}-{dd}-{ll} |")
    out += ["", "| when (UTC) | id | us | opponent | plies | result | queen lost | min clock | material end |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for g in games:
        q = g["queen_loss"]
        qtxt = f"ply {q[0]} by {q[1]}{' unseen' if q[2] else ''}" if q else ""
        res = {1.0: "win", 0.5: "draw", 0.0: "loss"}[g["score"]]
        out.append(f"| {g['created']} | {g['id']} | {g['colour']} | {g['opponent']} | {g['plies']} | {res} | {qtxt} | {g['min_clock']:.0f} s | {g['material_end'][0]}-{g['material_end'][1]} |")
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("version", type=int)
    parser.add_argument("--raw", default="data/raw")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    games = load_games(args.raw, args.version)
    text = report(args.version, games)
    output = args.output or f"data/reports/v{args.version}-watch.md"
    os.makedirs(os.path.dirname(output), exist_ok=True)
    open(output, "w").write(text)
    print(text.split("\n")[4] if len(games) else f"v{args.version}: no games yet")


if __name__ == "__main__":
    main()
