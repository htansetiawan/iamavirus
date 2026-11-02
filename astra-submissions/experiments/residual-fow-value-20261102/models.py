"""A bounded residual in log odds, conditional on board and SF certainty.

z = frozen calibrated SF logit
r = 2*tanh((a(board) + b(board)*clip(z/4,-1,1))/2)
prediction = sigmoid(z+r)

Zero output initialization exactly preserves the calibrated baseline. This
does not equal the arena's uncalibrated leaf map; a later policy experiment
would need a separate calibration-only control and untouched terminal values.
"""
import numpy as np
import torch
from torch import nn
from common import OLD, QUERY, module

flat = module('original_flat_model', OLD/'models.py')
query = module('original_query_model', QUERY/'models.py')


def combine(heads, z):
    adjustment=heads[:,0]+heads[:,1]*torch.clamp(z/4,-1,1)
    return z+2*torch.tanh(adjustment/2)


class FlatResidual(flat.Student):
    def __init__(self):
        super().__init__()
        self.output=nn.Linear(32,2)
        nn.init.zeros_(self.output.weight);nn.init.zeros_(self.output.bias)
    def forward(self,x,half,z):
        return combine(super().forward(x,half),z)


class QueryResidual(query.QueryStudent):
    def __init__(self):
        super().__init__()
        self.output=nn.Linear(64,2)
        nn.init.zeros_(self.output.weight);nn.init.zeros_(self.output.bias)
    def forward(self,x,half,z):
        return combine(super().forward(x,half),z)


def pack(model, kind):
    if kind=='query':return query.pack_native(model)
    state=model.cpu().eval().state_dict()
    order=('piece.weight','vision.weight','castle.weight','ep.weight','bias','half_weight',
           'hidden.weight','hidden.bias','output.weight','output.bias')
    return np.concatenate([state[k].numpy().reshape(-1) for k in order]).astype(np.float32)
