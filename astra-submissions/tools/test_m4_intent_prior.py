import unittest
import numpy as np
from m4_intent_prior import groups,fit_gate,probabilities


def data(X,counts,played):
    return dict(X=X,counts=np.array(counts),starts=np.r_[0,np.cumsum(counts)[:-1]],
                segment=np.repeat(np.arange(len(counts)),counts),played=np.array(played))


class IntentTests(unittest.TestCase):
    def test_zero_gate_preserves_base_with_missing_groups(self):
        rng=np.random.default_rng(73);X=np.zeros((9,32));X[:,12:15]=rng.normal(size=(9,3))
        X[0,18]=1;X[2,0]=1;X[8,18]=1
        d=data(X,[4,3,2],[0,1,1]);theta=rng.normal(size=26)
        g=groups(d,theta)
        np.testing.assert_allclose(probabilities(g,np.zeros(7)),g['base_p'],atol=1e-14)
        np.testing.assert_allclose(np.add.reduceat(probabilities(g,rng.normal(size=7)),d['starts']),1)

    def test_fits_known_class_frequencies(self):
        X=np.zeros((300,32));X[::3,18]=1;X[1::3,0]=1
        d=data(X,[3]*100,[0]*80+[1]*15+[2]*5);g=groups(d,np.zeros(26))
        theta,_=fit_gate(g,l2=1e-7)
        np.testing.assert_allclose(probabilities(g,theta).reshape(-1,3),np.tile([.8,.15,.05],(100,1)),atol=1e-4)

    def test_preserves_odds_inside_each_group(self):
        X=np.zeros((5,32));X[:2,18]=1;X[2,0]=1;X[:,12]=[.1,.7,-.2,.4,.5]
        d=data(X,[5],[1]);theta=np.zeros(26);theta[12]=2;g=groups(d,theta)
        p=probabilities(g,np.array([2.,-1.,.3,.2,-.4,.5,-.7]))
        self.assertAlmostEqual(p[0]/p[1],g['base_p'][0]/g['base_p'][1])
        self.assertAlmostEqual(p[3]/p[4],g['base_p'][3]/g['base_p'][4])


if __name__=='__main__':unittest.main()
