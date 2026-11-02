"""Segmented probability calculations: one normalization per parent and case."""
import numpy as np
import torch


def logsum(z, segment, n, mask=None):
    if mask is not None:
        z = torch.where(mask, z, torch.full_like(z, -1e300))
    maximum = torch.full((n,), -1e300, dtype=z.dtype, device=z.device)
    maximum.scatter_reduce_(0, segment, z.detach(), 'amax', include_self=True)
    e = (z - maximum[segment]).exp()
    if mask is not None:
        e = e * mask
    sums = torch.zeros_like(maximum).index_add_(0, segment, e)
    return maximum + sums.clamp_min(1e-300).log()


class Dataset:
    def __init__(self, cases, device):
        self.meta = [row['meta'] for row in cases]
        self.n = len(cases); self.parents = sum(len(row['u']) for row in cases)
        p_offsets = np.cumsum([0] + [len(row['u']) for row in cases[:-1]])
        values = {name: np.concatenate([row[name] for row in cases])
                  for name in ('x', 'base', 'counts', 'u', 'hn', 'valid', 'positive', 'actor_edge', 'actor_parent')}
        values['a_parent'] = np.concatenate([row['a_parent'] + offset for row, offset in zip(cases, p_offsets)])
        values['a_case'] = np.concatenate([np.full(len(row['base']), i, np.int64) for i, row in enumerate(cases)])
        values['p_case'] = np.concatenate([np.full(len(row['u']), i, np.int64) for i, row in enumerate(cases)])
        for name, value in values.items():
            dtype = torch.long if name in ('a_parent', 'a_case', 'p_case') else torch.bool if value.dtype == bool else torch.float64
            setattr(self, name, torch.tensor(value, dtype=dtype, device=device))
        # Give games equal total influence despite different exact-prefix lengths.
        game_n = {}
        for row in self.meta:
            game_n[row['game']] = game_n.get(row['game'], 0) + 1
        self.weight = torch.tensor([1 / game_n[row['game']] for row in self.meta], dtype=torch.float64, device=device)
        self.weight /= self.weight.sum()


def scores(data, theta):
    z = data.base + data.x @ theta
    logp = z - logsum(z, data.a_parent, data.parents)[data.a_parent]
    logh = torch.where(data.counts > 0, data.counts.clamp_min(1).log(), torch.full_like(data.counts, -torch.inf))
    hn = data.hn[data.a_parent]
    blend = torch.logaddexp(logh, logp + np.log(4.)) - (hn + 4).log()
    logp = torch.where(hn >= 3, blend, logp)
    edge = data.u[data.a_parent] + 2 * logp
    posterior = logsum(edge, data.a_case, data.n, data.positive) - logsum(edge, data.a_case, data.n, data.valid)
    # Recorded-move likelihood averaged over naturally retained true-parent histories.
    actor = logsum(data.u[data.a_parent] + logp, data.a_case, data.n, data.actor_edge)
    actor = actor - logsum(data.u, data.p_case, data.n, data.actor_parent)
    return posterior, actor


def objective(data, theta, kind, ridge):
    posterior, actor = scores(data, theta)
    selected = posterior if kind == 'posterior' else actor
    return -(selected * data.weight).sum() + ridge * theta.square().sum()
