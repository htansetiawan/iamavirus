"""Fused quadratic logit residual without a per-action quadratic feature matrix."""
import numpy as np
import torch
from settings import logsum

CONTINUOUS=(1,12,14,21,23,24)


def mask_array():
    mask=np.triu(np.ones((26,26)),1)
    for i in CONTINUOUS:mask[i,i]=1
    return mask


class Residual(torch.nn.Module):
    def __init__(self,kind,device):
        super().__init__();self.kind=kind
        self.linear=torch.nn.Parameter(torch.zeros(26,dtype=torch.float64,device=device))
        self.q=torch.nn.Parameter(torch.zeros((26,26),dtype=torch.float64,device=device),requires_grad=kind=='quadratic')
        self.register_buffer('mask',torch.tensor(mask_array(),dtype=torch.float64,device=device))

    def forward(self,x):
        result=x@self.linear
        if self.kind=='quadratic':result=result+((x@(self.q*self.mask))*x).sum(1)
        return result

    def penalty(self):return self.linear.square().sum()+(self.q*self.mask).square().sum()

    def coefficients(self):
        return dict(linear=self.linear.detach().cpu().tolist(),quadratic=(self.q*self.mask).detach().cpu().tolist())


def probabilities(data,model):
    z=data.base+model(data.x)
    logp=z-logsum(z,data.a_parent,data.parents)[data.a_parent]
    hn=data.hn[data.a_parent]
    logh=torch.where(data.counts>0,data.counts.clamp_min(1).log(),torch.full_like(data.counts,-torch.inf))
    mixed=torch.logaddexp(logh,logp+np.log(4.))-(hn+4).log()
    logp=torch.where(hn>=3,mixed,logp)
    edge=data.u[data.a_parent]+2*logp
    posterior=logsum(edge,data.a_case,data.n,data.positive)-logsum(edge,data.a_case,data.n,data.valid)
    actor=logsum(data.u[data.a_parent]+logp,data.a_case,data.n,data.actor_edge)-logsum(data.u,data.p_case,data.n,data.actor_parent)
    return posterior,actor


def values(data,model,floor):
    with torch.no_grad():values=[v.cpu().numpy() for v in probabilities(data,model)]
    for i,r in enumerate(data.meta):
        if not r['natural_support']:
            for v in values:v[i]=np.log(floor)
    return tuple(np.clip(v,np.log(floor),0) for v in values)
