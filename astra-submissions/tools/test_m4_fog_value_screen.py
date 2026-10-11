"""Feature semantics and optimizer recovery, independent of match outcomes."""
import importlib.util
from pathlib import Path
import unittest

import chess
import numpy as np
import m4_fog_value_screen as screen


class FogValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path('/home/henrytan/git/fow-starter/referee.py')
        spec=importlib.util.spec_from_file_location('test_referee',path)
        cls.referee=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.referee)

    def test_hidden_check_and_color_swap(self):
        row={'fen':'7k/8/8/8/4q3/8/8/4K3 w - - 0 1','cp':-420}
        features=screen.features(row,self.referee)
        self.assertEqual(features['hidden_king_attackers'],1)
        self.assertEqual(features['king_attacked'],1)
        mirrored={'fen':chess.Board(row['fen']).mirror().fen(),'cp':420}
        swapped=screen.features(mirrored,self.referee)
        for key,value in features.items():
            self.assertAlmostEqual(swapped[key],-value,msg=key)
        row.update(target=1,white='irrelevant',black='unused')
        self.assertEqual(screen.features(row,self.referee),features)

    def test_recovers_known_soft_probabilities(self):
        x=np.column_stack([np.ones(100),np.linspace(-2,2,100)])
        truth=np.array([.3,1.2]);y=screen.sigmoid(x@truth)
        weights,status=screen.fit(x,y,1e-4)
        self.assertTrue(status['converged'])
        np.testing.assert_allclose(weights,truth,atol=1e-4)
        self.assertLess(status['gradient_max'],1e-6)


if __name__=='__main__':unittest.main()
