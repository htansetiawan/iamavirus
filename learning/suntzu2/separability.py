"""Is the opponent linearly separable from what we see? Same samples, held out by game:
linear vs MLP on raw view features, on token histograms, and both together; plus a GRU over the token sequence.

    python -m learning.suntzu2.separability data/suntzu2/pairs-v1.npz checkpoints/suntzu2-tok-v1/tokens.npy
"""
from __future__ import annotations
import sys, collections
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F

def main():
    d = np.load(sys.argv[1]); toks = np.load(sys.argv[2])
    opp, gid, white, ply, after = d["opp"], d["gid"], d["white"], d["ply"], d["after"]
    teams = [str(t) for t in d["teams"]][:12]
    groups = collections.defaultdict(list)
    for i in range(len(opp)):
        if 0 <= opp[i] < 12: groups[(gid[i], int(white[i]))].append(i)
    keys = list(groups); rng = np.random.default_rng(0)
    ug = np.unique([k[0] for k in keys]); test = set(rng.choice(ug, len(ug) // 5, replace=False))
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    for N in (10, 20):
        Xraw, Xtok, Seq, y, te = [], [], [], [], []
        for k in keys:
            idx = sorted(groups[k], key=lambda i: ply[i])[:N]
            if len(idx) < N: continue
            A = after[idx]; enemy = np.zeros((6, 64), np.float32)
            for t in range(6): enemy[t] = (A == 8 + t).mean(0)
            vis = (A != 0).mean()
            Xraw.append(np.concatenate([enemy.ravel(), [vis]]))
            h = np.bincount(toks[idx], minlength=128).astype(np.float32) / N; Xtok.append(h)
            Seq.append(toks[idx]); y.append(opp[idx[0]]); te.append(k[0] in test)
        Xraw, Xtok, Seq, y, te = map(np.array, (Xraw, Xtok, Seq, y, te)); y = y.astype(np.int64)
        def fit(X, kind):
            mu, sd = X[~te].mean(0), X[~te].std(0) + 1e-4
            Xt = torch.tensor((X - mu) / sd, dtype=torch.float32, device=dev); yt = torch.tensor(y, device=dev)
            tr = torch.tensor(np.nonzero(~te)[0], device=dev); ts = torch.tensor(np.nonzero(te)[0], device=dev)
            if kind == "linear":
                m = nn.Linear(X.shape[1], 12).to(dev); wd = 1e-3
            else:
                m = nn.Sequential(nn.Linear(X.shape[1], 256), nn.GELU(), nn.Dropout(0.3), nn.Linear(256, 256), nn.GELU(), nn.Dropout(0.3), nn.Linear(256, 12)).to(dev); wd = 1e-4
            opt = torch.optim.AdamW(m.parameters(), lr=2e-3, weight_decay=wd)
            best = 0.0
            for ep in range(60):
                m.train(); perm = tr[torch.randperm(len(tr), device=dev)]
                for i in range(0, len(perm), 512):
                    j = perm[i:i + 512]; loss = F.cross_entropy(m(Xt[j]), yt[j]); opt.zero_grad(); loss.backward(); opt.step()
                m.eval()
                with torch.no_grad(): acc = (m(Xt[ts]).argmax(1) == yt[ts]).float().mean().item()
                best = max(best, acc)
            return acc, best
        res = {}
        for name, X in (("raw view features", Xraw), ("token histogram", Xtok), ("raw + tokens", np.concatenate([Xraw, Xtok], 1))):
            for kind in ("linear", "mlp"): res[(name, kind)] = fit(X, kind)
        # GRU over the token sequence (order-aware)
        S = torch.tensor(Seq, dtype=torch.long, device=dev); yt = torch.tensor(y, device=dev)
        tr = torch.tensor(np.nonzero(~te)[0], device=dev); ts = torch.tensor(np.nonzero(te)[0], device=dev)
        class G(nn.Module):
            def __init__(s):
                super().__init__(); s.e = nn.Embedding(128, 64); s.g = nn.GRU(64, 128, batch_first=True); s.o = nn.Linear(128, 12)
            def forward(s, x): return s.o(s.g(s.e(x))[0][:, -1])
        g = G().to(dev); opt = torch.optim.AdamW(g.parameters(), lr=2e-3, weight_decay=1e-4); gb = 0.0
        for ep in range(40):
            g.train(); perm = tr[torch.randperm(len(tr), device=dev)]
            for i in range(0, len(perm), 512):
                j = perm[i:i + 512]; loss = F.cross_entropy(g(S[j]), yt[j]); opt.zero_grad(); loss.backward(); opt.step()
            g.eval()
            with torch.no_grad(): ga = (g(S[ts]).argmax(1) == yt[ts]).float().mean().item()
            gb = max(gb, ga)
        print(f"\nafter {N} opponent moves: {len(y)} game sides ({te.sum()} held out); chance {np.bincount(y[te]).max() / te.sum():.1%}")
        for (name, kind), (acc, best) in res.items(): print(f"  {name:<18} {kind:<6} 12-way accuracy {acc:.1%} (best epoch {best:.1%})")
        print(f"  token sequence     GRU    12-way accuracy {ga:.1%} (best epoch {gb:.1%})")

if __name__ == "__main__":
    main()
