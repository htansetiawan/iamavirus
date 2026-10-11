#!/usr/bin/env python3
"""Diagnose recurrent-state dependence using a checkpoint's frozen source.

The ablation resets GRU state before every observation. Explicit last-seen
feature planes remain intact: this is not an all-history removal experiment.
No labels enter the model; replay targets only score its emitted predictions.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--step', type=int, default=1000)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--threads', type=int, default=2)
    args = p.parse_args()
    source = args.source_root.resolve()
    sys.path[:0] = [str(source / 'astra-submissions'), str(source)]
    import torch
    from learning import dataset as ds
    from learning import features
    from learning_experiments.models import ModelConfig, make_model
    from learning_experiments.run import isolate_rules, select_games, write_json
    from learning_experiments.evaluate import evaluate

    if args.output.exists():
        raise ValueError('output exists; retain the previous diagnostic')
    run = json.loads((args.run / 'run.json').read_text())
    for name, expected in run['source_sha256'].items():
        if digest(source / name) != expected:
            raise ValueError('source mismatch: ' + name)
    torch.set_num_threads(args.threads)
    native = isolate_rules(args.run)
    if native['sources'] != run['native']['sources']:
        raise ValueError('native rules mismatch')
    manifest = json.loads((args.run / 'dataset-manifest.json').read_text())
    shard = Path(manifest['shards']['validation'])
    if not shard.is_absolute():
        shard = source / shard
    if digest(shard) != run['identity']['shard_sha256']['validation']:
        raise ValueError('validation shard mismatch')
    checkpoint_path = args.run / f'step-{args.step:06d}.pt'
    checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
    if checkpoint['identity'] != run['identity'] or checkpoint['source_sha256'] != run['source_sha256']:
        raise ValueError('checkpoint and run metadata mismatch')
    model = make_model(ModelConfig(**run['identity']['model_config']))
    model.load_state_dict(checkpoint['state_dict'])
    feature_version = checkpoint.get('feature_version', features.FEATURE_VERSION)
    episodes = select_games(ds.load_episodes(shard), run['identity']['validation_games'])

    class ResetMemory(torch.nn.Module):
        def __init__(self, base):
            super().__init__()
            self.base = base
        def initial_hidden(self, batch, device):
            return self.base.initial_hidden(batch, device)
        def observe(self, planes, scalars, hidden):
            zero = self.base.initial_hidden(planes.shape[0], planes.device)
            return self.base.observe(planes, scalars, zero)
        def score(self, *inputs):
            return self.base.score(*inputs)

    start = time.monotonic()
    # CPU full-history pass is the precision/device control for CPU reset.
    full = evaluate(model, episodes, torch.device('cpu'))
    reset = evaluate(ResetMemory(model), episodes, torch.device('cpu'))
    if full['unique_decisions'] != reset['unique_decisions'] or full['by_game'].keys() != reset['by_game'].keys():
        raise ValueError('ablation decisions differ')
    for game in full['by_game']:
        if full['by_game'][game]['counts'] != reset['by_game'][game]['counts']:
            raise ValueError('ablation target counts differ')
    result = {'run': str(args.run), 'step': args.step, 'checkpoint_sha256': digest(checkpoint_path),
              'script_sha256': digest(__file__), 'source_sha256': run['source_sha256'],
              'feature_version': feature_version,
              'feature_version_provenance': 'checkpoint metadata' if 'feature_version' in checkpoint else 'hash-verified frozen feature module',
              'validation_sha256': digest(shard), 'device': 'cpu', 'threads': args.threads,
              'pid': os.getpid(), 'elapsed_seconds': time.monotonic() - start,
              'full': full, 'reset': reset,
              'limitations': ['Resetting recurrence is an inference intervention, not a retrained memoryless control.',
                              'Explicit history features and public history-dependent scalars remain unchanged.',
                              'This diagnoses recurrent-state dependence, not playing strength or causal strategic understanding.',
                              'Held-out game labels score predictions only; the test shard is never loaded.']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, result)
    metrics = ['policy_nll', 'hidden_enemy_nll', 'danger_brier']
    print(json.dumps({'output': str(args.output), 'elapsed_seconds': result['elapsed_seconds'],
                      'metrics': {m: [r['groups']['all']['metrics'][m] for r in (full, reset)] for m in metrics}}, indent=2))


if __name__ == '__main__':
    main()
