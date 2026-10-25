"""Analytic metric and gate-contract checks; no training or model inference."""
import copy
import math
import unittest

from compare_risk_panels import compare
from evaluate_risk_panel import metrics


class MetricsTests(unittest.TestCase):
    def test_calibration_and_ranking_orientation(self):
        m = metrics([2., -2.], [-2., 2.], [0, 1], ['a2a3', 'a2a4'])
        self.assertAlmostEqual(m['log_loss'], math.log1p(math.exp(-2)))
        self.assertAlmostEqual(m['brier'], (1 / (1 + math.exp(2))) ** 2)
        self.assertEqual(m['auc'], 1.)
        self.assertEqual(m['policy_fatal'], 0)
        self.assertEqual(m['min_risk_fatal'], 0)
        self.assertAlmostEqual(m['policy_fatal_mass'], 1 / (1 + math.exp(4)))

    def test_ties_and_unsupported_auc(self):
        m = metrics([0., 0.], [0., 0.], [0, 1], ['a2a3', 'a2a4'])
        self.assertEqual(m['auc'], .5)
        self.assertAlmostEqual(m['log_loss'], math.log(2))
        self.assertEqual(m['brier'], .25)
        self.assertIsNone(metrics([0.], [0.], [1], ['a2a3'])['auc'])
        self.assertFalse(metrics([0.], [0.], [1], ['a2a3'])['safe_available'])

    def test_no_change_cannot_pass_improvement_gate(self):
        metric = {'decisions': 2, 'mixed_decisions': 1, 'no_escape_decisions': 0,
                  'log_loss': .2, 'brier': .1, 'policy_fatal': .5, 'min_risk_fatal': 0.,
                  'policy_fatal_mass': .25, 'auc': .8, 'policy_fatal_count': 1,
                  'min_risk_fatal_count': 0, 'avoidable_policy_fatal_count': 1,
                  'avoidable_min_risk_fatal_count': 0}
        report = {'state': 'complete', 'full_panel': True, 'failures': [], 'games_requested': 2,
                  'panel_sha256': 'panel', 'collector_sha256': 'code',
                  'source_receipt_sha256': 'source', 'native_library_sha256': 'library',
                  'game_records': [{'game': str(i), 'side': 'white', 'actor_input_sha256': 'history',
                                    'replay_sha256': 'replay', 'metrics': metric} for i in range(2)]}
        result = compare(report, report, samples=100)
        self.assertFalse(result['advance_to_c_search_integration_test'])
        self.assertEqual(result['game_weighted_metrics']['log_loss']['paired_game_bootstrap_95'], [0., 0.])
        changed = copy.deepcopy(report)
        changed['game_records'][0]['actor_input_sha256'] = 'different history'
        with self.assertRaisesRegex(ValueError, 'History identity'):
            compare(report, changed, samples=100)
        partial = copy.deepcopy(report); partial['full_panel'] = False
        with self.assertRaisesRegex(ValueError, 'complete full-panel'):
            compare(report, partial, samples=100)


if __name__ == '__main__':
    unittest.main()
