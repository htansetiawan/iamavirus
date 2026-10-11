"""Experimental inference adapter: current-event GRU state for belief only.

Policy, danger, value and the persisted recurrent state retain full history.
The belief branch still sees explicit last-seen/age features. This is neither
a memoryless policy nor a retrained model, and has not passed a playing gate.
"""
import torch
from torch import nn
from torch.nn import functional as F


class CurrentEventBelief(nn.Module):
    def __init__(self, base):
        super().__init__()
        if getattr(base,'bottleneck',None) is not None:
            raise ValueError('compressed latent projection is not a spatial-map projection')
        self.base=base

    def initial_hidden(self,batch,device=None):
        return self.base.initial_hidden(batch,device)

    def observe(self,planes,scalars,hidden):
        next_hidden,spatial,_,value=self.base.observe(planes,scalars,hidden)
        encoded=torch.cat([spatial.flatten(1),scalars],dim=1)
        if encoded.shape[1]!=self.base.project.in_features:
            raise ValueError('unsupported encoder/projection contract')
        current=self.base.gru(F.relu(self.base.project(encoded)),self.initial_hidden(planes.shape[0],planes.device))
        squares=spatial.flatten(2).transpose(1,2)
        local=current.unsqueeze(1).expand(-1,64,-1)
        belief=self.base.belief2(F.relu(self.base.belief1(torch.cat([squares,local],dim=2))))
        return next_hidden,spatial,belief,value

    def score(self,*args):
        return self.base.score(*args)
