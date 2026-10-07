import copy
import unittest

import torch

from learning_experiments.models import ModelConfig
from learning_experiments.ssl import ActorHistory, MaskedTeacherStudent, mask_observation, representation_diagnostics


class SSLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)

    def test_targets_are_not_required_or_read(self):
        record = {"actor": {"side": 0, "observations": ["?" * 64],
                            "phases": [0], "plies": [0],
                            "decision_event_indices": [], "own_actions": []},
                  "metadata": {"game_id": "example1"}}
        first = ActorHistory.from_record(record)
        changed = copy.deepcopy(record)
        changed["targets"] = object()  # not even a valid label record
        second = ActorHistory.from_record(changed)
        self.assertEqual(first, second)
        self.assertFalse(hasattr(first, "targets"))

    def test_actual_observation_symbols_distinguish_empty_and_fog_for_both_colors(self):
        for side in (0, 1):
            history = ActorHistory('sample00', side, ['P-?' + '?' * 61], [0], [0], {})
            symbols = history.observed_symbols().flatten()
            offset = 56 if side else 0
            self.assertEqual(symbols[offset], 6 if side else 0)
            self.assertEqual(symbols[offset + 1], 12)
            self.assertEqual(symbols[offset + 2], -1)

    def test_collapse_diagnostics_distinguish_constant_and_diverse_representations(self):
        collapsed = representation_diagnostics(torch.ones(16, 64))
        self.assertEqual(collapsed['effective_covariance_rank'], 0)
        diverse = representation_diagnostics(torch.eye(64))
        self.assertGreater(diverse['effective_covariance_rank'], 60)
        self.assertLess(diverse['largest_variance_share'], 0.02)

    def test_mask_removes_all_square_channels_without_mutating_input(self):
        planes = torch.rand(2, 32, 8, 8)
        before = planes.clone()
        mask = torch.zeros(2, 8, 8, dtype=torch.bool)
        mask[:, 3, 5] = True
        altered = mask_observation(planes, mask)
        expected = torch.zeros(32)
        expected[12] = expected[28] = 1
        torch.testing.assert_close(altered[:, :, 3, 5], expected.expand(2, -1))
        torch.testing.assert_close(planes, before, rtol=0, atol=0)
        torch.testing.assert_close(altered[:, :, 4, 4], planes[:, :, 4, 4])

    def test_teacher_is_detached_updates_only_by_ema_and_padding_does_not_advance(self):
        torch.manual_seed(81)
        system = MaskedTeacherStudent(ModelConfig("attention"))
        system.train()
        self.assertFalse(system.teacher.training)
        planes = torch.zeros(2, 3, 32, 8, 8)
        planes[:, :, 13] = 1  # visibly empty; self-supervised observation target
        planes[0, 0, 0, 0, 0] = 1
        planes[0, 0, 13, 0, 0] = 0
        scalars = torch.rand(2, 3, 8)
        lengths = torch.tensor([1, 3])
        hs = system.student.initial_hidden(2)
        ht = system.teacher.initial_hidden(2)
        before = [p.detach().clone() for p in system.teacher.parameters()]
        symbols = torch.full((2, 3, 8, 8), 12, dtype=torch.long)
        symbols[0, 0, 0, 0] = 0
        loss, metrics, sh, th = system.window_loss(
            planes, scalars, lengths, hs, ht, torch.Generator().manual_seed(8),
            observed_symbols=symbols)
        self.assertEqual(metrics["events"], 4)
        self.assertGreater(metrics["masked_observed_squares"], 0)
        self.assertTrue(torch.isfinite(loss))
        loss.backward()
        self.assertTrue(all(p.grad is None for p in system.teacher.parameters()))
        self.assertTrue(all(p.grad is None for p in system.teacher_projector.parameters()))
        self.assertIsNotNone(system.student.token_embed.weight.grad)
        optimizer = torch.optim.SGD([p for p in system.parameters() if p.requires_grad], lr=0.01)
        optimizer.step()
        for old, target in zip(before, system.teacher.parameters()):
            torch.testing.assert_close(old, target, atol=0, rtol=0)
        with torch.no_grad():
            expected = system.teacher.observe(planes[:1, 0], scalars[:1, 0], ht[:1])[0]
        torch.testing.assert_close(th[:1], expected, atol=1e-6, rtol=1e-5)
        system.update_teacher(0.5)
        for old, target, online in zip(before, system.teacher.parameters(), system.student.parameters()):
            torch.testing.assert_close(target, (old + online) * 0.5)

    def test_unknown_squares_never_become_reconstruction_labels(self):
        system = MaskedTeacherStudent(ModelConfig("compressed_attention"))
        planes = torch.zeros(2, 1, 32, 8, 8)
        planes[:, :, 12] = 1
        loss, metrics, _, _ = system.window_loss(
            planes, torch.zeros(2, 1, 8), torch.ones(2, dtype=torch.long),
            system.student.initial_hidden(2), system.teacher.initial_hidden(2),
            observed_symbols=torch.full((2, 1, 8, 8), -1, dtype=torch.long))
        self.assertEqual(metrics["masked_observed_squares"], 0)
        self.assertEqual(metrics["observed_reconstruction_loss"], 0)
        self.assertTrue(torch.isfinite(loss))

    def test_visible_empty_is_masked_even_with_legacy_plane12(self):
        system = MaskedTeacherStudent(ModelConfig('attention'))
        history = ActorHistory('sample00', 0, ['-?' * 32], [0], [0], {})
        p, s = history.tensors()  # actual feature builder, not invented plane values
        planes = torch.from_numpy(p).unsqueeze(0).expand(2, -1, -1, -1, -1)
        scalars = torch.from_numpy(s).unsqueeze(0).expand(2, -1, -1)
        symbols = torch.from_numpy(history.observed_symbols()).unsqueeze(0).expand(2, -1, -1, -1)
        _, metrics, _, _ = system.window_loss(
            planes, scalars, torch.ones(2, dtype=torch.long),
            system.student.initial_hidden(2), system.teacher.initial_hidden(2),
            torch.Generator().manual_seed(10),
            observed_symbols=symbols)
        self.assertGreater(metrics['masked_observed_squares'], 0)
        self.assertEqual(metrics['masked_observed_pieces'], 0)


if __name__ == "__main__":
    unittest.main()
