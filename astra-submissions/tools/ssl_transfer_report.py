#!/usr/bin/env python3
"""Strict identical-source SSL-transfer comparisons, including legacy pilots.

This is an offline report reader. It does not relax training, export or runtime
feature contracts. Complete source and native-rule hashes must match.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

METRICS = {'policy_nll': 'policy', 'policy_accuracy': 'policy',
           'hidden_nll': 'hidden_squares', 'hidden_enemy_nll': 'hidden_enemy_squares',
           'danger_brier': 'danger_candidates', 'value_mse': 'value'}
METRICS.update({f'hidden_piece_{k}_{m}': f'hidden_piece_{k}' for k in range(6) for m in ('nll', 'recall')})


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def paired(a, b):
    games = sorted(a['by_game'])
    if not games or games != sorted(b['by_game']) or a['unique_decisions'] != b['unique_decisions']:
        raise ValueError('different held-out decisions')
    for g in games:
        if a['by_game'][g]['counts'] != b['by_game'][g]['counts']:
            raise ValueError('different target denominators: ' + g)
    draws = np.random.default_rng(253).integers(len(games), size=(10000, len(games)))
    result = {}
    for metric, denom in METRICS.items():
        counts = np.array([a['by_game'][g]['counts'].get(denom, 0) for g in games])
        sums = [np.array([r['by_game'][g]['sums'].get(metric, 0) for g in games]) for r in (a, b)]
        if not counts.sum():
            continue
        boot_count = counts[draws].sum(1)
        valid = boot_count > 0
        delta = (sums[1][draws].sum(1) - sums[0][draws].sum(1))[valid] / boot_count[valid]
        values = [float(s.sum() / counts.sum()) for s in sums]
        result[metric] = dict(control=values[0], candidate=values[1], candidate_minus_control=values[1]-values[0],
                              paired_game_bootstrap_95=np.percentile(delta, [2.5, 97.5]).tolist(),
                              target_count=int(counts.sum()))
    return {'games': len(games), 'decisions': a['unique_decisions'], 'metrics': result}


def logs(run, end):
    rows = [json.loads(x) for x in (run/'train.jsonl').read_text().splitlines()]
    rows = [r for r in rows if r['step'] <= end]
    if [r['step'] for r in rows] != list(range(1, end+1)):
        raise ValueError('missing/duplicated training updates')
    if any(y['elapsed_seconds'] < x['elapsed_seconds'] for x, y in zip(rows, rows[1:])):
        raise ValueError('fresh uninterrupted runs required for this timing comparison')
    return rows


def compare(control, candidate, control_step, candidate_step=1000):
    meta = [read(p/'run.json') for p in (control, candidate)]
    for key in ('identity', 'architecture', 'source_sha256', 'model_parameters'):
        if meta[0][key] != meta[1][key]:
            raise ValueError('different experiment contract: ' + key)
    if meta[0]['native']['sources'] != meta[1]['native']['sources']:
        raise ValueError('different native rules sources')
    # Legacy feature semantics are pinned by the complete feature source hash.
    if 'learning/features.py' not in meta[0]['source_sha256']:
        raise ValueError('feature source provenance absent')
    traces = [logs(p, s) for p, s in zip((control, candidate), (control_step, candidate_step))]
    n = min(control_step, candidate_step)
    if [r['decisions'] for r in traces[0][:n]] != [r['decisions'] for r in traces[1][:n]]:
        raise ValueError('different sampled decisions in shared training prefix')
    files = [p/f'validation-{s:06d}.json' for p,s in zip((control,candidate),(control_step,candidate_step))]
    out = paired(*map(read, files))
    out.update(control=str(control), candidate=str(candidate), control_step=control_step, candidate_step=candidate_step,
               validation_sha256=[sha(p) for p in files], source_sha256=meta[0]['source_sha256'],
               training_decisions=[sum(r['decisions'] for r in rows) for rows in traces],
               loop_wall_seconds=[r[-1]['elapsed_seconds'] for r in traces],
               danger_recall_at_fpr=[read(p)['groups']['all']['danger_recall_at_fpr'] for p in files])
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--control',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--control-step',type=int,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():
        raise ValueError('retain immutable comparison output')
    out=compare(args.control,args.candidate,args.control_step)
    out['limitations']=['One seed: game bootstrap does not cover initialization variation.',
                        'Validation games have been reused for architecture research; intervals do not account for experiment selection.',
                        'Equal downstream updates omit the SSL pretraining cost; report that separately.',
                        'Loop wall time includes intermediate validation but omits setup and final validation.',
                        'These legacy-source task metrics are not runtime compatibility or Elo evidence.']
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:out['metrics'][k] for k in ('policy_nll','hidden_enemy_nll','danger_brier')},indent=2))


if __name__=='__main__':
    main()
