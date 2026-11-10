"""Batch-local input decoding, without stored targets or outcome metadata."""
import sys
from pathlib import Path

import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'astra-submissions/experiments/world-quiet-attention-20261110'))
from data import CONTEXT,FRAME,PriorCache,Cache


class Inputs:
    def __init__(self,fit_plan):
        self.prior=PriorCache(fit_plan['feature_cache']);self.world=Cache(fit_plan['state_cache'])
        self.context=np.frombuffer(self.prior.contexts,dtype=CONTEXT)
        self.frames=np.frombuffer(self.world.data,dtype=FRAME)
        train=set(fit_plan['split']['train'])
        # Game identity serves only to reproduce the already frozen fit split.
        self.indices=np.asarray([i for i,r in enumerate(self.context) if self.world.games[int(r['game'])]['game'] in train],dtype=np.int64)

    def batch(self,indices,device='cpu',width=None):
        selected=self.context[indices];source=self.frames[selected['record']]
        count=selected['count'].astype(np.int64)
        if width is None:width=self.prior.manifest['max_width']
        assert width>=int(count.max())
        valid=np.arange(width)[None]<count[:,None]
        positions=selected['start'].astype(np.int64)[:,None]+np.minimum(np.arange(width)[None],count[:,None]-1)
        rows=self.prior.rows[positions];n=len(indices)
        piece=np.empty((n,64),np.int64)
        piece[:,0::2]=source['board']&15;piece[:,1::2]=source['board']>>4
        squares=np.arange(64,dtype=np.uint64)
        visibility=((source['white'][:,None]>>squares)&1)|(((source['black'][:,None]>>squares)&1)<<1)
        board=[piece,visibility.astype(np.int64),((source['castle'][:,None]>>squares)&1).astype(np.int64),
            (source['ep'][:,None]==np.arange(64)[None]).astype(np.int64),
            source['half'].astype(np.float32),source['side'].astype(np.int64)]
        tensor=lambda v:torch.from_numpy(np.ascontiguousarray(v)).to(device)
        batch=dict(board=[tensor(v) for v in board],x=tensor(np.array(rows['x'])),moves=tensor(rows['move'].astype(np.int64)),
            base=tensor(np.array(rows['base'][:,:,1])),counts=tensor(rows['history'].astype(np.float32)),
            valid=tensor(valid),capture=tensor(rows['x'][:,:,0]>0),history_n=tensor(selected['total'].astype(np.float32)))
        return batch,positions[valid]


def move_to(batch,device=None,dtype=None):
    def convert(t):
        t=t.to(device) if device is not None else t
        return t.to(dtype) if dtype is not None and t.is_floating_point() else t
    return {key:[convert(t) for t in value] if key=='board' else convert(value) for key,value in batch.items()}
