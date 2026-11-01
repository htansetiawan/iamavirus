#!/usr/bin/env python3
import ctypes
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy.optimize import linprog

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'stable-mix-20261101/build/base'
OUT=HERE.parents[2]/'astra-submissions/analysis/data-biased-search-20261101'


def library(name, src, flag):
    path=HERE/'build'/name
    command=['gcc','-O2','-shared','-fPIC','-std=c11',*flag,'-I'+str(src),str(HERE/'test_matrix.c'),str(src/'cfr.c'),'-lm','-o',str(path)]
    subprocess.run(command,check=True)
    lib=ctypes.CDLL(str(path));dp=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    lib.matrix_solve.argtypes=[dp,ctypes.c_int,ctypes.c_int,ctypes.c_double,dp,ctypes.c_int,dp]
    lib.matrix_solve.restype=ctypes.c_int;lib.grow_test.restype=ctypes.c_int
    lib.growth_trace.argtypes=[dp];lib.growth_trace.restype=ctypes.c_int
    return lib


def solve(lib,A,p,q,iters):
    r,c=A.shape[1:];out=np.zeros(5*(r+c)+3)
    n=lib.matrix_solve(np.ascontiguousarray(A),r,c,p,np.ascontiguousarray(q),iters,out)
    assert n==len(out)
    return out


def main():
    OUT.mkdir(exist_ok=True)
    original=library('base-cfr.so',BASE/'src',[])
    patched=library('dbr-cfr.so',HERE/'build/src',['-DRESTRICTED'])
    assert original.grow_test()==patched.grow_test()==1
    a=np.zeros(5000);b=np.zeros(5000)
    grown=original.growth_trace(a)
    assert patched.growth_trace(b)==grown and np.array_equal(a,b)
    rng=np.random.default_rng(2071101);max_gap=0;cases=0;off_checks=0;oracle_checks=0
    for seed in range(12):
        A=rng.uniform(-1,1,(2,3,4));q=rng.dirichlet(np.ones(4));mean=.3*A[0]+.7*A[1]
        for iters in [0,1,5,100]:
            x=solve(original,A,0,q,iters);y=solve(patched,A,0,q,iters)
            assert np.array_equal(x,y),(seed,iters,np.max(abs(x-y)))
            off_checks+=1
        for confidence in [0,.25,.5,.9,1.]:
            transformed=(1-confidence)*A+confidence*(A@q)[:,:,None]
            # An independent explicit chance at each column choice has this payoff matrix.
            for iters in [1,5,100]:
                a=solve(original,transformed,0,q,iters);b=solve(patched,A,confidence,q,iters)
                np.testing.assert_allclose(a[:3],b[:3],atol=2e-10,rtol=2e-10)
                np.testing.assert_allclose((1-confidence)*a[3:7]+confidence*q,b[3:7],atol=2e-10,rtol=2e-10)
                assert abs(a[7]-b[7])<2e-10
                oracle_checks+=1
            b=solve(patched,A,confidence,q,6000)
            B=(1-confidence)*mean+confidence*(mean@q)[:,None]
            # max_x min_j x^T B[:,j], solved independently by LP.
            lp=linprog(np.r_[np.zeros(3),-1],A_ub=np.c_[-B.T,np.ones(4)],b_ub=np.zeros(4),
                       A_eq=np.array([[1,1,1,0]]),b_eq=[1],bounds=[(0,None)]*3+[(None,None)],method='highs')
            assert lp.success
            value=lp.x[-1];gap=value-np.min(b[:3]@B);max_gap=max(max_gap,gap)
            assert gap < .003,(seed,confidence,gap)
            # Original-game best responses remain unrestricted diagnostics.
            assert abs(b[8]-max(mean@b[3:7]))<1e-9
            assert abs(b[9]+min(b[:3]@mean))<1e-9
            cases+=1
    result={'normal_form_lp_cases':cases,'zero_confidence_bit_identical_checks':off_checks,
            'explicit_chance_iteration_checks':oracle_checks,'max_row_value_gap_vs_lp':max_gap,
            'tree_growth_and_zero_iteration_average':'pass'}
    result['zero_confidence_growth_array_values_identical']=grown
    (OUT/'numeric-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
