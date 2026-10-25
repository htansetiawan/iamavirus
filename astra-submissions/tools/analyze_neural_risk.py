#!/usr/bin/env python3
"""Fit decision-weighted calibrators for particle and neural king-risk signals.

Uses only the actor-only predictions collected by collect_neural_risk.py. The
collector joins exact replay labels after inference. No prediction is used to
choose a move by this analysis.
"""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import random


EPS = 1e-12
CLIP = 1e-4
RIDGE = 0.001


def sigmoid(x):
    if x >= 0:
        z = math.exp(-min(x, 700.0))
        return 1.0 / (1.0 + z)
    z = math.exp(max(x, -700.0))
    return z / (1.0 + z)


def logit(p):
    p = min(1.0 - CLIP, max(CLIP, p))
    return math.log(p / (1.0 - p))


def load(path):
    decisions = []
    with gzip.open(path, 'rt') as f:
        for line in f:
            row = json.loads(line)
            if not row['label_valid']:
                continue
            candidates = row['candidates']
            if not candidates:
                raise ValueError('empty legal candidate set')
            records = []
            for c in candidates:
                records.append({
                    'particle_x': logit(c['particle']),
                    'neural_x': c['neural_logit'],
                    'y': int(c['fatal']),
                    'particle': c['particle'],
                    'neural_logit': c['neural_logit'],
                    'king_move': bool(c['king_move']),
                    'ply': row['ply'],
                })
            decisions.append({'game': row['game'], 'side': row['side'],
                              'event': row['event'], 'ply': row['ply'],
                              'candidates': records})
    return decisions


def weighted_standardize(decisions):
    sw = 0.0
    means = [0.0, 0.0]
    for d in decisions:
        w = 1.0 / len(d['candidates'])
        for c in d['candidates']:
            sw += w
            means[0] += w * c['particle_x']
            means[1] += w * c['neural_x']
    means = [x / sw for x in means]
    variances = [0.0, 0.0]
    for d in decisions:
        w = 1.0 / len(d['candidates'])
        for c in d['candidates']:
            variances[0] += w * (c['particle_x'] - means[0]) ** 2
            variances[1] += w * (c['neural_x'] - means[1]) ** 2
    scales = [max(EPS, math.sqrt(x / sw)) for x in variances]
    return means, scales


def rows(decisions, means, scales):
    out = []
    for d in decisions:
        weight = 1.0 / len(d['candidates'])
        for c in d['candidates']:
            out.append(([1.0, (c['particle_x'] - means[0]) / scales[0],
                         (c['neural_x'] - means[1]) / scales[1]],
                        c['y'], weight, d, c))
    return out


def objective(data, beta, active):
    value = 0.5 * RIDGE * sum(beta[j] ** 2 for j in active)
    for x, y, w, _, _ in data:
        z = sum(beta[j] * x[j] for j in range(3))
        value += w * (max(z, 0.0) + math.log1p(math.exp(-abs(z))) - y * z)
    return value


