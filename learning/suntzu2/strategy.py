"""SunTzu v2, level 1: strategy codes over the stream of move tokens.

    python -m learning.suntzu2.strategy data/suntzu2/pairs-v1.npz checkpoints/suntzu2-tok-v1/tokens.npy --output checkpoints/suntzu2-strat-v1

A GRU reads one game side's opponent-move tokens in order. Its state passes through a two-level residual
codebook (level 1 = the plan, level 2 = the tactic), and the heads see only the quantised state: who the
opponent is, whether our king falls within 10 plies (danger), whether theirs does (opportunity). So every code
must carry strategic meaning, and each code's danger and opportunity rates can be read off. A twin model
without the codebook measures what the discretisation costs.
"""
from __future__ import annotations
import argparse, collections, os
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F

class RVQ(nn.Module):
    def __init__(self, levels, codes, dim, beta=0.25):
        super().__init__()
        self.books = nn.ParameterList([nn.Parameter(torch.randn(codes, dim) * 0.1) for _ in range(levels)]); self.beta = beta
    def forward(self, z):
        r, q, idx, loss = z, torch.zeros_like(z), [], z.new_zeros(())
        for book in self.books:
            i = torch.cdist(r, book).argmin(-1); c = book[i]
            loss = loss + F.mse_loss(c, r.detach()) + self.beta * F.mse_loss(r, c.detach())
            q = q + c; r = r - c.detach(); idx.append(i)
        return z + (q - z).detach(), torch.stack(idx, -1), loss
    @torch.no_grad()
    def restart(self, z, usage):
        r = z; n = 0
        for l, book in enumerate(self.books):
            dead = (usage[l] == 0).nonzero().flatten(); n += len(dead)
            if len(dead): book.data[dead] = r[torch.randint(0, len(r), (len(dead),), device=r.device)]
            r = r - book[torch.cdist(r, book).argmin(-1)]
        return n

class Strategy(nn.Module):
    def __init__(self, tokens=128, dim=128, levels=2, codes=16, quantise=True):
        super().__init__()
        self.emb = nn.Embedding(tokens, 64); self.ply = nn.Embedding(64, 16)
        self.gru = nn.GRU(80, dim, batch_first=True); self.quantise = quantise
        self.rvq = RVQ(levels, codes, dim)
        self.team = nn.Linear(dim, 12); self.danger = nn.Linear(dim, 1); self.opp = nn.Linear(dim, 1)
    def forward(self, tok, plyb):
        h = self.gru(torch.cat([self.emb(tok), self.ply(plyb)], -1))[0]
        if self.quantise: q, idx, vql = self.rvq(h)
        else: q, idx, vql = h, None, h.new_zeros(())
        return self.team(q), self.danger(q).squeeze(-1), self.opp(q).squeeze(-1), idx, vql, h

