"""Independent two-pass conditional-value oracle and fixed-tree solver parity."""
import ctypes as C
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / 'astra-submissions/analysis/value-expansion-20261102'


class Node(C.Structure):
    _fields_ = [(k, C.c_int) for k in ('type','player','infoset','first','count')] + [('value',C.c_double)]


class Game(C.Structure):
    _fields_ = [('nodes',C.POINTER(Node)),('n_nodes',C.c_int),('cap_nodes',C.c_int),
        ('child',C.POINTER(C.c_int)),('prob',C.POINTER(C.c_double)),('n_edges',C.c_int),('cap_edges',C.c_int),
        ('is_player',C.POINTER(C.c_int)),('is_actions',C.POINTER(C.c_int)),('is_offset',C.POINTER(C.c_int)),
        ('n_infosets',C.c_int),('cap_infosets',C.c_int),('n_slots',C.c_int),('finalized_slots',C.c_int),
        *[(k,C.POINTER(C.c_double)) for k in ('regret','last','strategy','strategy_sum')],
        ('root',C.c_int),('pending',C.POINTER(C.c_int)),('n_pending',C.c_int),('cap_pending',C.c_int)]


class Values(C.Structure):
    _fields_ = [(k,C.POINTER(C.c_double)) for k in ('q','mass','own')] + [
        ('seen',C.POINTER(C.c_ubyte)),('recall_bad',C.POINTER(C.c_ubyte)),
        *[(k,C.c_int) for k in ('slots','infosets','cap_slots','cap_infosets')],
        *[(k,C.c_uint64) for k in ('nodes','refreshes','recall_failures')],('root_value',C.c_double)]


class Moment(C.Structure):
    _fields_ = [('mean',C.c_double),('m2',C.c_double),('count',C.c_uint64)]


def oracle(g, x):
    # First evaluate every subtree, without reach factors or infoset aggregation.
    values = {}
    def evaluate(i):
        n=g.nodes[i]
        if n.type==2: value=n.value
        else:
            value=sum((g.prob[n.first+a] if n.type==0 else x[g.is_offset[n.infoset]+a])*
                      evaluate(g.child[n.first+a]) for a in range(n.count))
        values[i]=value; return value
    root=evaluate(g.root)
    terms=[[] for _ in range(g.n_slots)]; masses=[[] for _ in range(g.n_infosets)]
    own=[[] for _ in range(g.n_infosets)]
    def paths(i, reach):
        n=g.nodes[i]
        if n.type==2:return
        if n.type==1:
            I=n.infoset;o=g.is_offset[I];mass=reach[2]*reach[n.player^1]
            masses[I].append(mass);own[I].append(reach[n.player])
            for a in range(n.count):terms[o+a].append(mass*(1 if n.player==0 else -1)*values[g.child[n.first+a]])
        for a in range(n.count):
            rr=list(reach);actor=2 if n.type==0 else n.player
            rr[actor]*=g.prob[n.first+a] if n.type==0 else x[g.is_offset[n.infoset]+a]
            paths(g.child[n.first+a],rr)
    paths(g.root,[1.,1.,1.])
    mass=[math.fsum(m) for m in masses];q=[0.]*g.n_slots
    bad=[bool(v and max(v)-min(v)>1e-12) for v in own]
    for I in range(g.n_infosets):
        for a in range(g.is_actions[I]):
            j=g.is_offset[I]+a;q[j]=math.fsum(terms[j])/(mass[I] if mass[I]>0 and not bad[I] else 1)
    return root,q,mass,bad


def state_digest(g):
    h=hashlib.sha256()
    for name in ('regret','last','strategy','strategy_sum'):
        h.update(C.string_at(getattr(g,name),8*g.n_slots))
    h.update(C.string_at(g.nodes,C.sizeof(Node)*g.n_nodes))
    return h.hexdigest()


