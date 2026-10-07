"""Paired game-level comparison of fixed-budget representation pilots."""
import argparse
import json
from pathlib import Path

import numpy as np

from learning_experiments.run import write_json


METRICS = {"policy_nll": "policy", "policy_accuracy": "policy", "hidden_nll": "hidden_squares",
           "hidden_enemy_nll": "hidden_enemy_squares", "danger_brier": "danger_candidates",
           "value_mse": "value"}


def compare(control, candidate, step, bootstrap=10000):
    runs = [json.loads((p / 'run.json').read_text()) for p in (control, candidate)]
    a, b = (dict(r['identity']) for r in runs)
    a.pop('model_config'); b.pop('model_config')
    if a != b:
        raise ValueError('training data or schedule differs between arms')
    if runs[0]['native']['sources'] != runs[1]['native']['sources']:
        raise ValueError('native feature rules snapshot differs between arms')
    logs = [[json.loads(line) for line in (p / 'train.jsonl').read_text().splitlines()] for p in (control, candidate)]
    logs = [[r for r in rows if r['step'] <= step] for rows in logs]
    if any(len(rows) != step or [r['step'] for r in rows] != list(range(1, step + 1)) for rows in logs):
        raise ValueError('missing or duplicated training updates')
    if [r['decisions'] for r in logs[0]] != [r['decisions'] for r in logs[1]]:
        raise ValueError('per-step valid decision counts differ')
    reports = [json.loads((p / f'validation-{step:06d}.json').read_text()) for p in (control, candidate)]
    games = sorted(reports[0]['by_game'])
    if games != sorted(reports[1]['by_game']):
        raise ValueError('held-out games differ')
    rng = np.random.default_rng(253)
    draws = rng.integers(len(games), size=(bootstrap, len(games)))
    results = {}
    for metric, denominator in METRICS.items():
        sums, counts = [], []
        for report in reports:
            sums.append(np.array([report['by_game'][g]['sums'][metric] for g in games]))
            counts.append(np.array([report['by_game'][g]['counts'][denominator] for g in games]))
        np.testing.assert_array_equal(counts[0], counts[1])
        values = [float(s.sum() / c.sum()) for s, c in zip(sums, counts)]
        deltas = ((sums[1][draws].sum(1) - sums[0][draws].sum(1)) / counts[0][draws].sum(1))
        results[metric] = {'control': values[0], 'candidate': values[1],
                           'candidate_minus_control': values[1] - values[0],
                           'paired_game_bootstrap_95': np.percentile(deltas, [2.5, 97.5]).tolist()}
    return {'step': step, 'seed': a['seed'], 'games': len(games),
            'validation_decisions': reports[0]['unique_decisions'],
            'training_decisions_each': sum(r['decisions'] for r in logs[0]),
            'control': str(control), 'candidate': str(candidate),
            'parameters': [r['model_parameters'] for r in runs],
            'elapsed_through_last_update_seconds': [rows[-1]['elapsed_seconds'] for rows in logs],
            'metrics': results,
            'danger_recall_at_fpr': [r['groups']['all']['danger_recall_at_fpr'] for r in reports],
            'limitations': ['One initialization seed; intervals cover held-out games, not training-seed variation.',
                            'Same optimizer updates and decisions, not equal elapsed compute.',
                            'Pilot allocation evidence, not an Elo estimate or a release gate.']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--control', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--step', type=int, default=1000)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = compare(args.control, args.candidate, args.step)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
