#!/usr/bin/env python3
"""Compare baseline and calibrated-fusion engine choices on fixed actor histories."""
import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path
import random


def read_choices(path):
    result = {}
    with path.open() as f:
        for line in f:
            row = json.loads(line)
            if 'engine_choice' not in row:
                continue
            key = (row['game'], row['side'], row['event'])
            if key in result:
                raise ValueError('duplicate engine choice')
            result[key] = row
    return result


def bootstrap(per_game, draws=10000, seed=20261011):
    games = sorted(per_game)
    rng = random.Random(seed)
    values = []
    for _ in range(draws):
        decisions = positives_base = positives_fused = 0
        for _ in games:
            d, b, f = per_game[games[rng.randrange(len(games))]]
            decisions += d
            positives_base += b
            positives_fused += f
        values.append((positives_fused - positives_base) / decisions)
    values.sort()
    total_d = sum(v[0] for v in per_game.values())
    base = sum(v[1] for v in per_game.values()) / total_d
    fused = sum(v[2] for v in per_game.values()) / total_d
    return {'baseline_rate': base, 'fused_rate': fused,
            'delta_fused_minus_baseline': fused - base,
            'game_bootstrap_95pct': [values[int(0.025 * draws)], values[int(0.975 * draws)]],
            'seed': seed, 'replicates': draws}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--labels', type=Path, required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--fused', type=Path, required=True)
    p.add_argument('--run-receipt', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--bootstrap', type=int, default=10000)
    args = p.parse_args()
    baseline, fused = read_choices(args.baseline), read_choices(args.fused)
    labels = {}
    with gzip.open(args.labels, 'rt') as f:
        for line in f:
            row = json.loads(line)
            key = (row['game'], row['side'], row['event'])
            if key in labels:
                raise ValueError('duplicate label decision')
            labels[key] = row
    if baseline.keys() != fused.keys() or baseline.keys() != labels.keys():
        raise ValueError(f'decision-key mismatch: baseline={len(baseline)} fused={len(fused)} labels={len(labels)}')

    changed = base_fatal = fused_fatal = 0
    changed_base_fatal_fused_safe = changed_base_safe_fused_fatal = 0
    base_risk_sum = fused_risk_sum = 0
    per_game = defaultdict(lambda: [0, 0, 0])
    for key, label_row in labels.items():
        b, f = baseline[key], fused[key]
        lc = label_row['candidates']
        bc, fc = b['candidates'], f['candidates']
        if {x['move'] for x in lc} != {x['move'] for x in bc} or {x['move'] for x in lc} != {x['move'] for x in fc}:
            raise ValueError('candidate-set mismatch')
        # Both arms consume the exact same actor prefix and neural outputs.
        bmap, fmap = {x['move']: x for x in bc}, {x['move']: x for x in fc}
        if bmap.keys() != fmap.keys():
            raise ValueError('candidate-key mismatch')
        for move in bmap:
            for field in ('particle', 'neural_logit', 'policy', 'king_move'):
                if bmap[move][field] != fmap[move][field]:
                    raise ValueError('non-risk prediction changed between arms')
        blabel = {x['move']: int(x['fatal']) for x in lc}
        bm, fm = b['engine_choice'], f['engine_choice']
        if bm not in blabel or fm not in blabel:
            raise ValueError('engine choice is not legal')
        by = blabel[bm]
        fy = blabel[fm]
        changed += bm != fm
        base_fatal += by
        fused_fatal += fy
        base_risk_sum += b['engine_choice_risk_permille']
        fused_risk_sum += f['engine_choice_risk_permille']
        changed_base_fatal_fused_safe += bm != fm and by == 1 and fy == 0
        changed_base_safe_fused_fatal += bm != fm and by == 0 and fy == 1
        g = per_game[key[0]]
        g[0] += 1
        g[1] += by
        g[2] += fy
    n = len(labels)
    run = json.loads(args.run_receipt.read_text())
    output = {
        'classification': 'fixed-history local choice ablation; each changed choice is followed by the recorded action sequence',
        'decisions': n,
        'games': len(per_game),
        'candidate_prediction_parity': 'exact for particle, neural logit, policy and legal moves across both binaries',
        'changed_choices': changed,
        'changed_choice_rate': changed / n,
        'baseline_selected_fatal': base_fatal,
        'fused_selected_fatal': fused_fatal,
        'baseline_selected_fatal_rate': base_fatal / n,
        'fused_selected_fatal_rate': fused_fatal / n,
        'fatal_rate_delta_bootstrap': bootstrap(per_game, args.bootstrap),
        'changed_choice_transitions': {
            'baseline_fatal_to_fused_safe': changed_base_fatal_fused_safe,
            'baseline_safe_to_fused_fatal': changed_base_safe_fused_fatal,
        },
        'mean_chosen_risk_permille': {'baseline': base_risk_sum / n, 'fused': fused_risk_sum / n},
        'runtime_seconds': {arm: run['arms'][arm]['elapsed_seconds'] for arm in ('baseline', 'fused')},
        'run_receipt_sha256': __import__('hashlib').sha256(args.run_receipt.read_bytes()).hexdigest(),
        'limitations': ['Retrospective fixed-history analysis, not a branched rollout or match.',
                        'Labels are immediate king-capturable outcomes only.',
                        'Fusion weights were fit on development-validation games; sealed test remains unread.',
                        'No Elo or release-strength claim.'],
    }
    args.output.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
