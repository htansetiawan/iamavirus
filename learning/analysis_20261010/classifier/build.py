"""Opponent-classifier dataset: from one side's own views only, features after N plies; label = the opponent team."""
import glob, json, os, random, sys
import numpy as np
CLASSES = ["Greek Gift", "Knight Vision", "Decent Chess Bot", "Strongly Invisible", "duck", "Instructors",
           "Mist Opportunities", "TA Baseline P", "TA Baseline A", "TA Baseline S", "Apricot Squad", "baseline.py"]
NS = [10, 20, 40]
PIECES = "pnbrqk"
def feats(F, colour, N):
    us_upper = colour == "white"
    cnt = np.zeros((6, 64), np.float32); seen = 0.0; ours = []
    for t in range(0, min(N, len(F) - 1) + 1):
        v = F[t][colour]
        for s, c in enumerate(v):
            if c in "?-": continue
            if c.isupper() != us_upper: cnt[PIECES.index(c.lower()), s] += 1
        seen += sum(c != "?" for c in v)
        ours.append(sum(1 for c in v if c not in "?-" and c.isupper() == us_upper))
    n = max(1, min(N, len(F) - 1) + 1)
    extra = np.array([seen / n / 64.0, (ours[0] - ours[-1]) / 16.0, 1.0 if us_upper else 0.0], np.float32)
    return np.concatenate([cnt.ravel() / n, extra])
def main():
    root = os.path.expanduser("~/git/iamavirus/data/raw/games")
    rng = random.Random(7)
    lst = []
    for p in glob.glob(os.path.join(root, "*", "listing.json")):
        try: l = json.load(open(p))
        except Exception: continue
        if l["createdAt"] < "2026-10-07": continue
        lst.append((l, p))
    ours = [x for x in lst if "IAmAVirus" in (x[0]["white"], x[0]["black"])]
    others = [x for x in lst if "IAmAVirus" not in (x[0]["white"], x[0]["black"])]
    rng.shuffle(others)
    pick = others[:7000] + ours
    X = {N: [] for N in NS}; y = []; persp = []; gid = []
    for i, (l, p) in enumerate(pick):
        try: r = json.load(open(p.replace("listing.json", "replay.json")))
        except Exception: continue
        F = r["frames"]
        for colour, opp_key in (("white", "black"), ("black", "white")):
            opp = l[opp_key]
            if opp not in CLASSES: continue
            for N in NS: X[N].append(feats(F, colour, N))
            y.append(CLASSES.index(opp)); persp.append(l[colour]); gid.append(l["id"])
        if (i + 1) % 1000 == 0: print(i + 1, "games", len(y), "samples", flush=True)
    out = os.path.join(os.path.dirname(__file__), "dataset.npz")
    np.savez_compressed(out, **{f"X{N}": np.stack(X[N]) for N in NS}, y=np.array(y), persp=np.array(persp), gid=np.array(gid), classes=np.array(CLASSES))
    print("wrote", out, len(y), "samples")
main()
