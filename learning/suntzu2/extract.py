"""SunTzu v2, level 0 data: (our view before, our view after) around every opponent move, from both sides of
each mirrored game. Squares are perspective-relative and Black's board is flipped so "we" are always at the
bottom: 0 unseen, 1 empty, 2-7 our P N B R Q K, 8-13 their p n b r q k.

    python -m learning.suntzu2.extract --games 20000 --workers 4 --output data/suntzu2/pairs-v1.npz
"""
from __future__ import annotations
import argparse, glob, json, os, random
from multiprocessing import Pool
import numpy as np

CODE = {"?": 0, "-": 1}
for i, c in enumerate("PNBRQK"): CODE[c] = 2 + i
for i, c in enumerate("pnbrqk"): CODE[c] = 8 + i
FLIP = np.array([(7 - s // 8) * 8 + s % 8 for s in range(64)])

def encode(view: str, white: bool) -> np.ndarray:
    a = np.array([CODE[c] for c in view], np.uint8)
    if not white:  # swap colours (their pieces are uppercase for Black) and flip ranks
        own = (a >= 2) & (a <= 7); enemy = (a >= 8)
        a = a.copy(); a[own] += 6; a[enemy] -= 6; a = a[FLIP]
    return a

def one(args):
    path, team_index = args
    try:
        l = json.load(open(path)); r = json.load(open(path.replace("listing.json", "replay.json")))
    except Exception:
        return None
    F = r["frames"]; n = len(F) - 1
    out = []
    res = l.get("result")
    for side, opp_key in (("white", "black"), ("black", "white")):
        white = side == "white"
        opp = l[opp_key]; me = l[side]
        score = 0.5 if res == "1/2-1/2" else (1.0 if (res == "1-0") == white else 0.0)
        # how the game ended: our king or theirs captured, and at which ply
        ended_by_capture = r.get("reason") == "King capturable"
        for k in range(1, n + 1):
            mover_white = F[k]["ply"] % 2 == 1
            if mover_white == white:  # our own move: skip (level 0 tokenizes the opponent's moves)
                continue
            before = encode(F[k - 1][side], white); after = encode(F[k][side], white)
            plies_left = n - k
            danger = int(ended_by_capture and score == 0.0 and plies_left <= 10)
            opportunity = int(ended_by_capture and score == 1.0 and plies_left <= 10)
            out.append((before, after, team_index.get(opp, -1), team_index.get(me, -1), k, danger, opportunity, l["id"], int(white)))
    return out

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--games", type=int, default=20000)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--since", default="2026-10-06")
    ap.add_argument("--output", default="data/suntzu2/pairs-v1.npz")
    args = ap.parse_args(argv)
    teams = ["Greek Gift", "Knight Vision", "Decent Chess Bot", "Strongly Invisible", "duck", "Instructors",
             "Mist Opportunities", "TA Baseline P", "TA Baseline A", "TA Baseline S", "Apricot Squad", "baseline.py", "IAmAVirus"]
    index = {t: i for i, t in enumerate(teams)}
    paths = []
    for p in glob.glob(os.path.join(args.raw, "games", "*", "listing.json")):
        try: l = json.load(open(p))
        except Exception: continue
        if l.get("createdAt", "") >= args.since: paths.append(p)
    random.Random(3).shuffle(paths); paths = paths[: args.games]
    B, A, OPP, ME, PLY, DAN, OPPT, GID, WH = [], [], [], [], [], [], [], [], []
    with Pool(args.workers) as pool:
        for i, res in enumerate(pool.imap_unordered(one, [(p, index) for p in paths], chunksize=32)):
            if res:
                for b, a, o, m, k, d, op, g, w in res:
                    B.append(b); A.append(a); OPP.append(o); ME.append(m); PLY.append(k); DAN.append(d); OPPT.append(op); GID.append(g); WH.append(w)
            if (i + 1) % 2000 == 0: print(f"{i + 1} games, {len(B)} pairs", flush=True)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    np.savez_compressed(args.output, before=np.stack(B), after=np.stack(A), opp=np.array(OPP, np.int16), me=np.array(ME, np.int16),
                        ply=np.array(PLY, np.int16), danger=np.array(DAN, np.int8), opportunity=np.array(OPPT, np.int8),
                        gid=np.array(GID), white=np.array(WH, np.int8), teams=np.array(teams))
    print(f"wrote {args.output}: {len(B)} opponent-move pairs from {len(paths)} games")

if __name__ == "__main__":
    main()
