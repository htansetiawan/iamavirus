"""Enumerated missing-cell extrema and independent weighted-tail checks."""
import itertools
import math
import unittest
from analysis import summarize


class BoundsChecks(unittest.TestCase):
    def test_unmatched_bounds_are_exact_extrema(self):
        for unknown in range(5):
            candidate=[dict(stratum=('known',1,'white'),score=.5)]
            candidate += [dict(stratum=('new',1,'white'),score=(i%3)/2) for i in range(unknown)]
            baseline=[dict(stratum=('known',1,'white'),score=0),dict(stratum=('known',1,'white'),score=1)]
            r=summarize(candidate,baseline);points=sum(g['score'] for g in candidate)
            explicit=[(points-.5-sum(v))/len(candidate) for v in itertools.product((0,.5,1),repeat=unknown)]
            self.assertEqual(r['full_schedule_proxy_range_unmatched'],[min(explicit),max(explicit)])

    def test_baseline_reuse_weights_match_explicit_game_weights(self):
        c=[dict(stratum=('a',1,'black'),score=1)]*3+[dict(stratum=('b',1,'white'),score=0)]*2
        b=[dict(stratum=('a',1,'black'),score=0)]*2+[dict(stratum=('b',1,'white'),score=.5)]*4
        r=summarize(c,b)
        weights=[1/5]*5+[-3/(5*2)]*2+[-2/(5*4)]*4
        explicit=math.fsum(w*w for w in weights)
        self.assertAlmostEqual(r['fixed_schedule_independent_working_model']['full_signed_weight_sum_squares'],explicit,places=15)
        self.assertAlmostEqual(r['effective_baseline_games'],25/(9/2+4/4),places=15)

    def test_exact_small_independent_bernoulli_tail(self):
        weights=(.5,.5,-.5,-.5)
        for probabilities in itertools.product((.1,.5,.9),repeat=4):
            mean=sum(w*p for w,p in zip(weights,probabilities))
            for alpha in (.05,.2,.8):
                radius=math.sqrt(.5*sum(w*w for w in weights)*math.log(2/alpha));violation=0
                for values in itertools.product((0,1),repeat=4):
                    probability=math.prod(p if x else 1-p for p,x in zip(probabilities,values))
                    if abs(sum(w*x for w,x in zip(weights,values))-mean)>radius:violation+=probability
                self.assertLessEqual(violation,alpha+1e-12)

    def test_unmatched_only_does_not_invent_a_baseline(self):
        c=[dict(stratum=('new',1,'white'),score=.5)]
        r=summarize(c,[])
        self.assertIsNone(r['matched_point_difference']);self.assertEqual(r['full_schedule_proxy_range_unmatched'],[-.5,.5])


if __name__=='__main__':unittest.main()
