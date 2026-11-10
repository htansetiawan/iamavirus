"""Factor a quiet-move residual into a shared board vector and move queries."""
import torch
from torch import nn


def relative_fields(piece, visibility, castle, ep, side):
    squares = torch.arange(64, device=piece.device)
    flip = side[:, None].bool()
    order = squares[None] ^ (56*side[:, None])
    piece = piece.gather(1, order)
    piece = torch.where(flip & (piece != 0), (piece+5)%12+1, piece)
    visibility = visibility.gather(1, order)
    swapped = ((visibility & 1)<<1) | (visibility>>1)
    visibility = torch.where(flip, swapped, visibility)
    return piece, visibility, castle.gather(1,order), ep.gather(1,order)


class CompactQuietPrior(nn.Module):
    """A board accumulator shared by all candidate moves in the same world."""
    def __init__(self, rank=16):
        super().__init__()
        self.rank = rank
        self.piece = nn.Embedding(64*13, rank)
        self.visibility = nn.Embedding(64*4, rank)
        self.castling = nn.Embedding(64, rank)
        self.en_passant = nn.Embedding(65, rank)
        self.halfmove = nn.Linear(1, rank)
        self.source = nn.Embedding(64*13, rank)
        self.target = nn.Embedding(64*13, rank)
        self.promotion = nn.Embedding(5, rank)
        self.move_features = nn.Linear(26, rank, bias=False)
        self.scalar = nn.Linear(26, 1, bias=False)
        for table in (self.piece,self.visibility,self.castling,self.en_passant,self.halfmove):
            nn.init.normal_(table.weight, std=.02)
        nn.init.zeros_(self.halfmove.bias)
        for table in (self.source,self.target,self.promotion,self.move_features,self.scalar):
            nn.init.zeros_(table.weight)

    def forward(self, batch):
        piece, visibility, castle, ep, half, side = batch['board']
        piece, visibility, castle, ep = relative_fields(piece,visibility,castle,ep,side)
        squares = torch.arange(64, device=piece.device)
        ep_index = (ep*(squares+1)).sum(1)
        context = self.piece(13*squares+piece).sum(1)
        context = context + self.visibility(4*squares+visibility).sum(1)
        context = context + castle.to(context.dtype) @ self.castling.weight
        context = context + self.en_passant(ep_index) + self.halfmove(half[:,None].clamp(0,100)/100)
        context = context.clamp(-1,1)
        moves = batch['moves']
        flip = 56*side[:,None]
        source = (moves&63) ^ flip
        target = ((moves>>6)&63) ^ flip
        query = self.source(13*source+piece.gather(1,source))
        query = query + self.target(13*target+piece.gather(1,target))
        query = query + self.promotion(moves>>12) + self.move_features(batch['x'])
        return (query*context[:,None]).sum(-1) + self.scalar(batch['x']).squeeze(-1)


def quiet_kl(teacher, student, quiet):
    """Weighted KL across the legal quiet mass preserved by both models."""
    t = teacher.masked_fill(~quiet,0)
    s = student.masked_fill(~quiet,0)
    return (t.exp()*(t-s)).masked_fill(~quiet,0).sum(-1).mean()
