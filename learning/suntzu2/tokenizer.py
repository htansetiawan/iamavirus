"""SunTzu v2, level 0: a latent-action VQ-VAE that turns each observed opponent move into a token.

    python -m learning.suntzu2.tokenizer data/suntzu2/pairs-v1.npz --codes 128 --output checkpoints/suntzu2-tok-v1

The encoder sees our view before and after the opponent's move; a vector-quantised bottleneck keeps one of K
codes; the decoder must predict the after-view from the before-view and the code alone. So each code is the
information needed to explain what visibly changed: a learned vocabulary of observed move types (the idea of
latent-action models such as Genie, applied to Fog of War, where we never see the move itself). A control
decoder without the code measures how much the tokens explain.
"""
from __future__ import annotations
import argparse, json, os
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F

C = 14  # square states: unseen, empty, our 6 pieces, their 6 pieces

class Encoder(nn.Module):
    def __init__(self, dim=64, width=128):
        super().__init__()
        self.net = nn.Sequential(nn.Conv2d(2 * C, width, 3, padding=1), nn.GELU(), nn.Conv2d(width, width, 3, padding=1), nn.GELU(),
                                 nn.Conv2d(width, width, 3, padding=1), nn.GELU())
        self.out = nn.Linear(width * 64, dim)
    def forward(self, b, a):
        x = torch.cat([F.one_hot(b.long(), C), F.one_hot(a.long(), C)], -1).float().view(-1, 8, 8, 2 * C).permute(0, 3, 1, 2)
        return self.out(self.net(x).flatten(1))

class Decoder(nn.Module):
    def __init__(self, dim=64, width=128):
        super().__init__()
        self.net = nn.Sequential(nn.Conv2d(C + dim, width, 3, padding=1), nn.GELU(), nn.Conv2d(width, width, 3, padding=1), nn.GELU(),
                                 nn.Conv2d(width, width, 3, padding=1), nn.GELU(), nn.Conv2d(width, C, 1))
    def forward(self, b, q):
        x = F.one_hot(b.long(), C).float().view(-1, 8, 8, C).permute(0, 3, 1, 2)
        z = q[:, :, None, None].expand(-1, -1, 8, 8)
        return self.net(torch.cat([x, z], 1)).permute(0, 2, 3, 1).reshape(-1, 64, C)

class VQ(nn.Module):
    def __init__(self, codes, dim, beta=0.25):
        super().__init__()
        self.book = nn.Parameter(torch.randn(codes, dim) * 0.1); self.beta = beta
    def forward(self, z):
        idx = torch.cdist(z, self.book).argmin(1); q = self.book[idx]
        loss = F.mse_loss(q, z.detach()) + self.beta * F.mse_loss(z, q.detach())
        return z + (q - z).detach(), idx, loss
    @torch.no_grad()
    def restart(self, z, usage):
        dead = (usage == 0).nonzero().flatten()
        if len(dead):
            self.book.data[dead] = z[torch.randint(0, len(z), (len(dead),), device=z.device)] + 0.01 * torch.randn(len(dead), z.shape[1], device=z.device)
        return len(dead)

class Tokenizer(nn.Module):
    def __init__(self, codes=128, dim=64):
        super().__init__()
        self.enc, self.vq, self.dec = Encoder(dim), VQ(codes, dim), Decoder(dim)
    def forward(self, b, a):
        z = self.enc(b, a); q, idx, vql = self.vq(z)
        return self.dec(b, q), idx, vql, z

def recon_loss(logits, a, b):
    ce = F.cross_entropy(logits.reshape(-1, C), a.long().reshape(-1), reduction="none").view(-1, 64)
    w = 1.0 + 9.0 * (a != b).float()  # the changed squares are what the token must explain
    return (ce * w).sum() / w.sum()

def changed_accuracy(logits, a, b):
    m = a != b
    return ((logits.argmax(-1) == a.long()) & m).sum().item() / max(1, m.sum().item())

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pairs"); ap.add_argument("--codes", type=int, default=128); ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--output", default="checkpoints/suntzu2-tok-v1")
    args = ap.parse_args(argv)
    d = np.load(args.pairs, allow_pickle=False)
    B = torch.tensor(d["before"]); A = torch.tensor(d["after"]); gid = d["gid"]
    ug = np.unique(gid); rng = np.random.default_rng(0); test = set(rng.choice(ug, len(ug) // 10, replace=False))
    te = torch.tensor(np.array([g in test for g in gid])); tr = ~te
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = Tokenizer(args.codes).to(dev)
    control = Decoder().to(dev)  # the same decoder with a zero code: how much the after-view is predictable without the token
    opt = torch.optim.Adam(list(model.parameters()) + list(control.parameters()), lr=1e-3)
    tri = tr.nonzero().flatten(); tei = te.nonzero().flatten()
    zero = None
    for epoch in range(args.epochs):
        perm = tri[torch.randperm(len(tri))]; usage = torch.zeros(args.codes, device=dev); tot = 0.0; zs = []
        model.train(); control.train()
        for i in range(0, len(perm), 4096):
            j = perm[i:i + 4096]; b, a = B[j].to(dev), A[j].to(dev)
            logits, idx, vql, z = model(b, a)
            if zero is None or zero.shape[0] != len(j): zero = torch.zeros(len(j), 64, device=dev)
            loss = recon_loss(logits, a, b) + vql + recon_loss(control(b, zero), a, b)
            opt.zero_grad(); loss.backward(); opt.step()
            usage += torch.bincount(idx, minlength=args.codes); tot += loss.item() * len(j)
            if len(zs) < 8: zs.append(z.detach())
        dead = model.vq.restart(torch.cat(zs), usage) if epoch < args.epochs - 2 else 0
        model.eval(); control.eval()
        with torch.no_grad():
            accs, caccs = [], []
            for i in range(0, min(len(tei), 200000), 8192):
                j = tei[i:i + 8192]; b, a = B[j].to(dev), A[j].to(dev)
                logits, idx, _, _ = model(b, a); accs.append(changed_accuracy(logits, a, b))
                caccs.append(changed_accuracy(control(b, torch.zeros(len(j), 64, device=dev)), a, b))
        p = usage / usage.sum(); ppl = torch.exp(-(p[p > 0] * p[p > 0].log()).sum()).item()
        print(f"epoch {epoch}: loss {tot / len(perm):.4f}; held-out changed-square accuracy {np.mean(accs):.3f} with the token vs {np.mean(caccs):.3f} without; "
              f"codes used {(usage > 0).sum().item()}/{args.codes}, perplexity {ppl:.1f}, restarted {dead}", flush=True)
    # tokenize everything
    model.eval(); toks = np.zeros(len(B), np.int16)
    with torch.no_grad():
        for i in range(0, len(B), 16384):
            b, a = B[i:i + 16384].to(dev), A[i:i + 16384].to(dev)
            toks[i:i + 16384] = model.vq(model.enc(b, a))[1].cpu().numpy()
    os.makedirs(args.output, exist_ok=True)
    torch.save({"model": model.state_dict(), "codes": args.codes}, os.path.join(args.output, "model.pt"))
    np.save(os.path.join(args.output, "tokens.npy"), toks)
    print("wrote", args.output)

if __name__ == "__main__":
    main()
