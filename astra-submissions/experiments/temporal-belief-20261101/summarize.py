#!/usr/bin/env python3
"""Audit first-result posterior traces, retaining the original failed exit."""
import hashlib
import json
import math
import sys
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(sys.argv[1])
    plan = json.loads((root / 'plan.json').read_text())
    pins = json.loads((root / 'pins.json').read_text())
    completion = json.loads((root / 'diagnostic-completion.json').read_text())
    assert pins['state'] == 'failed' and completion['state'] == 'complete'
    assert sha(root / 'pins.json') == completion['original_failed_receipt_sha256']
    assert sha(root / 'plan.json') == pins['plan_sha256']
    for name, digest in pins['sources'].items():
        assert sha(Path(name)) == digest, name
    receipts = pins['completed'] + completion['completed']
    indexed = {(r['game'], r['arm']): r for r in receipts}
    assert len(indexed) == len(receipts) == 3 * len(plan['cases'])
    arms = list(plan['arms'])
    traces = {}
    for case in plan['cases']:
        game = case['id']
        for kind in ('input', 'truth'):
            assert sha(root / f'{game}.{kind}.json') == case[f'{kind}_sha256']
        feed = json.loads((root / f'{game}.input.json').read_text())
        truth = {r['ply']: r for r in json.loads((root / f'{game}.truth.json').read_text())['rows']}
        steps = [s for s in feed['steps'] if s['ply'] <= plan['max_ply']]
        decision_plies = [s['ply'] for s in steps if 'next_own_move' in s]
        for arm in arms:
            path = root / 'runs' / f'{game}-{arm}.json'
            assert sha(path) == indexed[game, arm]['sha256']
            data = json.loads(path.read_text())
            assert data['game'] == game and data['us'] == case['us']
            assert data['cap'] == plan['cap'] and data['seed'] == plan['seed']
            assert not data['truth_redacted']
            assert [r['ply'] for r in data['updates']] == [s['ply'] for s in steps]
            assert [r['ply'] for r in data['decisions']] == decision_plies
            assert len(decision_plies) == case['decisions']
            assert math.isclose(sum(r['seconds'] for r in data['updates']), data['total_update_seconds'], abs_tol=1e-8)
            for row in data['decisions']:
                assert 0 <= row['truth_share'] <= 1.00000001
                assert row['actual_king_loss'] == truth[row['ply']]['fatal']
                assert (row['king_risk'] is None) == (row['worlds'] == 0)
                if row['king_risk'] is not None:
                    assert 0 <= row['king_risk'] <= 1.00000001
            traces[game, arm] = data

    def summarize(cases):
        rows = {arm: [r for c in cases for r in traces[c['id'], arm]['decisions']] for arm in arms}
        common = [i for i in range(len(rows[arms[0]])) if all(rows[a][i]['king_risk'] is not None for a in arms)]
        stats = {}
        for arm in arms:
            seq = rows[arm]
            covered = [r for r in seq if r['king_risk'] is not None]
            stats[arm] = {
                'decisions': len(seq),
                'truth_present': sum(r['truth_entries'] > 0 for r in seq),
                'truth_support': sum(r['truth_entries'] > 0 for r in seq) / len(seq),
                'empty_decisions': sum(r['worlds'] == 0 for r in seq),
                'games_with_empty_belief': sum(any(r['worlds'] == 0 for r in traces[c['id'], arm]['decisions']) for c in cases),
                'truth_nll_by_clip': {str(eps): sum(-math.log(max(eps, r['truth_share'])) for r in seq) / len(seq) for eps in (1e-9, 1e-12, 1e-15)},
                'covered_risk_decisions': len(covered),
                'common_risk_decisions': len(common),
                'common_actual_king_losses': sum(seq[i]['actual_king_loss'] for i in common),
                'common_king_brier': sum((seq[i]['king_risk'] - seq[i]['actual_king_loss']) ** 2 for i in common) / len(common) if common else None,
                'update_seconds': sum(traces[c['id'], arm]['total_update_seconds'] for c in cases),
                'mean_worlds': sum(r['worlds'] for r in seq) / len(seq),
                'mean_unique_boards': sum(r['unique_boards'] for r in seq) / len(seq),
            }
        comparisons = {}
        temporal = stats['temporal_context']
        for control in ('static_merged', 'static_context'):
            baseline = stats[control]
            gain = baseline['truth_nll_by_clip']['1e-12'] - temporal['truth_nll_by_clip']['1e-12']
            support = temporal['truth_support'] - baseline['truth_support']
            brier = temporal['common_king_brier'] - baseline['common_king_brier'] if common else None
            ratio = temporal['update_seconds'] / baseline['update_seconds']
            checks = {'nll': gain >= .1, 'support': support >= -.02,
                      'king_brier': brier is not None and brier <= .002, 'time': ratio <= 2}
            comparisons[control] = {'truth_nll_gain': gain, 'support_change': support,
                                    'common_king_brier_change': brier, 'update_time_ratio': ratio,
                                    'checks': checks, 'numerical_gate_pass': all(checks.values())}
        return {'games': len(cases), 'arms': stats, 'comparisons': comparisons}

    report = {
        'measurement': 'Development posterior diagnostic; no decision or playing-strength claim',
        'original_runtime_failure': pins['error'],
        'original_successful_cells': len(pins['completed']),
        'completion_cells': len(completion['completed']),
        'retained_failed_exit_cells': [r for r in completion['completed'] if r.get('retained_failed_exit_output')],
        'receipts_verified': len(receipts),
        'plan_sha256': sha(root / 'plan.json'),
        'pins_sha256': sha(root / 'pins.json'),
        'completion_sha256': sha(root / 'diagnostic-completion.json'),
        'all_cases': summarize(plan['cases']),
        'excluding_failed_process_game': summarize([c for c in plan['cases'] if c['id'] != 'ze9rzvsl']),
        'by_opponent': {op: summarize([c for c in plan['cases'] if c['opponent'] == op]) for op in sorted({c['opponent'] for c in plan['cases']})},
        'promotion_eligible': False,
        'limitations': [
            'One unresolved process SIGSEGV after a complete output; diagnostic repeats do not erase it.',
            'Only 18 games, one fixed seed and a 20,000-entry cap; no arena clock thinning.',
            'No rebuild after empty belief; continued decisions remain in support and clipped NLL denominators.',
            'Risk compares the recorded own action, not a new policy; common nonempty coverage is selected.',
            'Total update time can shrink when the belief empties; this is not a throughput benchmark.',
            'Context splitting consumes the entry cap; this implementation is not a test of all temporal belief designs.',
        ],
    }
    (root / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('receipts_verified', 'all_cases', 'excluding_failed_process_game', 'promotion_eligible')}, indent=2))


if __name__ == '__main__':
    main()
