"""Paired whole-game comparison of complete frozen-panel model evaluations.

The gate allows only a subsequent C-search integration test, never promotion.
Inputs must cover identical observation histories from the whole frozen panel.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def compare(control, candidate, samples=20000, seed=20261025):
    for report in (control, candidate):
        if report['state'] != 'complete' or not report['full_panel'] or report['failures']:
            raise ValueError('Only complete full-panel evaluations can enter this gate')
    for key in ('panel_sha256', 'collector_sha256', 'source_receipt_sha256', 'native_library_sha256'):
        if control[key] != candidate[key]:
            raise ValueError('Evaluation identity differs: ' + key)
    def by_game(report):
        records = {(r['game'], r['side']): r for r in report['game_records']}
        if len(records) != len(report['game_records']):
            raise ValueError('Repeated game/side')
        return records
    a, b = by_game(control), by_game(candidate)
    if set(a) != set(b) or len(a) != control['games_requested'] or len(b) != candidate['games_requested']:
        raise ValueError('Coverage differs')
    keys = sorted(a)
    for key in keys:
        for field in ('actor_input_sha256', 'replay_sha256'):
            if a[key][field] != b[key][field]:
                raise ValueError('History identity differs: ' + str(key))
        for field in ('decisions', 'mixed_decisions', 'no_escape_decisions'):
            if a[key]['metrics'][field] != b[key]['metrics'][field]:
                raise ValueError('Label coverage differs: ' + str(key))
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(keys), size=(samples, len(keys)))
    result = {}
    for metric in ('log_loss', 'brier', 'policy_fatal', 'min_risk_fatal', 'policy_fatal_mass'):
        x = np.array([a[k]['metrics'][metric] for k in keys])
        y = np.array([b[k]['metrics'][metric] for k in keys])
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError('Nonfinite metric')
        delta = y - x
        result[metric] = {'control_game_mean': float(x.mean()), 'candidate_game_mean': float(y.mean()),
                          'candidate_minus_control': float(delta.mean()),
                          'paired_game_bootstrap_95': np.quantile(delta[indices].mean(1), [.025, .975]).tolist()}
    mixed = [k for k in keys if a[k]['metrics']['auc'] is not None]
    if any((a[k]['metrics']['auc'] is None) != (b[k]['metrics']['auc'] is None) for k in keys):
        raise ValueError('Mixed-label game coverage differs')
    auc_delta = float(np.mean([b[k]['metrics']['auc'] - a[k]['metrics']['auc'] for k in mixed])) if mixed else None
    counts = {name: {'control': sum(a[k]['metrics'][name] for k in keys),
                     'candidate': sum(b[k]['metrics'][name] for k in keys)}
              for name in ('policy_fatal_count', 'min_risk_fatal_count',
                           'avoidable_policy_fatal_count', 'avoidable_min_risk_fatal_count')}
    conditions = {
        'risk_log_loss_interval_below_zero': result['log_loss']['paired_game_bootstrap_95'][1] < 0,
        'within_position_ordering_not_worse': auc_delta is not None and auc_delta >= 0,
        'policy_fatal_count_not_worse': counts['policy_fatal_count']['candidate'] <= counts['policy_fatal_count']['control'],
        'avoidable_policy_fatal_count_not_worse': counts['avoidable_policy_fatal_count']['candidate'] <= counts['avoidable_policy_fatal_count']['control'],
    }
    return {'games': len(keys), 'game_weighted_metrics': result,
            'mixed_label_games': len(mixed), 'game_mean_auc_delta': auc_delta, 'choice_counts': counts,
            'conditions': conditions, 'advance_to_c_search_integration_test': all(conditions.values()),
            'bootstrap': {'samples': samples, 'seed': seed, 'unit': 'whole replay game'},
            'limits': ['No training-return or arena-strength evidence; selected actions were not played.',
                       'The interval is approximate and does not model correlations between games with shared openings.',
                       'Within-position ordering and safety are point-estimate non-regression checks, not proven equivalence.',
                       'No policy distribution, search root mask, or arena release is changed by this gate.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(json.loads(args.control.read_bytes()), json.loads(args.candidate.read_bytes()))
    result['inputs'] = {name: {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                       for name, p in (('control', args.control), ('candidate', args.candidate))}
    result['comparator_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'advance_to_c_search_integration_test': result['advance_to_c_search_integration_test'],
                      'conditions': result['conditions']}))


if __name__ == '__main__':
    main()
