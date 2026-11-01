import copy
import json
from pathlib import Path
import unittest

import numpy as np
import torch

import data
import model

torch.set_num_threads(2)


class Tests(unittest.TestCase):
    def setUp(self):
        self.replay = json.loads((data.ROOT/'data/raw/games/irxgf70v/replay.json').read_text())

    def test_private_inputs_only(self):
        for side in [0, 1]:
            altered = copy.deepcopy(self.replay)
            for frame in altered['frames']:
                frame['board'] = 'X'*64; frame[['black', 'white'][side]] = 'X'*64
            original = list(data.actor_decisions(self.replay, side))
            redacted = list(data.actor_decisions(altered, side))
            self.assertEqual(len(original), len(redacted))
            for x, y in zip(original, redacted):
                self.assertEqual(x[0], y[0]); np.testing.assert_array_equal(x[1], y[1]); self.assertEqual(x[2:], y[2:])

    def test_current_label_cannot_change_input(self):
        for side in [0, 1]:
            first = next(data.actor_decisions(self.replay, side))
            altered = copy.deepcopy(self.replay)
            altered['frames'][side+1]['move'] = next(m for m in first[2] if m != first[3])
            changed = next(data.actor_decisions(altered, side))
            np.testing.assert_array_equal(first[1], changed[1]); self.assertEqual(first[2], changed[2]); self.assertNotEqual(first[3], changed[3])

    def test_black_canonicalization(self):
        view = self.replay['frames'][0]['white']
        mirror = ''.join(view[i^56].swapcase() for i in range(64))
        np.testing.assert_array_equal(data.encode_view(view, 0), data.encode_view(mirror, 1))
        self.assertEqual(data.encode_move('e2e4', 0), data.encode_move('e7e5', 1))
        self.assertEqual(data.encode_move('a7a8n', 0), data.encode_move('a2a1n', 1))
        self.assertNotEqual(data.encode_view('?'*64, 0)[0], data.encode_view('-'*64, 0)[0])

    def test_mask_order_and_gradients(self):
        _, obs, legal, _ = next(data.actor_decisions(self.replay, 0))
        tokens = torch.tensor(obs.copy()).long()[None]
        actions = torch.tensor([[data.encode_move(m, 0) for m in legal]])
        for cls in [model.LinearPolicy, model.StudentPolicy, model.TeacherPolicy]:
            net = cls().eval(); original = net(tokens, actions)
            torch.testing.assert_close(net(tokens, actions.flip(1)), original.flip(1), atol=1e-6, rtol=1e-6)
            padded = torch.cat([actions, torch.zeros((1, 3), dtype=torch.long)], 1)
            mask = torch.arange(padded.shape[1])[None] < len(legal)
            lp = model.masked_log_probs(net(tokens, padded), mask)
            torch.testing.assert_close(lp.exp().sum(1), torch.ones(1))
            torch.testing.assert_close(lp[:, :len(legal)], torch.log_softmax(original, -1))
            self.assertTrue((lp.exp()[:, len(legal):] == 0).all())
            (-lp[0, 0]).backward()
            self.assertTrue(all(torch.isfinite(p.grad).all() for p in net.parameters() if p.grad is not None))

    def test_distillation_with_padding(self):
        logits = torch.tensor([[2., -1., 8.], [.1, .4, -.3]], requires_grad=True)
        teacher = torch.tensor([[1., 0., -7.], [.8, -.2, .4]])
        mask = torch.tensor([[True, True, False], [True, True, True]])
        q = model.masked_log_probs(teacher, mask, 2).exp()
        student = model.masked_log_probs(logits, mask, 2)
        kl = (q*(q.clamp_min(1e-30).log()-student)).sum(1)
        for row in range(2):
            t = torch.softmax(teacher[row,mask[row]]/2, 0)
            expected = torch.nn.functional.kl_div(torch.log_softmax(logits[row,mask[row]]/2, 0),t,reduction='sum')
            torch.testing.assert_close(kl[row], expected)
        kl.mean().backward(); self.assertTrue(torch.isfinite(logits.grad).all())
        self.assertEqual(float(logits.grad[0,2]),0.)


if __name__ == '__main__': unittest.main()
