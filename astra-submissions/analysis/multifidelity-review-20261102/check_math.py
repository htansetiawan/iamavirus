"""Exact toy expectations and continuous-budget cost algebra, not a bot trial."""
from fractions import Fraction as F
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import itertools
import json
import math


def allocation(rho, cheap_cost_ratio):
    """Normalized variance at equal cost; optional independent cheap samples.

    One paired sample costs 1+r. m/n=t additional cheap samples cost t*r.
    Continuous counts, known moments and fixed coefficients; not a scheduler.
    """
    assert math.isfinite(rho) and abs(rho) < 1
    assert math.isfinite(cheap_cost_ratio) and cheap_cost_ratio > 0
    s, r = rho * rho, cheap_cost_ratio
    k = max(1.0, math.sqrt(s / (r * (1 - s))))
    t = k - 1
    paired_ratio = (1 + r * k) * (1 - s * t / k)
    use = paired_ratio < 1
    return dict(rho=rho, cheap_cost_ratio=r, extra_cheap_per_pair=t,
                paired_method_variance_ratio=paired_ratio,
                selected_variance_ratio=min(1.0, paired_ratio),
                selected='paired_plus_cheap' if use else 'high_only')


def enumerate_fixture(agreement, theta):
    # The same source distribution supplies the paired and independent-cheap
    # pools. x varies, so this also checks a two-parameter regression gradient.
    population = []
    for x, h, same in itertools.product((F(-1), F(2)), (F(-1), F(1)), (True, False)):
        prob = F(1, 2) * (F(3, 5) if h == 1 else F(2, 5))
        prob *= agreement if same else 1 - agreement
        low = 1 + x + (2 * h if same else -2 * h)
        prediction = theta[0] + theta[1] * x
        high_grad = (2 * (prediction - h), 2 * (prediction - h) * x)
        low_grad = (2 * (prediction - low), 2 * (prediction - low) * x)
        population.append((prob, h, low, high_grad, low_grad))
    assert sum(r[0] for r in population) == 1
    mean_h = sum(p * h for p, h, _, _, _ in population)
    mean_l = sum(p * l for p, _, l, _, _ in population)
    true_grad = tuple(sum(r[0] * r[3][j] for r in population) for j in (0, 1))
    var_h = sum(p * (h - mean_h) ** 2 for p, h, _, _, _ in population)
    var_l = sum(p * (l - mean_l) ** 2 for p, _, l, _, _ in population)
    cov = sum(p * (h - mean_h) * (l - mean_l) for p, h, l, _, _ in population)
    for beta in (F(0), F(1), F(-1, 2), cov / (2 * var_l)):
        mean = variance = F(0)
        grad = [F(0), F(0)]
        for paired, independent in itertools.product(population, repeat=2):
            p = paired[0] * independent[0]
            estimate = paired[1] - beta * paired[2] + beta * independent[2]
            mean += p * estimate
            variance += p * (estimate - mean_h) ** 2
            for j in (0, 1):
                grad[j] += p * (paired[3][j] - beta * paired[4][j] + beta * independent[4][j])
        assert mean == mean_h
        assert tuple(grad) == true_grad
        assert variance == var_h + 2 * beta * beta * var_l - 2 * beta * cov
    assert mean_l != mean_h  # naive substitution is biased in these fixtures
    return dict(agreement=float(agreement), target_mean=float(mean_h),
                cheap_mean=float(mean_l), exact_estimator_and_gradient_checks=4)


def main():
    fixtures = [enumerate_fixture(q, (F(1, 3), F(-2, 5)))
                for q in (F(0), F(1, 4), F(1, 2), F(4, 5), F(1))]
    checked = 0
    for rho in (-0.99, -0.8, -0.3, 0, 0.3, 0.8, 0.99):
        for r in (0.02, 0.1, 0.2, 1, 2):
            a = allocation(rho, r)
            for t in (0.01, 0.1, 0.5, 1, 2, 5, 10, 50, 500):
                n = 1000 / (1 + r * (1 + t)); m = t * n
                beta = rho / (1 + n / m)
                v = (1 + beta * beta - 2 * beta * rho) / n + beta * beta / m
                ratio = (1 + r * (1 + t)) * (1 - rho * rho * t / (1 + t))
                assert abs(v * 1000 - ratio) < 1e-10
                assert a['paired_method_variance_ratio'] <= ratio + 1e-10
                checked += 1
            if r < 1:
                threshold = 4 * r / (1 + r) ** 2
                assert (a['selected'] != 'high_only') == (rho * rho > threshold)
    scenarios = [allocation(rho, r) for r in (0.02, 0.1, 0.2) for rho in (0.5, 0.8, 0.95)]
    out = Path(__file__).resolve().parent
    result = dict(at=datetime.now(timezone.utc).isoformat(), passed=True,
                  exact_fixtures=fixtures, allocation_checks=checked, hypothetical_scenarios=scenarios,
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  scope='Synthetic exact enumeration and continuous-budget algebra only. '
                        'No arena correlation, policy strength, learned model or launch decision measured.')
    with (out / 'math-check.json').open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
