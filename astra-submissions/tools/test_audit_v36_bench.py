"""Integrity failures must never masquerade as a passing 104-game screen."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("v36audit", Path(__file__).with_name("audit_v36_bench.py"))
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def fixture():
    roles = {r: r for r in MOD.ROLES}
    paths = {n: str(Path('/tmp') / f'v36-test-{n}.zip') for n in ('candidate', 'baseline', 'misty')}
    hashes = {p: str(i) * 64 for i, p in enumerate(paths.values(), 1)}
    matches = []
    rows = []
    for role, (n, seed) in MOD.ROLES.items():
        a = paths['baseline' if role == 'baseline_misty' else 'candidate']
        b = paths['baseline' if role == 'direct' else 'misty']
        matches.append(dict(id=role, a=a, b=b, max_games=n, seed=seed))
        wins_per_color = {'direct': 11, 'candidate_misty': 10, 'baseline_misty': 8}[role]
        for pair in range(n // 2):
            for color in ('white', 'black'):
                score = float(pair < wins_per_color)
                result = '1-0' if (score == 1) == (color == 'white') else '0-1'
                rows.append(dict(matchup=role, pair=pair, a_colour=color, seed=seed+2*pair,
                                 a=a, b=b, a_sha=hashes[a][:12], b_sha=hashes[b][:12],
                                 a_env=[], b_env=[], a_score=score, result=result,
                                 reason='King capturable', clocks=[40., 40.], plies=70,
                                 ts='2026-10-27T02:00:00Z', replay='unused-by-mock.json'))
    pins = dict(created_at='2026-10-27T00:00:00Z', queue_sha256='abc',
                queue={'matchups': matches}, roles=roles,
                artifacts_sha256=hashes, wall_cap_seconds=43200)
    receipt = dict(state='complete', started_at='2026-10-27T01:00:00Z',
                   finished_at='2026-10-27T03:00:00Z', queue_sha256='abc',
                   attempted_jobs=104, failed_jobs=0)
    return pins, rows, receipt


class GateIntegrity(unittest.TestCase):
    def setUp(self):
        self.pins, self.rows, self.receipt = fixture()
        self.patch = patch.object(MOD, 'replay_check', return_value={
            'normal_board_termination': True, 'sha256': 'unused', 'frames': 71,
            'minimum_recorded_clocks': [40., 40.]})
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def audit(self, **kwargs):
        return MOD.audit(self.pins, self.rows, self.receipt, referee=object(), **kwargs)

    def test_complete_positive_screen(self):
        report = self.audit()
        self.assertEqual(report['status'], 'passed_screen')
        self.assertAlmostEqual(report['metrics']['combined_direction_D'], .0875)

    def test_missing_job_is_not_a_smaller_successful_run(self):
        self.rows.pop()
        self.receipt.update(attempted_jobs=103, state='wall_cap')
        report = self.audit()
        self.assertEqual(report['status'], 'incomplete')
        self.assertEqual(len(report['missing_jobs']), 1)
        self.assertFalse(report['metrics'])

    def test_duplicate_cannot_replace_missing_color(self):
        self.rows[-1] = copy.deepcopy(self.rows[-2])
        self.assertEqual(self.audit()['status'], 'invalid')

    def test_archive_change_or_wrong_seed_is_invalid(self):
        for field, value in [('a_sha', 'wrong'), ('seed', 0), ('a', '/tmp/wrong.zip')]:
            with self.subTest(field=field):
                old = self.rows[0][field]
                self.rows[0][field] = value
                self.assertEqual(self.audit()['status'], 'invalid')
                self.rows[0][field] = old

    def test_unknown_result_is_retained_and_blocks_pass(self):
        self.rows[0]['result'] = '*'
        self.rows[0]['reason'] = 'Infrastructure startup failure'
        report = self.audit()
        self.assertEqual(report['status'], 'incomplete')
        self.assertEqual(report['seen_jobs'], 104)
        self.assertEqual(report['valid_jobs'], 103)

    def test_unlogged_attempt_is_invalid(self):
        self.receipt['attempted_jobs'] = 105
        self.assertEqual(self.audit()['status'], 'invalid')

    def test_running_attempt_without_result_is_pending(self):
        self.rows.pop()
        self.receipt.update(state='running', finished_at=None)
        report = self.audit()
        self.assertEqual(report['status'], 'incomplete')
        self.assertFalse(report['errors'])

    def test_missing_runtime_receipt_blocks_pass(self):
        self.receipt = None
        self.assertEqual(self.audit()['status'], 'incomplete')

    def test_wrong_queue_or_result_time_is_invalid(self):
        self.receipt['queue_sha256'] = 'other'
        self.assertEqual(self.audit()['status'], 'invalid')
        self.receipt['queue_sha256'] = 'abc'
        self.rows[0]['ts'] = '2026-10-26T23:59:59Z'
        self.assertEqual(self.audit()['status'], 'invalid')

    def test_wall_cap_is_enforced(self):
        self.receipt['finished_at'] = '2026-10-27T13:00:01Z'
        self.assertEqual(self.audit()['status'], 'invalid')

    def test_replay_mismatch_and_bot_failure_block_pass(self):
        with patch.object(MOD, 'replay_check', side_effect=ValueError('board mismatch')):
            self.assertEqual(self.audit()['status'], 'invalid')
        with patch.object(MOD, 'replay_check', return_value={'normal_board_termination': False}):
            self.assertEqual(self.audit()['status'], 'rejected')

    def test_minimum_clock_cannot_hide_in_median(self):
        self.rows[0]['clocks'][0] = 9.9
        report = self.audit()
        self.assertEqual(report['status'], 'rejected')
        self.assertIn('candidate end clock below 10s', report['rejections'])

    def test_clock_comparison_uses_same_opponent(self):
        for row in self.rows:
            if row['matchup'] == 'candidate_misty':
                row['clocks'][0 if row['a_colour'] == 'white' else 1] = 29.
        self.assertIn('candidate median Misty clock worsened by over 10s', self.audit()['rejections'])

    def test_two_nonpositive_score_directions_do_not_pass(self):
        for row in self.rows:
            target = {'direct': 10, 'candidate_misty': 8, 'baseline_misty': 8}[row['matchup']]
            row['a_score'] = float(row['pair'] < target)
            row['result'] = '1-0' if (row['a_score'] == 1) == (row['a_colour'] == 'white') else '0-1'
        report = self.audit()
        self.assertIn('combined score direction is not positive', report['rejections'])

    def test_mutated_pinned_input_blocks_pass(self):
        self.assertEqual(self.audit(input_failures=['changed Stockfish'])['status'], 'invalid')

    def test_pins_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'pins.json'
            MOD.write_json(path, {'original': True}, exclusive=True)
            with self.assertRaises(FileExistsError):
                MOD.write_json(path, {'replacement': True}, exclusive=True)
            self.assertIn('original', path.read_text())


if __name__ == '__main__':
    unittest.main()
