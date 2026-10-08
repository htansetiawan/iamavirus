#!/usr/bin/env python3
"""Run three matched capacity pilots from frozen committed source and data.

Requires the existing coordinated Astra GPU lease; it never preempts a holder.
Only train/validation shards are copied. These pilots are not arena releases.
"""
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
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--lease-token', required=True)
    parser.add_argument('--steps', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=253)
    args = parser.parse_args()
    if args.steps < 1:
        parser.error('steps must be positive')
    lease = Path('/tmp/gpu_queue/claimed_by')
    owner = lease.read_text()
    if not owner.lower().startswith('astra') or args.lease_token not in owner:
        parser.error('matching Astra GPU lease required')
    output = args.output.resolve()
    if output.is_relative_to('/media/henrytan/seagate') and not os.path.ismount('/media/henrytan/seagate'):
        parser.error('Seagate is not mounted')
    output.mkdir(parents=True, exist_ok=False)
    state = {'state': 'preparing', 'pid': os.getpid(), 'started_at': datetime.now(timezone.utc).isoformat(),
             'seed': args.seed, 'steps': args.steps, 'arms': {}, 'test_shard_used': False}
    write(output / 'campaign.json', state)
    try:
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', revision], cwd=ROOT, text=True).splitlines()
        source = output / 'source'
        source.mkdir()
        sources = {}
        for name in names:
            p = Path(name)
            if not (name.startswith(('learning/', 'astra-submissions/learning_experiments/')) or
                    (len(p.parts) == 1 and p.suffix in ('.cc', '.h'))):
                continue
            target = source / p
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(subprocess.check_output(['git', 'show', revision + ':' + name], cwd=ROOT))
            sources[name] = sha(target)
        data = output / 'dataset'
        data.mkdir()
        original = args.manifest.resolve()
        original_hash = sha(original)
        manifest = json.loads(original.read_text())
        shutil.copyfile(original, data / 'original-manifest.json')
        shards = {}
        for split in ('train', 'validation'):
            p = Path(manifest['shards'][split])
            p = p if p.is_absolute() else ROOT / p
            before = sha(p)
            target = data / (split + '.jsonl.gz')
            shutil.copyfile(p, target)
            if sha(target) != before or sha(p) != before:
                raise RuntimeError('dataset changed during snapshot')
            shards[split] = before
            manifest['shards'][split] = str(target)
        if sha(original) != original_hash:
            raise RuntimeError('manifest changed during snapshot')
        # Keep test inaccessible to this selection campaign, including by an
        # accidental relative-path lookup from the frozen source tree.
        manifest['shards']['test'] = str(data / 'TEST_NOT_COPIED')
        write(data / 'manifest.json', manifest)
        state.update(revision=revision, sources_sha256=sources,
                     original_manifest_sha256=original_hash, shard_sha256=shards)
        env = {k: v for k, v in os.environ.items() if not k.startswith(('FOW_', 'ASTRA_'))}
        env.update(PYTHONPATH=str(source / 'astra-submissions') + ':' + str(source),
                   OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
        python = str(ROOT / '.venv/bin/python')
        arms = [('cnn', ['--variant', 'cnn']),
                ('attention-small', ['--variant', 'attention']),
                ('attention-large', ['--variant', 'attention', '--attention-channels', '256',
                                     '--attention-blocks', '6', '--attention-heads', '8'])]
        for name, flags in arms:
            if not lease.exists() or lease.read_text() != owner:
                raise RuntimeError('GPU lease changed before next arm')
            command = [python, '-m', 'learning_experiments.run', '--manifest', str(data / 'manifest.json'),
                       '--output', str(output / name), '--phase', 'supervised', '--device', 'cuda',
                       '--steps', str(args.steps), '--evaluate-every', str(args.steps), '--threads', '1',
                       '--seed', str(args.seed), '--batch', '4', '--window', '32',
                       '--train-games', '512', '--validation-games', '64', *flags]
            state.update(state='running', current_arm=name)
            state['arms'][name] = {'command': command, 'state': 'running'}
            write(output / 'campaign.json', state)
            started = time.monotonic()
            with (output / (name + '.log')).open('w') as log:
                process = subprocess.run(command, cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT)
            state['arms'][name].update(returncode=process.returncode,
                                      elapsed_seconds=time.monotonic()-started,
                                      state='complete' if process.returncode == 0 else 'failed')
            write(output / 'campaign.json', state)
            if process.returncode:
                raise RuntimeError('capacity arm failed: ' + name)
            print(json.dumps({'arm': name, **state['arms'][name]}), flush=True)
        for control, candidate in [('cnn', 'attention-small'), ('attention-small', 'attention-large')]:
            command = [python, '-m', 'learning_experiments.compare_pilots',
                       '--control', str(output / control), '--candidate', str(output / candidate),
                       '--step', str(args.steps), '--output', str(output / (control + '-vs-' + candidate + '.json'))]
            with (output / (control + '-vs-' + candidate + '.log')).open('w') as log:
                subprocess.run(command, cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        state.update(state='complete', completed_at=datetime.now(timezone.utc).isoformat(),
                     limitations=['One seed, matched decisions; equal-compute control still required.',
                                  'Validation allocation experiment, not playing-strength evidence.',
                                  'No teacher distillation or precision conversion performed here.'])
    except BaseException as error:
        state.update(state='failed', error=repr(error))
        raise
    finally:
        write(output / 'campaign.json', state)
        if lease.exists() and lease.read_text() == owner:
            lease.unlink()
        print(json.dumps({k: state[k] for k in ('state', 'seed', 'steps', 'test_shard_used')}), flush=True)


if __name__ == '__main__':
    main()
