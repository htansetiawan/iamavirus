#!/usr/bin/env python3
"""Audit the completed EP gate without running any bots or new games."""
import collections
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys

import numpy as np

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    path = HERE / 'v35-ep-history-paired-20pairs-seed20261080.json'
    m = json.loads(path.read_text())
    assert m['state'] == 'complete' and m['completed_games'] == 40
    assert m['pairs_planned'] == 20 and len(m['games']) == 40
    identities = {k: sha(p) for k, p in [
        ('candidate_binary_sha256', Path(m['candidate']) / 'mist'),
        ('baseline_binary_sha256', Path(m['baseline']) / 'mist'),
        ('referee_sha256', m['referee'])]}
    assert identities == m['hashes']
    sys.path.insert(0, str(Path(m['referee']).parent))
    spec = importlib.util.spec_from_file_location('gate_referee', m['referee'])
    referee = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(referee)
    seen = set()
    by_color = collections.defaultdict(collections.Counter)
    pairs = collections.defaultdict(list)
    reasons = collections.Counter()
    frames = 0
    ep = []
    for row in m['games']:
        p = HERE / Path(row['replay']).name
        assert sha(p) == row['replay_sha256']
        key = row['pair'], row['candidate_color']
        assert key not in seen
        seen.add(key)
        assert row['candidate_seed'] == m['seed'] + 2 * row['pair']
        assert row['baseline_seed'] == row['candidate_seed'] + 1
        g = json.loads(p.read_text())
        assert g['result'] == row['result'] and g['reason'] == row['reason']
        board = referee.FowBoard()
        repetitions = collections.Counter({referee.position_key(board): 1})
        ended = None
        for i, frame in enumerate(g['frames']):
            if i:
                assert ended is None
                board.push(board.parse_uci(frame['move']))
                repetitions[referee.position_key(board)] += 1
            expected = referee.make_frame(board, frame['clocks'], frame['move'])
            for field in ('ply', 'board', 'white', 'black'):
                assert expected[field] == frame[field], (p.name, i, field)
            ended = referee.outcome(board, repetitions)
            candidate_turn = board.turn == (row['candidate_color'] == 'white')
            if candidate_turn and ended is None and i + 1 < len(g['frames']):
                options = [move.uci() for move in board.generate_pseudo_legal_moves()
                           if board.is_en_passant(move)]
                if options:
                    played = g['frames'][i + 1]['move']
                    ep.append({'replay': p.name, 'ply': i, 'options': options,
                               'played': played, 'selected_ep': played in options})
            frames += 1
        assert ended == (g['result'], g['reason']), (p.name, ended)
        score = .5 if g['result'] == '1/2-1/2' else float((g['result'] == '1-0') == (row['candidate_color'] == 'white'))
        assert score == row['candidate_score']
        by_color[row['candidate_color']]['wins' if score == 1 else 'draws' if score == .5 else 'losses'] += 1
        pairs[row['pair']].append(score)
        reasons[row['reason']] += 1
    assert seen == {(i, side) for i in range(20) for side in ('white', 'black')}
    ps = [sum(pairs[i]) / 2 for i in range(20)]
    rng = np.random.default_rng(20261026)
    draws = np.asarray(ps)[rng.integers(0, 20, (20000, 20))].mean(axis=1)
    report = {'classification': 'closed local paired screen; not an Elo estimate',
              'audited_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'manifest_sha256': sha(path), 'auditor_sha256': sha(__file__),
              'identities': identities, 'games': 40, 'frames_verified': frames,
              'by_color': dict(by_color), 'candidate_score': sum(ps) / 20,
              'pair_scores': ps, 'pair_bootstrap_95': np.quantile(draws, [.025, .975]).tolist(),
              'reasons': dict(reasons), 'ep_candidate_opportunities': ep,
              'ep_candidate_selections': sum(x['selected_ep'] for x in ep),
              'exposure_limit': 'All true legal EP opportunities, not proof that baseline view_moves omitted each one or that the candidate would choose differently.',
              'elapsed_game_seconds': sum(x['elapsed_seconds'] for x in m['games']),
              'median_plies': statistics.median(x['plies'] for x in m['games']),
              'completed_at': m['completed_at']}
    out = HERE / 'completed-gate-audit.json'
    out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('games', 'frames_verified', 'by_color', 'candidate_score', 'pair_bootstrap_95', 'ep_candidate_selections')}, indent=2))


if __name__ == '__main__':
    main()
