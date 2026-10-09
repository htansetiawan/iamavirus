"""SunTzu step 2: a residual-quantized autoencoder over strategy windows (note 027).

    python -m learning.suntzu_rvq data/suntzu/windows-v1.npz --levels 3 --codes 16 --output checkpoints/suntzu-rvq-v1

Encoder -> RVQ (level 1 = the chief's grand strategy, level 2 = the general's
plan, level 3 = the officer's tactic) -> decoder that reconstructs the window
features and predicts the outcome signals (the side's game score and the next
window's material trend), so codes carry what matters for winning.

Writes the model, every window's code triple, and a report naming each code by
the features it over-represents, the teams that use it, and its score.
"""
from __future__ import annotations

import argparse
import collections
import json
import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class ResidualVQ(nn.Module):
    def __init__(self, levels: int, codes: int, dim: int, beta: float = 0.25):
        super().__init__()
        self.books = nn.ParameterList([nn.Parameter(torch.randn(codes, dim) * 0.1) for _ in range(levels)])
        self.beta = beta

    def forward(self, z):
        residual, quantized, indices, loss = z, torch.zeros_like(z), [], z.new_zeros(())
        for book in self.books:
            d = torch.cdist(residual, book)
            idx = d.argmin(dim=1)
            q = book[idx]
            loss = loss + F.mse_loss(q, residual.detach()) + self.beta * F.mse_loss(residual, q.detach())
            quantized = quantized + q
            residual = residual - q.detach()
            indices.append(idx)
        quantized = z + (quantized - z).detach()  # straight-through
        return quantized, torch.stack(indices, 1), loss

    @torch.no_grad()
    def restart_dead(self, z, usage):
        """Re-seed unused codes from random encoder outputs (level by level residuals)."""
        residual = z
        for level, book in enumerate(self.books):
            dead = (usage[level] == 0).nonzero().flatten()
            if len(dead):
                pick = residual[torch.randint(0, len(residual), (len(dead),), device=z.device)]
                book.data[dead] = pick + 0.01 * torch.randn_like(pick)
            idx = torch.cdist(residual, book).argmin(dim=1)
            residual = residual - book[idx]


class SunTzuRVQ(nn.Module):
    def __init__(self, features: int, levels: int = 3, codes: int = 16, dim: int = 32):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(features, 128), nn.GELU(), nn.Linear(128, 64), nn.GELU(), nn.Linear(64, dim))
        self.rvq = ResidualVQ(levels, codes, dim)
        self.decoder = nn.Sequential(nn.Linear(dim, 64), nn.GELU(), nn.Linear(64, 128), nn.GELU(), nn.Linear(128, features))
        self.outcome = nn.Sequential(nn.Linear(dim, 32), nn.GELU(), nn.Linear(32, 2))  # score logit, next trend

    def forward(self, x):
        z = self.encoder(x)
        q, idx, vq_loss = self.rvq(z)
        return self.decoder(q), self.outcome(q), idx, vq_loss, z


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("windows")
    ap.add_argument("--levels", type=int, default=3)
    ap.add_argument("--codes", type=int, default=16)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--output", default="checkpoints/suntzu-rvq-v1")
    args = ap.parse_args(argv)
    d = np.load(args.windows)
    X, names = d["X"].astype(np.float32), [str(f) for f in d["features"]]
    meta = [json.loads(m) for m in d["meta"]]
    mean, std = X.mean(0), X.std(0) + 1e-3
    Xn = (X - mean) / std
    score = np.array([m["score"] for m in meta], np.float32)
    trend = np.array([m["next_trend"] for m in meta], np.float32)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    xs, ss, ts = (torch.tensor(a, device=device) for a in (Xn, score, trend))
    model = SunTzuRVQ(X.shape[1], args.levels, args.codes).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=2e-3)
    n = len(xs)
    for epoch in range(args.epochs):
        perm = torch.randperm(n, device=device)
        usage = torch.zeros(args.levels, args.codes, device=device)
        total = 0.0
        for i in range(0, n, 512):
            b = perm[i:i + 512]
            recon, out, idx, vq_loss, _ = model(xs[b])
            loss = (F.mse_loss(recon, xs[b]) + vq_loss + 0.5 * F.binary_cross_entropy_with_logits(out[:, 0], ss[b]) +
                    0.5 * F.mse_loss(out[:, 1], ts[b]))
            opt.zero_grad(); loss.backward(); opt.step()
            for level in range(args.levels):
                usage[level] += torch.bincount(idx[:, level], minlength=args.codes)
            total += loss.item() * len(b)
        if epoch < args.epochs - 10:
            with torch.no_grad():
                model.rvq.restart_dead(model.encoder(xs), usage)
        if epoch % 10 == 0 or epoch == args.epochs - 1:
            used = [(usage[l] > 0).sum().item() for l in range(args.levels)]
            print(f"epoch {epoch} loss {total / n:.4f} codes used per level {used}", flush=True)

    with torch.no_grad():
        recon, out, idx, _, _ = model(xs)
    idx = idx.cpu().numpy()
    os.makedirs(args.output, exist_ok=True)
    torch.save({"model": model.state_dict(), "mean": mean, "std": std, "features": names,
                "levels": args.levels, "codes": args.codes}, os.path.join(args.output, "model.pt"))
    np.save(os.path.join(args.output, "codes.npy"), idx)

    lines = [f"# SunTzu codebook v1: {n} windows, {args.levels} levels x {args.codes} codes", "",
             "Each code: share of windows, the side's mean game score, the features it over-represents (z-score vs all windows), and the teams that use it most (share of that team's windows).", ""]
    teams = collections.Counter(m["team"] for m in meta)
    for level in range(args.levels):
        lines += [f"## Level {level + 1}" + (" (chief: grand strategy)" if level == 0 else " (general: plan)" if level == 1 else " (officer: tactic)"), "",
                  "| code | share | score | over-represented features | used most by |", "| --- | --- | --- | --- | --- |"]
        for c in range(args.codes):
            m = idx[:, level] == c
            if not m.any():
                continue
            z = (X[m].mean(0) - X.mean(0)) / (X.std(0) + 1e-6)
            top = [f"{names[i].split(':', 1)[-1] if not names[i].startswith(('own_', 'enemy_')) else names[i]} {z[i]:+.1f}"
                   for i in np.argsort(-z)[:4] if z[i] > 0.3]
            by_team = collections.Counter(meta[i]["team"] for i in np.nonzero(m)[0])
            fav = sorted(((k, v / teams[k]) for k, v in by_team.items() if teams[k] >= 200), key=lambda kv: -kv[1])[:3]
            lines.append(f"| {level + 1}.{c} | {m.mean():.1%} | {score[m].mean():.2f} | {', '.join(top) or '—'} | "
                         f"{', '.join(f'{k} {v:.0%}' for k, v in fav)} |")
        lines.append("")
    with open(os.path.join(args.output, "report.md"), "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {args.output}/report.md")


if __name__ == "__main__":
    main()
