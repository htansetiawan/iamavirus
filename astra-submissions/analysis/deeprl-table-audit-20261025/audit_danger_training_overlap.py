"""Establish diagnostic-panel overlap with the frozen attention model's data.

Uses the model's recorded run identity and hashes the actual shards. Exact whole
move sequences are reconstructed from both player episodes, including a terminal
move when stored as the final own action. Does not infer a clean statistical
holdout merely from a distinct game ID or a later date.
"""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def signature(moves):
    return hashlib.sha256(' '.join(moves).encode()).hexdigest()


def read_shard(path):
    games = defaultdict(dict)
    with gzip.open(path, 'rt') as stream:
        for line in stream:
            record = json.loads(line)
            actor = record['actor']
            game = record['metadata']['game_id']
            side = actor['side']
            if side in games[game]:
                raise ValueError('duplicate side for ' + game)
            if len(actor['decision_event_indices']) != len(actor['own_actions']):
                raise ValueError('incomplete action/event alignment for ' + game)
            own_moves = {
                actor['plies'][event]: move
                for event, move in zip(actor['decision_event_indices'], actor['own_actions'])
            }
            if len(own_moves) != len(actor['own_actions']) or any(ply % 2 != side for ply in own_moves):
                raise ValueError('duplicate decision or wrong acting side for ' + game)
            games[game][side] = own_moves
    hashes = {}
    for game, sides in games.items():
        if set(sides) != {0, 1}:
            raise ValueError('both player episodes required for ' + game)
        merged = {**sides[0], **sides[1]}
        if set(merged) != set(range(len(merged))):
            raise ValueError('nonconsecutive decision history for ' + game)
        hashes[game] = signature([merged[i] for i in range(len(merged))])
    return hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=Path('/media/henrytan/seagate1/iamavirus/astra/representations/capacity-v4-full3766-20261008/attention-small/run.json'))
    parser.add_argument('--manifest', type=Path, help='Defaults to the model run\'s frozen dataset-manifest.json')
    args = parser.parse_args()
    start = time.monotonic()
    run = json.loads(args.run.read_bytes())
    identity = run['identity']
    args.manifest = args.manifest or args.run.parent / 'dataset-manifest.json'
    assert sha(args.manifest) == identity['manifest_sha256']
    manifest = json.loads(args.manifest.read_bytes())
    partitions = {}
    provenance = {}
    for name in ('train', 'validation'):
        recorded_path = manifest['shards'][name]
        # The same drive is now mounted as seagate1. Content hashes, not this
        # path substitution, establish identity with the recorded training data.
        path = ROOT / recorded_path.replace('/media/henrytan/seagate/', '/media/henrytan/seagate1/')
        assert sha(path) == identity['shard_sha256'][name]
        all_games = read_shard(path)
        ordered = sorted(all_games, key=lambda game: hashlib.sha256(game.encode()).hexdigest())
        limit = identity[name + '_games']
        selected = ordered[:limit] if limit else ordered
        partitions[name] = {game: all_games[game] for game in selected}
        provenance[name] = {'recorded_path': recorded_path, 'resolved_path': str(path), 'sha256': sha(path),
                            'all_games': len(all_games), 'selected_games': len(selected)}
    analysis_path = HERE / 'existing-danger-80-analysis.json'
    predictions_path = HERE / 'existing-danger-80-result.json'
    analysis = json.loads(analysis_path.read_bytes())
    predictions = json.loads(predictions_path.read_bytes())
    assessed = {(row['game'], row['frame']): row for row in analysis['cases']}
    rows = []
    groups = defaultdict(list)
    for item in predictions['cases']:
        case = item['case']
        path = ROOT / case['replay']
        assert sha(path) == case['replay_sha256']
        replay = json.loads(path.read_bytes())
        move_hash = signature([f['move'] for f in replay['frames'] if f.get('move')])
        overlap = {}
        for name, games in partitions.items():
            overlap[name] = {'id_match': case['game'] in games,
                             'same_complete_moves': [g for g, h in games.items() if h == move_hash]}
        category = ('training_overlap' if overlap['train']['id_match'] or overlap['train']['same_complete_moves']
                    else 'validation_overlap' if overlap['validation']['id_match'] or overlap['validation']['same_complete_moves']
                    else 'no_recorded_training_or_validation_overlap')
        row = {'game': case['game'], 'frame': case['frame'], 'slice': case['slice'],
               'created_at': replay.get('createdAt'), 'complete_move_sha256': move_hash,
               'overlap': overlap, 'category': category}
        rows.append(row)
        groups[category].append(assessed[(case['game'], case['frame'])])
    summaries = {}
    for category, cases in groups.items():
        summaries[category] = {'cases': len(cases)}
        for selector in ['v35_base', 'min_risk_all_native', 'min_risk_current_root']:
            summaries[category][selector + '_fatal'] = sum(c['selected'][selector]['true_king_fatal'] for c in cases)
    print(json.dumps({'classification': 'post-hoc recorded-data overlap audit; no fitting or model selection',
                      'run_sha256': sha(args.run), 'manifest_sha256': sha(args.manifest),
                      'analyzed_prediction_sha256': sha(predictions_path),
                      'analysis_sha256': sha(analysis_path), 'auditor_sha256': sha(Path(__file__)),
                      'partition_provenance': provenance, 'summary': summaries,
                      'wall_seconds': time.monotonic() - start, 'cases': rows,
                      'limits': ['No-overlap is limited to the recorded training and selected validation histories.',
                                 'Does not prove absence from other experiments, pretraining, or human analysis.',
                                 'Shared shorter prefixes, transpositions, and related positions remain possible.',
                                 'The 80-position panel remains balanced and selected, not a population-calibration set.']}, indent=2))


if __name__ == '__main__':
    main()
