"""Four query slots attend to 64 squares; shared token K/V fold into tables.

Inputs describe a hypothetical world, in experiment237's canonical encoding.
The two king queries are piece-local; the other two slots can represent global
relations. No true board, future observation or player identity is required at
runtime beyond the hypothesized world being scored.
"""
import torch
from torch import nn

WIDTH = 32
QUERIES = 4
HEADS = 2
ROUNDS = 2


class QueryBlock(nn.Module):
    def __init__(self):
        super().__init__()
        self.norm1 = nn.LayerNorm(WIDTH)
        self.query = nn.Linear(WIDTH, WIDTH)
        self.output = nn.Linear(WIDTH, WIDTH)
        self.norm2 = nn.LayerNorm(WIDTH)
        self.ff1 = nn.Linear(WIDTH, 64)
        self.ff2 = nn.Linear(64, WIDTH)

    def forward(self, z, keys, values):
        q = self.query(self.norm1(z)).reshape(-1, QUERIES, HEADS, WIDTH // HEADS).transpose(1, 2)
        scores = (q @ keys.transpose(-1, -2)) / (WIDTH // HEADS) ** .5
        v = (scores.softmax(dim=-1) @ values).transpose(1, 2).reshape(-1, QUERIES, WIDTH)
        z = z + self.output(v)
        return z + self.ff2(torch.relu(self.ff1(self.norm2(z))))


class QueryStudent(nn.Module):
    def __init__(self):
        super().__init__()
        self.piece = nn.Embedding(64 * 13, WIDTH)
        self.vision = nn.Embedding(64 * 4, WIDTH)
        self.castle = nn.Embedding(64, WIDTH)
        self.ep = nn.Embedding(64, WIDTH)
        self.latent = nn.Parameter(torch.empty(QUERIES, WIDTH))
        self.half_weight = nn.Parameter(torch.zeros(WIDTH))
        self.key = nn.Linear(WIDTH, WIDTH)
        self.value = nn.Linear(WIDTH, WIDTH)
        self.blocks = nn.ModuleList([QueryBlock() for _ in range(ROUNDS)])
        self.final_norm = nn.LayerNorm(WIDTH)
        self.hidden = nn.Linear((QUERIES + 1) * WIDTH, 64)
        self.output = nn.Linear(64, 1)
        for e in (self.piece, self.vision, self.castle, self.ep):
            nn.init.normal_(e.weight, std=.02)
        nn.init.normal_(self.latent, std=.05)

    def forward(self, x, half):
        sq = torch.arange(64, device=x.device)[None, :]
        tokens = self.piece(13 * sq + x[:, :, 0]) + self.vision(4 * sq + x[:, :, 1] + 2 * x[:, :, 2])
        tokens = tokens + self.castle(sq) * x[:, :, 3, None] + self.ep(sq) * x[:, :, 4, None]
        kings = torch.stack([(tokens * (x[:, :, 0] == p)[:, :, None]).sum(1) for p in (6, 12)], dim=1)
        z = self.latent[None, :, :] + (half[:, None, None] / 100) * self.half_weight
        z = z + torch.cat([kings, torch.zeros_like(kings)], dim=1)
        keys = self.key(tokens).reshape(-1, 64, HEADS, WIDTH // HEADS).transpose(1, 2)
        values = self.value(tokens).reshape(-1, 64, HEADS, WIDTH // HEADS).transpose(1, 2)
        for block in self.blocks:
            z = block(z, keys, values)
        summary = torch.cat([self.final_norm(z).flatten(1), tokens.sum(1) / 8], dim=1)
        return self.output(torch.relu(self.hidden(summary))).squeeze(-1)


def pack_native(model):
    """FP32 layout consumed by query_infer.c, including folded K/V embeddings.

    No token nonlinearity precedes K/V, so W(sum embeddings)+b equals the sum
    of individually projected tables plus one bias. Rounding parity is tested.
    """
    import numpy as np
    state = model.cpu().eval().state_dict()
    tables = [state[n + '.weight'] for n in ('piece', 'vision', 'castle', 'ep')]
    tensors = list(tables)
    for projection in ('key', 'value'):
        tensors.extend(t @ state[projection + '.weight'].T for t in tables)
        tensors.append(state[projection + '.bias'])
    tensors.extend([state['latent'], state['half_weight']])
    for i in range(ROUNDS):
        for component in ('norm1', 'query', 'output', 'norm2', 'ff1', 'ff2'):
            tensors.extend([state[f'blocks.{i}.{component}.weight'], state[f'blocks.{i}.{component}.bias']])
    for component in ('final_norm', 'hidden', 'output'):
        tensors.extend([state[component + '.weight'], state[component + '.bias']])
    return np.concatenate([t.detach().numpy().reshape(-1) for t in tensors]).astype(np.float32)
