"""Algebra checks before any replay extraction or model fitting."""
import json
import numpy as np
import torch
from objective import edge_scores, loss


def main():
    torch.set_num_threads(2)
    rng = np.random.default_rng(2301102)
    x = torch.tensor(rng.normal(size=(9, 4)), dtype=torch.float64)
    base = torch.tensor(rng.normal(size=9), dtype=torch.float64)
    counts = torch.tensor([0, 5, 0, 4, 0, 0, 0, 0, 0], dtype=torch.float64)
    totals = torch.tensor([12, 4, 0], dtype=torch.float64)
    weights = torch.tensor([-1., -.4, -2.], dtype=torch.float64)
    offsets = [0, 3, 7, 9]
    consistent = torch.tensor([1, 1, 0, 1, 0, 1, 0, 1, 1], dtype=torch.bool)
    positive = torch.tensor([0, 1, 0, 1, 0, 0, 0, 0, 0], dtype=torch.bool)
    theta = torch.tensor([.1, -.2, .3, -.4], dtype=torch.float64, requires_grad=True)
    value = loss(x, base, counts, totals, weights, offsets, consistent, positive, theta)
    value.backward()
    gradient = theta.grad.detach().numpy().copy()
    numerical = []
    for i in range(4):
        plus, minus = theta.detach().clone(), theta.detach().clone()
        plus[i] += 1e-5; minus[i] -= 1e-5
        numerical.append(float((loss(x, base, counts, totals, weights, offsets, consistent, positive, plus)
                                - loss(x, base, counts, totals, weights, offsets, consistent, positive, minus)) / 2e-5))
    error = float(np.max(np.abs(gradient - numerical)))
    assert error < 1e-8
    # An independent direct probability sum, including duplicate positive histories.
    mass = []
    for i, (lo, hi) in enumerate(zip(offsets[:-1], offsets[1:])):
        z = base[lo:hi].numpy() + x[lo:hi].numpy() @ theta.detach().numpy()
        p = np.exp(z - z.max()); p /= p.sum()
        if totals[i] >= 3:
            p = (counts[lo:hi].numpy() + 4 * p) / (float(totals[i]) + 4)
        mass.extend(np.exp(float(weights[i])) * p**2)
    mass = np.array(mass)
    assert abs(float(value.detach()) - np.log(mass[consistent].sum() / mass[positive].sum())) < 1e-12
    # Dropping incompatible actions from the per-parent normalizer is a different objective.
    changed = base.clone(); changed[2] += 3
    wrong = loss(x, changed, counts, totals, weights, offsets, consistent, positive, theta)
    assert abs(float(wrong.detach() - value.detach())) > 1e-4
    try:
        loss(x, base, counts, totals, weights, offsets, consistent, positive & False, theta)
    except ValueError:
        pass
    else:
        raise AssertionError('Missing support must not silently train')
    print(json.dumps({'finite_difference_max_error': error, 'direct_probability_sum': True,
        'multiple_parents_and_duplicate_positive_histories': True, 'all_legal_denominator_matters': True,
        'zero_count_history_gradient_finite': bool(np.isfinite(gradient).all()), 'missing_positive_rejected': True}))


if __name__ == '__main__':
    main()
