import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import torch

from learning_experiments.evaluate import Totals, evaluate, recall_at_fpr


def decision(event):
    return {"event": event, "count": 2, "from": np.array([0, 1]), "to": np.array([8, 9]),
            "promo": np.array([0, 0]), "demonstrated": 0, "policy_valid": True,
            "danger_valid": True, "danger": np.array([0., 1.]), "return": 1.,
            "value_valid": True, "belief_valid": True, "belief": np.full(64, 6),
            "belief_mask": np.ones(64, dtype=bool)}


class CounterPolicy(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.events = 0

    def initial_hidden(self, batch, device):
        return torch.zeros(batch, 256, device=device)

    def observe(self, planes, scalars, hidden):
        self.events += 1
        return hidden + 1, torch.zeros(1, 64, 8, 8), torch.zeros(1, 64, 7), torch.zeros(1, 1)

    def score(self, hidden, spatial, src, dst, promo):
        return torch.zeros_like(src).float(), torch.zeros_like(src).float()


class EvaluationTests(unittest.TestCase):
    def test_equal_score_ties_do_not_create_artificial_recall(self):
        result = recall_at_fpr([0.5] * 100, [1] * 10 + [0] * 90)
        self.assertEqual(result['0.05']['recall'], 0.0)
        result = recall_at_fpr([0.9, 0.8, 0.3, 0.1], [1, 1, 0, 0])
        self.assertEqual(result['0.01']['recall'], 1.0)
        self.assertIsNone(recall_at_fpr([0.9], [1])['0.05']['recall'])

    def test_hidden_enemy_metric_is_separate_from_empty_accuracy(self):
        d = decision(0)
        d['belief'][0] = 2
        belief = np.full((64, 7), 0.001)
        belief[:, 6] = 0.994
        stats = Totals()
        stats.add(d, np.log([0.8, 0.2]), np.array([0.1, 0.9]), belief, 0.5)
        summary = stats.summary()
        self.assertEqual(summary['counts']['hidden_enemy_squares'], 1)
        self.assertGreater(summary['metrics']['hidden_enemy_nll'], 6)
        self.assertEqual(summary['metrics']['hidden_piece_2_recall'], 0)

    def test_policy_slate_distinguishes_forced_and_avoidable_fatalities(self):
        stats = Totals()
        d = decision(0)
        d.update(policy_valid=False, value_valid=False, belief_valid=False,
                 danger=np.array([1., 1., 1., 1., 0.]))
        # A tied top four are all fatal; a fifth available move escapes.
        stats.add(d, np.log(np.full(5, 0.2)), np.full(5, 0.1), None, 0.)
        d['danger'] = np.ones(2)
        stats.add(d, np.log([0.6, 0.4]), np.full(2, 0.9), None, 0.)
        report = stats.summary()
        self.assertEqual(report['counts']['danger_decisions'], 2)
        self.assertEqual(report['counts']['avoidable_danger_decisions'], 1)
        self.assertEqual(report['metrics']['policy_top1_fatal'], 1.)
        self.assertEqual(report['metrics']['policy_top1_avoidable_fatal'], 1.)
        self.assertEqual(report['metrics']['policy_top4_all_fatal_when_escape_exists'], 1.)
        self.assertEqual(report['counts']['policy_top4_candidates'], 6)
        self.assertEqual(report['metrics']['policy_top4_fatal_fraction'], 1.)
        self.assertIsNone(report['metrics']['policy_hit4'])

    def test_policy_slate_masks_ties_and_short_candidate_lists(self):
        stats = Totals()
        d = decision(0)
        d.update(value_valid=False, belief_valid=False, demonstrated=1)
        stats.add(d, np.log([0.5, 0.5]), np.array([0.9, 0.1]), None, 0.)
        report = stats.summary()
        self.assertEqual(report['metrics']['policy_top1_fatal'], 0.)
        self.assertEqual(report['metrics']['policy_top4_fatal_fraction'], 0.5)
        self.assertEqual(report['metrics']['policy_hit4'], 1.)
        self.assertEqual(report['metrics']['policy_accuracy'], 0.)
        self.assertAlmostEqual(report['metrics']['policy_entropy'], np.log(2))
        # A protocol failure can invalidate danger targets while a legal
        # demonstrated move still contributes to policy coverage.
        d.update(danger_valid=False, danger=np.ones(2))
        stats.add(d, np.log([0.1, 0.9]), np.ones(2), None, 0.)
        report = stats.summary()
        self.assertEqual(report['counts']['danger_decisions'], 1)
        self.assertEqual(report['counts']['policy'], 2)
        self.assertEqual(report['metrics']['policy_top1_fatal'], 0.)

    def test_each_decision_once_in_unequal_length_episodes(self):
        def episode(game, length):
            return SimpleNamespace(metadata=SimpleNamespace(game_id=game, player_id='a', opponent_id='b'),
                                   actor=SimpleNamespace(side=0, plies=list(range(length))))
        episodes = [episode('game0001', 1), episode('game0002', 5)]
        def tensors(e):
            n = len(e.actor.plies)
            return np.zeros((n, 32, 8, 8), np.float32), np.zeros((n, 8), np.float32), [decision(i) for i in range(n)]
        model = CounterPolicy()
        with patch('learning_experiments.evaluate.ds.episode_tensors', side_effect=tensors):
            report = evaluate(model, episodes, 'cpu')
        self.assertEqual(report['unique_decisions'], 6)
        self.assertEqual(model.events, 6)
        self.assertEqual(report['by_game']['game0001']['counts']['decisions'], 1)
        self.assertEqual(report['by_game']['game0002']['counts']['decisions'], 5)
        self.assertTrue(model.training)


if __name__ == '__main__':
    unittest.main()
