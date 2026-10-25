"""Exercise an unapplied PPO patch in a temporary copy, without native builds.

Uses the real recurrent actor and real rollout/update function bodies. A tiny
deterministic simulator double checks label timing and information boundaries;
these are plumbing/gradient tests, not self-play or playing-strength evidence.
"""
import ast
import collections
import copy
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess
import tempfile
import unittest

import numpy as np
import torch
from torch.nn import functional as F

from learning.model import FogPolicy, masked_log_softmax


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def functions_from_source(source):
    # Load original function bodies, without importing BatchEnv (which builds
    # Fable's shared native library at import time). Their dependencies below
    # are real torch/numpy/model functions; only the test simulator is a double.
    tree = ast.parse(source)
    tree.body = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                 or isinstance(node, ast.ImportFrom) and node.module == '__future__']
    namespace = dict(np=np, torch=torch, F=F, math=math, random=random,
                     collections=collections, dataclass=dataclass,
                     FogPolicy=FogPolicy, masked_log_softmax=masked_log_softmax,
                     __name__=__name__)
    exec(compile(tree, 'pinned-rl-train', 'exec'), namespace)
    return namespace


class FixedAssignment(random.Random):
    def randrange(self, *args, **kwargs):
        return 0


class LabelEnv:
    """One decision ends in a draw; truth labels can vary independently of input."""
    n = 1

    def __init__(self, labels=(0, 1)):
        self.labels = np.array(labels, dtype=np.int32)
        self.actions = []
        self.queries = []
        self.stepped = False

    def side_to_move(self, i):
        return 0

    def take_events(self, i, side):
        return np.zeros((1, 32, 8, 8), np.float32), np.zeros((1, 8), np.float32)

    def candidates(self, i):
        return tuple(np.array(x, dtype=np.int32) for x in ([8, 9], [16, 17], [0, 0]))

    def board(self, i):
        return 'RNBQKBNRPPPPPPPP' + '-' * 32 + 'pppppppprnbqkbnr'

    def danger(self, i):
        if self.stepped:
            raise AssertionError('labels were queried after the move')
        self.queries.append(i)
        return self.labels  # Intentionally reused buffer: collector must copy.

    def step_all(self, actions):
        self.stepped = True
        self.actions.append(actions.copy())
        return np.array([3], dtype=np.int32)

    def reset(self, i):
        self.stepped = False