def main():
    path=HERE/'build/values.so'
    subprocess.run(['gcc','-std=c11','-O2','-shared','-fPIC','-I'+str(HERE/'build/base/src'),
        str(HERE/'build/base/src/cfr.c'),str(HERE/'expansion_values.c'),str(HERE/'test_bridge.c'),'-lm','-o',str(path)],check=True)
    lib=C.CDLL(str(path));G=C.POINTER(Game);V=C.POINTER(Values);D=C.POINTER(C.c_double)
    lib.fixture.argtypes=[C.c_int,C.c_int];lib.fixture.restype=G
    lib.wide_fixture.restype=G;lib.new_values.restype=V
    lib.drop_fixture.argtypes=[G];lib.drop_values.argtypes=[V];lib.grow_fixture.argtypes=[G]
    lib.expansion_values_refresh.argtypes=[V,G,D]
    lib.expansion_values_available.argtypes=[V,C.c_int,C.c_int,C.c_int]
    lib.pcfr_current.argtypes=[G,D];lib.pcfr_iteration.argtypes=[G,C.c_int]
    lib.expansion_moment_init.argtypes=[C.POINTER(Moment)];lib.expansion_moment_add.argtypes=[C.POINTER(Moment),C.c_double]
    lib.expansion_score.argtypes=[C.c_double,C.POINTER(Moment),C.c_uint64,C.c_uint64];lib.expansion_score.restype=C.c_double
    rng=random.Random(2341102);worst=0.;checks=0;zero_mass=0;recall_bad=0
    for seed in range(80):
        g=lib.fixture(seed,int(seed%10==0));v=lib.new_values()
        for trial in range(8):
            if trial==4:lib.grow_fixture(g)
            x=(C.c_double*g.contents.n_slots)()
            for I in range(g.contents.n_infosets):
                n=g.contents.is_actions[I];p=[rng.random() for _ in range(n)]
                if trial%3==0:p[rng.randrange(n)]=0
                z=sum(p)
                for a in range(n):x[g.contents.is_offset[I]+a]=p[a]/z
            before=state_digest(g.contents);lib.expansion_values_refresh(v,g,x);assert before==state_digest(g.contents)
            root,q,mass,bad=oracle(g.contents,x)
            for left,right in [(root,v.contents.root_value),*zip(q,v.contents.q[:len(q)]),*zip(mass,v.contents.mass[:len(mass)])]:
                worst=max(worst,abs(left-right));assert abs(left-right)<1e-12,(seed,trial,left,right)
            for I in range(len(mass)):
                assert bool(v.contents.recall_bad[I])==bad[I]
                available=lib.expansion_values_available(v,I,g.contents.is_offset[I],g.contents.is_actions[I])
                assert bool(available)==(mass[I]>0 and not bad[I])
                zero_mass+=mass[I]==0;recall_bad+=bad[I]
            checks+=1
        lib.drop_values(v);lib.drop_fixture(g)
    # More than the solver's small stack buffer, and player-1 value sign.
    g=lib.wide_fixture();v=lib.new_values();x=(C.c_double*257)(*([1/257]*257))
    lib.expansion_values_refresh(v,g,x)
    for a in range(257):assert abs(v.contents.q[a]+(a-128)/128)<1e-14
    lib.drop_values(v);lib.drop_fixture(g)
    # Reader never changes solver evolution, including growing arrays.
    parity=0
    for seed in range(8):
        a=lib.fixture(seed,0);b=lib.fixture(seed,0);v=lib.new_values()
        for it in range(1,151):
            if it==75:lib.grow_fixture(a);lib.grow_fixture(b)
            lib.pcfr_iteration(a,it);lib.pcfr_iteration(b,it)
            x=(C.c_double*b.contents.n_slots)();lib.pcfr_current(b,x);lib.expansion_values_refresh(v,b,x)
            for name in ('regret','last','strategy','strategy_sum'):
                assert C.string_at(getattr(a.contents,name),a.contents.n_slots*8)==C.string_at(getattr(b.contents,name),b.contents.n_slots*8)
            parity+=1
        lib.drop_fixture(a);lib.drop_fixture(b);lib.drop_values(v)
    moment=Moment();lib.expansion_moment_init(C.byref(moment));values=[-1.,1.]
    for t in range(500):
        q=rng.uniform(-2,1);n=rng.randrange(1000);chosen=rng.randrange(n+1)
        mean=math.fsum(values)/len(values);variance=math.fsum((z-mean)**2 for z in values)/len(values)
        expected=q+variance*math.sqrt(n)/(1+chosen)
        assert abs(expected-lib.expansion_score(q,C.byref(moment),n,chosen))<1e-12
        lib.expansion_moment_add(C.byref(moment),q);values.append(q)
    result={'conditional_value_oracle_cases':checks,'maximum_error':worst,'zero_mass_infosets':zero_mass,
        'invalid_recall_infosets_rejected':recall_bad,'wide_actions':257,'solver_iteration_byte_parity':parity,
        'moment_score_checks':500,'scope':'Correctness only; no strength or throughput inference.'}
    (OUT/'value-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
