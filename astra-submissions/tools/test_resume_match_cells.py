import unittest

from resume_match_cells import first_cells, missing_cells


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.match = {'id': 'm', 'a': 'a.zip', 'b': 'b.zip', 'seed': 100, 'max_games': 4}
        self.hashes = {'a': 'a'*64, 'b': 'b'*64}

    def row(self, pair, color):
        return dict(matchup='m', pair=pair, a_colour=color, seed=100+2*pair,
                    a='a.zip', b='b.zip', a_sha='a'*12, b_sha='b'*12)

    def test_partial_pair_does_not_repeat_completed_color(self):
        rows = [self.row(0, 'white'), self.row(1, 'white'), self.row(0, 'black')]
        self.assertEqual(missing_cells(self.match, rows, self.hashes), [(1, 'black')])

    def test_recorded_failed_attempt_is_not_retried(self):
        row = dict(self.row(0, 'white'), attempt='failed', a_score=None)
        self.assertNotIn((0, 'white'), missing_cells(self.match, [row], self.hashes))

    def test_duplicates_and_changed_provenance_fail_closed(self):
        row = self.row(0, 'white')
        for rows in ([row, row], [dict(row, seed=999)], [dict(row, a_sha='c'*12)],
                     [dict(row, a_env=['MIST_SAMPLES=1'])]):
            with self.assertRaises(ValueError):
                missing_cells(self.match, rows, self.hashes)

    def test_complete_is_idempotent(self):
        rows = [self.row(p,c) for p in range(2) for c in ('white','black')]
        self.assertEqual(missing_cells(self.match, rows, self.hashes), [])

    def test_reconciliation_keeps_first_not_best_result(self):
        first = dict(self.row(0, 'white'), a_score=0.)
        second = dict(self.row(0, 'white'), a_score=1.)
        kept, excluded = first_cells(self.match, [first, second], self.hashes)
        self.assertEqual(kept, [first]); self.assertEqual(excluded, [second])
        self.assertNotIn((0, 'white'), missing_cells(self.match, kept, self.hashes))
        with self.assertRaises(ValueError):
            first_cells(self.match, [first, dict(second, seed=900)], self.hashes)


if __name__ == '__main__':
    unittest.main()
