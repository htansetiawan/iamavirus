#!/usr/bin/env python3
"""Small numerical checks for the standard-library calibration implementation."""
import unittest

from analyze_neural_risk import fit, rows, weighted_standardize


class CalibrationTests(unittest.TestCase):
    def test_nonnegative_fused_slopes_recover_complementary_signal(self):
        decisions = []
        for i in range(160):
            x1 = (i % 16 - 7.5) / 3
            x2 = (i // 16 - 4.5) / 2
            label = int(x1 + x2 > 0.1)
            decisions.append({'candidates': [{
                'particle_x': x1, 'neural_x': x2, 'y': label,
            }]})
        fitted = fit(rows(decisions, [0.0, 0.0], [1.0, 1.0]), [1, 2])
        self.assertGreaterEqual(fitted['beta'][1], 0.0)
        self.assertGreaterEqual(fitted['beta'][2], 0.0)
        self.assertIn(1, fitted['active_features'])
        self.assertIn(2, fitted['active_features'])

    def test_each_decision_gets_equal_total_weight(self):
        decisions = [
            {'candidates': [{'particle_x': 0.0, 'neural_x': 0.0, 'y': 0}]},
            {'candidates': [{'particle_x': 0.0, 'neural_x': 0.0, 'y': 0}
                            for _ in range(100)]},
        ]
        means, scales = weighted_standardize(decisions)
        weighted_rows = rows(decisions, means, scales)
        self.assertAlmostEqual(sum(row[2] for row in weighted_rows), 2.0)
        self.assertAlmostEqual(sum(row[2] for row in weighted_rows[:1]), 1.0)
        self.assertAlmostEqual(sum(row[2] for row in weighted_rows[1:]), 1.0)


if __name__ == '__main__':
    unittest.main()
