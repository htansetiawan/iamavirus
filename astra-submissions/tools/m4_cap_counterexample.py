#!/usr/bin/env python3
"""Expose the expectation change from keeping old weights after weighted top-k.

Source: Kool et al., ICML 2019, section 4.2, equations 13/14.
https://proceedings.mlr.press/v97/kool19a/kool19a.pdf
This is a probability diagnostic, not evidence of chess strength or a shipped fix.
"""
import argparse
import itertools
import json
from pathlib import Path
import numpy as np


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    w=np.array([.8,.1,.1]);old=np.zeros(3);inclusion=np.zeros(3)
    for i,j in itertools.permutations(range(3),2):
        probability=w[i]*w[j]/(1-w[i]);chosen=[i,j]
        old[chosen]+=probability*w[chosen]/w[chosen].sum();inclusion[chosen]+=probability
    rng=np.random.default_rng(192);trials=200000;totals=np.zeros((3,3));squares=np.zeros((3,3))
    for _ in range(trials//10000):
        # Same exponential race as belief.c: smallest log(E_i)-log(w_i).
        key=np.log(-np.log(rng.random((10000,3))))-np.log(w)
        order=np.argsort(key,axis=1);selected=order[:,:2];threshold=np.take_along_axis(key,order[:,2:],axis=1)
        inclusion_given_threshold=-np.expm1(-np.exp(np.log(w)+threshold))
        keep=np.zeros_like(key,dtype=bool);np.put_along_axis(keep,selected,True,axis=1)
        naive=w*keep;naive/=naive.sum(1,keepdims=True)
        corrected=w*keep/inclusion_given_threshold
        normalized=corrected/corrected.sum(1,keepdims=True)
        for i,x in enumerate([naive,corrected,normalized]):totals[i]+=x.sum(0);squares[i]+=(x*x).sum(0)
    means=totals/trials;se=np.sqrt(np.maximum(squares/trials-means*means,0)/trials)
    assert np.max(abs(means[0]-old))<6*max(se[0])
    assert np.max(abs(means[1]-w))<6*max(se[1])
    report=dict(weights=w.tolist(),cap=2,exact_inclusion=inclusion.tolist(),
        exact_old_normalized_expectation=old.tolist(),trials=trials,
        estimators={name:dict(mean=means[i].tolist(),standard_error=se[i].tolist())
                    for i,name in enumerate(['old_retained_weights','threshold_corrected_unnormalized','threshold_corrected_normalized'])},
        source='https://proceedings.mlr.press/v97/kool19a/kool19a.pdf',
        limitation='Unnormalized importance estimates are unbiased; normalizing is a ratio estimate and remains biased at finite sample size. This three-world example does not prove the cause of the replay regressions.')
    args.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
