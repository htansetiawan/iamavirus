"""Action distributions over actor-visible inputs only."""
import torch
from torch import nn
import torch.nn.functional as F


def move_parts(moves):
    return moves & 63, (moves >> 6) & 63, (moves >> 12) & 7


def geometry(fr, to):
    fx, fy, tx, ty = fr%8, fr//8, to%8, to//8
    dx, dy = tx-fx, ty-fy
    return torch.stack([fx/7, fy/7, tx/7, ty/7, dx/7, dy/7,
                        torch.maximum(dx.abs(), dy.abs())/7,
                        (abs(tx-3.5)+abs(ty-3.5))/7], -1)


class LinearPolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.source = nn.Embedding(6*64, 1); self.destination = nn.Embedding(6*64, 1)
        self.target = nn.Embedding(14, 1); self.promotion = nn.Embedding(5, 1)
        self.geometry = nn.Linear(8, 1, bias=False)
        for p in self.parameters(): nn.init.zeros_(p)

    def forward(self, tokens, moves):
        fr, to, pr = move_parts(moves)
        piece = tokens.gather(1, fr).clamp(0, 5)
        target = tokens.gather(1, to)
        return (self.source(piece*64+fr)+self.destination(piece*64+to)
                +self.target(target)+self.promotion(pr)+self.geometry(geometry(fr, to))).squeeze(-1)


class StudentPolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.board = nn.Sequential(nn.Linear(64*14, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU())
        self.action = nn.Sequential(nn.Linear(64+14+14+8+5, 64), nn.ReLU(), nn.Linear(64, 1))

    def forward(self, tokens, moves):
        fr, to, pr = move_parts(moves)
        one = F.one_hot(tokens, 14).float()
        context = self.board(one.flatten(1))
        src = one.gather(1, fr[..., None].expand(-1, -1, 14))
        dst = one.gather(1, to[..., None].expand(-1, -1, 14))
        x = torch.cat([context[:, None].expand(-1, moves.shape[1], -1), src, dst,
                       geometry(fr, to), F.one_hot(pr, 5).float()], -1)
        return self.action(x).squeeze(-1)


class TeacherPolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = nn.Embedding(14, 128)
        self.position = nn.Parameter(torch.randn(1, 64, 128)*.02)
        self.layers = nn.ModuleList([nn.TransformerEncoderLayer(128, 4, 256, .1, batch_first=True, norm_first=True)
                                     for _ in range(2)])
        self.norm = nn.LayerNorm(128)
        self.action = nn.Sequential(nn.Linear(3*128+8+5, 64), nn.ReLU(), nn.Linear(64, 1))

    def forward(self, tokens, moves):
        fr, to, pr = move_parts(moves)
        x = self.embedding(tokens)+self.position
        for layer in self.layers: x = layer(x)
        x = self.norm(x)
        src = x.gather(1, fr[..., None].expand(-1, -1, 128))
        dst = x.gather(1, to[..., None].expand(-1, -1, 128))
        joined = torch.cat([x.mean(1)[:, None].expand(-1, moves.shape[1], -1), src, dst,
                            geometry(fr, to), F.one_hot(pr, 5).float()], -1)
        return self.action(joined).squeeze(-1)


def masked_log_probs(logits, mask, temperature=1.):
    return F.log_softmax((logits/temperature).masked_fill(~mask, -1e9), -1)
