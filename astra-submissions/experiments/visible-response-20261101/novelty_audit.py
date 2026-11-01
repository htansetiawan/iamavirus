#!/usr/bin/env python3
"""Input-only novelty audit; never reads targets or prediction scores."""
import hashlib
import json
from pathlib import Path

import numpy as np

import data


def keys(split):
    raw = np.load(data.BUILD/(split+'.npz'))
    tokens, actions, offsets = raw['tokens'], raw['actions'], raw['offsets']
    result=[]
    for i, view in enumerate(tokens):
        legal=np.sort(actions[int(offsets[i]):int(offsets[i+1])])
        result.append(hashlib.sha256(view.tobytes()+legal.astype('<u2').tobytes()).digest())
    return result,raw['ply']


def main():
    train,_=keys('train'); seen=set(train)
    result=dict(scope='Exact current-view plus legal-set overlap, independent of outcomes and targets.',
                train_decisions=len(train),train_distinct_inputs=len(seen),splits={})
    for split in ['validation','test']:
        values,plies=keys(split); novel=np.array([x not in seen for x in values])
        after=plies//2+1>8
        result['splits'][split]=dict(decisions=len(values),novel=int(novel.sum()),
                                     post8=int(after.sum()),novel_post8=int((novel&after).sum()))
        np.save(data.BUILD/(split+'-novel.npy'),novel)
    (data.OUT/'input-novelty.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
