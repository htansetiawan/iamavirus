#!/usr/bin/env python3
"""The frozen split for the v20 piece guard (chatroom 159), built before any lambda is tried.

    .venv/bin/python fable-submissions/analysis/v20-material-guard-20261027/build_split.py \
        data/raw ~/fable-persist/suite/v20 [--version 35]

Three suites in tools/suite_run.py's format (feed, forced, board, played, kind):
  calib.json    our v35 losses to the fixed top six created up to 2026-10-19 23:59:59 UTC:
                the first decision of the game after which, within two plies, our material
                fell by 3+ net and a rook, bishop or knight of ours disappeared while our queen
                did not (kind "piece"), when our material lead before it was -3 or better (not
                already lost); decisions that left our king capturable are excluded
  oos.json      the same for games created 2026-10-20 00:00 to 2026-10-26 10:12 UTC
  control.json  our v35 wins and draws against the same opponents in both periods: every
                4th decision from our 6th on, where no material was lost within two plies
                and the king was safe (kind "control"), at most 3 per game, 400 in all
split.json lists the game ids and decision counts of the three sets.
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.expanduser("~/git/fowsearch-c/tools"))
from suite_build import board, material, king_safe_after, VALUE  # noqa: E402
import chess  # noqa: E402

TOP6 = ["Greek Gift", "Knight Vision", "Strongly Invisible", "Decent Chess Bot", "duck", "Instructors"]
CALIB_END = "2026-10-19T23:59:59"
OOS_END = "2026-10-26T10:12:00"


def counts(b64, white):
    c = {"q": 0, "r": 0, "b": 0, "n": 0}
    for ch in b64:
        if ch != "-" and ch.isupper() == white and ch.lower() in c:
            c[ch.lower()] += 1
    return c


def decisions(raw, gid, side, want):
    """want: 'piece' or 'control'. Yields suite entries."""
    rp = json.load(open(os.path.join(raw, "games", gid, "replay.json")))
    f = rp["frames"]
    w = side == "white"; ci = 0 if w else 1; col = chess.WHITE if w else chess.BLACK
    feed = ["fow", f"{'w' if w else 'b'} 180 2"]; forced = []; k = 0; taken = 0; since = 99
    for p in range(len(f) - 1):
        feed.append(f[p][side])
        if (p % 2 == 0) != w:
            continue
        feed.append("%.9f" % f[p]["clocks"][ci]); k += 1
        played = f[p + 1]["move"]
        b = board(f[p]["board"], w)
        if b.king(col) is None or p + 2 >= len(f):
            break
        mv = chess.Move.from_uci(played)
        fatal = mv in b.pseudo_legal_moves and not king_safe_after(b, mv, col)
        before = material(f[p]["board"], w) - material(f[p]["board"], not w)
        after = material(f[p + 2]["board"], w) - material(f[p + 2]["board"], not w)
        swing = before - after
        c0, c2 = counts(f[p]["board"], w), counts(f[p + 2]["board"], w)
        piece_gone = any(c2[x] < c0[x] for x in "rbn") and c2["q"] >= c0["q"]
        entry = {"game": gid, "side": side, "k": k, "ply": p, "feed": "\n".join(feed) + "\n",
                 "forced": ",".join(forced), "board": f[p]["board"], "played": played, "swing": swing,
                 "safe": any(king_safe_after(b, m, col) for m in b.pseudo_legal_moves)}
        if want == "piece" and not fatal and swing >= 3 and piece_gone and before >= -3:
            entry.update(kind="piece", kinds=["piece"], before=before); yield entry
            return   # the first clean piece loss of the game only
        if want == "control":
            since += 1
            if k >= 6 and not fatal and swing <= 0 and not piece_gone and since >= 4 and taken < 3:
                since = 0; taken += 1
                entry.update(kind="control", kinds=["control"]); yield entry
        forced.append(played)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw"); ap.add_argument("out"); ap.add_argument("--version", type=int, default=35)
    ap.add_argument("--controls", type=int, default=400)
    a = ap.parse_args()
    games = []
    for line in open(os.path.join(a.raw, "accepted.jsonl")):
        r = json.loads(line)
        for side, other in (("white", "black"), ("black", "white")):
            if r.get(side) == "IAmAVirus" and r.get(side + "Version") == a.version and r.get(other) in TOP6:
                s = {"1-0": 1, "0-1": 0}.get(r["result"], 0.5); s = s if side == "white" else 1 - s
                created = r.get("createdAt") or ""
                if created > OOS_END:
                    continue
                games.append((created, r["id"], side, r[other], s))
    games.sort()
    suites = {"calib": [], "oos": [], "control": []}
    for created, gid, side, opp, s in games:
        try:
            if s == 0:
                dest = "calib" if created <= CALIB_END else "oos"
                for e in decisions(a.raw, gid, side, "piece"):
                    e.update(opponent=opp, created=created, version=a.version); suites[dest].append(e)
            elif len(suites["control"]) < a.controls:
                for e in decisions(a.raw, gid, side, "control"):
                    e.update(opponent=opp, created=created, version=a.version); suites["control"].append(e)
        except FileNotFoundError:
            continue
    os.makedirs(a.out, exist_ok=True)
    split = {}
    for name, entries in suites.items():
        json.dump(entries, open(os.path.join(a.out, name + ".json"), "w"))
        gids = sorted({e["game"] for e in entries})
        split[name] = {"decisions": len(entries), "games": len(gids), "ids": [f"{e['game']}:{e['k']}" for e in entries],
                       "by_opponent": {o: sum(1 for e in entries if e["opponent"] == o) for o in TOP6}}
        print(f"{name}: {len(entries)} decisions from {len(gids)} games; by opponent {split[name]['by_opponent']}")
    split["definition"] = __doc__
    json.dump(split, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "split.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
