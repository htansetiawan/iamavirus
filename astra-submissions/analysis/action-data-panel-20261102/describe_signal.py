"""Post-hoc signal/cost description; does not fit a coefficient or select a policy.

All source games remain in the covariance bounds. Censored returns are never
filled with zero and incomplete sources do not disappear from the statistic.
"""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def covariance_bounds(xs, intervals):
    assert len(xs) == len(intervals) and len(xs) > 1
    assert all(math.isfinite(x) for x in xs)
    assert all(math.isfinite(lo) and math.isfinite(hi) and lo <= hi for lo, hi in intervals)
    centered = [x - sum(xs) / len(xs) for x in xs]
    # Cov(X,H) = mean((X-mean(X))*H); the mean(H) term cancels.
    bounds = [0.0, 0.0]
    for x, (lo, hi) in zip(centered, intervals):
        a, b = x * lo, x * hi
        bounds[0] += min(a, b) / len(xs)
        bounds[1] += max(a, b) / len(xs)
    return bounds


def main():
    dataset = json.loads((OUT / 'dataset.json').read_text())
    for name, digest in dataset['artifacts'].items():
        assert sha(OUT / name) == digest
    pairs = [json.loads(line) for line in (OUT / 'paired-targets.jsonl').read_text().splitlines()]
    roots = [json.loads(line) for line in (OUT / 'root-targets.jsonl').read_text().splitlines()]
    fixed = json.loads((OUT / 'baseline-choices.json').read_text())['rows']
    groups = defaultdict(list)
    costs = defaultdict(float)
    for p in pairs:
        groups[p['source_group']].append(p)
    for r in roots:
        costs[r['source_group']] += r['wall_seconds']
    rows = []
    for entry in fixed:
        group = groups[entry['source']]
        assert len(group) == 2 and {p['repeat'] for p in group} == {0, 1}
        proposal = json.loads((OUT / f'proposal-{entry["case"]}' / 'proposal.json').read_text())
        score = {r['move']: r['value'] for r in proposal['rows']}
        difference = score[proposal['alternative']] - score[proposal['chosen']]
        assert difference == entry['value_difference']
        interval = [sum(p['return_difference_interval'][k] for p in group) / 2 for k in (0, 1)]
        rows.append(dict(source=entry['source'], case=entry['case'],
                         current=entry['chosen'], alternative=entry['alternative'],
                         search_value_difference=difference,
                         two_repeat_return_difference_bounds=interval,
                         fully_observed=all(p['complete'] for p in group),
                         proposal_generator_seconds=proposal['checked']['wall_seconds'],
                         four_branch_generator_seconds=costs[entry['source']]))
    assert len(rows) == len(groups) == len(dataset['source_groups'])
    xs = [r['search_value_difference'] for r in rows]
    intervals = [r['two_repeat_return_difference_bounds'] for r in rows]
    bounds = covariance_bounds(xs, intervals)
    correlation = None
    if all(lo == hi for lo, hi in intervals):
        ys = [lo for lo, _ in intervals]
        vx = sum((x - sum(xs) / len(xs)) ** 2 for x in xs) / len(xs)
        vy = sum((y - sum(ys) / len(ys)) ** 2 for y in ys) / len(ys)
        if vx > 0 and vy > 0:
            correlation = bounds[0] / math.sqrt(vx * vy)
    cheap_cost = sum(r['proposal_generator_seconds'] for r in rows)
    high_cost = sum(r['four_branch_generator_seconds'] for r in rows)
    result = dict(at=datetime.now(timezone.utc).isoformat(), post_hoc=True, rows=rows,
                  all_source_covariance_bounds=bounds,
                  empirical_correlation_if_fully_observed=correlation,
                  fully_observed_sources=sum(r['fully_observed'] for r in rows),
                  measured_proposal_to_four_branch_cost_ratio=cheap_cost / high_cost,
                  proposal_generator_seconds=cheap_cost, four_branch_generator_seconds=high_cost,
                  dataset_sha256=sha(OUT / 'dataset.json'),
                  choices_sha256=sha(OUT / 'baseline-choices.json'),
                  source_sha256=sha(Path(__file__)),
                  scope='Equal-weight source-level description. Bounds quantify missing returns, '
                        'not population uncertainty. No complete-case correlation, fitted coefficient, '
                        'model selection, cost-saving claim or change to the frozen experiment.')
    with (OUT / 'signal-description.json').open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))


if __name__ == '__main__':
    main()
