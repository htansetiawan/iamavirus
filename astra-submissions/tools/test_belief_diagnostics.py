import unittest
import numpy as np
from belief_diagnostics import components


class BeliefDiagnosticsTests(unittest.TestCase):
    def test_occupancy_boost_does_not_improve_location_or_type(self):
        p=np.zeros((3,7));p[:,0]=[.2,.1,.05];p[:,3]=[.1,.05,.05];p[:,6]=1-p[:,:6].sum(1)
        q=p.copy();q[:,:6]*=2;q[:,6]=1-q[:,:6].sum(1)
        y=np.array([0,6,6]);mask=np.ones(3,bool)
        a,empty=components(p,mask,y);b,_=components(q,mask,y)
        self.assertEqual(empty,2)
        self.assertAlmostEqual(a['hidden_location_nll'],b['hidden_location_nll'])
        self.assertAlmostEqual(a['hidden_conditional_type_nll'],b['hidden_conditional_type_nll'])
        self.assertGreater(b['hidden_empty_nll'],a['hidden_empty_nll'])

    def test_conditional_decomposition(self):
        p=np.full((2,7),1/7);y=np.array([1,6]);a,_=components(p,np.ones(2,bool),y)
        enemy_nll=-np.log(p[0,1]);enemy_occupancy_nll=-np.log(1-p[0,6])
        self.assertAlmostEqual(enemy_nll,enemy_occupancy_nll+a['hidden_conditional_type_nll'])
        self.assertAlmostEqual(a['hidden_location_nll'],np.log(2))

    def test_visible_squares_never_enter_spatial_normalizer(self):
        p=np.full((2,7),1/7);y=np.array([1,0]);a,_=components(p,np.array([True,False]),y)
        self.assertEqual(a['hidden_location_nll'],0)


if __name__=='__main__':unittest.main()
