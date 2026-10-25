#!/usr/bin/env python3
"""Verify and summarize a completed, fixed-size color-swapped match gate.

This never runs games or changes the input manifest. Bootstrap units are whole
color-swapped pairs. Replay checks use the match referee and establish internal
integrity, not independent confirmation of the referee's rules.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--referee-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.manifest.read_bytes()
    manifest = json.loads(raw)
    require(manifest['state'] == 'complete', 'Gate is not complete; do not summarize a partial run as final')
    pairs_planned = manifest['pairs_planned']
    require(len(manifest['games']) == 2 * pairs_planned, 'Game count differs from fixed cap')
    sys.path.insert(0, str(args.referee_dir.resolve()))
    from referee import FowBoard, make_frame, outcome, position_key

    pins = manifest.get('hashes', {})
    identities = {
        'baseline_binary': (Path(manifest['baseline']) / 'mist',
                            pins.get('baseline_binary_sha256', manifest.get('baseline_sha256'))),
        'candidate_binary': (Path(manifest['candidate']) / 'mist',
                             pins.get('candidate_binary_sha256', manifest.get('candidate_sha256'))),
        'referee': (args.referee_dir / 'referee.py',
                    pins.get('referee_sha256', manifest.get('referee_sha256'))),
    }
    for name, (path, digest) in identities.items():
        require(sha(path) == digest, f'{name} differs from recorded hash')

    results = Counter()
    colors = {'white': Counter(), 'black': Counter()}
    pair_games = defaultdict(dict)
    rows = []
    for record in manifest['games']:
        pair, side = record['pair'], record['candidate_color']
        require(0 <= pair < pairs_planned and side in colors, 'Invalid pair or side')
        require(side not in pair_games[pair], 'Repeated pair/side')
        require(record['candidate_seed'] == manifest['seed'] + 2 * pair, 'Candidate seed mismatch')
        require(record['baseline_seed'] == manifest['seed'] + 2 * pair + 1, 'Baseline seed mismatch')
        path = Path(record['replay'])
        digest = sha(path)
        require(digest == record['replay_sha256'], f'Replay hash changed: {path}')
        replay = json.loads(path.read_bytes())
        require(replay['result'] in ('1-0', '0-1', '1/2-1/2'), f'Unknown result: {path}')
        require(bool(replay['frames']), f'Empty replay: {path}')
        require(replay['result'] == record['result'] and replay['reason'] == record['reason'],
                f'Result metadata mismatch: {path}')
        board = FowBoard()
        repetitions = Counter({position_key(board): 1})
        ended = None
        for index, frame in enumerate(replay['frames']):
            if index:
                require(ended is None, f'Move after board termination: {path}, frame {index}')
                board.push(board.parse_uci(frame['move']))
                repetitions[position_key(board)] += 1
            expected = make_frame(board, frame['clocks'], frame['move'])
            for key in ('ply', 'board', 'white', 'black'):
                require(frame[key] == expected[key], f'{key} mismatch: {path}, frame {index}')
            require(len(frame['clocks']) == 2 and all(math.isfinite(t) for t in frame['clocks']),
                    f'Invalid clocks: {path}, frame {index}')
            ended = outcome(board, repetitions)
        require(len(replay['frames']) - 1 == record['plies'], f'Ply count mismatch: {path}')
        require(replay['frames'][-1]['clocks'] == record['final_clocks'], f'Final clocks mismatch: {path}')
        if ended is not None:
            require(tuple(ended) == (replay['result'], replay['reason']), f'Board outcome mismatch: {path}')
        score = 0.5 if replay['result'] == '1/2-1/2' else float(
            replay['result'] == ('1-0' if side == 'white' else '0-1'))
        require(score == record['candidate_score'], f'Score mismatch: {path}')
        label = {0.: 'losses', .5: 'draws', 1.: 'wins'}[score]
        results[label] += 1
        colors[side][label] += 1
        pair_games[pair][side] = score
        rows.append({'pair': pair, 'candidate_color': side, 'replay': str(path),
                     'sha256': digest, 'frames_verified': len(replay['frames']),
                     'board_terminal_verified': ended is not None,
                     'result': replay['result'], 'reason': replay['reason'], 'candidate_score': score})

    require(set(pair_games) == set(range(pairs_planned)), 'Missing pair')
    require(all(set(v) == {'white', 'black'} for v in pair_games.values()), 'Unpaired game')
    pair_scores = [statistics.mean(pair_games[p].values()) for p in range(pairs_planned)]
    mean_score = statistics.mean(pair_scores)
    rng = random.Random(20261025)
    boot = sorted(statistics.mean(rng.choices(pair_scores, k=pairs_planned)) for _ in range(20000))
    quantiles = statistics.quantiles(boot, n=40, method='inclusive')
    result = {
        'classification': 'completed local head-to-head screen; not an arena Elo estimate',
        'audited_at': datetime.now(timezone.utc).isoformat(),
        'manifest': str(args.manifest), 'manifest_sha256': hashlib.sha256(raw).hexdigest(),
        'auditor_sha256': sha(Path(__file__)),
        'identities': {name: {'path': str(p), 'sha256': digest} for name, (p, digest) in identities.items()},
        'pairs': pairs_planned, 'games': len(rows),
        'candidate_record': {key: results[key] for key in ('wins', 'draws', 'losses')},
        'candidate_points': sum(r['candidate_score'] for r in rows), 'candidate_score_rate': mean_score,
        'by_color': {side: {key: counts[key] for key in ('wins', 'draws', 'losses')}
                     for side, counts in colors.items()},
        'pair_scores': pair_scores,
        'pair_bootstrap': {'resamples': 20000, 'seed': 20261025,
                           'percentile_95_interval': [quantiles[0], quantiles[-1]],
                           'limits': 'Approximate interval from whole pairs; assumes independent representative pairs. No cross-opponent generalization.'},
        'reasons': dict(Counter(r['reason'] for r in rows)),
        'frames_verified': sum(r['frames_verified'] for r in rows),
        'non_board_terminal_games': [r['replay'] for r in rows if not r['board_terminal_verified']],
        'summed_match_wall_seconds': sum(r['elapsed_seconds'] for r in manifest['games']),
        'median_plies': statistics.median(r['plies'] for r in manifest['games']),
        'replays': rows,
        'limitations': ['Validation replays the recorded games with the same referee; it is not a second rules implementation.',
                        'Clock fields are checked for finiteness only; no reconstruction of process scheduling.',
                        'Only this fixed run is summarized. Earlier exploratory screens are not pooled.',
                        'Actual runtime binaries are verified now; the manifest does not prove past resource isolation.'],
    }
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('pairs', 'games', 'candidate_record', 'candidate_score_rate',
                                           'pair_bootstrap', 'frames_verified', 'non_board_terminal_games')}))


if __name__ == '__main__':
    main()
