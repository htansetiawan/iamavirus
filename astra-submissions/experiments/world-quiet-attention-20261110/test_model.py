"""Mathematical and candidate-layout contracts, not predictive evidence."""
from pathlib import Path
import importlib.util
import math
import unittest

import torch
from model import WorldQuietTeacher, quiet_logp

ROOT = Path(__file__).resolve().parents[3]
old_path = ROOT / 'astra-submissions/experiments/capture-fixed-prior-20261110/model.py'
spec = importlib.util.spec_from_file_location('original293model', old_path)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)


class PriorContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)

    def setUp(self):
        torch.manual_seed(3191110)
        self.base = torch.randn(7, 11)
        self.valid = torch.ones(7, 11, dtype=torch.bool)
        self.valid[3:, -3:] = False
        self.capture = torch.rand(7, 11) > .6
        self.capture[0] = True
        self.capture[1] = True; self.capture[1, 0] = False
        self.counts = torch.zeros(7, 11)
        self.counts[2, :8] = torch.arange(8).float()
        self.total = torch.tensor([0., 1., 34., 0., 0., 100., 2.])

    def logp(self, residual):
        return quiet_logp(self.base, residual, self.valid, self.capture, self.counts, self.total)

    def test_identity_and_zero_singleton_quiet(self):
        baseline = self.logp(torch.zeros_like(self.base))
        reference = self.base.masked_fill(~self.valid, -torch.inf).log_softmax(-1)
        assert torch.equal(baseline[self.total < 3], reference[self.total < 3])
        changed = self.logp(torch.randn_like(self.base) * 10)
        assert torch.equal(changed[:2], baseline[:2])

    def test_capture_exact_and_zero_capture_gradient(self):
        residual = torch.randn_like(self.base, requires_grad=True)
        baseline = self.logp(torch.zeros_like(self.base))
        changed = self.logp(residual)
        capture = self.capture & self.valid
        assert torch.equal(changed[capture], baseline[capture])
        (-changed[capture].sum()).backward()
        assert torch.isfinite(residual.grad).all()
        assert torch.count_nonzero(residual.grad) == 0

    def test_finite_quiet_gradient_with_padding_and_empty_quiet(self):
        residual = torch.randn_like(self.base, requires_grad=True)
        changed = self.logp(residual)
        assert torch.isfinite(changed[self.valid]).all()
        assert torch.isneginf(changed[~self.valid]).all()
        (-changed[self.valid].sum()).backward()
        assert torch.isfinite(residual.grad).all()
        assert torch.count_nonzero(residual.grad) > 0
        assert torch.count_nonzero(residual.grad[~self.valid]) == 0

    def test_capture_and_quiet_mass_before_history(self):
        self.total.zero_();self.counts.zero_()
        p0 = self.logp(torch.zeros_like(self.base)).exp()
        p = self.logp(torch.randn_like(self.base) * 4).exp()
        quiet = self.valid & ~self.capture
        torch.testing.assert_close(p.sum(-1), torch.ones(7), atol=2e-6, rtol=0)
        torch.testing.assert_close((p * quiet).sum(-1), (p0 * quiet).sum(-1), atol=2e-6, rtol=0)
        assert torch.equal(p[self.capture], p0[self.capture])

    def test_native_history_deficit_not_renormalized(self):
        self.total.fill_(100); self.counts.zero_()
        changed = self.logp(torch.randn_like(self.base)).exp()
        torch.testing.assert_close(changed.sum(-1), torch.full((7,), 4 / 104), atol=1e-7, rtol=0)
        reference = self.base.log_softmax(-1)[0, 0].item() + math.log(4) - math.log(104)
        assert abs(self.logp(torch.randn_like(self.base))[0, 0].item() - reference) < 1e-6

    def test_exact_original293_math(self):
        x = torch.randn(7, 11, 26)
        linear = torch.randn(22) * .1
        quadratic = torch.randn(22, 22) * .03 * old.mask(22)
        features = x[:, :, old.COLUMNS]
        residual = features @ linear + torch.sum((features @ quadratic) * features, dim=-1)
        data = dict(x=x, base=torch.stack((self.base, self.base), dim=-1), valid=self.valid,
                    capture=self.capture, counts=self.counts, history_n=self.total)
        expected = old.logp(data, torch.arange(7), 22, linear, quadratic)
        actual = self.logp(residual)
        assert torch.equal(actual, expected)

    def test_teacher_identity_and_candidate_permutation(self):
        model = WorldQuietTeacher().eval()
        batch = 3
        arguments = [torch.randint(0, 13, (batch, 64)), torch.randint(0, 4, (batch, 64)),
                     torch.randint(0, 2, (batch, 64)), torch.zeros(batch, 64, dtype=torch.long),
                     torch.arange(batch).float(), torch.tensor([0, 1, 0])]
        moves = torch.randint(0, 4096, (batch, 11))
        moves[:, 0] |= 4 << 12
        features = torch.randn(batch, 11, 26)
        with torch.no_grad():
            encoded = model.encode_board(*arguments)
            assert torch.count_nonzero(model.score_moves(encoded, moves, features)) == 0
            model.head[-1].weight.normal_(0, .02)
            a = model.score_moves(encoded, moves, features)
            permutation = torch.randperm(11)
            b = model.score_moves(encoded, moves[:, permutation], features[:, permutation])
            torch.testing.assert_close(a[:, permutation], b, atol=2e-6, rtol=0)
            partial = model.score_moves(encoded, moves[:, :4], features[:, :4])
            torch.testing.assert_close(a[:, :4], partial, atol=2e-6, rtol=0)
            assert torch.isfinite(a).all() and torch.count_nonzero(a) > 0

    def test_teacher_backpropagates_through_board_and_latents(self):
        model = WorldQuietTeacher(width=32)
        with torch.no_grad():model.head[-1].weight.normal_(0, .02)
        args = [torch.randint(0, 13, (2, 64)), torch.randint(0, 4, (2, 64)),
                torch.zeros(2, 64, dtype=torch.long), torch.zeros(2, 64, dtype=torch.long),
                torch.zeros(2), torch.tensor([0, 1]), torch.randint(0, 4096, (2, 8)), torch.randn(2, 8, 26)]
        output = model(*args)
        base = torch.randn(2, 8);valid = torch.ones(2, 8, dtype=torch.bool)
        lp = quiet_logp(base, output, valid, ~valid, torch.zeros(2, 8), torch.zeros(2))
        (-lp[:, 0].mean()).backward()
        assert all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
        assert torch.count_nonzero(model.piece.weight.grad) > 0
        assert torch.count_nonzero(model.latent_queries.grad) > 0


if __name__ == '__main__':
    unittest.main()
