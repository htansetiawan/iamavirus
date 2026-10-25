import unittest

import torch
from torch.nn import functional as F

from learning_experiments.risk_auxiliary import candidate_risk_loss


class RiskAuxiliaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)

    def test_bound_and_gradient_direction_against_explicit_pairs(self):
        generator = torch.Generator().manual_seed(19)
        for ns, nf in [(1, 1), (2, 7), (9, 3)]:
            for _ in range(8):
                z = torch.randn(1, ns + nf, generator=generator, dtype=torch.float64, requires_grad=True)
                y = torch.tensor([[0] * ns + [1] * nf])
                loss = candidate_risk_loss(z, y, torch.ones_like(y, dtype=torch.bool))
                exact = F.softplus(z[0, :ns, None] - z[0, None, ns:]).mean()
                self.assertGreaterEqual(float(loss.separation.detach()) + 1e-12, float(exact.detach()))
                if ns == nf == 1:
                    torch.testing.assert_close(loss.separation, exact)
                loss.separation.backward()
                self.assertTrue(bool((z.grad[0, :ns] > 0).all()))
                self.assertTrue(bool((z.grad[0, ns:] < 0).all()))

    def test_ranking_shift_invariance_but_bce_keeps_probability_offset(self):
        z = torch.tensor([[2., -3., 0., 4.]], dtype=torch.float64)
        y = torch.tensor([[0., 1., 0., 1.]])
        mask = torch.ones_like(y, dtype=torch.bool)
        base = candidate_risk_loss(z, y, mask)
        shifted = candidate_risk_loss(z + 37, y, mask)
        torch.testing.assert_close(base.separation, shifted.separation)
        self.assertGreater(float(shifted.bce), float(base.bce))
        torch.testing.assert_close(base.total, base.bce)

    def test_padding_never_affects_loss_or_gradient(self):
        small = torch.tensor([[2., -2.]], requires_grad=True)
        padded = torch.tensor([[2., -2., float('nan'), -float('inf')]], requires_grad=True)
        a = candidate_risk_loss(small, torch.tensor([[0., 1.]]), torch.tensor([[True, True]]), separation_coef=.5)
        b = candidate_risk_loss(padded, torch.tensor([[0., 1., float('nan'), 6.]]),
                                torch.tensor([[True, True, False, False]]), separation_coef=.5)
        torch.testing.assert_close(a.total, b.total)
        a.total.backward(); b.total.backward()
        torch.testing.assert_close(small.grad, padded.grad[:, :2])
        torch.testing.assert_close(padded.grad[:, 2:], torch.zeros(1, 2))

    def test_single_class_empty_and_zero_weight_have_finite_gradients(self):
        for shape, labels, mask in [
            ((2, 3), [[0., 0., 0.], [1., 1., 1.]], [[True] * 3] * 2),
            ((2, 3), [[float('nan')] * 3] * 2, [[False] * 3] * 2),
            ((0, 3), [], []), ((2, 0), [[], []], [[], []]),
        ]:
            z = torch.zeros(shape, requires_grad=True)
            y = torch.tensor(labels).reshape(shape)
            m = torch.tensor(mask, dtype=torch.bool).reshape(shape)
            loss = candidate_risk_loss(z, y, m, separation_coef=1.)
            self.assertEqual(float(loss.separation.detach()), 0.)
            loss.total.backward()
            self.assertTrue(bool(torch.isfinite(z.grad).all()))
        z = torch.tensor([[2., -2.]], requires_grad=True)
        result = candidate_risk_loss(z, torch.tensor([[0., 1.]]), torch.tensor([[True, True]]),
                                     separation_coef=1., decision_weights=torch.zeros(1))
        result.total.backward()
        self.assertEqual(float(result.total.detach()), 0.)
        torch.testing.assert_close(z.grad, torch.zeros_like(z))

    def test_decision_weighting_and_duplicate_candidate_invariance(self):
        z = torch.tensor([[1., -2.], [0., 4.]], dtype=torch.float64)
        y = torch.tensor([[0., 1.], [0., 1.]])
        mask = torch.ones_like(y, dtype=torch.bool)
        weights = torch.tensor([1., 3.], dtype=torch.float64)
        result = candidate_risk_loss(z, y, mask, separation_coef=.25, decision_weights=weights)
        rows = [candidate_risk_loss(z[i:i+1], y[i:i+1], mask[i:i+1], separation_coef=.25) for i in range(2)]
        torch.testing.assert_close(result.total, .25 * rows[0].total + .75 * rows[1].total)
        repeated = candidate_risk_loss(z.repeat_interleave(3, dim=1), y.repeat_interleave(3, dim=1),
                                      mask.repeat_interleave(3, dim=1), separation_coef=.25,
                                      decision_weights=weights * 1e300)
        torch.testing.assert_close(result.total, repeated.total)
        self.assertEqual((result.labelled_decisions, result.contrast_decisions), (2, 2))

    def test_extreme_half_precision_logits_promote_and_remain_finite(self):
        for dtype in [torch.float16, torch.bfloat16]:
            z = torch.tensor([[10000., -10000., -10000., 10000.]], dtype=dtype, requires_grad=True)
            result = candidate_risk_loss(z, torch.tensor([[0., 1., 0., 1.]]),
                                         torch.ones_like(z, dtype=torch.bool), separation_coef=.1)
            self.assertEqual(result.total.dtype, torch.float32)
            self.assertTrue(bool(torch.isfinite(result.total)))
            result.total.backward()
            self.assertTrue(bool(torch.isfinite(z.grad).all()))

    def test_rejects_bad_labelled_data_and_metadata(self):
        z = torch.tensor([[0., 1.]])
        y = torch.tensor([[0., 1.]])
        m = torch.tensor([[True, True]])
        bad_inputs = [
            (torch.tensor([[float('nan'), 1.]]), y, m, {}),
            (z, torch.tensor([[.5, 1.]]), m, {}),
            (z, y, m.float(), {}),
            (z, y, m, {'separation_coef': -1.}),
            (z, y, m, {'separation_coef': float('nan')}),
            (z, y, m, {'decision_weights': torch.tensor([-1.])}),
            (z, y, m, {'decision_weights': torch.tensor([float('inf')])}),
            (z, y, m, {'decision_weights': torch.ones(1, requires_grad=True)}),
            (z, y, m, {'decision_weights': torch.ones(2)}),
        ]
        for a, b, c, kwargs in bad_inputs:
            with self.assertRaises(ValueError):
                candidate_risk_loss(a, b, c, **kwargs)


if __name__ == '__main__':
    unittest.main()
