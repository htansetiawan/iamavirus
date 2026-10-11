#!/usr/bin/env python3
"""Native/Python probability parity over the complete validation feature corpus."""
import argparse
import ctypes
import json
from pathlib import Path
import numpy as np
from m4_intent_prior import groups,probabilities
from m4_prior_fit import load,sha


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,required=True)
    ap.add_argument('--model',type=Path,required=True);ap.add_argument('--library',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    m=json.loads(args.model.read_text());manifest=json.loads((args.data/'manifest.json').read_text())
    hashes=json.loads((args.data/'features.json').read_text())
    assert sha(args.data/'validation.bin')==hashes['validation']['sha256']
    d=load(args.data/'validation.bin',manifest['games']['validation']);base=np.array(m['base_theta'])
    g=groups(d,base);theta=np.array(m['gate_theta']);want=probabilities(g,theta)
    lib=ctypes.CDLL(str(args.library.resolve()));fn=lib.m4_intent_scores
    ptr=ctypes.POINTER(ctypes.c_float);fn.argtypes=[ctypes.c_int,ptr,ptr,ptr,ptr];fn.restype=ctypes.c_int
    def pointer(a):return a.ctypes.data_as(ptr)
    b=base.astype('float32');gamma=theta.astype('float32');zero=np.zeros(7,dtype='float32')
    worst=0.;actions=0
    for start,n in zip(d['starts'],d['counts']):
        X=np.ascontiguousarray(d['X'][start:start+n,:26],dtype='float32');out=np.empty(n,dtype='float32')
        for weights,target in [(zero,g['base_p']),(gamma,want)]:
            assert fn(int(n),pointer(X),pointer(b),pointer(weights),pointer(out))==1
            z=out.astype(float);e=np.exp(z-z.max());p=e/e.sum()
            error=float(np.max(np.abs(np.log(p)-np.log(target[start:start+n]))));worst=max(worst,error)
            assert error<1e-5,(int(start),error)
        actions+=int(n)
    assert fn(0,pointer(X),pointer(b),pointer(gamma),pointer(out))==0
    assert fn(257,pointer(X),pointer(b),pointer(gamma),pointer(out))==0
    result={'positions':len(d['starts']),'actions':actions,'arms':['zero','trained'],
            'max_absolute_log_probability_error':worst,'tolerance':1e-5,
            'library_sha256':sha(args.library),'model_sha256':sha(args.model),
            'validation_sha256':hashes['validation']['sha256']}
    args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
