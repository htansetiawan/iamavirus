"""Synthetic reference-implementation contracts, without trained checkpoint use."""
import sys
from pathlib import Path
import unittest

import torch
from torch.nn.attention import SDPBackend, sdpa_kernel

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'world-quiet-attention-20261110'))
from model import WorldQuietTeacher, quiet_logp
from reference import forward


class ReferenceContracts(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(3251110); torch.set_num_threads(2)
        torch.set_float32_matmul_precision('highest')
        self.model = WorldQuietTeacher(width=16, latents=2).double().eval()
        with torch.no_grad(): self.model.head[-1].weight.normal_(std=.1)
        self.board = [torch.randint(13,(3,64)), torch.randint(4,(3,64)),
            torch.randint(2,(3,64)), torch.randint(2,(3,64)), torch.tensor([0.,20.,150.]).double(), torch.tensor([0,1,0])]
        self.moves = torch.randint(64*64,(3,9)) + 4096*torch.randint(5,(3,9))
        self.x = torch.randn(3,9,26,dtype=torch.float64)

    def test_grad_path_equivalence(self):
        # Grad-enabled eval is the original architecture without fused encoder.
        before = torch.backends.mha.get_fastpath_enabled()
        with torch.enable_grad(), sdpa_kernel(SDPBackend.MATH):
            original = self.model(*self.board,self.moves,self.x).detach()
        explicit = forward(self.model,*self.board,self.moves,self.x)
        torch.testing.assert_close(explicit,original,atol=2e-12,rtol=2e-12)
        self.assertEqual(before,torch.backends.mha.get_fastpath_enabled())
        self.assertFalse(explicit.requires_grad)

    def test_fused_operations_absent(self):
        with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as prof:
            forward(self.model,*self.board,self.moves,self.x)
        operations = {e.key for e in prof.key_averages()}
        self.assertNotIn('aten::_transformer_encoder_layer_fwd',operations)
        self.assertNotIn('aten::_native_multi_head_attention',operations)
        self.assertNotIn('aten::_addmm_activation',operations)
        self.assertIn('aten::_scaled_dot_product_attention_math',operations)
        self.assertIn('aten::gelu',operations)

    def test_candidate_and_batch_independence(self):
        full = forward(self.model,*self.board,self.moves,self.x)
        permutation = torch.tensor([3,1,8,4,7,0,2,5,6])
        permuted = forward(self.model,*self.board,self.moves[:,permutation],self.x[:,permutation])
        torch.testing.assert_close(full[:,permutation],permuted,atol=2e-12,rtol=2e-12)
        subset = forward(self.model,*self.board,self.moves[:,:4],self.x[:,:4])
        torch.testing.assert_close(full[:,:4],subset,atol=2e-12,rtol=2e-12)
        separate = torch.cat([forward(self.model,*[v[i:i+1] for v in self.board],self.moves[i:i+1],self.x[i:i+1]) for i in range(3)])
        torch.testing.assert_close(full,separate,atol=2e-12,rtol=2e-12)

    def test_capture_and_zero_identity(self):
        residual=forward(self.model,*self.board,self.moves,self.x)
        base=torch.randn(3,9,dtype=torch.float64);valid=torch.ones(3,9,dtype=torch.bool)
        capture=torch.zeros_like(valid);capture[:,::3]=True
        counts=torch.randint(4,(3,9)).double();total=counts.sum(-1)+torch.tensor([0,3,20])
        zero=quiet_logp(base,torch.zeros_like(residual),valid,capture,counts,total)
        learned=quiet_logp(base,residual,valid,capture,counts,total)
        self.assertTrue(torch.equal(learned[capture],zero[capture]))
        self.assertTrue(torch.isfinite(learned).all())
        for name,value in self.model.named_parameters(): self.assertIsNone(value.grad,name)

    def test_exception_restores_attention_selection(self):
        initial=[torch.backends.cuda.flash_sdp_enabled(),torch.backends.cuda.math_sdp_enabled(),torch.backends.cuda.mem_efficient_sdp_enabled()]
        bad=self.moves.clone();bad[0,0]=4096*5
        with self.assertRaises(IndexError):forward(self.model,*self.board,bad,self.x)
        current=[torch.backends.cuda.flash_sdp_enabled(),torch.backends.cuda.math_sdp_enabled(),torch.backends.cuda.mem_efficient_sdp_enabled()]
        self.assertEqual(initial,current)


if __name__ == '__main__': unittest.main()
