#!/usr/bin/env python3
"""CPU-only feasibility screen: does fog geometry add to an orthodox value?

Not a deployable bot. Uses complete sampled-world features, as a leaf evaluator
would, and final recorded outcomes. No team identity or future moves as inputs.
All selected positions sharing a board/turn/rights/EP/halfmove key share a fold.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time

import chess
import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def features(row, referee):
    board = referee.FowBoard(row['fen'])
    sides = []
    for side in [chess.WHITE, chess.BLACK]:
        view = referee.observation(board, side)
        enemy_view = referee.observation(board, not side)
        king = board.king(side)
        zone = board.attacks(king) | chess.SquareSet([king])
        attackers = board.attackers(not side, king)
        b = board.copy(stack=False)
        b.turn = side
        if side != board.turn:
            b.ep_square = None
        moves = referee.fow_moves(b)
        counts = [len(board.pieces(piece, side)) for piece in range(1, 6)]
        hidden_zone = sum(sum(view[a] == '?' for a in board.attackers(not side, s)) for s in zone)
        hidden_queen = 0
        hanging = 0
        hidden_hanging = 0
        concealed_material = 0
        values = {1: 1, 2: 3.2, 3: 3.3, 4: 5, 5: 9, 6: 0}
        for sq, piece in board.piece_map().items():
            if piece.color != side or piece.piece_type == chess.KING:
                continue
            aa = board.attackers(not side, sq)
            hidden = any(view[a] == '?' for a in aa)
            if piece.piece_type == chess.QUEEN and hidden:
                hidden_queen += 1
            if aa and not board.is_attacked_by(side, sq):
                hanging += values[piece.piece_type]
                if hidden:
                    hidden_hanging += values[piece.piece_type]
            if enemy_view[sq] == '?':
                concealed_material += values[piece.piece_type]
        sides.append({
            'pawn': counts[0], 'knight': counts[1], 'bishop': counts[2],
            'rook': counts[3], 'queen': counts[4], 'mobility': len(moves),
            'king_attacked': int(bool(attackers)), 'hanging_material': hanging,
            'visible_squares': 64-view.count('?'),
            'hidden_king_attackers': sum(view[a] == '?' for a in attackers),
            'hidden_king_zone_attacks': hidden_zone,
            'hidden_queen_attack': hidden_queen,
            'hidden_hanging_material': hidden_hanging,
            'concealed_material': concealed_material,
        })
    cp = np.clip(row['cp']/200., -20., 20.)
    result = {'cp': float(cp), 'cp_clip1': float(np.clip(cp, -1, 1)),
              'cp_clip3': float(np.clip(cp, -3, 3)), 'to_move': 1. if board.turn else -1.}
    for name in sides[0]:
        result[name] = float(sides[0][name]-sides[1][name])
    return result


def sigmoid(x):
    return 1/(1+np.exp(-np.clip(x, -40, 40)))


def fit(x, y, ridge):
    weights = np.zeros(x.shape[1])
    penalty = np.ones(x.shape[1])*ridge
    penalty[0] = .001
    def loss(w):
        z = x@w
        return np.sum(np.logaddexp(0, z)-y*z)+.5*np.dot(penalty*w, w)
    converged = False
    for iteration in range(80):
        p = sigmoid(x@weights)
        gradient = x.T@(p-y)+penalty*weights
        hessian = x.T@(x*(p*(1-p))[:, None])+np.diag(penalty)
        step = np.linalg.solve(hessian, gradient)
        old = loss(weights)
        scale = 1.
        while scale > 1e-7 and loss(weights-scale*step) > old:
            scale *= .5
        weights -= scale*step
        if np.max(np.abs(scale*step)) < 1e-7:
            converged = True
            break
    return weights, {'iterations': iteration+1, 'converged': converged,
                     'gradient_max': float(np.max(np.abs(x.T@(sigmoid(x@weights)-y)+penalty*weights)))}


def metrics(y, p):
    p = np.clip(p, 1e-9, 1-1e-9)
    return {'n': len(y), 'brier': float(np.mean((p-y)**2)),
            'log_loss': float(np.mean(-y*np.log(p)-(1-y)*np.log(1-p)))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--positions', type=Path, required=True)
    parser.add_argument('--exclude', type=Path, required=True, help='Previously inspected pilot games are excluded entirely')
    parser.add_argument('--referee', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('fog_screen_referee', args.referee)
    referee = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(referee)
    excluded = {json.loads(s)['game'] for s in args.exclude.read_text().splitlines()}
    rows = [r for r in map(json.loads, args.positions.read_text().splitlines()) if r['game'] not in excluded]
    # Canonical state grouping excludes move number; keep the fifty-move clock.
    keys = [' '.join(r['fen'].split()[:5]) for r in rows]
    folds = np.array([int(hashlib.sha256(('fog-value-v1/'+key).encode()).hexdigest()[:16], 16)%10 for key in keys])
    train, val, test = folds < 6, (folds >= 6)&(folds < 8), folds >= 8
    assert all(np.any(mask) for mask in [train, val, test])
    families = {
        'cp': ['cp', 'cp_clip1', 'cp_clip3', 'to_move'],
        'ordinary': ['pawn', 'knight', 'bishop', 'rook', 'queen', 'mobility', 'king_attacked', 'hanging_material'],
        'fog': ['visible_squares', 'hidden_king_attackers', 'hidden_king_zone_attacks', 'hidden_queen_attack',
                'hidden_hanging_material', 'concealed_material'],
    }
    manifest = {'tool_sha256': sha(Path(__file__)), 'positions_sha256': sha(args.positions),
        'excluded_sha256': sha(args.exclude), 'referee_sha256': sha(args.referee),
        'rows': len(rows), 'excluded_games': len(excluded), 'feature_families': families,
        'split': 'SHA256(fog-value-v1/ + first five FEN fields) modulo 10; train0..5,val6..7,test8..9',
        'ridge_grid': [1., 10., 100.], 'selection': 'minimum validation log loss, then one test evaluation',
        'classification': 'offline predictive feasibility; no search integration or strength evidence'}
    (args.out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    start = time.monotonic()
    fs = [features(row, referee) for row in rows]
    feature_seconds = time.monotonic()-start
    y = np.array([r['target'] for r in rows])
    names = families['cp']+families['ordinary']+families['fog']
    x = np.array([[f[n] for n in names] for f in fs])
    report = {'manifest': manifest, 'feature_seconds': feature_seconds,
        'fold_sizes': {k: int(v.sum()) for k, v in [('train', train), ('validation', val), ('test', test)]},
        'unique_state_groups': len(set(keys)), 'models': {}, 'limitations': [
            'Outcomes follow recorded policies; this is not an equilibrium value or a causal treatment effect.',
            'Current-state grouping blocks exact position leakage; related games, teams and dates remain correlated.',
            'Features use a complete sampled world. This is not an observation-only policy or an oracle available to the arena bot.',
            'No time-split or opponent-holdout generalization claim. No runtime cost or playing strength measured.']}
    predictions = {}
    for name, count in [('cp', len(families['cp'])), ('ordinary', len(families['cp'])+len(families['ordinary'])), ('fog', len(names))]:
        mean = x[train, :count].mean(axis=0)
        std = x[train, :count].std(axis=0)
        std[std < 1e-8] = 1
        xx = np.column_stack([np.ones(len(rows)), (x[:, :count]-mean)/std])
        candidates = []
        for ridge in manifest['ridge_grid']:
            w, status = fit(xx[train], y[train], ridge)
            assert status['converged'], status
            candidates.append((metrics(y[val], sigmoid(xx[val]@w))['log_loss'], ridge, w, status))
        _, ridge, w, status = min(candidates, key=lambda item: item[0])
        p = sigmoid(xx@w)
        predictions[name] = p[test]
        report['models'][name] = {'ridge': ridge, 'validation': metrics(y[val], p[val]),
            'test': metrics(y[test], p[test]), 'fit': status,
            'weights': dict(zip(['intercept']+names[:count], w.tolist())),
            'feature_mean': mean.tolist(), 'feature_std': std.tolist()}
    # Paired bootstrap over state groups, not individual correlated duplicates.
    indices = np.flatnonzero(test)
    grouped = {}
    for j, i in enumerate(indices):
        grouped.setdefault(keys[i], []).append(j)
    rng = np.random.default_rng(20261011)
    comparisons = {}
    for baseline in ['cp', 'ordinary']:
        delta = (predictions['fog']-y[test])**2-(predictions[baseline]-y[test])**2
        sums = np.array([delta[js].sum() for js in grouped.values()])
        counts = np.array([len(js) for js in grouped.values()])
        boot = []
        for _ in range(2000):
            sample = rng.integers(0, len(sums), len(sums))
            boot.append(sums[sample].sum()/counts[sample].sum())
        comparisons['fog_minus_'+baseline] = {'brier_delta': float(delta.mean()),
            'group_bootstrap_95_percent': np.quantile(boot, [.025, .975]).tolist()}
    report['comparisons'] = comparisons
    (args.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    with (args.out/'test-predictions.jsonl').open('w') as output:
        for j, i in enumerate(indices):
            output.write(json.dumps({'game': rows[i]['game'], 'state_key': keys[i], 'target': y[i],
                'prediction': {k: float(v[j]) for k, v in predictions.items()}})+'\n')
    print(json.dumps({k: report[k] for k in ['feature_seconds', 'fold_sizes', 'comparisons']}, indent=2))


if __name__ == '__main__':
    main()
