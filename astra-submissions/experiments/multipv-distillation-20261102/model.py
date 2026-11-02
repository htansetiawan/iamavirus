"""Encode each hypothesized parent once, then query all scored moves."""
import torch
from torch import nn


class MultiPVStudent(nn.Module):
    def __init__(self):
        super().__init__()
        self.piece = nn.Embedding(64*13,128)
        self.castle = nn.Embedding(64,128)
        self.ep = nn.Embedding(65,128)
        self.bias = nn.Parameter(torch.zeros(128))
        self.half_weight = nn.Parameter(torch.zeros(128))
        self.parent = nn.Linear(128,64)
        self.src = nn.Embedding(64,16)
        self.dst = nn.Embedding(64,16)
        self.promo = nn.Embedding(5,8)
        self.mover = nn.Embedding(13,8)
        self.victim = nn.Embedding(13,8)
        self.head = nn.Linear(120,32)
        self.output = nn.Linear(32,1)
        self.base = nn.Linear(64,1)
        for e in (self.piece,self.castle,self.ep):
            nn.init.normal_(e.weight,std=.02)

    def forward(self,piece,castle,ep,half,actions):
        sq = torch.arange(64,device=piece.device)[None,:]
        z = (self.piece(13*sq+piece)+self.castle(sq)*castle[:,:,None]).sum(1)
        z = z+self.ep(ep)+self.bias+half[:,None]/100*self.half_weight
        parent = torch.clamp(self.parent(torch.clamp(z,0,1)),0,1)
        src,dst,promo = actions.unbind(-1)
        a = torch.cat([parent[:,None,:].expand(-1,actions.shape[1],-1),self.src(src),self.dst(dst),
                       self.promo(promo),self.mover(piece.gather(1,src)),self.victim(piece.gather(1,dst))],-1)
        return torch.tanh(self.base(parent)+self.output(torch.relu(self.head(a))).squeeze(-1))
