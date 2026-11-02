"""Teacher and CPU-oriented student share only permitted per-world features."""
import torch
from torch import nn


class Teacher(nn.Module):
    def __init__(self):
        super().__init__();d=128
        self.piece=nn.Embedding(13,d);self.vision=nn.Embedding(4,d)
        self.castle=nn.Embedding(2,d);self.ep=nn.Embedding(2,d);self.square=nn.Embedding(64,d)
        self.global_token=nn.Parameter(torch.zeros(1,1,d));self.half_projection=nn.Linear(1,d)
        layer=nn.TransformerEncoderLayer(d,4,512,dropout=.1,activation='gelu',batch_first=True,norm_first=True)
        self.transformer=nn.TransformerEncoder(layer,4,enable_nested_tensor=False)
        self.head=nn.Sequential(nn.LayerNorm(d),nn.Linear(d,1))

    def forward(self,x,half):
        z=self.piece(x[:,:,0])+self.vision(x[:,:,1]+2*x[:,:,2])+self.castle(x[:,:,3])+self.ep(x[:,:,4])
        z=z+self.square(torch.arange(64,device=x.device))[None,:,:]
        global_=self.global_token.expand(len(x),-1,-1)+self.half_projection(half[:,None,None]/100)
        z=self.transformer(torch.cat([global_,z],dim=1))
        return self.head(z[:,0]).squeeze(-1)


class Student(nn.Module):
    def __init__(self):
        super().__init__();d=128
        self.piece=nn.Embedding(64*13,d);self.vision=nn.Embedding(64*4,d)
        self.castle=nn.Embedding(64,d);self.ep=nn.Embedding(64,d)
        self.bias=nn.Parameter(torch.zeros(d));self.half_weight=nn.Parameter(torch.zeros(d))
        self.hidden=nn.Linear(d,32);self.output=nn.Linear(32,1)
        for e in (self.piece,self.vision,self.castle,self.ep):nn.init.normal_(e.weight,std=.02)

    def forward(self,x,half):
        sq=torch.arange(64,device=x.device)[None,:]
        z=self.piece(13*sq+x[:,:,0])+self.vision(4*sq+x[:,:,1]+2*x[:,:,2])
        z=z+self.castle(sq)*x[:,:,3,None]+self.ep(sq)*x[:,:,4,None]
        z=z.sum(dim=1)+self.bias+(half[:,None]/100)*self.half_weight
        z=torch.clamp(z,0,1)
        return self.output(torch.clamp(self.hidden(z),0,1)).squeeze(-1)
