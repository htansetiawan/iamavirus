#!/usr/bin/env python3
"""Freeze provenance, train once, score development validation, enforce gate."""
import argparse
import gzip
import json
import time
from pathlib import Path

import numpy as np
import torch

import model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT/'astra-submissions/analysis/temporal-prior-20261101'
OUT = ROOT/'astra-submissions/analysis/style-mixture-20261101'


def dump(p, value):
    p.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def freeze():
    OUT.mkdir(exist_ok=False)
    paths = [HERE/n for n in ('model.py', 'run.py', 'test_model.py', 'README.md')]
    paths += [OLD/'fit/static.json', OLD/'data-v2/manifest.json', OLD/'data-v2/extraction.json']
    paths += [OLD/f'data-v2/{s}.features.bin.gz' for s in ('train', 'validation')]
    dump(OUT/'plan.json', {'files': {str(p.relative_to(ROOT)): model.sha(p) for p in paths},
          'experts': 3, 'l2': .001, 'seed': 11012027, 'device': 'cpu', 'threads': 2,
          'development_games': {'train': 1200, 'validation': 300},
          'no_team_input': True, 'known_true_parents': True,
          'validation_gate': {'ambiguous_gain_vs_both': .05, 'max_all_move_nll_regression': .005,
                              'min_reference_ambiguous_gain': 0},
          'scope': 'Reused development validation, not unseen confirmation. No test scored unless gate passes.'})
    print('Frozen', OUT/'plan.json', flush=True)


def describe(d, scores, mask):
    amb = mask & d.ambiguous
    return {'moves': int(mask.sum()), 'ambiguous_moves': int(amb.sum()),
            'nll': -float(scores['logp'][mask].mean()) if mask.any() else None,
            'ambiguous_conditional_nll': -float(scores['conditional_logp'][amb].mean()) if amb.any() else None}


def run():
    plan = json.loads((OUT/'plan.json').read_text())
    for p, h in plan['files'].items():
        assert model.sha(ROOT/p) == h, p
    dest = OUT/'fit'; dest.mkdir(exist_ok=False)
    torch.set_num_threads(2)
    base = np.array(json.loads((OLD/'fit/static.json').read_text())['coefficients'])
    started = time.monotonic()
    d = model.Data(OLD/'data-v2/train.features.bin.gz', base)
    print(json.dumps({'loaded_train': d.N, 'actions': len(d.seg), 'sequences': d.G}), flush=True)
    fitted = {}
    for name, k in [('pooled_residual', 1), ('mixture', 3)]:
        delta, alpha, stats = model.fit(d, k)
        fitted[name] = (delta, alpha)
        dump(dest/(name+'.json'), {'delta': delta.tolist(), 'alpha': alpha.tolist(),
                                  'prior': torch.softmax(alpha, 0).tolist(), 'fit': stats})
        print(json.dumps({'fit_finished': name, 'seconds': stats['seconds'],
                          'max_gradient': stats['max_gradient']}), flush=True)
    frozen = {name: model.sha(dest/(name+'.json')) for name in fitted}
    dump(dest/'frozen-models.json', {'sha256': frozen, 'base_sha256': model.sha(OLD/'fit/static.json'),
                                   'plan_sha256': model.sha(OUT/'plan.json')})
    del d
    d = model.Data(OLD/'data-v2/validation.features.bin.gz', base)
    all_scores = {'static': model.scores(d, torch.zeros((1, 39), dtype=torch.float64),
                                       torch.zeros(1, dtype=torch.float64))['reset']}
    all_scores['pooled_residual'] = model.scores(d, *fitted['pooled_residual'])['reset']
    all_scores.update({'mixture_'+k: v for k, v in model.scores(d, *fitted['mixture']).items()})
    teams = json.loads((OLD/'data-v2/manifest.json').read_text())['teams']
    masks = {'overall': np.ones(d.N, dtype=bool)}
    masks.update({name: d.head[:, 3] == i for i, name in enumerate(teams)})
    masks['references'] = np.isin(d.head[:, 3], [teams.index(t) for t in ('Instructors', 'duck', 'HYPOTHERMIA')])
    report = {'by_group': {group: {arm: describe(d, values, mask) for arm, values in all_scores.items()}
                           for group, mask in masks.items()}, 'comparisons': {}}
    actual = all_scores['mixture_view_history']
    passed = True
    for arm in ('static', 'pooled_residual'):
        old = all_scores[arm]
        diff = actual['conditional_logp']-old['conditional_logp']
        row = {'ambiguous_gain': float(diff[d.ambiguous].mean()),
               'all_move_nll_change': float((old['logp']-actual['logp']).mean()),
               'reference_ambiguous_gain': float(diff[d.ambiguous & masks['references']].mean())}
        row['passes'] = (row['ambiguous_gain'] >= .05 and row['all_move_nll_change'] <= .005
                         and row['reference_ambiguous_gain'] >= 0)
        passed = passed and row['passes']
        report['comparisons'][arm] = row
    report['passes_development_gate'] = passed
    report['scope'] = plan['scope']
    dump(OUT/'validation.json', report)
    with (OUT/'validation-scores.jsonl.gz').open('wb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as gz:
            for i, h in enumerate(d.head):
                row = {'game_index': int(h[0]), 'ply': int(h[1]), 'side': int(h[2]), 'team_index': int(h[3]),
                       'ambiguous': bool(d.ambiguous[i])}
                row['scores'] = {arm: {key: float(v[i]) if np.isfinite(v[i]) else None
                                      for key, v in values.items()} for arm, values in all_scores.items()}
                gz.write((json.dumps(row, allow_nan=False)+'\n').encode())
    for name, h in frozen.items():
        assert model.sha(dest/(name+'.json')) == h
    dump(OUT/'status.json', {'state': 'complete', 'passes_development_gate': passed, 'test_scored': False,
                            'earns_new_test': passed, 'earns_belief_integration': False,
                            'elapsed_seconds': time.monotonic()-started, 'torch': torch.__version__,
                            'reason': 'Freeze fresh test before further scoring' if passed else 'Development gate failed'})
    print(json.dumps({'validation': report['comparisons'], 'passes': passed}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('command', choices=['freeze', 'run'])
    globals()[parser.parse_args().command]()
