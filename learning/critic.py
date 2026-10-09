"""Training-only critic that sees the true board (Experiment 1 of
reports/Deep RL for Fog of War chess.md, first step).

    python -m learning.critic --manifest data/manifests/v6.json --out checkpoints/critic-vs

V(s): value of the decision position from the TRUE board (both sides' pieces), which
replays record at every ply and our simulator knows at training time. Compared with
V(h), the deployed network's observation-only value head (validation MSE ~0.94, about
what always guessing a draw gives), to see how much of the outcome is predictable once
the fog is removed. A critic for asymmetric actor-critic RL; never used to pick moves.

Planes (13 x 8 x 8, mover-relative and canonical as in features.py: Black's board is
flipped vertically): own P N B R Q K, enemy P N B R Q K, and a constant plane.
Target: the final result from the mover's side (+1 / 0 / -1).
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from . import dataset as ds

PIECES = "PNBRQK"


def planes_from_board(board: str, side: int) -> np.ndarray:
    out = np.zeros((13, 8, 8), dtype=np.uint8)
    for sq, c in enumerate(board):
        if c == "-":
            continue
        white = c.isupper()
        own = white == (side == 0)
        k = PIECES.index(c.upper()) + (0 if own else 6)
        s = sq ^ 56 if side == 1 else sq
        out[k, s // 8, s % 8] = 1
    out[12] = 1
    return out


def build(shard: Path, limit: int | None = None):
    episodes = ds.load_episodes(shard, limit)
    xs, ys = [], []
    for e in episodes:
        side = e.actor.side
        ret = float(e.targets.terminal_return)
        for i, valid in enumerate(e.targets.value_valid):
            if not valid:
                continue
            xs.append(planes_from_board(e.targets.boards[i], side))
            ys.append(ret)
    return np.stack(xs), np.asarray(ys, dtype=np.float32)


class Critic(nn.Module):
    def __init__(self, channels: int = 64, blocks: int = 4):
        super().__init__()
        self.stem = nn.Conv2d(13, channels, 3, padding=1)
        self.blocks = nn.ModuleList()
        for _ in range(blocks):
            self.blocks.append(nn.ModuleList([nn.Conv2d(channels, channels, 3, padding=1),
                                              nn.Conv2d(channels, channels, 3, padding=1)]))
        self.head1 = nn.Linear(channels * 64, 256)
        self.head2 = nn.Linear(256, 1)

    def forward(self, x):
        x = F.relu(self.stem(x))
        for a, b in self.blocks:
            x = F.relu(x + b(F.relu(a(x))))
        return torch.tanh(self.head2(F.relu(self.head1(x.flatten(1))))).squeeze(-1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, default=Path("data/manifests/v6.json"))
    ap.add_argument("--out", type=Path, default=Path("checkpoints/critic-vs"))
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--batch", type=int, default=512)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    m = json.loads(args.manifest.read_text())
    t0 = time.time()
    xtr, ytr = build(Path(m["shards"]["train"]), args.limit)
    xte, yte = build(Path(m["shards"]["test"]), args.limit)
    print(f"train {len(ytr):,} positions, test {len(yte):,}; built in {time.time() - t0:.0f}s; "
          f"test MSE of always 0: {float(np.mean(yte ** 2)):.4f}", file=sys.stderr, flush=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    xtr_t = torch.from_numpy(xtr).to(device)
    ytr_t = torch.from_numpy(ytr).to(device)
    xte_t = torch.from_numpy(xte).to(device)
    yte_t = torch.from_numpy(yte).to(device)
    model = Critic().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    steps = args.epochs * math.ceil(len(ytr) / args.batch)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=1e-3, total_steps=steps)
    best = 9.0
    args.out.mkdir(parents=True, exist_ok=True)
    for epoch in range(args.epochs):
        model.train()
        perm = torch.randperm(len(ytr_t), device=device)
        for i in range(0, len(perm), args.batch):
            idx = perm[i:i + args.batch]
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
                pred = model(xtr_t[idx].float())
            loss = F.mse_loss(pred.float(), ytr_t[idx])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            sched.step()
        model.eval()
        with torch.no_grad():
            preds = torch.cat([model(xte_t[i:i + 4096].float()) for i in range(0, len(yte_t), 4096)])
            mse = float(F.mse_loss(preds, yte_t))
            var = float(torch.var(yte_t))
            ev = 1 - mse / var
            sign = float(((preds > 0) == (yte_t > 0)).float()[yte_t != 0].mean())
        print(f"epoch {epoch + 1}: test MSE {mse:.4f}, explained variance {ev:.3f}, decisive-game sign accuracy {sign:.3f}", flush=True)
        if mse < best:
            best = mse
            torch.save({"state_dict": model.state_dict(), "test_mse": mse, "explained_variance": ev}, args.out / "best.pt")
    print(json.dumps({"best_test_mse": round(best, 4), "positions_train": int(len(ytr)), "positions_test": int(len(yte))}))


if __name__ == "__main__":
    main()
