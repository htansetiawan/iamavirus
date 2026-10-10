"""What the top five do against duck that we do not: move-taxonomy rates per 100 moves."""
import glob, json, os, random, sys
sys.path.insert(0, os.path.expanduser("~/git/iamavirus"))
from learning.move_taxonomy import label_game, aggregate

TOP5 = {"Greek Gift", "Knight Vision", "Decent Chess Bot", "Strongly Invisible", "Instructors"}
ours, top = [], []
for p in glob.glob(os.path.expanduser("~/git/iamavirus/data/raw/games/*/listing.json")):
    try: l = json.load(open(p))
    except Exception: continue
    if "duck" not in (l["white"], l["black"]): continue
    opp = l["black"] if l["white"] == "duck" else l["white"]
    if opp == "IAmAVirus":
        v = l["whiteVersion"] if l["white"] == "IAmAVirus" else l["blackVersion"]
        if v in (18, 20, 21): ours.append(l)
    elif opp in TOP5: top.append(l)
random.Random(1).shuffle(top); top = sorted(top, key=lambda l: l["createdAt"])[-300:]
def lab(ls):
    out = []
    for l in ls:
        try:
            g = label_game(json.load(open(os.path.expanduser(f"~/git/iamavirus/data/raw/games/{l['id']}/replay.json"))))
            g["_l"] = l; out.append(g)
        except Exception: pass
    return out
LO, LT = lab(ours), lab(top)
side = lambda name, duck: (lambda g: ("white" if (g["_l"]["white"] == "duck") == duck else "black"))
cols = [("us vs duck", aggregate(LO, side("us", False))), ("duck vs us", aggregate(LO, side("d", True))),
        ("top5 vs duck", aggregate(LT, side("t", False))), ("duck vs top5", aggregate(LT, side("d", True)))]
rows = ["visible_mean", "vision_gain", "capture_unseen_share", "capture_unseen", "fog_route", "long_strike", "king_threat",
        "king_threat_unseen", "king_hunt_sacrifice", "sacrifice", "queen_raid", "queen_exposed_unseen", "walk_into_unseen",
        "victim_walked_in", "back_rank_bare", "king_move", "king_leaves_home", "castle"]
print(f"{'per 100 moves':<24}" + "".join(f"{c:>14}" for c, _ in cols))
print(f"{'games':<24}" + "".join(f"{a['games']:>14}" for _, a in cols))
for k in rows: print(f"{k:<24}" + "".join(f"{a[k]:>14.2f}" for _, a in cols))
