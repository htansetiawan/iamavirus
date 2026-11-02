"""Check the vectorized losses on 230 development cases, without fitting."""
import json
import numpy as np
import torch
from config import ROOT, PREVIOUS, StateKey, encode
from model import Dataset, scores
from objective import loss as loop_loss
from learning import ingest


def main():
    torch.set_num_threads(2)
    previous = ROOT / 'astra-submissions/analysis/posterior-objective-20261102'
    checked = json.loads((previous / 'gradient-checks.json').read_text())
    cases = json.loads((previous / 'cases.json').read_text())
    by_key = {(r['game'], r['ply']): r for r in cases}
    rows = []; originals = []
    for r in checked:
        record = by_key[r['game'], r['ply']]
        with np.load(record['data_path'], allow_pickle=False) as z:
            old = {k: z[k] for k in z.files}
        replay = json.loads((ROOT / 'data/raw/games' / r['game'] / 'replay.json').read_text())
        truth, errors = ingest.validate_replay(replay); assert not errors
        before = truth[r['ply'] - 1].board
        key = StateKey()(before.board_string(), before.side, before.castling, before.en_passant)
        parent = np.repeat(np.arange(len(old['parent_weights'])), np.diff(old['offsets']))
        mask = old['parent_keys'] == key
        actor_edge = mask[parent] & (old['actions']['move'] == encode(replay['frames'][r['ply']]['move']))
        assert actor_edge.any()
        row = dict(x=old['actions']['x'].copy(), base=old['actions']['base'].copy(),
            counts=old['actions']['history_count'].copy(), u=old['parent_weights'], hn=old['history_n'],
            valid=old['actions']['key'] != 0, positive=old['positive'], a_parent=parent,
            actor_parent=mask, actor_edge=actor_edge, meta={'game': r['game']})
        rows.append(row); originals.append(old)
    data = Dataset(rows, 'cpu')
    theta = torch.tensor(np.random.default_rng(2311102).normal(0, .03, 26), requires_grad=True)
    posterior, actor = scores(data, theta)
    expected = []; actors = []
    for row, old in zip(rows, originals):
        t = lambda value: torch.tensor(value, dtype=torch.float64)
        expected.append(loop_loss(t(row['x']), t(row['base']), t(row['counts']), t(row['hn']), t(row['u']),
            old['offsets'].tolist(), torch.tensor(row['valid']), torch.tensor(row['positive']), theta))
        probabilities = []
        for i, (lo, hi) in enumerate(zip(old['offsets'][:-1], old['offsets'][1:])):
            z = row['base'][lo:hi].astype(float) + row['x'][lo:hi].astype(float) @ theta.detach().numpy()
            p = np.exp(z - z.max()); p /= p.sum()
            if row['hn'][i] >= 3:
                p = (row['counts'][lo:hi] + 4 * p) / (row['hn'][i] + 4)
            probabilities.append(p[row['actor_edge'][lo:hi]].sum())
        weights = np.exp(row['u'].astype(float)); weights *= row['actor_parent']; weights /= weights.sum()
        actors.append(np.log(np.dot(weights, probabilities)))
    expected = torch.stack(expected)
    error = float(torch.max(torch.abs(posterior + expected)).detach())
    actor_error = float(np.max(np.abs(actor.detach().numpy() - actors)))
    vgrad = torch.autograd.grad(posterior.sum(), theta, retain_graph=True)[0]
    rgrad = torch.autograd.grad(-expected.sum(), theta, retain_graph=True)[0]
    grad_error = float((vgrad - rgrad).abs().max())
    agrad = torch.autograd.grad(actor.mean(), theta)[0].numpy()
    numerical = []
    for i in range(26):
        plus, minus = theta.detach().clone(), theta.detach().clone(); plus[i] += 1e-5; minus[i] -= 1e-5
        numerical.append(float((scores(data, plus)[1].mean() - scores(data, minus)[1].mean()) / 2e-5))
    actor_grad_error = float(np.max(np.abs(agrad - numerical)))
    assert max(error, actor_error, grad_error) < 1e-10
    assert actor_grad_error < 1e-7
    print(json.dumps({'real_cases': len(rows), 'posterior_value_error': error, 'actor_numpy_error': actor_error,
        'posterior_gradient_error': grad_error, 'actor_finite_difference_error': actor_grad_error, 'no_fit': True}))


if __name__ == '__main__':
    main()
