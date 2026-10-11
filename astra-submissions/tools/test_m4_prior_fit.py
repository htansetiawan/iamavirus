"""Independent numerical and binary-format checks for the replay-prior fit."""
import contextlib
import io
from pathlib import Path
import struct
import tempfile
import unittest
import numpy as np
from m4_prior_fit import bootstrap,fit,load,stats


class PriorFitTests(unittest.TestCase):
    def test_known_optimum_and_tie_policy(self):
        X=np.tile([[1.,0.],[0.,1.],[0.,0.]],(100,1))
        d=dict(X=X,starts=np.arange(100)*3,counts=np.full(100,3),
               played=np.array([0]*80+[1]*15+[2]*5),segment=np.repeat(np.arange(100),3))
        with contextlib.redirect_stdout(io.StringIO()):theta,_=fit(d,2,l2=1e-6)
        np.testing.assert_allclose(theta,np.log([16.,3.]),atol=.001)
        lp,p,top=stats(np.zeros(2),d)
        np.testing.assert_allclose(p,1/3)
        np.testing.assert_allclose(lp,-np.log(3))
        self.assertAlmostEqual(top.mean(),.8)

    def test_cluster_estimator_preserves_move_weighting(self):
        delta=np.array([1.,1.,-1.]);groups=np.array([0,0,1])
        r=bootstrap(delta,groups,200)
        self.assertEqual(r['games'],2);self.assertEqual(r['moves'],3)
        self.assertAlmostEqual(r['mean'],1/3)
        self.assertEqual(bootstrap(np.full(5,2.),np.array([0,0,1,1,1]),100)['ci95'],[2.,2.])

    def test_binary_alignment_and_reject_truncation(self):
        games=[dict(plies=1,used_sides=[True,False])]
        raw=struct.pack('<I5I',32,2,1,0,0,0)+np.arange(64,dtype='<f4').tobytes()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'features.bin';path.write_bytes(raw)
            d=load(path,games)
            self.assertEqual(d['X'].shape,(2,32));self.assertEqual(d['played'].tolist(),[1])
            path.write_bytes(raw[:-1])
            with self.assertRaisesRegex(ValueError,'truncated features'):load(path,games)
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'missing replay rows'):
                load(path,[dict(plies=3,used_sides=[True,False])])


if __name__=='__main__':unittest.main()
