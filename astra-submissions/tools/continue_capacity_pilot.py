#!/usr/bin/env python3
"""Continue frozen capacity arms to a longer common budget, preserving originals."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--initial', type=Path, required=True)
    p.add_argument('--controls', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--steps', type=int, default=6000)
    p.add_argument('--evaluate-every', type=int, default=2000)
    p.add_argument('--lease-token', required=True)
    p.add_argument('--check-only', action='store_true')
    args = p.parse_args()
    if min(args.steps, args.evaluate_every) < 1:
        p.error('update budgets must be positive')
    initial, controls, out = args.initial.resolve(), args.controls.resolve(), args.output.resolve()
    parent = json.loads((initial / 'campaign.json').read_text())
    continuation = json.loads((controls / 'continuation.json').read_text())
    if parent['state'] != 'complete' or continuation['state'] != 'complete':
        p.error('parent runs must be complete')
    source = initial / 'source'
    for name, digest in parent['sources_sha256'].items():
        if sha(source / name) != digest:
            p.error('frozen source differs: ' + name)
    plans = []
    for name, directory in (('cnn', controls / 'cnn'), ('attention-small', controls / 'attention-small'),
                            ('attention-large', initial / 'attention-large')):
        run = json.loads((directory / 'run.json').read_text())
        status = json.loads((directory / 'status.json').read_text())
        if status['state'] != 'complete' or status['step'] >= args.steps:
            p.error('invalid continuation budget: ' + name)
        plans.append({'arm': name, 'parent': str(directory), 'first_step': status['step'],
                      'target_step': args.steps, 'parent_checkpoint_sha256': sha(directory / 'latest.pt'),
                      'identity': run['identity']})
    if args.check_only:
        print(json.dumps({'source_revision': parent['revision'], 'plans': plans, 'test_shard_used': False}))
        return
    lease = Path('/tmp/gpu_queue/claimed_by')
    owner = lease.read_text()
    if not owner.lower().startswith('astra') or args.lease_token not in owner:
        p.error('matching Astra GPU lease required')
    out.mkdir(parents=True, exist_ok=False)
    state = {'state': 'running', 'pid': os.getpid(), 'started_at': datetime.now(timezone.utc).isoformat(),
             'source_revision': parent['revision'], 'source': str(source), 'plans': plans,
             'runner_sha256': sha(Path(__file__)), 'test_shard_used': False, 'arms': {},
             'purpose': 'Longer matched learning curve; one seed, no deployment or Elo claim.'}
    def save():
        tmp = out / 'campaign.tmp'; tmp.write_text(json.dumps(state, indent=2) + '\n')
        tmp.replace(out / 'campaign.json')
    save()
    try:
        env = {k: v for k, v in os.environ.items() if not k.startswith(('FOW_', 'ASTRA_'))}
        env.update(PYTHONPATH=str(source / 'astra-submissions') + ':' + str(source),
                   OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
        for plan in plans:
            if not lease.exists() or lease.read_text() != owner:
                raise RuntimeError('GPU lease changed before next arm')
            name = plan['arm']; directory = out / name
            shutil.copytree(plan['parent'], directory)
            if sha(directory / 'latest.pt') != plan['parent_checkpoint_sha256']:
                raise RuntimeError('parent checkpoint changed while copying')
            identity = plan['identity']; config = identity['model_config']
            command = [str(ROOT / '.venv/bin/python'), '-m', 'learning_experiments.run',
                       '--manifest', str(initial / 'dataset/manifest.json'), '--output', str(directory),
                       '--phase', 'supervised', '--device', 'cuda', '--resume', '--threads', '1',
                       '--steps', str(args.steps), '--evaluate-every', str(args.evaluate_every),
                       '--variant', config['variant'], '--attention-channels', str(config['attention_channels']),
                       '--attention-blocks', str(config['attention_blocks']), '--attention-heads', str(config['attention_heads']),
                       '--seed', str(identity['seed']), '--batch', str(identity['batch']),
                       '--window', str(identity['window']), '--train-games', str(identity['train_games']),
                       '--validation-games', str(identity['validation_games'])]
            arm = state['arms'][name] = {'state': 'running', 'command': command}
            state['current_arm'] = name; save(); start = time.monotonic()
            with (out / (name + '.log')).open('w') as log:
                result = subprocess.run(command, cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT)
            arm.update(state='complete' if result.returncode == 0 else 'failed',
                       returncode=result.returncode, elapsed_seconds=time.monotonic()-start)
            save(); print(json.dumps({name: arm}), flush=True)
            if result.returncode:
                raise RuntimeError('capacity arm failed: ' + name)
        state.update(state='complete', completed_at=datetime.now(timezone.utc).isoformat())
    except BaseException as error:
        state.update(state='failed', error=repr(error))
        raise
    finally:
        save()
        if lease.exists() and lease.read_text() == owner:
            lease.unlink()
        print(json.dumps({'state': state['state'], 'output': str(out)}), flush=True)


if __name__ == '__main__':
    main()
