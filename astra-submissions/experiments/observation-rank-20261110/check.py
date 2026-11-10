"""Independent finite reference and algebra tests; no model/replay input."""
import ctypes
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import random
import struct
import subprocess

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/observation-rank-20261110'
BUILD=HERE/'build'
bits=lambda x:struct.pack('=d',x)


def reference(groups,old,ranking,eligible):
    result=list(old)
    for group in set(groups):
        indices=[i for i,g in enumerate(groups) if g==group and eligible[i]]
        donors=sorted(indices,key=lambda i:(-old[i],i))
        receivers=sorted(indices,key=lambda i:(-ranking[i],i))
        for i,j in zip(receivers,donors):result[i]=old[j]
    return result


def main():
    OUT.mkdir(exist_ok=False);BUILD.mkdir(exist_ok=False)
    cmd=['gcc','-O2','-std=c11','-shared','-fPIC',str(HERE/'rank.c'),'-o',str(BUILD/'rank.so')]
    run=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
    assert run.returncode==0,run.stderr
    lib=ctypes.CDLL(str(BUILD/'rank.so'))
    U=ctypes.c_uint32;D=ctypes.c_double;B=ctypes.c_uint8
    fn=lib.astra_rank_reassign
    fn.argtypes=[ctypes.c_int,ctypes.POINTER(U),ctypes.POINTER(D),ctypes.POINTER(D),ctypes.POINTER(B),ctypes.POINTER(D)]
    fn.restype=ctypes.c_int
    rng=random.Random(2991110);cases=0;values_checked=0;moment_checks=0
    for n in list(range(257))+[rng.randint(1,256) for _ in range(743)]:
        group=[rng.randrange(9) for _ in range(n)]
        old=[-rng.randrange(1,1000)/100. for _ in range(n)]
        score=[rng.uniform(-20,20) for _ in range(n)]
        eligible=[rng.randrange(2) for _ in range(n)]
        if n>3:old[0]=-math.inf;old[1]=0.;old[2]=-0.
        g,o,s,e= (U*n)(*group),(D*n)(*old),(D*n)(*score),(B*n)(*eligible)
        out=(D*n)(*([999.]*n));original=bytes(o)
        assert fn(n,g,o,s,e,out)==0
        expected=reference(group,old,score,eligible)
        assert bytes(out)==b''.join(map(bits,expected))
        assert bytes(o)==original
        for i in range(n):
            if not eligible[i]:assert bits(out[i])==bits(old[i])
        for k in set(group):
            idx=[i for i in range(n) if group[i]==k and eligible[i]]
            assert sorted(bits(old[i]) for i in idx)==sorted(bits(out[i]) for i in idx)
            for tau in (.5,1.,2.,3.):
                a=math.fsum(math.exp(tau*old[i]) for i in idx)
                b=math.fsum(math.exp(tau*out[i]) for i in idx)
                assert math.isclose(a,b,rel_tol=1e-14,abs_tol=1e-14)
                moment_checks+=1
        identity=(D*n)(*old)
        assert fn(n,g,o,identity,e,out)==0 and bytes(out)==original
        assert fn(n,g,o,s,e,o)==0 and bytes(o)==b''.join(map(bits,expected))
        cases+=1;values_checked+=n
    # Mass preservation at temperature1 alone is insufficient at temperature2.
    assert math.isclose(.2+.2,.3+.1)
    assert not math.isclose(.2**2+.2**2,.3**2+.1**2)
    # A merged state's fitted measure is nonlinear; its sum need not survive.
    old_guard=math.sqrt(.8**2)+math.sqrt(.2**2+.2**2)
    new_guard=math.sqrt(.2**2)+math.sqrt(.8**2+.2**2)
    assert not math.isclose(old_guard,new_guard)
    assert math.isclose(.8**2+.2**2+.2**2,.2**2+.8**2+.2**2)
    # Invalid inputs must leave output untouched. Empty input accepts nulls.
    assert fn(0,None,None,None,None,None)==0
    assert fn(-1,None,None,None,None,None)==-1 and fn(257,None,None,None,None,None)==-1
    g=(U*2)(1,1);o=(D*2)(-.1,-.2);s=(D*2)(0,1);e=(B*2)(1,1);out=(D*2)(123,456)
    for bad in (math.nan,math.inf,.1):
        o[1]=bad;assert fn(2,g,o,s,e,out)==-1 and list(out)==[123,456]
    o[1]=-.2;s[0]=math.nan
    assert fn(2,g,o,s,e,out)==-1 and list(out)==[123,456]
    s[0]=0;e[1]=2
    assert fn(2,g,o,s,e,out)==-1 and list(out)==[123,456]
    receipt=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,cases=cases,values_checked=values_checked,
                 powered_mass_checks=moment_checks,temperatures=[.5,1,2,3],invalid_inputs_checked=True,
                 zero_change_identity=True,ineligible_bits_unchanged=True,per_group_multisets_bit_exact=True,
                 aliasing_checked=True,merge_measure_counterexample=True,untempered_only_counterexample=True,
                 source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'rank.c',Path(__file__))},
                 command=cmd,scope='Synthetic C primitive correctness only. Exact observation grouping and native-filter integration are not implemented; no model, replay, posterior or strength test.')
    (OUT/'synthetic-check.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__':main()