def auc(score, label):
    o = np.argsort(score); r = np.empty(len(score)); r[o] = np.arange(len(score)); pos = label.astype(bool)
    npos, nneg = pos.sum(), (~pos).sum()
    return (r[pos].sum() - npos * (npos - 1) / 2) / max(1, npos * nneg)

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pairs"); ap.add_argument("tokens"); ap.add_argument("--maxlen", type=int, default=60)
    ap.add_argument("--epochs", type=int, default=12); ap.add_argument("--output", default="checkpoints/suntzu2-strat-v1")
    args = ap.parse_args(argv)
    d = np.load(args.pairs); toks = np.load(args.tokens)
    opp, gid, white, ply, dan, opt_ = d["opp"], d["gid"], d["white"], d["ply"], d["danger"], d["opportunity"]
    teams = [str(t) for t in d["teams"]][:12]
    groups = collections.defaultdict(list)
    for i in range(len(opp)):
        if 0 <= opp[i] < 12: groups[(gid[i], int(white[i]))].append(i)
    keys = list(groups); L = args.maxlen
    T = np.zeros((len(keys), L), np.int64); P = np.zeros((len(keys), L), np.int64); M = np.zeros((len(keys), L), bool)
    D = np.zeros((len(keys), L), np.float32); O = np.zeros((len(keys), L), np.float32); Y = np.zeros(len(keys), np.int64); G = []
    for n, k in enumerate(keys):
        idx = sorted(groups[k], key=lambda i: ply[i])[:L]
        T[n, :len(idx)] = toks[idx]; P[n, :len(idx)] = np.minimum(ply[idx] // 4, 63); M[n, :len(idx)] = True
        D[n, :len(idx)] = dan[idx]; O[n, :len(idx)] = opt_[idx]; Y[n] = opp[idx[0]]; G.append(k[0])
    rng = np.random.default_rng(0); ug = np.unique(G); test = set(rng.choice(ug, len(ug) // 5, replace=False))
    te = np.array([g in test for g in G]); dev = "cuda" if torch.cuda.is_available() else "cpu"
    tt = lambda a: torch.tensor(a, device=dev)
    T_, P_, M_, D_, O_, Y_ = map(tt, (T, P, M, D, O, Y)); tr = tt(np.nonzero(~te)[0]); ts = tt(np.nonzero(te)[0])
    results = {}
    for quantise in (True, False):
        torch.manual_seed(0)
        m = Strategy(quantise=quantise).to(dev); opt = torch.optim.AdamW(m.parameters(), lr=2e-3, weight_decay=1e-4)
        pw = torch.tensor(20.0, device=dev)
        for ep in range(args.epochs):
            m.train(); perm = tr[torch.randperm(len(tr), device=dev)]; usage = torch.zeros(2, 16, device=dev); hs = []
            for i in range(0, len(perm), 256):
                j = perm[i:i + 256]; mt = M_[j]
                team, dl, ol, idx, vql, h = m(T_[j], P_[j])
                yy = Y_[j][:, None].expand(-1, L)
                loss = F.cross_entropy(team[mt], yy[mt]) + F.binary_cross_entropy_with_logits(dl[mt], D_[j][mt], pos_weight=pw) \
                       + F.binary_cross_entropy_with_logits(ol[mt], O_[j][mt], pos_weight=pw) + vql
                opt.zero_grad(); loss.backward(); opt.step()
                if quantise:
                    for l in range(2): usage[l] += torch.bincount(idx[..., l][mt], minlength=16)
                    if len(hs) < 4: hs.append(h[mt].detach())
            if quantise and ep < args.epochs - 3: m.rvq.restart(torch.cat(hs), usage)
        m.eval()
        with torch.no_grad():
            team, dl, ol, idx, _, _ = m(T_[ts], P_[ts]); mt = M_[ts]
            acc = {t: (team[:, t - 1].argmax(-1) == Y_[ts]).float()[mt[:, t - 1]].mean().item() for t in (5, 10, 20, 40)}
            da = auc(dl[mt].cpu().numpy(), D_[ts][mt].cpu().numpy()); oa = auc(ol[mt].cpu().numpy(), O_[ts][mt].cpu().numpy())
        results[quantise] = (acc, da, oa, m, idx, mt)
        print(f"{'2x16 codes' if quantise else 'continuous'}: team accuracy after 5/10/20/40 opponent moves "
              + "/".join(f"{acc[t]:.1%}" for t in (5, 10, 20, 40)) + f"; danger AUC {da:.3f}; opportunity AUC {oa:.3f}", flush=True)
    # read the codes: danger / opportunity / teams per (plan, tactic)
    acc, da, oa, m, idx, mt = results[True]
    os.makedirs(args.output, exist_ok=True); torch.save({"model": m.state_dict(), "teams": teams}, os.path.join(args.output, "model.pt"))
    with torch.no_grad():
        _, _, _, idx_all, _, _ = m(T_, P_)
    I = idx_all.cpu().numpy(); Mm = M; lines = ["# SunTzu v2 strategy codes (level 1 plan x level 2 tactic)", "",
            f"Held-out: team accuracy after 10 opponent moves {acc[10]:.1%}, after 20 {acc[20]:.1%}; danger AUC {da:.3f}; opportunity AUC {oa:.3f}.", "",
            "| plan | share | our king falls within 10 plies | theirs falls within 10 plies | teams that use it most (share of their moves) |", "| --- | --- | --- | --- | --- |"]
    base = Mm.sum(); team_moves = collections.Counter(); per = collections.defaultdict(collections.Counter)
    for n in range(len(keys)):
        for t in range(L):
            if Mm[n, t]: team_moves[Y[n]] += 1; per[I[n, t, 0]][Y[n]] += 1
    for c in range(16):
        sel = (I[..., 0] == c) & Mm
        if not sel.any(): continue
        fav = sorted(((teams[k], v / team_moves[k]) for k, v in per[c].items()), key=lambda kv: -kv[1])[:3]
        lines.append(f"| {c} | {sel.sum() / base:.1%} | {D[sel].mean():.1%} | {O[sel].mean():.1%} | " + ", ".join(f"{t} {s:.0%}" for t, s in fav) + " |")
    open(os.path.join(args.output, "report.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))

if __name__ == "__main__":
    main()
