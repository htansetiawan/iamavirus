"""Independent small-game checks of inference and training algebra."""
import json
import unittest
from types import SimpleNamespace

import numpy as np
import torch

import model


def toy():
    rng = np.random.default_rng(71)
    counts = np.array([3, 2, 4, 2, 3, 2])
    starts = np.r_[0, counts.cumsum()]
    head = np.zeros((6, 9), dtype=np.int64)
    head[:, 0] = [0, 0, 0, 0, 1, 1]
    head[:, 1] = [0, 1, 2, 3, 0, 2]
    head[:, 2] = [0, 1, 0, 1, 0, 0]
    group = torch.tensor([0, 1, 0, 1, 2, 2])
    selected = starts[:-1] + np.array([1, 0, 1, 0, 2, 1])
    compatible = np.ones(counts.sum(), dtype=bool)
    compatible[[2, 5, 10]] = False
    return SimpleNamespace(N=6, G=3, X=torch.tensor(rng.normal(size=(counts.sum(), 39))),
          base=torch.tensor(rng.normal(size=counts.sum())), head=head, counts=counts,
          starts=starts, group=group, seg=torch.tensor(np.repeat(np.arange(6), counts)),
          played=torch.tensor(selected), compatible=torch.tensor(compatible),
          observation_valid=np.ones(6, dtype=bool))


class MixtureTest(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        self.d = toy()
        self.delta = torch.tensor(np.random.default_rng(81).normal(0, .1, (3, 39)), requires_grad=True)
        self.alpha = torch.tensor([.4, -.2, .1], requires_grad=True, dtype=torch.float64)

    def test_independent_probabilities_objective_and_gradient(self):
        d = self.d
        p, z, _ = model.expert_logprobs(d, self.delta)
        z = z.detach().numpy()
        naive = []
        for i, (a, b) in enumerate(zip(d.starts[:-1], d.starts[1:])):
            probs = np.exp(z[a:b] - np.max(z[a:b], axis=0))
            probs /= probs.sum(0)
            np.testing.assert_allclose(probs.sum(0), 1, atol=1e-14)
            naive.append(np.log(probs[int(d.played[i])-a]))
        np.testing.assert_allclose(p.detach(), naive, atol=1e-13)
        priors = torch.softmax(self.alpha, 0).detach().numpy()
        ll = 0
        for g in range(d.G):
            likelihood = np.exp(np.array(naive)[d.group.numpy() == g].sum(0))
            ll += np.log(np.dot(priors, likelihood))
        expected = -ll/d.N + .0005 * np.square(self.delta.detach().numpy()).sum()
        self.assertAlmostEqual(float(model.objective(d, self.delta, self.alpha).detach()), expected, places=12)
        self.assertTrue(torch.autograd.gradcheck(lambda x, y: model.objective(d, x, y),
                                                (self.delta, self.alpha), eps=1e-6, atol=1e-6))

    def test_sequence_identity_and_no_future_leak(self):
        d = self.d
        p, z, den = model.expert_logprobs(d, self.delta)
        p = p.detach().numpy()
        obs = (model.segment_logsumexp(d, z, True)-den).detach().numpy()
        prior = torch.log_softmax(self.alpha, 0).detach().numpy()
        scored = model.online_scores(d.head, p, obs, prior, d.observation_valid)
        for arm, evidence, key in [('view_history', obs, 'observation_logp'),
                                  ('true_move_history', p, 'logp')]:
            for g in range(d.G):
                ix = d.group.numpy() == g
                expected = model.np_lse(prior + evidence[ix].sum(0))
                self.assertAlmostEqual(scored[arm][key][ix].sum(), expected, places=12)
        changed = p.copy(); changed[2:] -= 2
        other_obs = obs.copy(); other_obs[2:] -= 1
        future = model.online_scores(d.head, changed, other_obs, prior, d.observation_valid)
        for arm in scored:
            np.testing.assert_array_equal(scored[arm]['logp'][:2], future[arm]['logp'][:2])
        # Changing the current observation cannot alter its unconditional prediction.
        other_obs = obs.copy(); other_obs[0] -= np.arange(3)
        future = model.online_scores(d.head, p, other_obs, prior, d.observation_valid)
        self.assertEqual(scored['view_history']['logp'][0], future['view_history']['logp'][0])
        # Updating White's style cannot affect Black's first prediction.
        self.assertEqual(scored['view_history']['logp'][1], future['view_history']['logp'][1])

    def test_team_ids_unused_and_identical_experts_reduce_to_static(self):
        d = self.d
        delta = torch.zeros((3, 39), dtype=torch.float64)
        first = model.scores(d, delta, self.alpha.detach())
        d.head[:, 3] = np.arange(d.N) + 700
        second = model.scores(d, delta, self.alpha.detach())
        for arm in first:
            np.testing.assert_allclose(first[arm]['logp'], first['reset']['logp'], atol=1e-14)
            np.testing.assert_array_equal(first[arm]['logp'], second[arm]['logp'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
