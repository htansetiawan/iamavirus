"""Read-only CPU reevaluation of all development rows and selected checkpoints."""
import gzip
import json
import os
import time

import numpy as np
import torch

from data import Dataset
from fit import OUT, read, sha, ScalarResidual, WorldQuietTeacher, evaluate, summarize


def main():
    started = time.monotonic(); plan = read(OUT / 'plan.json')
    assert read(OUT / 'execution.json')['status'] == 'complete'
    for path, expected in plan['dependencies'].items(): assert sha(path) == expected, path
    os.sched_setaffinity(0, set(plan['cores'])); torch.set_num_threads(2)
    dataset = Dataset(plan, 'cpu'); dev = dataset.indices['development']
    with gzip.open(OUT / 'development-scores.jsonl.gz', 'rt') as stream:
        saved = [json.loads(line) for line in stream]
    meta = [dataset.meta[i] for i in dev]
    assert len(saved) == len(meta)
    assert [{k: r[k] for k in meta[0]} for r in saved] == meta
    predictions = {}; errors = {}; capture_actions = {}
    for kind in ('base', 'linear', 'quadratic', 'teacher'):
        model = None
        if kind != 'base':
            model = WorldQuietTeacher(**plan['architecture']) if kind == 'teacher' else ScalarResidual(kind)
            model.load_state_dict(torch.load(OUT / (kind + '-best.pt'), map_location='cpu', weights_only=True))
        values, checks = evaluate(dataset, dev, kind, model)
        expected = np.array([r['logp'][kind] for r in saved])
        error = float(abs(values - expected).max(initial=0))
        assert error < 1e-4, (kind, error)
        errors[kind] = error; predictions[kind] = values; capture_actions[kind] = checks
    result = read(OUT / 'result.json')
    metrics, conditions = summarize(plan, meta, predictions)
    assert conditions == result['conditions'], 'CPU decision differs'
    for key in ('gain', 'matched_quadratic_gain', 'all_move_gain'):
        assert abs(metrics[key] - result['metrics'][key]) < 1e-6, key
    assert result['scores_sha256'] == sha(OUT / 'development-scores.jsonl.gz')
    # Independent aggregation of the saved raw rows, without summarize().
    selected = [r for r in saved if r['primary']]
    scalar = {kind: -sum(r['logp'][kind] for r in selected) / len(selected)
              for kind in ('base', 'linear', 'quadratic', 'teacher')}
    assert all(abs(scalar[k] - result['metrics']['nll'][k]) < 1e-10 for k in scalar)
    assert sum(r['capture'] for r in saved) == result['metrics']['capture_targets']
    assert all(r['logp']['teacher'] == r['logp']['base'] for r in saved if r['capture'])
    grouped = {}
    for row in selected:
        item = grouped.setdefault(row['game'], [0., 0])
        item[0] += row['logp']['teacher'] - row['logp']['quadratic']; item[1] += 1
    rng = np.random.default_rng(plan['seed']); keys = sorted(grouped); estimates = []
    for _ in range(plan['bootstrap_draws']):
        entries = [grouped[keys[i]] for i in rng.integers(0, len(keys), len(keys))]
        estimates.append(sum(e[0] for e in entries) / sum(e[1] for e in entries))
    interval = np.quantile(estimates, [.025, .975])
    assert np.max(abs(interval - result['metrics']['interval95_vs_quadratic'])) < 1e-10
    review = dict(passed=True, rows=len(saved), primary=len(selected), cpu_gpu_max_error=errors,
                  cpu_capture_actions=capture_actions, cpu_conditions=conditions,
                  independent_saved_nll=scalar, independent_interval95=interval.tolist(),
                  seconds=time.monotonic()-started,
                  limitation='CPU inference uses the same model/loader; independent scalar aggregation checks saved scores, not a separately implemented attention network.')
    with (OUT / 'independent-review.json').open('x') as stream:
        json.dump(review, stream, indent=2); stream.write('\n')
    print(json.dumps(review, indent=2), flush=True)


if __name__ == '__main__': main()
