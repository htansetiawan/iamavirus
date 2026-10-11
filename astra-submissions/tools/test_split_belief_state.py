import unittest
import torch
from learning_experiments.models import ModelConfig,make_model
from split_belief_state import CurrentEventBelief


class SplitBeliefTests(unittest.TestCase):
    def test_preserves_recurrence_and_other_heads_exactly(self):
        torch.set_num_threads(2);torch.manual_seed(83)
        for variant in ['cnn','attention']:
            with self.subTest(variant=variant),torch.no_grad():
                base=make_model(ModelConfig(variant)).eval();adapter=CurrentEventBelief(base).eval()
                state=torch.randn(2,256);ours=state.clone()
                for _ in range(4):
                    planes=torch.randn(2,32,8,8);scalars=torch.randn(2,8)
                    full=base.observe(planes,scalars,state);cold=base.observe(planes,scalars,torch.zeros_like(state))
                    split=adapter.observe(planes,scalars,ours)
                    for k in [0,1,3]:torch.testing.assert_close(full[k],split[k],atol=0,rtol=0)
                    torch.testing.assert_close(cold[2],split[2],atol=0,rtol=0)
                    f=torch.tensor([[0,1],[2,3]]);t=torch.tensor([[8,9],[10,11]]);p=torch.zeros_like(f)
                    for a,b in zip(base.score(full[0],full[1],f,t,p),adapter.score(split[0],split[1],f,t,p)):
                        torch.testing.assert_close(a,b,atol=0,rtol=0)
                    state,ours=full[0],split[0]

    def test_rejects_compressed_latent_contract(self):
        with self.assertRaises(ValueError):
            CurrentEventBelief(make_model(ModelConfig('compressed_attention')))


if __name__=='__main__':unittest.main()
