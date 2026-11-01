import unittest
from types import SimpleNamespace
import torch
from fit import FEATURES,PARAMS,objective,logits,log_sums

class LikelihoodTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(4)
        self.d=SimpleNamespace(N=2,X=torch.randn(5,FEATURES,dtype=torch.float64),
            pf=torch.tensor([1,2,3,2,5]),pt=torch.tensor([4,3,2,1,0]),
            seg=torch.tensor([0,0,1,1,1]),played=torch.tensor([1,4]),compatible=torch.tensor([False,True,True,False,True]))
        self.theta=torch.randn(PARAMS,dtype=torch.float64)*.01
    def test_gradient_and_all_action_denominator(self):
        t=self.theta.requires_grad_();loss=objective(self.d,t,True);loss.backward()
        for j in [0,38,39,90,FEATURES+2,FEATURES+385]:
            a=t.detach().clone();b=a.clone();a[j]+=1e-5;b[j]-=1e-5
            numerical=(objective(self.d,a,True)-objective(self.d,b,True))/2e-5
            self.assertAlmostEqual(float(numerical),float(t.grad[j]),places=7)
        self.d.compatible=~self.d.compatible
        self.assertEqual(float(loss.detach()),float(objective(self.d,t,True).detach()))
    def test_conditional_factorization(self):
        z=logits(self.d,self.theta,True);allz=log_sums(self.d,z);part=log_sums(self.d,z,self.d.compatible)
        self.assertTrue(torch.allclose(z[self.d.played]-allz,(z[self.d.played]-part)+(part-allz)))
        self.assertAlmostEqual(float(part[0]),float(z[1]),places=12)
        self.assertAlmostEqual(float(part[1]),float(torch.logsumexp(z[[2,4]],0)),places=12)
    def test_static_ablation(self):
        a=logits(self.d,self.theta,False);b=self.theta.clone();b[39:FEATURES]+=100
        self.assertTrue(torch.equal(a,logits(self.d,b,False)))
if __name__=='__main__':unittest.main()
