import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from collect_neural_risk import actor_stream, join_predictions, select_partitions, trajectory


def actors(first='e2e4', second='e7e5'):
    answer = {}
    for side, move in enumerate((first, second)):
        answer[side] = {'actor': {'side': side, 'observations': ['?' * 64] * 2,
                                 'phases': [0, 1 if side == 0 else 2], 'plies': [0, 1],
                                 'decision_event_indices': [side], 'own_actions': [move],
                                 'legal_actions': [[move, 'g1f3' if side == 0 else 'g8f6']]},
                        'targets': {'king_loss_by_action': [[0, 1]], 'danger_valid': [True]},
                        'metadata': {'opponent_id': 'test'}}
    return answer


class BoundaryTests(unittest.TestCase):
    def test_truth_and_current_action_cannot_change_score_prefix(self):
        original = actors()[0]
        changed = copy.deepcopy(original)
        changed['targets']['king_loss_by_action'][0] = [1, 0]
        changed['targets']['boards'] = ['SECRET']
        before = ''.join(actor_stream('a', original, 1))
        self.assertEqual(before, ''.join(actor_stream('a', changed, 1)))
        changed['actor']['own_actions'][0] = 'd2d4'
        after = ''.join(actor_stream('a', changed, 1))
        self.assertEqual(before.split('SCORE 0\n')[0], after.split('SCORE 0\n')[0])
        self.assertLess(before.index('SCORE 0'), before.index('MOVE e2e4'))
        self.assertNotIn('SECRET', after)

    def test_duplicate_trajectories_and_pilot_games_stay_out(self):
        val = {f'g{i}': actors(first=f'a{i}a{i+1}') for i in range(7)}
        val['duplicate'] = copy.deepcopy(val['g0'])
        parts, seq = select_partitions({}, val, {'g0'}, 2)
        selected = parts['calibration'] + parts['evaluation']
        self.assertEqual(len({seq[g] for g in selected}), 4)
        self.assertNotIn('g0', selected)
        self.assertNotIn('duplicate', selected)
        with self.assertRaises(ValueError):
            select_partitions({'train': actors(first='a3a4')}, val, {'g0'}, 2)

    def test_empty_startup_failure_is_valid_but_missing_actions_are_not(self):
        empty = actors()
        for e in empty.values():
            e['actor'].update(decision_event_indices=[], own_actions=[])
        self.assertEqual(trajectory(empty), hashlib.sha256(b'').hexdigest())
        broken = actors()
        broken[0]['actor'].update(decision_event_indices=[], own_actions=[])
        with self.assertRaises(ValueError):
            trajectory(broken)

    def test_labels_join_by_move_not_candidate_order_and_missing_rows_fail(self):
        games = {'a': actors()}
        records = []
        for side, e in games['a'].items():
            records.append({'game': 'a', 'side': side, 'event': side, 'ply': side,
                            'candidates': [{'move': m, 'particle': .1, 'neural_logit': -2., 'policy': .5}
                                           for m in reversed(e['actor']['legal_actions'][0])]})
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'predictions.jsonl'
            path.write_text(''.join(json.dumps(r) + '\n' for r in records))
            joined = list(join_predictions(path, games, ['a'], 1))
            self.assertEqual([c['fatal'] for c in joined[0]['candidates']], [1, 0])
            path.write_text(json.dumps(records[0]) + '\n')
            with self.assertRaises(ValueError):
                list(join_predictions(path, games, ['a'], 1))


if __name__ == '__main__':
    unittest.main()
