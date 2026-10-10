"""duck against everyone: record by opponent, how duck's own king falls, and duck's move fingerprint vs ours."""
import collections, glob, json, os, sys
import chess
sys.path.insert(0, os.path.expanduser("~/git/iamavirus"))
from learning.top6_report import loss_anatomy
from learning.move_taxonomy import label_game, aggregate, KEYS

D = sys.argv[1] if len(sys.argv) > 1 else "duck"
games = []
for p in glob.glob(os.path.expanduser("~/git/iamavirus/data/raw/games/*/listing.json")):
    try: l = json.load(open(p))
    except Exception: continue
    if D in (l["white"], l["black"]): games.append(l)
rec = collections.defaultdict(lambda: [0, 0, 0])
for l in games:
    dw = l["white"] == D; opp = l["black"] if dw else l["white"]
    res = l["result"]; s = 0.5 if res == "1/2-1/2" else (1.0 if (res == "1-0") == dw else 0.0)
    rec[opp][0 if s == 1 else 1 if s == 0.5 else 2] += 1
print(f"{D}: {len(games)} games in the mirror. Record (duck W-D-L) by opponent, most games first:")
for opp, (w, d, l_) in sorted(rec.items(), key=lambda kv: -sum(kv[1]))[:16]:
    print(f"  {opp:<22} {w}-{d}-{l_}  duck scores {(w + d / 2) / (w + d + l_):.2f}")
# how duck loses (its own king), against anyone
fell = collections.Counter(); killers = collections.Counter(); who = collections.Counter(); led = 0; n = 0
for l in games:
    dw = l["white"] == D; res = l["result"]
    if res == "1/2-1/2" or (res == "1-0") == dw: continue
    try: r = json.load(open(os.path.expanduser(f"~/git/iamavirus/data/raw/games/{l['id']}/replay.json")))
    except Exception: continue
    a = loss_anatomy(r, "white" if dw else "black"); n += 1
    fell[a.get("king_fell", a["reason"])] += 1; killers[a.get("king_attackers", "?")] += 1
    who[l["black"] if dw else l["white"]] += 1; led += a["max_lead"] >= 3
print(f"\nduck's {n} losses: how duck's king fell {dict(fell.most_common())}\n  killers {dict(killers.most_common())}\n  beaten by {dict(who.most_common(8))}\n  duck had led by 3+ in {led}")