def solve_linear(a, b):
    n = len(b)
    m = [list(a[i]) + [b[i]] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-14:
            return None
        m[col], m[pivot] = m[pivot], m[col]
        div = m[col][col]
        for j in range(col, n + 1):
            m[col][j] /= div
        for r in range(n):
            if r == col:
                continue
            factor = m[r][col]
            for j in range(col, n + 1):
                m[r][j] -= factor * m[col][j]
    return [m[i][n] for i in range(n)]


def fit_face(data, active):
    indices = [0, *active]
    beta = [0.0] * 3
    prevalence = sum(w * y for _, y, w, _, _ in data) / sum(w for _, _, w, _, _ in data)
    prevalence = min(1.0 - 1e-8, max(1e-8, prevalence))
    beta[0] = math.log(prevalence / (1.0 - prevalence))
    for _ in range(100):
        n = len(indices)
        grad = [0.0] * n
        hess = [[0.0] * n for _ in range(n)]
        for x, y, w, _, _ in data:
            z = sum(beta[j] * x[j] for j in range(3))
            p = sigmoid(z)
            v = w * p * (1.0 - p)
            for a, ia in enumerate(indices):
                grad[a] += w * (p - y) * x[ia]
                for b, ib in enumerate(indices):
                    hess[a][b] += v * x[ia] * x[ib]
        for a, ia in enumerate(indices):
            if ia in active:
                grad[a] += RIDGE * beta[ia]
                hess[a][a] += RIDGE
        delta = solve_linear(hess, grad)
        if delta is None:
            break
        old = objective(data, beta, active)
        step = 1.0
        while step > 1e-8:
            candidate = beta[:]
            for a, ia in enumerate(indices):
                candidate[ia] -= step * delta[a]
            if objective(data, candidate, active) <= old + 1e-12:
                beta = candidate
                break
            step *= 0.5
        if step <= 1e-8 or max(abs(step * x) for x in delta) < 1e-8:
            break
    return beta


def fit(data, active):
    faces = []
    for mask in range(1 << len(active)):
        face = [active[i] for i in range(len(active)) if mask & (1 << i)]
        beta = fit_face(data, face)
        if any(beta[j] < -1e-9 for j in face):
            continue
        for j in active:
            if j not in face:
                beta[j] = 0.0
        faces.append((objective(data, beta, face), beta, face))
    if not faces:
        raise RuntimeError('no feasible calibration face')
    score, beta, face = min(faces, key=lambda x: x[0])
    return {'beta': beta, 'active_features': face, 'objective': score}


def score(beta, x):
    return sigmoid(sum(beta[j] * x[j] for j in range(3)))


def weighted_metrics(records, probability_fn):
    by_game = defaultdict(lambda: [0.0, 0.0, 0.0])
    # total, brier, logloss; each decision gets unit total weight.
    for d in records:
        n = len(d['candidates'])
        g = by_game[d['game']]
        g[0] += 1.0
        for c in d['candidates']:
            p = min(1.0 - 1e-12, max(1e-12, probability_fn(d, c)))
            w = 1.0 / n
            y = c['y']
            g[1] += w * (p - y) ** 2
            g[2] += w * (-(y * math.log(p) + (1 - y) * math.log1p(-p)))
    decisions_n = sum(v[0] for v in by_game.values())
    return {'decisions': int(decisions_n),
            'brier': sum(v[1] for v in by_game.values()) / decisions_n,
            'log_loss': sum(v[2] for v in by_game.values()) / decisions_n,
            'by_game': by_game}


def paired_bootstrap(a, b, seed=20261011, replicates=10000):
    games = sorted(set(a['by_game']) & set(b['by_game']))
    per_game = []
    for game in games:
        da, ba, la = a['by_game'][game]
        db, bb, lb = b['by_game'][game]
        if da != db:
            raise ValueError('paired game decisions differ')
        per_game.append((da, bb - ba, lb - la))
    rng = random.Random(seed)
    vals = [[], []]
    for _ in range(replicates):
        n = 0
        sums = [0.0, 0.0]
        for _ in games:
            d, db, dl = per_game[rng.randrange(len(games))]
            n += d
            sums[0] += db
            sums[1] += dl
        vals[0].append(sums[0] / n)
        vals[1].append(sums[1] / n)
    result = {}
    for i, name in enumerate(('brier', 'log_loss')):
        vals[i].sort()
        result[name] = {'mean_delta_b_minus_a': sum(x[1 + i] for x in per_game) /
                        sum(x[0] for x in per_game),
                        'game_bootstrap_95pct': [vals[i][int(0.025 * replicates)],
                                                 vals[i][int(0.975 * replicates)]]}
    return result


def threshold_for_fpr(decisions, predictor, target):
    negatives = []
    total_negative = 0.0
    for d in decisions:
        w = 1.0 / len(d['candidates'])
        for c in d['candidates']:
            if not c['y']:
                negatives.append((predictor(d, c), w))
                total_negative += w
    negatives.sort(reverse=True)
    allowed = target * total_negative
    taken, threshold = 0.0, math.inf
    i = 0
    while i < len(negatives):
        value = negatives[i][0]
        j = i
        group = 0.0
        while j < len(negatives) and negatives[j][0] == value:
            group += negatives[j][1]
            j += 1
        if taken + group > allowed + 1e-12:
            break
        taken += group
        threshold = value
        i = j
    return threshold


def operating_point(decisions, predictor, threshold):
    fp = neg = tp = pos = 0.0
    for d in decisions:
        w = 1.0 / len(d['candidates'])
        for c in d['candidates']:
            predicted = predictor(d, c) >= threshold
            if c['y']:
                pos += w
                if predicted: tp += w
            else:
                neg += w
                if predicted: fp += w
    return {'threshold': threshold if math.isfinite(threshold) else None,
            'false_positive_rate': fp / neg if neg else None,
            'recall': tp / pos if pos else None,
            'positive_weight': pos, 'negative_weight': neg}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--calibration', type=Path, required=True)
    p.add_argument('--evaluation', type=Path, required=True)
    p.add_argument('--collection-state', type=Path, required=True)
    p.add_argument('--design', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--bootstrap', type=int, default=10000)
    args = p.parse_args()
    cal, eva = load(args.calibration), load(args.evaluation)
    collection = json.loads(args.collection_state.read_text())
    design = json.loads(args.design.read_text())
    means, scales = weighted_standardize(cal)
    cal_rows, eva_rows = rows(cal, means, scales), rows(eva, means, scales)
    fitted = {
        'particle_only': fit(cal_rows, [1]),
        'neural_only': fit(cal_rows, [2]),
        'fused': fit(cal_rows, [1, 2]),
    }
    def features(d, c):
        return [1.0, (c['particle_x'] - means[0]) / scales[0],
                (c['neural_x'] - means[1]) / scales[1]]
    predictors = {
        'raw_particle': lambda d, c: c['particle'],
        'calibrated_particle': lambda d, c: score(fitted['particle_only']['beta'], features(d, c)),
        'calibrated_neural': lambda d, c: score(fitted['neural_only']['beta'], features(d, c)),
        'fused': lambda d, c: score(fitted['fused']['beta'], features(d, c)),
    }
    metrics = {name: weighted_metrics(eva, fn) for name, fn in predictors.items()}
    deltas = paired_bootstrap(metrics['calibrated_particle'], metrics['fused'],
                              replicates=args.bootstrap)
    thresholds = {}
    for name, fn in predictors.items():
        thresholds[name] = {}
        for fpr in (0.01, 0.05):
            threshold = threshold_for_fpr(cal, fn, fpr)
            thresholds[name][str(fpr)] = {
                'calibration': operating_point(cal, fn, threshold),
                'evaluation': operating_point(eva, fn, threshold),
            }
    subgroups = {}
    for group_name, predicate in (
        ('zero_particle_risk', lambda d, c: c['particle'] == 0.0),
        ('king_moves', lambda d, c: c['king_move']),
        ('early_ply_lt20', lambda d, c: c['ply'] < 20),
        ('middle_ply_20_59', lambda d, c: 20 <= c['ply'] < 60),
        ('late_ply_ge60', lambda d, c: c['ply'] >= 60),
    ):
        selected = []
        for d in eva:
            cs = [c for c in d['candidates'] if predicate(d, c)]
            if cs:
                selected.append({**d, 'candidates': cs})
        subgroups[group_name] = {'decisions': len(selected), 'candidates': sum(len(d['candidates']) for d in selected)}
        for name in ('calibrated_particle', 'fused'):
            subgroups[group_name][name] = weighted_metrics(selected, predictors[name])
            subgroups[group_name][name].pop('by_game')
    summary = {
        'classification': 'actor-only held-out validation; model predictions fixed before label join; no move selection changed',
        'calibration_games': len(set(d['game'] for d in cal)),
        'evaluation_games': len(set(d['game'] for d in eva)),
        'calibration_decisions': len(cal), 'evaluation_decisions': len(eva),
        'calibration_candidates': sum(len(d['candidates']) for d in cal),
        'evaluation_candidates': sum(len(d['candidates']) for d in eva),
        'calibration_positive_candidates': sum(c['y'] for d in cal for c in d['candidates']),
        'evaluation_positive_candidates': sum(c['y'] for d in eva for c in d['candidates']),
        'decision_weighting': 'each sampled decision has total weight 1, divided equally among its legal candidates',
        'provenance': {
            'calibration_sha256': hashlib.sha256(args.calibration.read_bytes()).hexdigest(),
            'evaluation_sha256': hashlib.sha256(args.evaluation.read_bytes()).hexdigest(),
            'collection_state_sha256': hashlib.sha256(args.collection_state.read_bytes()).hexdigest(),
            'collection_inputs': collection['inputs'],
            'model_checkpoint_sha256': design['model_checkpoint_sha256'],
            'model_graphs': design['model_graphs'],
            'probe_sha256': design['probe_sha256'],
            'test_shard_used': design['test_shard_used'],
            'bootstrap_seed': 20261011,
            'bootstrap_replicates': args.bootstrap,
        },
        'feature_standardization': {'weighted_mean': means, 'weighted_std': scales},
        'ridge': RIDGE,
        'calibrators': fitted,
        'evaluation': {name: {k: v for k, v in value.items() if k != 'by_game'}
                       for name, value in metrics.items()},
        'fused_minus_calibrated_particle': deltas,
        'operating_points': thresholds,
        'subgroups': subgroups,
        'limitations': ['One trained model and one particle-filter seed.',
                        'Validation-development data, not sealed test data.',
                        'Calibration targets immediate king-capturable labels only.',
                        'Calibrated risk is not a joint posterior or multi-ply forced-loss probability.'],
    }
    args.output.write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: summary[k] for k in ('calibration_games', 'evaluation_games',
          'calibration_decisions', 'evaluation_decisions', 'calibration_candidates',
          'evaluation_candidates', 'evaluation', 'fused_minus_calibrated_particle')}, indent=2))


if __name__ == '__main__':
    main()
