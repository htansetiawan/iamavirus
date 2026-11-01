#!/usr/bin/env python3
"""Normal-form LP oracle for a persistent opponent-mode game, not local DBR."""
import ctypes,hashlib,itertools,json,subprocess
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/persistent-response-20261101'
PARENT=HERE.parent/'observable-response-search-20261101'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def payoff(p0,p1):
    value=np.zeros((len(p0),len(p1)))
    for a,b in itertools.permutations(range(3),2):
        win=1 if a>b else -1
        after=-p0[:,a,1,0,None]+p0[:,a,1,1,None]*2*win
        check=p1[None,:,b,0,0]*win+p1[None,:,b,0,1]*after
        bet=p1[None,:,b,1,0]+p1[None,:,b,1,1]*2*win
        value+=(p0[:,a,0,0,None]*check+p0[:,a,0,1,None]*bet)/6
    return value
def main():
    OUT.mkdir(parents=True,exist_ok=True);build=HERE/'math-build';build.mkdir(exist_ok=False)
    pins=json.loads((PARENT/'provenance.json').read_text())
    for p in ['cfr.c','cfr.h']:
        source=PARENT/'build/src'/p;assert sha(source)==pins['source_sha256'][str(source.relative_to(ROOT))]
    cmd=['gcc','-O2','-shared','-fPIC','-std=c11','-I'+str(PARENT/'build/src'),'-I'+str(HERE),str(HERE/'test_game.c'),str(PARENT/'build/src/cfr.c'),'-lm','-o',str(build/'game.so')]
    subprocess.run(cmd,check=True);lib=ctypes.CDLL(str(build/'game.so'));dp=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    lib.persistent_kuhn.argtypes=[ctypes.c_double,dp,ctypes.c_int,dp];lib.persistent_trap.argtypes=[ctypes.c_int,ctypes.c_double,ctypes.c_int,ctypes.c_int,dp]
    pure=np.eye(2)[np.array(list(itertools.product(range(2),repeat=6)))].reshape(64,3,2,2)
    rng=np.random.default_rng(2141101);cases=[];traps=[]
    for model in range(3):
        q=np.ascontiguousarray(rng.dirichlet(np.ones(2),6).reshape(3,2,2))
        for p in [0,.25,.75,1]:
            native=np.zeros(41);lib.persistent_kuhn(p,q.ravel(),24000,native)
            x=native[:12].reshape(1,3,2,2);y=native[12:24].reshape(1,3,2,2)
            np.testing.assert_allclose(native[24:36],q.ravel(),atol=0,rtol=0)
            # The opponent chooses ONE whole free strategy, not a local mixture.
            A=p*payoff(pure,q[None])+(1-p)*payoff(pure,pure)
            lp=linprog(np.r_[np.zeros(64),-1],A_ub=np.c_[-A.T,np.ones(64)],b_ub=np.zeros(64),A_eq=np.array([[*np.ones(64),0]]),b_eq=[1],bounds=[(0,None)]*64+[(None,None)],method='highs');assert lp.success
            lower=float((p*payoff(x,q[None])+(1-p)*payoff(x,pure)).min())
            upper=float((p*payoff(pure,q[None])+(1-p)*payoff(pure,y)).max())
            value=float((p*payoff(x,q[None])+(1-p)*payoff(x,y))[0,0])
            assert abs(value-native[36])<1e-10 and abs(value-(p*native[37]+(1-p)*native[38]))<1e-10
            assert lower-1e-9<=lp.x[-1]<=upper+1e-9 and upper-lower<.012,(model,p,lower,upper)
            if p==0:assert abs(lp.x[-1]+1/18)<1e-12
            cases.append(dict(model=model,p=p,q=q.tolist(),value=value,lp_value=float(lp.x[-1]),lower=lower,upper=upper,gap=upper-lower,own=x.tolist(),free=y.tolist()))
    for depth in [1,2,5,10]:
        for local in [0,1]:
            out=np.zeros(5);lib.persistent_trap(depth,.25,local,16000,out)
            expected=1-2*.75**depth if local else -.5
            assert abs(out[3]-expected)<1e-10 and abs(out[2]-max(0,expected))<1e-8,(depth,local,out,expected)
            traps.append(dict(depth=depth,local=bool(local),root=out[:2].tolist(),value=out[2],trap_value=out[3],analytic_trap_value=expected))
    result=dict(lp_cases=cases,trap_cases=traps,scope='Algorithm correctness and an illustrative failure mechanism, not evidence of chess strength.',
                source_sha256={str(p):sha(p) for p in [Path(__file__),HERE/'mode.h',HERE/'test_game.c',PARENT/'build/src/cfr.c',PARENT/'build/src/cfr.h']},command=cmd,
                shared_own_infosets='Explicit construction uses the same own information-set IDs in both latent modes, including the later check-bet response.')
    (OUT/'math-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'lp_cases':len(cases),'max_gap':max(r['gap'] for r in cases),'trap_cases':traps}))
if __name__=='__main__':main()
