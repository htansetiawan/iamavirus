"""Verify native selection by independent inclusion and mass identities."""
import ctypes as ct
import math
from pathlib import Path
import random
import subprocess
import tempfile
import unittest


class FiniteResampleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='m4-finite-test-')
        src=Path(__file__).with_name('m4_finite_resample.c')
        library=Path(cls.tmp.name)/'finite.so'
        subprocess.run(['cc','-O2','-std=c11','-Wall','-Wextra','-Wpedantic',
                        '-shared','-fPIC',str(src),'-lm','-o',str(library)],check=True)
        cls.lib=ct.CDLL(str(library));cls.fn=cls.lib.m4_finite_resample
        cls.fn.argtypes=[ct.POINTER(ct.c_float),ct.c_size_t,ct.c_size_t,ct.c_double,
                         ct.POINTER(ct.c_uint32),ct.POINTER(ct.c_float)]
        cls.fn.restype=ct.c_int

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def run_case(self,logw,k,u):
        a=(ct.c_float*len(logw))(*logw);before=bytes(a)
        idx=(ct.c_uint32*k)();weights=(ct.c_float*k)()
        self.assertEqual(self.fn(a,len(logw),k,u,idx,weights),0)
        self.assertEqual(bytes(a),before)
        indices=list(idx);self.assertEqual(len(set(indices)),k)
        self.assertTrue(all(0<=i<len(logw) for i in indices))
        return indices,list(weights),list(a)

    def test_no_compression_is_identity(self):
        i,w,source=self.run_case([-1,-4,-2,-1000],4,.71)
        self.assertEqual(i,list(range(4)));self.assertEqual(w,source)

    def test_known_inclusions_and_unbiased_mass(self):
        # Analytic threshold .4: keep .6; tail inclusions .5,.25,.25.
        counts=[0]*4;sums=[0.]*4;n=4096
        for j in range(n):
            idx,weights,_=self.run_case([math.log(x) for x in [.6,.2,.1,.1]],2,(j+.5)/n)
            self.assertIn(0,idx)
            self.assertAlmostEqual(sum(math.exp(w) for w in weights),1,places=6)
            for i,w in zip(idx,weights):counts[i]+=1;sums[i]+=math.exp(w)/n
        for actual,expected in zip(counts,[n,n/2,n/4,n/4]):self.assertAlmostEqual(actual,expected,delta=1)
        for actual,expected in zip(sums,[.6,.2,.1,.1]):self.assertAlmostEqual(actual,expected,places=6)

    def test_grid_average_matches_each_input_mass(self):
        rng=random.Random(92);logs=[rng.uniform(-8,0) for _ in range(11)]
        source=[ct.c_float(v).value for v in logs];target=[math.exp(v) for v in source]
        mass=sum(target);estimated=[0.]*11;n=8192
        for j in range(n):
            idx,weights,_=self.run_case(logs,5,(j+.5)/n)
            self.assertAlmostEqual(sum(math.exp(w) for w in weights),mass,places=6)
            for i,w in zip(idx,weights):estimated[i]+=math.exp(w)/n
        for a,b in zip(estimated,target):self.assertAlmostEqual(a,b,delta=2*mass/n)

    def test_equal_weights_and_extreme_offsets(self):
        for n in [2,7,29,101]:
            for k in [1,n//2,n-1,n]:
                for u in [0,1e-15,.5,math.nextafter(1,0)]:
                    idx,w,_=self.run_case([0]*n,k,u)
                    self.assertAlmostEqual(sum(math.exp(x) for x in w),n,delta=2e-5)

    def test_large_dynamic_range_and_permutations(self):
        rng=random.Random(81)
        for _ in range(50):
            logs=[0,-1,-50,-100,-1000,-10000];rng.shuffle(logs)
            for k in range(1,7):
                idx,w,source=self.run_case(logs,k,rng.random())
                self.assertAlmostEqual(sum(math.exp(x) for x in w),sum(math.exp(x) for x in source),places=6)
                if k>1:self.assertIn(source.index(0),idx)

    def test_production_size_equal_tail(self):
        n=100003
        for u in [0,.381,math.nextafter(1,0)]:
            _,w,_=self.run_case([0]*n,10000,u)
            self.assertAlmostEqual(sum(math.exp(x) for x in w),n,delta=n*2e-7)

    def test_invalid_inputs_fail(self):
        a=(ct.c_float*2)(0,float('nan'));i=(ct.c_uint32*2)();w=(ct.c_float*2)()
        self.assertEqual(self.fn(a,2,1,.5,i,w),-1)
        a[1]=0
        for k,u in [(0,.5),(3,.5),(1,1),(1,-1),(1,float('nan'))]:
            self.assertEqual(self.fn(a,2,k,u,i,w),-1)


if __name__=='__main__':unittest.main()
