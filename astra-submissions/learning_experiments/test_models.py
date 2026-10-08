"""CPU correctness gates, including a real bottleneck and candidate ordering."""
import unittest

import torch

from learning.model import FogPolicy, parameter_count
from learning_experiments.models import ModelConfig, ResidualBottleneck, make_model


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)

    def inputs(self, batch=2, candidates=11):
        g = torch.Generator().manual_seed(123)
        return (torch.randn(batch, 32, 8, 8, generator=g),
                torch.randn(batch, 8, generator=g),
                torch.randn(batch, 256, generator=g),
                torch.randint(64, (batch, candidates), generator=g),
                torch.randint(64, (batch, candidates), generator=g),
                torch.randint(5, (batch, candidates), generator=g))

    def test_control_is_unchanged(self):
        torch.manual_seed(14)
        expected = FogPolicy()
        torch.manual_seed(14)
        actual = make_model(ModelConfig("cnn"))
        self.assertIs(type(actual), FogPolicy)
        self.assertEqual(parameter_count(actual), 1872394)
        self.assertEqual(list(actual.state_dict()), list(expected.state_dict()))
        for key, value in expected.state_dict().items():
            torch.testing.assert_close(value, actual.state_dict()[key], rtol=0, atol=0)

    def test_shapes_gradients_and_candidate_permutation(self):
        for variant in ("cnn", "attention", "compressed_attention"):
            with self.subTest(variant=variant):
                torch.manual_seed(42)
                model = make_model(ModelConfig(variant))
                planes, scalars, hidden, src, dst, promo = self.inputs()
                h, spatial, belief, value = model.observe(planes, scalars, hidden)
                self.assertEqual(h.shape, (2, 256))
                self.assertEqual(spatial.shape, (2, 64, 8, 8))
                self.assertEqual(belief.shape, (2, 64, 7))
                self.assertEqual(value.shape, (2, 1))
                policy, danger = model.score(h, spatial, src, dst, promo)
                order = torch.tensor([6, 10, 2, 5, 1, 8, 3, 0, 9, 7, 4])
                pp, dp = model.score(h, spatial, src[:, order], dst[:, order], promo[:, order])
                torch.testing.assert_close(pp, policy[:, order])
                torch.testing.assert_close(dp, danger[:, order])
                loss = policy.square().mean() + danger.square().mean() + belief.square().mean() + value.square().mean()
                loss.backward()
                for name, p in model.named_parameters():
                    self.assertIsNotNone(p.grad, name)
                    self.assertTrue(torch.isfinite(p.grad).all(), name)
                with torch.no_grad():
                    different = model.observe(planes, scalars, hidden + 0.3)[0]
                self.assertGreater((h - different).abs().max().item(), 1e-4)

    def test_bottleneck_is_not_bypassed(self):
        model = make_model(ModelConfig("compressed_attention"))
        planes, scalars, hidden, *_ = self.inputs()
        def discard_map(module, args, result):
            latent, decoded = result
            return torch.zeros_like(latent), torch.zeros_like(decoded)
        handle = model.bottleneck.register_forward_hook(discard_map)
        with torch.no_grad():
            first = model.observe(planes, scalars, hidden)
            second = model.observe(planes.flip(2) * 5, scalars, hidden)
        handle.remove()
        for a, b in zip(first, second):
            torch.testing.assert_close(a, b, atol=0, rtol=0)

    def test_larger_encoder_keeps_runtime_interface(self):
        config = ModelConfig("attention", attention_blocks=6,
                             attention_heads=8, attention_channels=256)
        model = make_model(config)
        small = make_model(ModelConfig("attention"))
        self.assertGreater(parameter_count(model), 2 * parameter_count(small))
        planes, scalars, hidden, src, dst, promo = self.inputs(batch=1)
        h, spatial, belief, value = model.observe(planes, scalars, hidden)
        self.assertEqual(h.shape, (1, 256))
        self.assertEqual(spatial.shape, (1, 64, 8, 8))
        policy, danger = model.score(h, spatial, src, dst, promo)
        self.assertEqual(policy.shape, src.shape)
        (policy.square().mean() + danger.square().mean() + belief.square().mean() + value.square().mean()).backward()
        for name, p in model.named_parameters():
            self.assertIsNotNone(p.grad, name)
            self.assertTrue(torch.isfinite(p.grad).all(), name)

    def test_old_attention_checkpoints_keep_parameter_contract(self):
        model = make_model(ModelConfig("attention"))
        self.assertFalse(any(k.startswith('spatial_adapter.') for k in model.state_dict()))
        # Older metadata omitted the width. Loading it must reconstruct the
        # exact old shape, including all recurrence and scoring parameters.
        old = ModelConfig(**dict(variant='attention', attention_blocks=2,
                                 attention_heads=4, latent_channels=32))
        restored = make_model(old)
        restored.load_state_dict(model.state_dict(), strict=True)
        args = self.inputs()
        with torch.no_grad():
            a, b = model.observe(*args[:3]), restored.observe(*args[:3])
        for x, y in zip(a, b):
            torch.testing.assert_close(x, y, rtol=0, atol=0)

    def test_residual_base_at_full_capacity_is_lossless(self):
        # With no channel reduction, the fixed rearrangement must be invertible.
        codec = ResidualBottleneck(256)
        spatial = torch.randn(2, 64, 8, 8)
        latent, decoded = codec(spatial)
        self.assertEqual(latent.numel(), spatial.numel())
        torch.testing.assert_close(decoded, spatial, rtol=0, atol=0)

    def test_compact_capacity_and_configuration_errors(self):
        codec = ResidualBottleneck(32)
        spatial = torch.randn(2, 64, 8, 8)
        latent, decoded = codec(spatial)
        self.assertEqual(spatial.numel(), latent.numel() * 8)
        self.assertEqual(decoded.shape, spatial.shape)
        self.assertLess(parameter_count(make_model(ModelConfig("compressed_attention"))),
                        parameter_count(make_model(ModelConfig("attention"))))
        for config in (ModelConfig("nope"), ModelConfig(attention_heads=3),
                       ModelConfig(latent_channels=31), ModelConfig(attention_blocks=0)):
            with self.assertRaises(ValueError):
                make_model(config)


if __name__ == "__main__":
    unittest.main()
