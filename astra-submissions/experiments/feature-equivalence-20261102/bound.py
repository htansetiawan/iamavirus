"""A conditional lower bound on NLL for any scorer of the existing features.

Groups have identical move probability for every f(x), including its legal
normalizer and empirical-history blend. Incoming weights stay fixed. The true
successor probability is therefore a weighted average of fixed group fractions.
It cannot exceed the largest fraction. Independent group weights relax the
real model constraints, so this is an upper bound, not an attainable oracle.
"""
from collections import defaultdict
import numpy as np


def lse(x):
    if not len(x):return -np.inf
    maximum=np.max(x)
    return float(maximum+np.log(np.exp(np.asarray(x)-maximum).sum()))


def partition(row,geometry=False,parent_local=False):
    # Exact byte equality is conservative: -0/+0 are kept separate.
    tokens=[row['x'][i].tobytes()+row['base'][i].tobytes()+
            (row['moves'][i].tobytes() if geometry else b'') for i in range(len(row['base']))]
    offsets=np.r_[0,np.cumsum(np.bincount(row['a_parent'],minlength=len(row['u'])))]
    groups={};normalizers={};ids=np.full(len(tokens),-1,np.int64);members=[]
    for parent,(lo,hi) in enumerate(zip(offsets[:-1],offsets[1:])):
        # The multiset includes every legal move, not only observed-compatible moves.
        # Intern each legal-move multiset once. Rehashing a full A-move tuple
        # for every edge would introduce an avoidable O(P*A*A) grouping pass.
        if parent_local:normalizer_id=parent
        else:
            signature=tuple(sorted(tokens[lo:hi]))
            normalizer_id=normalizers.setdefault(signature,len(normalizers))
        hn=int(row['hn'][parent]);hn=hn if hn>=3 else 0
        for i in range(lo,hi):
            if not row['valid'][i]:continue
            key=(normalizer_id,hn,tokens[i],int(row['counts'][i]) if hn else 0)
            if key not in groups:groups[key]=len(members);members.append([])
            group=groups[key];ids[i]=group;members[group].append(i)
    return ids,[np.array(m,np.int64) for m in members]


def audit(row,geometry=False,parent_local=False):
    ids,members=partition(row,geometry,parent_local);fractions=[];mixed=0;positive_groups=0
    for group in members:
        positives=group[row['positive'][group]]
        if not len(positives):fractions.append(-np.inf);continue
        positive_groups+=1;mixed+=len(positives)<len(group)
        value=(float(np.log(len(positives)/len(group))) if parent_local else
               lse(row['u'][row['a_parent'][positives]].astype(float))-lse(row['u'][row['a_parent'][group]].astype(float)))
        assert value<=1e-12;fractions.append(min(0.,value))
    if not positive_groups:
        return dict(supported=False,groups=len(members),positive_groups=0,mixed_positive_groups=0),ids,members
    ceiling=max(fractions);floor=max(0.,-ceiling)
    return dict(supported=True,groups=len(members),positive_groups=positive_groups,
                mixed_positive_groups=mixed,nll_floor=floor,probability_ceiling=float(np.exp(ceiling))),ids,members


def log_probabilities(row,logits):
    offsets=np.r_[0,np.cumsum(np.bincount(row['a_parent'],minlength=len(row['u'])))]
    logp=np.empty(len(logits),float)
    for i,(lo,hi) in enumerate(zip(offsets[:-1],offsets[1:])):
        values=logits[lo:hi]-lse(logits[lo:hi])
        if row['hn'][i]>=3:
            with np.errstate(divide='ignore'):
                values=np.logaddexp(np.log(row['counts'][lo:hi].astype(float)),np.log(4.)+values)-np.log(row['hn'][i]+4.)
        logp[lo:hi]=values
    edges=row['u'].astype(float)[row['a_parent']]+2*logp
    return lse(edges[row['positive']])-lse(edges[row['valid']]),logp


def uci(move):
    square=lambda i:'abcdefgh'[i%8]+str(i//8+1)
    promo=(int(move)>>12)&7
    return square(int(move)&63)+square((int(move)>>6)&63)+('pnbrqk'[promo] if promo!=6 else '')
