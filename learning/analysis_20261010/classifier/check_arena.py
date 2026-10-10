"""The exported classifier on our real arena games (our side), grouped by the real opponent."""
import glob, json, os, re, sys, collections, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_local.py")).read().split("G = [")[0])  # reuse parser + feats
G = ["TA-P/A", "TA-S", "top six", "Mist", "others"]
agg = collections.defaultdict(lambda: np.zeros(5)); n = collections.Counter(); hit = collections.Counter()
for p in glob.glob(os.path.expanduser("~/git/iamavirus/data/raw/games/*/listing.json")):
    l = json.load(open(p))
    if "IAmAVirus" not in (l["white"], l["black"]) or l["createdAt"] < "2026-10-08": continue
    F = json.load(open(p.replace("listing.json", "replay.json")))["frames"]
    if len(F) < 21: continue
    colour = "white" if l["white"] == "IAmAVirus" else "black"; opp = l["black"] if colour == "white" else l["white"]
    z = ((feats(F, colour) - mu) / sd) @ W + b; z = np.exp(z - z.max()); z /= z.sum()
    post = np.zeros(5)
    for k in range(12): post[grp[k]] += z[k]
    agg[opp] += post; n[opp] += 1
    truth = 0 if opp in ("TA Baseline P", "TA Baseline A") else 1 if opp == "TA Baseline S" else 3 if opp.startswith("Mist") else 2 if opp in ("Greek Gift", "Knight Vision", "Decent Chess Bot", "Strongly Invisible", "duck", "Instructors") else 4
    hit[opp] += int(post.argmax() == truth)
for k in sorted(agg, key=lambda k: -n[k]):
    if n[k] >= 6: print(f"{k:<20} {n[k]:>4} games: argmax right {hit[k] / n[k]:5.1%}; mean posterior " + ", ".join(f"{G[i]} {agg[k][i] / n[k]:.2f}" for i in range(5)))
