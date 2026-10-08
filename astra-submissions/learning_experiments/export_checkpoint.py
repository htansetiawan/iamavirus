"""Export an experimental checkpoint with its true architecture and history parity."""
import argparse
import json
from pathlib import Path

import torch

from learning import dataset as ds
from learning.export import export_graphs, parity_check
from learning.features import FEATURE_VERSION
from learning_experiments.models import ModelConfig, make_model, model_metadata
from learning_experiments.run import file_hash, isolate_rules, select_games, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--shard', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--games', type=int, default=4)
    args = parser.parse_args()
    if args.games < 1:
        parser.error('games must be positive')
    if (args.output / 'model_manifest.json').exists():
        parser.error('export already exists; use a new output directory')
    torch.set_num_threads(2)
    payload = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
    if payload.get('feature_version') != FEATURE_VERSION:
        raise ValueError('checkpoint feature contract differs; use its frozen implementation or an explicit migration')
    config = ModelConfig(**payload['model_config'])
    model = make_model(config)
    model.load_state_dict(payload['state_dict'])
    native = isolate_rules(args.output)
    graphs = export_graphs(model, args.output)
    episodes = select_games(ds.load_episodes(args.shard), args.games)
    parity = parity_check(model, graphs, episodes, max_episodes=len(episodes))
    result = {**model_metadata(config), 'checkpoint_sha256': file_hash(args.checkpoint),
              'feature_version': FEATURE_VERSION, 'action_version': payload.get('action_version'),
              'rules_fingerprint': payload.get('rules_fingerprint'),
              'training_step': payload['step'], 'training_phase': payload['identity']['phase'],
              'dataset_manifest_sha256': payload['identity']['manifest_sha256'],
              'shard_sha256': file_hash(args.shard), 'native': native,
              'graphs': {name: {'sha256': file_hash(path), 'bytes': path.stat().st_size}
                         for name, path in graphs.items()}, 'parity': parity,
              'status': 'experimental export; not a packaged or strength-gated arena submission',
              'danger_calibration': 'uncalibrated; diagnostic only'}
    write_json(args.output / 'model_manifest.json', result)
    print(json.dumps({'architecture': config.architecture, 'parity': parity}))
    if parity['failure_count']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
