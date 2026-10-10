"""Run the exported classifier (parsed from classifier_weights.h) on local sparring games, from our side."""
import glob, json, os, re, sys, collections, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
hdr = open(sys.argv[1]).read()
arr = lambda name: np.array([float(v) for v in re.search(name + r"\[[^\]]*\] = \{([^}]*)\}", hdr).group(1).split(",")])
mu, sd, b, W = arr("kClassifierMean"), arr("kClassifierScale"), arr("kClassifierBias"), arr("kClassifierWeights").reshape(387, 12)
grp = arr("kClassifierGroup").astype(int)
PIECES = "pnbrqk"
def feats(F, colour, N=20):
    us_upper = colour == "white"; cnt = np.zeros((6, 64)); seen = 0.0; ours = []
    for t in range(0, min(N, len(F) - 1) + 1):
        v = F[t][colour]
        for s, c in enumerate(v):
            if c in "?-": continue
            if c.isupper() != us_upper: cnt[PIECES.index(c.lower()), s] += 1
        seen += sum(c != "?" for c in v); ours.append(sum(1 for c in v if c not in "?-" and c.isupper() == us_upper))
    n = min(N, len(F) - 1) + 1
    return np.concatenate([cnt.ravel() / n, [seen / n / 64.0, (ours[0] - ours[-1]) / 16.0, 1.0 if us_upper else 0.0]])
G = ["TA-P/A", "TA-S", "top six", "Mist", "others"]
agg = collections.defaultdict(lambda: np.zeros(5)); n = collections.Counter()
for f in glob.glob(os.path.expanduser("~/git/iamavirus/data/arena_local/builds/*.json")):
    g = json.load(open(f)); F = g["frames"]
    if len(F) < 21: continue
    for colour, opp_colour in (("white", "black"), ("black", "white")):
        me, opp = g[colour], g[opp_colour]
        if "iamavirus" not in me: continue
        z = ((feats(F, colour) - mu) / sd) @ W + b; z = np.exp(z - z.max()); z /= z.sum()
        post = np.zeros(5)
        for k in range(12): post[grp[k]] += z[k]
        key = re.sub(r"-hybrid$|\.zip$", "", opp); agg[key] += post; n[key] += 1
for k in sorted(agg, key=lambda k: -n[k]):
    if n[k] >= 6: print(f"{k:<40} {n[k]:>4} games: mean posterior " + ", ".join(f"{G[i]} {agg[k][i] / n[k]:.2f}" for i in range(5)))