class TinyCritic(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.value = torch.nn.Linear(13 * 64, 1)

    def forward(self, x):
        return self.value(x.flatten(1)).squeeze(-1)


class RLRiskIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)
        manifest = json.loads((HERE / 'rl-risk-integration-manifest.json').read_text())
        original = (ROOT / manifest['source_path']).read_bytes()
        patch = HERE / 'rl_risk_auxiliary.patch'
        sha = lambda b: hashlib.sha256(b).hexdigest()
        if sha(original) != manifest['source_sha256'] or sha(patch.read_bytes()) != manifest['patch_sha256']:
            raise RuntimeError('source or patch changed; review and repin before testing')
        with tempfile.TemporaryDirectory(prefix='astra-rl-risk-review-') as temp:
            source = Path(temp) / 'learning/rl_train.py'
            source.parent.mkdir()
            source.write_bytes(original)
            subprocess.run(['patch', '--quiet', '--batch', '--fuzz=0', '-p1', '-i', str(patch)],
                           cwd=temp, check=True, capture_output=True)
            changed = source.read_bytes()
        if sha(changed) != manifest['patched_sha256']:
            raise RuntimeError('patched source differs from reviewed hash')
        cls.base = functions_from_source(original.decode())
        cls.patched = functions_from_source(changed.decode())

    def model(self):
        torch.manual_seed(42)
        return FogPolicy(channels=8, blocks=1, hidden=16, cand_width=16)

    def collect(self, namespace, model, labels=(0, 1), enabled=None):
        env = LabelEnv(labels)
        member = namespace['Member']('reference', copy.deepcopy(model), 1.)
        kwargs = {} if enabled is None else {'collect_risk': enabled}
        collector = namespace['Rollout'](env, model, copy.deepcopy(model), [member],
                                         torch.device('cpu'), FixedAssignment(1), **kwargs)
        torch.manual_seed(52)
        transitions, _ = collector.collect(1)
        return env, transitions

    def update_once(self, namespace, model, transitions, config):
        torch.manual_seed(61)
        np.random.seed(61)
        critic = TinyCritic()
        opt = torch.optim.SGD(model.parameters(), lr=.01)
        opt_c = torch.optim.SGD(critic.parameters(), lr=.01)
        n = len(transitions)
        return namespace['update'](model, critic, opt, opt_c, transitions,
                                   np.linspace(-1, 1, n, dtype=np.float32),
                                   np.zeros(n, np.float32), np.zeros((n, 13, 8, 8), np.float32),
                                   config, torch.device('cpu'))

    @staticmethod
    def config(**extra):
        return dict(minibatch=2, epochs=1, clip=.2, kl_ref_coef=.1,
                    entropy_coef=.01, grad_clip=1., **extra)

    def test_disabled_patch_preserves_original_rollout_and_update(self):
        a, b = self.model(), self.model()
        ea, ta = self.collect(self.base, a)
        eb, tb = self.collect(self.patched, b, enabled=False)
        self.assertEqual(eb.queries, [])
        self.assertNotIn('danger', tb[0])
        np.testing.assert_array_equal(ea.actions, eb.actions)
        self.assertEqual(ta[0]['old_logp'], tb[0]['old_logp'])
        sa = self.update_once(self.base, a, ta * 2, self.config())
        sb = self.update_once(self.patched, b, tb * 2, self.config())
        self.assertEqual(sa, sb)
        for name, value in a.state_dict().items():
            torch.testing.assert_close(value, b.state_dict()[name], atol=0, rtol=0)
        self.assertIsNone(b.danger_out.weight.grad)

    def test_truth_labels_are_copied_before_step_and_never_affect_sampling(self):
        a, b = self.model(), self.model()
        ea, ta = self.collect(self.patched, a, (0, 1), True)
        eb, tb = self.collect(self.patched, b, (1, 0), True)
        np.testing.assert_array_equal(ea.actions, eb.actions)
        self.assertEqual(ta[0]['old_logp'], tb[0]['old_logp'])
        self.assertEqual(ea.queries, [0])
        ea.labels[:] = 1
        np.testing.assert_array_equal(ta[0]['danger'], [0, 1])
        np.testing.assert_array_equal(tb[0]['danger'], [1, 0])

    def test_enabled_update_trains_existing_danger_head(self):
        model = self.model()
        _, trans = self.collect(self.patched, model, enabled=True)
        before = model.danger_out.weight.detach().clone()
        stats = self.update_once(self.patched, model, trans * 2,
                                 self.config(risk_aux_coef=1., risk_separation_coef=.25))
        self.assertTrue(bool(torch.isfinite(model.danger_out.weight.grad).all()))
        self.assertGreater(float(model.danger_out.weight.grad.abs().sum()), 0)
        self.assertFalse(torch.equal(before, model.danger_out.weight))
        self.assertEqual(stats['risk_contrast_decisions'], 2.)
        self.assertGreater(stats['risk_bce'], 0.)

    def test_rejects_missing_labels_and_invalid_configuration(self):
        model = self.model()
        _, trans = self.collect(self.patched, model, enabled=False)
        with self.assertRaisesRegex(ValueError, 'require labels'):
            self.update_once(self.patched, model, trans, self.config(risk_aux_coef=1.))
        for cfg in [{'risk_aux_coef': -1.}, {'risk_aux_coef': float('nan')},
                    {'risk_separation_coef': .25}]:
            with self.assertRaises(ValueError):
                self.patched['risk_coefficients'](cfg)
        with self.assertRaisesRegex(ValueError, 'binary'):
            self.collect(self.patched, self.model(), (0, 7), True)


if __name__ == '__main__':
    unittest.main()
