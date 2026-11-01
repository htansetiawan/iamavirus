#!/usr/bin/env python3
"""Audit completed first outputs and apply the recorded posterior gate."""
import hashlib
import json
import math
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(sys.argv[1])
    plan = json.loads((root / 'plan.json').read_text())
    pins = json.loads((root / 'runs-receipt.json').read_text())
    assert pins['state'] == 'complete' and sha(root / 'plan.json') == pins['plan_sha256']
    for path, digest in (pins['sources'] | pins['dependencies']).items():
        assert sha(Path(path)) == digest, path
    for library in pins['libraries'].values():
        assert sha(Path(library['path'])) == library['sha256']
    entries = {(r['game'], r['arm']): r for r in pins['completed']}
    assert len(entries) == len(pins['completed']) == 3 * len(plan['cases'])
    arms = list(plan['arms']); data = {}
    for case in plan['cases']:
        game = case['id']
        for kind in ('input', 'truth'):
            assert sha(root / f'{game}.{kind}.json') == case[f'{kind}_sha256']
        feed = json.loads((root / f'{game}.input.json').read_text())
        labels = {r['ply']: r for r in json.loads((root / f'{game}.truth.json').read_text())['rows']}
        steps = [s for s in feed['steps'] if s['ply'] <= plan['max_ply']]
        for arm in arms:
            item = entries[game, arm]; path = Path(item['path'])
            assert item['exit_code'] == 0 and not item['redacted'] and sha(path) == item['sha256']
            result = json.loads(path.read_text()); data[game, arm] = result
            assert result['game'] == game and result['us'] == case['us']
            assert result['cap'] == plan['cap'] and result['seed'] == plan['seed']
            assert not result['truth_redacted']
            assert [r['ply'] for r in result['updates']] == [s['ply'] for s in steps]
            assert [r['ply'] for r in result['decisions']] == [s['ply'] for s in steps if 'next_own_move' in s]
            assert len(result['decisions']) == case['decisions']
            assert math.isclose(sum(r['seconds'] for r in result['updates']), result['total_update_seconds'], abs_tol=1e-8)
            for row in result['decisions']:
                assert 0 <= row['truth_context_share'] <= row['truth_share'] + 1e-8 <= 1.0000001
                assert row['actual_king_loss'] == labels[row['ply']]['fatal']
                assert (row['king_risk'] is None) == (row['worlds'] == 0)
                if row['king_risk'] is not None:
                    assert 0 <= row['king_risk'] <= 1.00000001

    def aggregate(cases):
        if not cases:
            return None
        rows = {arm: [r for c in cases for r in data[c['id'], arm]['decisions']] for arm in arms}
        common = [i for i in range(len(rows[arms[0]])) if all(rows[a][i]['king_risk'] is not None for a in arms)]
        stats = {}
        for arm, seq in rows.items():
            stats[arm] = {
                'decisions': len(seq), 'truth_present': sum(r['truth_entries'] > 0 for r in seq),
                'truth_support': sum(r['truth_entries'] > 0 for r in seq) / len(seq),
                'empty_decisions': sum(r['worlds'] == 0 for r in seq),
                'truth_nll_by_clip': {str(eps): math.fsum(-math.log(max(eps, r['truth_share'])) for r in seq) / len(seq) for eps in (1e-9, 1e-12, 1e-15)},
                'common_risk_decisions': len(common), 'common_actual_king_losses': sum(seq[i]['actual_king_loss'] for i in common),
                'common_king_brier': math.fsum((seq[i]['king_risk'] - seq[i]['actual_king_loss']) ** 2 for i in common) / len(common) if common else None,
                'update_seconds': sum(data[c['id'], arm]['total_update_seconds'] for c in cases),
                'max_rss_kib': max(data[c['id'], arm]['max_rss_kib'] for c in cases),
                'mean_boards': sum(r['worlds'] for r in seq) / len(seq),
                'mean_contexts': sum(r.get('contexts', r['worlds']) for r in seq) / len(seq),
                'max_contexts_per_board': max(r.get('max_contexts_per_board', 1) for r in seq),
                'max_retained_bytes': max((r.get('retained_bytes', 0) for r in seq)),
            }
        temporal = stats['temporal_mixture']; comparisons = {}
        for control in ('static_merged', 'static_mixture'):
            baseline = stats[control]
            gain = baseline['truth_nll_by_clip']['1e-12'] - temporal['truth_nll_by_clip']['1e-12']
            support = temporal['truth_support'] - baseline['truth_support']
            brier = temporal['common_king_brier'] - baseline['common_king_brier'] if common else None
            ratio = temporal['update_seconds'] / baseline['update_seconds']
            checks = {'nll': gain >= .1, 'support': support >= -.02, 'king_brier': brier is not None and brier <= .002, 'time': ratio <= 2}
            comparisons[control] = {'truth_nll_gain': gain, 'support_change': support, 'common_king_brier_change': brier,
                                    'update_time_ratio': ratio, 'checks': checks, 'passes': all(checks.values())}
        return {'games': len(cases), 'arms': stats, 'comparisons': comparisons}

    all_cases = aggregate(plan['cases'])
    report = {'measurement': 'Development posterior diagnostic; no policy or Elo estimate',
              'receipt_sha256': sha(root / 'runs-receipt.json'), 'plan_sha256': sha(root / 'plan.json'),
              'verified_cells': len(entries), 'all_cases': all_cases,
              'our_observer_seats': aggregate([c for c in plan['cases'] if c['observer'] == 'IAmAVirus']),
              'by_opponent': {op: aggregate([c for c in plan['cases'] if c['opponent'] == op]) for op in sorted({c['opponent'] for c in plan['cases']})},
              'passes_to_larger_cap_test': all(c['passes'] for c in all_cases['comparisons'].values()),
              'release_eligible': False,
              'limitations': ['One fixed seed, 18 games, 20k physical-board cap; no empirical history blend or arena-clock thinning.',
                             'Two Instructors observer seats belong to other teams; report our-only subset separately.',
                             'No rebuilding after empty belief; risk subset and total runtime depend on coverage.',
                             'Probability tests use recorded own moves, not a new policy.',
                             'Context mixtures do not preserve full opponent information histories for CFR.']}
    (root / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('verified_cells', 'all_cases', 'passes_to_larger_cap_test')}, indent=2))


if __name__ == '__main__':
    main()
