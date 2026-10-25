"""Prepare, but never launch, a concrete matched PPO auxiliary experiment.

Pins compatible CNN checkpoints, verifies dataset content, freezes recent
evaluation games, and builds an isolated copy of the reviewed trainer patch.
No GPU use, optimization, arena modification or shared-source edits.
"""
import argparse
from collections import Counter
import copy
from datetime import datetime, timezone
import gc
import gzip
import hashlib
import heapq
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
import torch
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''): h.update(block)
    return h.hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def dataset_identity(manifest, accepted_rows):
    """Reassemble the dataset builder's original interleaved SHA-256 stream."""
    ranks = {}
    for i, row in enumerate(accepted_rows): ranks.setdefault(row['id'], i)
    heap = []; streams = {}; hashes = {}; previous = {}; counts = Counter()
    content = hashlib.sha256(); games = {}; pending = {}

    def advance(name):
        line = streams[name].readline()
        if not line: return
        record = json.loads(line)
        game, side = record['metadata']['game_id'], record['actor']['side']
        key = (ranks[game], side)
        if name in previous and key <= previous[name]:
            raise ValueError('Shard ordering differs from accepted source order: ' + name)
        previous[name] = key
        heapq.heappush(heap, (key, name, line, record))

    try:
        for name, filename in manifest['shards'].items():
            path = ROOT / filename
            hashes[name] = sha(path)
            streams[name] = gzip.open(path, 'rb')
            advance(name)
        while heap:
            _, name, line, record = heapq.heappop(heap)
            content.update(line.rstrip(b'\n'))
            counts[name] += 1
            game = record['metadata']['game_id']; actor = record['actor']; side = actor['side']
            assert len(actor['decision_event_indices']) == len(actor['own_actions'])
            moves = {actor['plies'][e]: m for e, m in zip(actor['decision_event_indices'], actor['own_actions'])}
            assert len(moves) == len(actor['own_actions']) and all(p % 2 == side for p in moves)
            if side == 0:
                assert game not in pending and game not in games
                pending[game] = moves
            else:
                merged = {**pending.pop(game), **moves}
                assert set(merged) == set(range(len(merged)))
                games[game] = hashlib.sha256(' '.join(merged[i] for i in range(len(merged))).encode()).hexdigest()
            advance(name)
    finally:
        for stream in streams.values(): stream.close()
    assert not pending
    assert content.hexdigest() == manifest['content_sha256'], 'Dataset contents differ from checkpoint provenance'
    assert all(counts[n] == manifest['counts'][n]['episodes'] for n in streams)
    return games, {'content_sha256': content.hexdigest(), 'shard_sha256': hashes,
                   'episodes_by_split': dict(counts), 'unique_games': len(games)}


