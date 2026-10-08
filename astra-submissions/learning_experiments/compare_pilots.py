"""Paired game-level comparison of fixed-budget representation pilots."""
import argparse
import json
from pathlib import Path

import numpy as np

from learning_experiments.run import write_json


METRICS = {"policy_nll": "policy", "policy_accuracy": "policy", "hidden_nll": "hidden_squares",
           "hidden_enemy_nll": "hidden_enemy_squares", "danger_brier": "danger_candidates",
           "value_mse": "value"}
SLATE_METRICS = {"policy_entropy": "decisions", "policy_hit4": "policy",
                 "policy_hit8": "policy", "policy_hit16": "policy",
                 "policy_top1_fatal": "danger_decisions",
                 "policy_top1_avoidable_fatal": "avoidable_danger_decisions",
                 "policy_top4_all_fatal_when_escape_exists": "avoidable_danger_decisions",
                 "policy_top4_fatal_fraction": "policy_top4_candidates"}


def recorded_update_time(rows):
    """Sum recorded training-loop time across explicit restart time resets.

    This includes intermediate validation inside each training loop, but not
    setup or the validation following its last logged update. It is a wall-time
    proxy, not a GPU FLOP count or an isolated throughput measurement.
    """
    completed, previous = 0.0, 0.0
    for row in rows:
        elapsed = row['elapsed_seconds']
        if elapsed < previous:
            completed += previous
        previous = elapsed
    return completed + previous


def compare(control, candidate, step, bootstrap=10000, control_step=None, candidate_step=None):
    steps = [step if control_step is None else control_step,
             step if candidate_step is None else candidate_step]
    runs = [json.loads((p / 'run.json').read_text()) for p in (control, candidate)]
    a, b = (dict(r['identity']) for r in runs)
    a.pop('model_config'); b.pop('model_config')
    if a != b:
        raise ValueError('training data or schedule differs between arms')
    if runs[0]['native']['sources'] != runs[1]['native']['sources']:
        raise ValueError('native feature rules snapshot differs between arms')
    logs = [[json.loads(line) for line in (p / 'train.jsonl').read_text().splitlines()] for p in (control, candidate)]
    logs = [[r for r in rows if r['step'] <= end] for rows, end in zip(logs, steps)]
    if any(len(rows) != end or [r['step'] for r in rows] != list(range(1, end + 1))
           for rows, end in zip(logs, steps)):
        raise ValueError('missing or duplicated training updates')
    common_steps = min(steps)
    if [r['decisions'] for r in logs[0][:common_steps]] != [r['decisions'] for r in logs[1][:common_steps]]:
        raise ValueError('per-step valid decision counts differ within shared training prefix')
    reports = [json.loads((p / f'validation-{end:06d}.json').read_text())
               for p, end in zip((control, candidate), steps)]
    games = sorted(reports[0]['by_game'])
    if games != sorted(reports[1]['by_game']):
        raise ValueError('held-out games differ')
    rng = np.random.default_rng(253)
    draws = rng.integers(len(games), size=(bootstrap, len(games)))
    results = {}
    omitted = []
    for metric, denominator in (METRICS | SLATE_METRICS).items():
        if metric in SLATE_METRICS and not all(
                metric in report['by_game'][g]['sums'] for report in reports for g in games):
            omitted.append(metric)  # Preserve comparisons of legacy reports.
            continue
        sums, counts = [], []
        for report in reports:
            sums.append(np.array([report['by_game'][g]['sums'][metric] for g in games]))
            counts.append(np.array([report['by_game'][g]['counts'][denominator] for g in games]))
        np.testing.assert_array_equal(counts[0], counts[1])
        if counts[0].sum() == 0:
            results[metric] = {'control': None, 'candidate': None,
                               'candidate_minus_control': None, 'paired_game_bootstrap_95': None}
            continue
        values = [float(s.sum() / c.sum()) for s, c in zip(sums, counts)]
        bootstrap_counts = counts[0][draws].sum(1)
        valid = bootstrap_counts > 0
        deltas = ((sums[1][draws].sum(1) - sums[0][draws].sum(1))[valid] / bootstrap_counts[valid])
        results[metric] = {'control': values[0], 'candidate': values[1],
                           'candidate_minus_control': values[1] - values[0],
                           'paired_game_bootstrap_95': np.percentile(deltas, [2.5, 97.5]).tolist(),
                           'bootstrap_samples_with_nonzero_denominator': int(valid.sum())}
    return {'step': steps[0] if steps[0] == steps[1] else None,
            'control_step': steps[0], 'candidate_step': steps[1],
            'seed': a['seed'], 'games': len(games),
            'validation_decisions': reports[0]['unique_decisions'],
            'training_decisions_each': sum(r['decisions'] for r in logs[0]) if steps[0] == steps[1] else None,
            'training_decisions': [sum(r['decisions'] for r in rows) for rows in logs],
            'control': str(control), 'candidate': str(candidate),
            'parameters': [r['model_parameters'] for r in runs],
            'elapsed_through_last_update_seconds': [recorded_update_time(rows) for rows in logs],
            'metrics': results,
            'legacy_metrics_unavailable': omitted,
            'danger_recall_at_fpr': [r['groups']['all']['danger_recall_at_fpr'] for r in reports],
            'limitations': ['One initialization seed; intervals cover held-out games, not training-seed variation.',
                            ('Same optimizer updates and decisions, not equal elapsed compute.' if steps[0] == steps[1]
                             else 'Different update budgets; observed training-loop wall times are reported, including intermediate validation.'),
                            'Pilot allocation evidence, not an Elo estimate or a release gate.']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--control', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--step', type=int, default=1000)
    p.add_argument('--control-step', type=int)
    p.add_argument('--candidate-step', type=int)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = compare(args.control, args.candidate, args.step,
                     control_step=args.control_step, candidate_step=args.candidate_step)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
