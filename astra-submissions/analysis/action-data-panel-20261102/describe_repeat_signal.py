"""Post-hoc repeatability description, retaining every censored source.

If two independent repeats D0,D1 share a source's action contrast delta,
E[D0*D1 | source] = delta**2 and E[(D0-D1)**2/2 | source] = Var(D | source).
These assumptions are not established by two timed runs. The empirical
quantities below are diagnostics, not fitted targets or a promotion test.
"""
from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repeat_bounds(left, right):
    lo, hi = left
    other_lo, other_hi = right
    assert lo <= hi and other_lo <= other_hi
    products = [a*b for a in left for b in right]
    d_lo, d_hi = lo-other_hi, hi-other_lo
    return dict(product=[min(products), max(products)],
                within_source_variation=[
                    0.0 if d_lo <= 0 <= d_hi else min(d_lo*d_lo, d_hi*d_hi)/2,
                    max(d_lo*d_lo, d_hi*d_hi)/2])


def selftest():
    intervals = list(itertools.combinations_with_replacement(range(-2, 3), 2))
    for left, right in itertools.product(intervals, repeat=2):
        actual = repeat_bounds(left, right)
        points = list(itertools.product(range(left[0], left[1]+1),
                                        range(right[0], right[1]+1)))
        products = [a*b for a, b in points]
        variation = [(a-b)**2/2 for a, b in points]
        assert actual['product'] == [min(products), max(products)]
        assert actual['within_source_variation'] == [min(variation), max(variation)]
    return dict(interval_pairs=len(intervals)**2, passed=True)


def main():
    dataset = json.loads((OUT/'dataset.json').read_text())
    for name, digest in dataset['artifacts'].items():
        assert sha(OUT/name) == digest
    grouped = defaultdict(dict)
    for line in (OUT/'paired-targets.jsonl').read_text().splitlines():
        row = json.loads(line)
        assert row['repeat'] not in grouped[row['source_group']]
        grouped[row['source_group']][row['repeat']] = row
    rows = []
    for source, repeats in sorted(grouped.items()):
        assert set(repeats) == {0, 1}
        intervals = [repeats[i]['return_difference_interval'] for i in (0, 1)]
        rows.append(dict(source=source, contrast_intervals=intervals,
                         fully_observed=all(repeats[i]['complete'] for i in (0, 1)),
                         **repeat_bounds(*intervals)))
    assert len(rows) == len(dataset['source_groups'])
    mean = {key: [sum(r[key][i] for r in rows)/len(rows) for i in (0, 1)]
            for key in ('product', 'within_source_variation')}
    result = dict(rows=rows, all_source_mean_bounds=mean,
                  preflight=selftest(), dataset_sha256=sha(OUT/'dataset.json'),
                  source_sha256=sha(Path(__file__)),
                  scope='Post-hoc, source-weighted description. Missing-return bounds are not '
                        'confidence intervals. No complete-case filtering or clipping a negative '
                        'product to zero. Conditional independent identically distributed repeats '
                        'would give product the interpretation of squared action effect; timed '
                        'runs do not prove that assumption. No policy/model fit or promotion.')
    with (OUT/'repeat-signal.json').open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'rows'}))


if __name__ == '__main__':
    main()
