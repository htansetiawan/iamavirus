import copy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from ssl_transfer_report import paired, compare


def report():
    return {'unique_decisions': 5, 'by_game': {
        'one': {'counts': {'policy': 2}, 'sums': {'policy_nll': 4., 'policy_accuracy': 1.}},
        'two': {'counts': {'policy': 3}, 'sums': {'policy_nll': 9., 'policy_accuracy': 2.}}}}


class ReportTests(unittest.TestCase):
    def test_weighted_delta_and_game_resampling(self):
        a=report();b=copy.deepcopy(a)
        for r in b['by_game'].values():
            r['sums']['policy_nll'] += .2*r['counts']['policy']
        out=paired(a,b)['metrics']['policy_nll']
        self.assertAlmostEqual(out['control'],13/5)
        self.assertAlmostEqual(out['candidate_minus_control'],.2)
        np.testing.assert_allclose(out['paired_game_bootstrap_95'],[.2,.2])

    def test_rejects_game_or_target_changes(self):
        for which in ('game','count','decision'):
            a=report();b=copy.deepcopy(a)
            if which=='game':b['by_game']['three']=b['by_game'].pop('two')
            elif which=='count':b['by_game']['two']['counts']['policy']=4
            else:b['unique_decisions']=6
            with self.assertRaises(ValueError):paired(a,b)

    def test_source_and_native_changes_cannot_be_compared(self):
        base={'identity':{'seed':253},'architecture':'a','model_parameters':10,
              'source_sha256':{'learning/features.py':'abc'},'native':{'sources':{'rules.c':'def'}}}
        with tempfile.TemporaryDirectory() as root:
            a,b=Path(root)/'a',Path(root)/'b';a.mkdir();b.mkdir()
            (a/'run.json').write_text(json.dumps(base))
            for which in ('source','native','seed'):
                meta=copy.deepcopy(base)
                if which=='source':meta['source_sha256']['learning/features.py']='changed'
                elif which=='native':meta['native']['sources']['rules.c']='changed'
                else:meta['identity']['seed']=99
                (b/'run.json').write_text(json.dumps(meta))
                with self.assertRaises(ValueError):compare(a,b,1000)


if __name__=='__main__':unittest.main()