def validate_replay(path, referee_dir):
    sys.path.insert(0, str(referee_dir))
    from referee import FowBoard, observation, outcome, position_key
    replay = json.loads(path.read_bytes()); board = FowBoard()
    repetitions = Counter({position_key(board): 1})
    for ply, frame in enumerate(replay['frames']):
        assert frame['ply'] == ply
        if ply:
            assert outcome(board, repetitions) is None, 'replay continues after termination'
            board.push(board.parse_uci(frame['move']))
            repetitions[position_key(board)] += 1
        actual = ''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64))
        assert actual == frame['board']
        assert observation(board, True) == frame['white'] and observation(board, False) == frame['black']
    assert outcome(board, repetitions) == (replay['result'], replay['reason'])
    return replay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE / 'risk-run-preflight')
    parser.add_argument('--checkpoint-root', type=Path, default=Path('/media/henrytan/seagate1/iamavirus/checkpoints'))
    parser.add_argument('--referee-dir', type=Path, default=Path('/home/henrytan/git/fow-starter'))
    args = parser.parse_args(); args.output.mkdir(exist_ok=True)
    started = time.monotonic(); torch.set_num_threads(2)
    from learning.model import parameter_count
    from learning.pretrain import load_model
    from learning.critic import Critic
    from learning import _native
    config = yaml.safe_load((ROOT / 'learning/configs/rl_l.yaml').read_text())['rl']
    config = copy.deepcopy(config)

    def mounted(path):
        path = Path(path)
        assert path.parts[0] == 'checkpoints'
        return str(args.checkpoint_root / Path(*path.parts[1:]))

    config['init'] = mounted(config['init'])
    config['critic_init'] = mounted(config['critic_init'])
    config['league']['replicas'] = {name: mounted(path) for name, path in config['league']['replicas'].items()}
    assert not config['league']['snapshots']
    config.update(iterations=60, seed=20261025)
    actor_paths = {'initial_actor_and_reference': config['init'], **config['league']['replicas']}
    actor_receipts = {}; loaded = {}; initial_dataset_hash = None
    for name, filename in actor_paths.items():
        path = Path(filename)
        if filename not in loaded:
            model, payload = load_model(path, 'cpu'); model.eval()
            assert payload.get('feature_version') == 'features-v2'
            assert payload.get('action_version') == 'actions-v1'
            with torch.no_grad():
                h, spatial, _, _ = model.observe(torch.zeros(1, 32, 8, 8), torch.zeros(1, 8), model.initial_hidden(1))
                choices = [torch.tensor([[8, 9]]), torch.tensor([[16, 17]]), torch.zeros(1, 2, dtype=torch.long)]
                policy, danger = model.score(h, spatial, *choices)
                assert policy.shape == danger.shape == (1, 2)
                assert torch.isfinite(policy).all() and torch.isfinite(danger).all()
            loaded[filename] = {'path': filename, 'sha256': sha(path), 'architecture': model.architecture,
                                'model_config': model.size_config, 'parameters': parameter_count(model),
                                'checkpoint_step': payload.get('step'), 'cpu_forward_pass': 'finite, expected shapes'}
            if name == 'initial_actor_and_reference': initial_dataset_hash = payload['dataset_manifest_sha256']
            del model, payload; gc.collect()
        actor_receipts[name] = loaded[filename]
    critic = Critic()
    payload = torch.load(config['critic_init'], map_location='cpu', weights_only=False)
    critic.load_state_dict(payload['state_dict'])
    with torch.no_grad(): assert torch.isfinite(critic(torch.zeros(1, 13, 8, 8))).all()
    critic_receipt = {'path': config['critic_init'], 'sha256': sha(config['critic_init']),
                      'parameters': parameter_count(critic), 'cpu_forward_pass': 'finite'}
    del critic, payload; gc.collect()

    rows = [json.loads(line) for line in (ROOT / 'data/raw/accepted.jsonl').read_text().splitlines() if line]
    manifest_path = ROOT / 'data/manifests/v6.json'; manifest = json.loads(manifest_path.read_bytes())
    # In this checkpoint schema the misleading field name stores content_sha256,
    # not the SHA of the manifest JSON file. Verify actual shard content below.
    assert initial_dataset_hash == manifest['content_sha256']
    prior_games, dataset = dataset_identity(manifest, rows)
    signatures = set(prior_games.values()); seen = set(); pool = []
    team = 'a2c35173659545c99752376a70418438'
    for row in rows:
        if not row.get('createdAt') or row['createdAt'] < '2026-10-24T00:00:00': continue
        if row.get('termination') != 'normal': continue
        side = 'white' if row.get('whitePlayerId') == team else 'black' if row.get('blackPlayerId') == team else None
        if side is None or row.get(side + 'Version') != 35: continue
        if row['id'] in prior_games or row['moves_sha256'] in signatures or row['moves_sha256'] in seen: continue
        seen.add(row['moves_sha256']); pool.append((row, side))
    pool.sort(key=lambda pair: hashlib.sha256(('astra-risk-holdout-20261025:' + pair[0]['id']).encode()).hexdigest())
    selected = []
    for row, side in pool[:128]:
        path = ROOT / 'data/raw/games' / row['id'] / 'replay.json'
        replay = validate_replay(path, args.referee_dir)
        move_hash = hashlib.sha256(' '.join(f['move'] for f in replay['frames'] if f.get('move')).encode()).hexdigest()
        assert move_hash == row['moves_sha256'] and replay['id'] == row['id']
        selected.append({'game': row['id'], 'side': side, 'replay': str(path.relative_to(ROOT)),
                         'replay_sha256': sha(path), 'moves_sha256': move_hash,
                         'created_at': row['createdAt'], 'opponent': replay['black' if side == 'white' else 'white'],
                         'decision_frames': list(range(0 if side == 'white' else 1, len(replay['frames']) - 1, 2))})
    assert len(selected) == 128
    holdout = {'classification': 'frozen later-time validation; not used for fitting',
               'selection': 'hash order, unique full move sequences, normal arena-v35 games from 2026-10-24 onward',
               'eligible_pool': len(pool), 'games': selected, 'dataset_disjoint_from': dataset,
               'referee_sha256': sha(args.referee_dir / 'referee.py'),
               'limits': ['Disjointness established for the initial actor v6 data, not every historical experiment.',
                          'Shared openings/transpositions remain; cluster metrics by game.',
                          'This is validation, not a final untouched promotion test.']}
    write(args.output / 'validation-games.json', holdout)

    patch_folder = ROOT / 'astra-submissions/learning_experiments'
    patch_manifest = json.loads((patch_folder / 'rl-risk-integration-manifest.json').read_bytes())
    assert sha(ROOT / 'learning/rl_train.py') == patch_manifest['source_sha256']
    assert sha(patch_folder / 'rl_risk_auxiliary.patch') == patch_manifest['patch_sha256']
    isolated = ROOT / 'astra-submissions/build/ppo-risk-review-20261025'
    if isolated.exists(): raise RuntimeError('Prepared source already exists; inspect it before replacing')
    (isolated / 'learning').mkdir(parents=True)
    for path in (ROOT / 'learning').glob('*.py'): shutil.copy2(path, isolated / 'learning' / path.name)
    for name in _native.SOURCES + _native.HEADERS: shutil.copy2(ROOT / name, isolated / name)
    (isolated / 'learning_experiments').mkdir()
    for name in ['__init__.py', 'risk_auxiliary.py']: shutil.copy2(patch_folder / name, isolated / 'learning_experiments' / name)
    subprocess.run(['patch', '--quiet', '--batch', '--fuzz=0', '-p1', '-i', str(patch_folder / 'rl_risk_auxiliary.patch')], cwd=isolated, check=True)
    assert sha(isolated / 'learning/rl_train.py') == patch_manifest['patched_sha256']
    source_hashes = {str(p.relative_to(isolated)): sha(p) for p in isolated.rglob('*') if p.is_file()}
    for arm, coefficient in [('control', 0.), ('auxiliary', .1)]:
        arm_config = copy.deepcopy(config)
        arm_config.update(risk_aux_coef=coefficient, risk_separation_coef=.25 if coefficient else 0.)
        (args.output / (arm + '.yaml')).write_text(yaml.safe_dump({'rl': arm_config}, sort_keys=False))
    receipt = {'classification': 'prepared, not launched; no GPU use or optimizer updates',
               'prepared_at': datetime.now(timezone.utc).isoformat(), 'preparer_sha256': sha(Path(__file__)),
               'source_root': str(isolated), 'source_sha256': source_hashes,
               'actor_checkpoints': actor_receipts, 'critic_checkpoint': critic_receipt,
               'dataset': dataset, 'dataset_manifest_file_sha256': sha(manifest_path),
               'validation_sha256': sha(args.output / 'validation-games.json'),
               'configuration_sha256': {n: sha(args.output / (n + '.yaml')) for n in ['control', 'auxiliary']},
               'limits': {'iterations_per_arm': 60, 'wall_seconds_per_arm': 3600, 'gpu_seconds_total': 7200},
               'initialization': 'Both arms start from identical supervised actor and critic; fresh optimizers; no actor-only resume.',
               'comparison': 'Use the largest common completed snapshot (multiples of 10); discard incomplete rollout updates.',
               'wall_seconds': time.monotonic() - started}
    write(args.output / 'preflight.json', receipt)
    print(json.dumps({'prepared_source': str(isolated), 'checkpoints': len(loaded),
                      'validation_games': len(selected), 'validation_decisions': sum(len(g['decision_frames']) for g in selected),
                      'dataset_games_verified': dataset['unique_games'], 'seconds': receipt['wall_seconds']}))


if __name__ == '__main__': main()
