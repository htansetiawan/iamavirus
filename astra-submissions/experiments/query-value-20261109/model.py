"""Relational compression: 64 square tokens -> eight latent queries -> value."""
import torch
from torch import nn


class QueryValue(nn.Module):
    def __init__(self):
        super().__init__();d=64
        self.piece=nn.Embedding(13,d);self.vision=nn.Embedding(4,d)
        self.castle=nn.Embedding(2,d);self.ep=nn.Embedding(2,d);self.square=nn.Embedding(64,d)
        self.queries=nn.Parameter(torch.randn(1,8,d)*.02)
        self.half_projection=nn.Linear(1,d)
        self.token_norm=nn.LayerNorm(d);self.query_norm=nn.LayerNorm(d)
        self.cross=nn.MultiheadAttention(d,4,dropout=.05,batch_first=True)
        self.cross_ff=nn.Sequential(nn.LayerNorm(d),nn.Linear(d,128),nn.GELU(),nn.Linear(128,d))
        self.latent=nn.TransformerEncoderLayer(d,4,128,dropout=.05,activation='gelu',batch_first=True,norm_first=True)
        self.head=nn.Sequential(nn.LayerNorm(d),nn.Linear(d,1))

    def forward(self,x,half):
        tokens=self.piece(x[:,:,0])+self.vision(x[:,:,1]+2*x[:,:,2])+self.castle(x[:,:,3])+self.ep(x[:,:,4])
        tokens=self.token_norm(tokens+self.square(torch.arange(64,device=x.device))[None,:,:])
        q=self.queries.expand(x.shape[0],-1,-1)+self.half_projection(half[:,None,None]/100)
        q=q+self.cross(self.query_norm(q),tokens,tokens,need_weights=False)[0]
        q=q+self.cross_ff(q);q=self.latent(q)
        return self.head(q[:,0]).squeeze(-1)
