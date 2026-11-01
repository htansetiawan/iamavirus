import unittest
import numpy as np
from collect import full_protocol
from fit import fit_logistic,predict,paired_game_intervals


class PipelineTests(unittest.TestCase):
    def test_protocol_uses_own_views_and_own_actions(self):
        replay={'frames':[{'white':'W'*64,'black':'B'*64,'board':'SECRET','clocks':[180-i,170-i],
                           'move':None if i==0 else ('e2e4' if i%2 else 'e7e5')} for i in range(5)]}
        for side in (0,1):
            feed,moves,plies=full_protocol(replay,side)
            self.assertNotIn('SECRET',feed)
            self.assertNotIn(('B' if side==0 else 'W')*64,feed)
            self.assertEqual(moves,['e2e4' if side==0 else 'e7e5']*2)
            self.assertEqual(plies,[side,side+2])

    def test_calibration_recovers_known_probability_map(self):
        p=np.repeat([.02,.1,.3,.7],1000)
        target=predict(p,{'intercept':.7,'slope':.8})
        # Fractional targets isolate optimizer correctness from sampling noise.
        model=fit_logistic(p,target,np.ones(len(p)))
        self.assertAlmostEqual(model['intercept'],.7,places=2)
        self.assertAlmostEqual(model['slope'],.8,places=2)
        self.assertTrue(np.all(np.diff(predict(np.linspace(0,1,100),model))>=0))

    def test_game_bootstrap_keeps_identical_predictions_equal(self):
        rows=[{'game':str(i//3),'fatal':i%2,'played':True,'decision_weight':1/3} for i in range(12)]
        p=np.linspace(.1,.9,12)
        result=paired_game_intervals(rows,p,p,repetitions=50)
        for metric in result.values():
            self.assertEqual(metric['delta'],0)
            self.assertEqual(metric['game_bootstrap_95'],[0,0])
            self.assertEqual(metric['games'],4)


if __name__=='__main__':unittest.main()
