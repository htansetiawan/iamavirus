"""Check marginal control-variate cost when the paired score already exists.

This reads every source in the completed development panel. It does not fit
beta, drop censored sources, train a model, or certify population moments.
"""
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent
PANEL = OUT.parent/'action-data-panel-20261102'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def allocation(rho, extra_cost_ratio):
    """One high sample includes its score; only extra scores cost r each."""
    assert math.isfinite(rho) and abs(rho) < 1
    assert math.isfinite(extra_cost_ratio) and extra_cost_ratio > 0
    r, s = extra_cost_ratio, rho*rho
    k = max(1.0, math.sqrt((1-r)*s/(r*(1-s)))) if r < 1 else 1.0
    t = k-1
    ratio = (1+r*t)*(1-s*t/k)
    return dict(extra_scores_per_high=t, variance_ratio=ratio,
                use_extra_scores=t > 0)


def checks():
    nchecks = 0
    for rho in (-0.99, -0.8, -0.3, 0, 0.3, 0.8, 0.99):
        for r in (0.001, 0.02, 0.1, 0.2, 0.8, 1, 2):
            choice = allocation(rho, r)
            assert choice['use_extra_scores'] == (rho*rho > r)
            for t in (0.01, 0.1, 0.5, 1, 2, 5, 10, 50, 500):
                n = 1000/(1+r*t)
                m = t*n
                beta = rho/(1+n/m)  # unit variances, known population moments
                direct = (1+beta*beta-2*beta*rho)/n + beta*beta/m
                ratio = (1+r*t)*(1-rho*rho*t/(1+t))
                assert abs(1000*direct-ratio) < 1e-10
                assert choice['variance_ratio'] <= ratio+1e-10
                nchecks += 1
    return nchecks


def moments(xs, ys):
    n = len(xs)
    xm, ym = sum(xs)/n, sum(ys)/n
    vx = sum((x-xm)**2 for x in xs)/n
    vy = sum((y-ym)**2 for y in ys)/n
    cov = sum((x-xm)*(y-ym) for x, y in zip(xs, ys))/n
    return dict(covariance=cov, high_variance=vy, score_variance=vx,
                rho=cov/math.sqrt(vx*vy) if vx*vy > 0 else None)


def main():
    tested = checks()
    signal = json.loads((PANEL/'signal-description.json').read_text())
    assert sha(PANEL/'dataset.json') == signal['dataset_sha256']
    rows = signal['rows']
    xs = [r['search_value_difference'] for r in rows]
    intervals = [r['two_repeat_return_difference_bounds'] for r in rows]
    cheap = signal['proposal_generator_seconds']
    branches = signal['four_branch_generator_seconds']
    ratio = cheap/(cheap+branches)
    # Do not silently treat unknown returns as draws. Each endpoint vector is
    # a feasible completion; it is not an estimate of the missing outcomes.
    completions = []
    for ys in itertools.product(*[sorted(set(bounds)) for bounds in intervals]):
        m = moments(xs, ys)
        assert m['rho'] is not None
        a = allocation(m['rho'], ratio)
        completions.append(dict(returns=list(ys), **m, **a))
    lo = min(completions, key=lambda r: abs(r['rho']))
    hi = max(completions, key=lambda r: abs(r['rho']))
    maxvar = max(r['high_variance'] for r in completions)
    # Variance is convex in the unknown returns; its maximum over this box
    # occurs at a vertex. Together with the exact covariance bound this gives
    # a conservative lower bound, NOT an exact minimum correlation.
    covlo = signal['all_source_covariance_bounds'][0]
    rho_lower = max(0.0, covlo)/math.sqrt(lo['score_variance']*maxvar)
    result = dict(at=datetime.now(timezone.utc).isoformat(), passed=True,
                  allocation_checks=tested,
                  marginal_extra_to_total_high_cost_ratio=ratio,
                  known_moment_break_even_absolute_correlation=math.sqrt(ratio),
                  proposal_generator_seconds=cheap,
                  high_source_seconds_including_proposals=cheap+branches,
                  retained_sources=len(rows), endpoint_completions=len(completions),
                  conservative_finite_panel_absolute_rho_lower_bound=rho_lower,
                  feasible_endpoint_low_correlation=lo,
                  feasible_endpoint_high_correlation=hi,
                  endpoint_completions_benefiting_under_oracle_moments=sum(r['use_extra_scores'] for r in completions),
                  saving_certified_by_all_missing_outcomes=rho_lower*rho_lower > ratio,
                  hypothetical_allocations=[dict(rho=r, **allocation(r, ratio)) for r in (0.2, 0.5, 0.8)],
                  signal_sha256=sha(PANEL/'signal-description.json'),
                  source_sha256=sha(Path(__file__)),
                  scope='Post-hoc finite-panel feasibility and continuous known-moment cost algebra. '
                        'Endpoint extrema are not exact extrema of correlation over the box. '
                        'No missing label is chosen, no beta fitted, no population confidence '
                        'interval or demonstrated saving, policy strength or learning result.')
    with (OUT/'existing-score-cost.json').open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in (
        'feasible_endpoint_low_correlation','feasible_endpoint_high_correlation')}, indent=2))
    print('feasible endpoint rho range',lo['rho'],hi['rho'])


if __name__ == '__main__':
    main()
