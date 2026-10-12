"""Cut the decisive bad move from each of our arena losses into a gym seat file.
    python -m learning.fatal_corpus --versions 32 33 --out data/gym/mistc-fatal-seats.txt [--opponents top]
For each loss, walk our moves in order and take the first one that, on the true
board, (a) leaves our king capturable, (b) puts our queen en prise for 5+, or
(c) gives 3+ points away, while we were not already 3+ points down. Also count
how many legal alternatives were clean of all three (so the suite can tell
"a safer move existed" from "already lost"). Seat line format is the gym's:
    id side result reason label moves...   (moves up to and including the decision)
label = kind:alternatives:opponent-with-underscores
"""
import argparse, glob, json, collections
from learning.gym_replay import score_move, position_at

TEAM = "a2c35173659545c99752376a70418438"
TOP = {"Greek Gift", "Knight Vision", "Decent Chess Bot", "Strongly Invisible", "duck", "Instructors"}

def material(board, side):
    return sum(VALUE_B[c.lower()] for c in board if c != "-" and (c.isupper() == (side == 0)))
VALUE_B = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 0}

ap = argparse.ArgumentParser()
ap.add_argument("--versions", nargs="+", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--opponents", default="all")
ap.add_argument("--raw", default="data/raw")
a = ap.parse_args()
rows, kinds, by_opp = [], collections.Counter(), collections.Counter()
for f in sorted(glob.glob(f"{a.raw}/games/*/replay.json")):
    try:
        g = json.load(open(f))
    except Exception:
        continue
    side = 0 if g.get("whitePlayerId") == TEAM else 1 if g.get("blackPlayerId") == TEAM else None
    if side is None:
        continue
    if str(g.get("whiteVersion" if side == 0 else "blackVersion")) not in a.versions:
        continue
    opp = g["black" if side == 0 else "white"]
    if a.opponents == "top" and opp not in TOP:
        continue
    lost = g["result"] == ("0-1" if side == 0 else "1-0")
    if not lost:
        continue
    fr = g["frames"]
    moves = [x["move"] for x in fr[1:]]
    for t in range(len(moves)):
        if t % 2 != side:
            continue
        board = fr[t]["board"]
        if material(board, side) - material(board, 1 - side) <= -3:
            break                                   # already lost; the decisive move came earlier or never
        try:
            s = score_move(board, moves[:t], moves[t], side)
        except Exception as e:
            break
        if not s.get("legal"):
            break
        kind = "king" if s["king_lost"] else "queen" if s["queen_en_prise"] else "give" if s["giveaway"] else None
        if kind is None:
            continue
        clean = 0
        pos = position_at(board, side, moves[:t])
        for m in pos.legal_moves():
            r = score_move(board, moves[:t], m, side)
            if r.get("legal") and not (r["king_lost"] or r["queen_en_prise"] or r["giveaway"]):
                clean += 1
        label = f"{kind}:{clean}:{opp.replace(' ', '_')}"
        rows.append(f"{g['id']} {'w' if side == 0 else 'b'} {g['result']} {g['reason'].replace(' ', '_')} {label} " + " ".join(moves[:t + 1]))
        kinds[kind] += 1
        by_opp[opp] += 1
        break
with open(a.out, "w") as out:
    out.write("\n".join(rows) + "\n")
print(f"wrote {len(rows)} seats to {a.out}: {dict(kinds)}")
for opp, n in by_opp.most_common():
    print(f"  {opp}: {n}")
