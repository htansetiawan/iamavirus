"""Small stationary mixture of conditional logits. CPU, float64, no team inputs."""
import gzip
import hashlib
import json
import struct
from pathlib import Path

import numpy as np
import torch

STATIC = 39
ALL_FEATURES = 91


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


class Data:
    def __init__(self, path, base):
        with gzip.open(path, 'rb') as f:
            payload = f.read()
        assert struct.unpack_from('<4i', payload) == (0x54503131, 39, 52, 95)
        heads, xs, zs, masks = [], [], [], []
        off = 16
        while off < len(payload):
            h = struct.unpack_from('<9i', payload, off)
            off += 36
            n = h[4]
            assert 0 < n <= 256 and 0 <= h[5] < n
            a = np.frombuffer(payload, dtype='<f4', count=n * 95, offset=off).reshape(n, 95)
            idx = a[:, 91:94].astype(np.int64)
            assert np.all((0 <= idx[:, 0]) & (idx[:, 0] < 6))
            assert np.all((0 <= idx[:, 1:]) & (idx[:, 1:] < 64))
            x = a[:, :STATIC].astype(np.float64)
            xs.append(x)
            zs.append(x @ base[:STATIC] + base[ALL_FEATURES + 64 * idx[:, 0] + idx[:, 1]]
                      + base[ALL_FEATURES + 384 + 64 * idx[:, 0] + idx[:, 2]])
            masks.append(a[:, -1] > .5)
            heads.append(h)
            off += 4 * n * 95
        assert off == len(payload)
        del payload
        self.head = np.asarray(heads, dtype=np.int64)
        self.N = len(heads)
        self.counts = self.head[:, 4]
        self.starts = np.r_[0, np.cumsum(self.counts)]
        self.X = torch.from_numpy(np.concatenate(xs))
        self.base = torch.from_numpy(np.concatenate(zs))
        self.compatible = torch.from_numpy(np.concatenate(masks))
        self.seg = torch.from_numpy(np.repeat(np.arange(self.N), self.counts))
        self.played = torch.from_numpy(self.starts[:-1] + self.head[:, 5])
        _, seq = np.unique(self.head[:, 0] * 2 + self.head[:, 2], return_inverse=True)
        self.group = torch.from_numpy(seq)
        self.G = int(seq.max()) + 1
        compat = self.compatible.numpy()
        self.ambiguous = (np.add.reduceat(compat, self.starts[:-1]) > 1) & compat[self.played.numpy()]
        self.observation_valid = compat[self.played.numpy()]
        for g in range(self.G):
            plies = self.head[seq == g, 1]
            assert np.all(np.diff(plies) > 0)


def segment_logsumexp(d, logits, compatible=False):
    """Reduce legal actions to decisions; max is detached for stable gradients."""
    ix = d.seg[:, None].expand_as(logits)
    z = logits
    if compatible:
        z = torch.where(d.compatible[:, None], z, torch.full_like(z, -1e100))
    maxima = torch.full((d.N, logits.shape[1]), -1e100, dtype=z.dtype)
    maxima.scatter_reduce_(0, ix, z.detach(), 'amax')
    e = torch.exp(z - maxima[d.seg])
    if compatible:
        e = e * d.compatible[:, None]
    sums = torch.zeros_like(maxima).index_add(0, d.seg, e)
    return maxima + torch.log(sums.clamp_min(1e-300))


def expert_logprobs(d, delta):
    z = d.base[:, None] + d.X @ delta.T
    denominator = segment_logsumexp(d, z)
    return z[d.played] - denominator, z, denominator


def objective(d, delta, alpha, l2=.001):
    played, _, _ = expert_logprobs(d, delta)
    sequence = torch.zeros((d.G, delta.shape[0]), dtype=delta.dtype).index_add(0, d.group, played)
    ll = torch.logsumexp(sequence + torch.log_softmax(alpha, 0), 1).sum()
    return -ll / d.N + .5 * l2 * delta.square().sum()


def np_lse(a, axis=None):
    m = np.max(a, axis=axis, keepdims=True)
    out = m + np.log(np.exp(a - m).sum(axis=axis, keepdims=True))
    return out.squeeze(axis=axis) if axis is not None else out.item()


def online_scores(head, played, observed, logprior, valid):
    """Score before updating. Both adapted arms still assume known true parents."""
    n, k = played.shape
    result = {mode: {key: np.zeros(n) for key in ('logp', 'conditional_logp', 'observation_logp')}
              for mode in ('reset', 'view_history', 'true_move_history')}
    weights = {mode: {} for mode in ('view_history', 'true_move_history')}
    for i, h in enumerate(head):
        group = (int(h[0]), int(h[2]))
        for mode in result:
            before = logprior if mode == 'reset' else weights[mode].get(group, logprior)
            lp = np_lse(before + played[i])
            lo = np_lse(before + observed[i]) if valid[i] else float('nan')
            result[mode]['logp'][i] = lp
            result[mode]['conditional_logp'][i] = lp - lo
            result[mode]['observation_logp'][i] = lo
            if mode != 'reset':
                # The terminal move has no matching nonterminal observation class.
                # It is still scored unconditionally, and has no next prediction.
                evidence = played[i] if mode == 'true_move_history' else observed[i]
                if mode == 'true_move_history' or valid[i]:
                    after = before + evidence
                    weights[mode][group] = after - np_lse(after)
    return result


@torch.no_grad()
def scores(d, delta, alpha):
    played, z, den = expert_logprobs(d, delta)
    observed = segment_logsumexp(d, z, compatible=True) - den
    return online_scores(d.head, played.numpy(), observed.numpy(),
                         torch.log_softmax(alpha, 0).numpy(), d.observation_valid)


def fit(d, k, seed=11012027):
    import time
    torch.manual_seed(seed)
    delta = ((torch.randn((k, STATIC), dtype=torch.float64) * .05) if k > 1
             else torch.zeros((1, STATIC), dtype=torch.float64)).requires_grad_()
    alpha = torch.zeros(k, dtype=torch.float64, requires_grad=True)
    optimizer = torch.optim.LBFGS([delta, alpha], lr=1, max_iter=120, max_eval=160,
                                 tolerance_grad=1e-7, tolerance_change=1e-10,
                                 history_size=15, line_search_fn='strong_wolfe')
    trace = []
    start = time.monotonic()

    def closure():
        optimizer.zero_grad()
        loss = objective(d, delta, alpha)
        loss.backward()
        trace.append(float(loss.detach()))
        if len(trace) % 10 == 0:
            print(json.dumps({'experts': k, 'evaluations': len(trace), 'objective': trace[-1],
                              'seconds': time.monotonic() - start}), flush=True)
        return loss

    optimizer.step(closure)
    closure()
    return delta.detach(), alpha.detach(), {'trace': trace, 'seconds': time.monotonic() - start,
          'max_gradient': max(float(delta.grad.abs().max()), float(alpha.grad.abs().max())),
          'optimizer_iterations': optimizer.state[delta]['n_iter']}
