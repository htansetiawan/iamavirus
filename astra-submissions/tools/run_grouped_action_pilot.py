#!/usr/bin/env python3
"""Freeze a model and compare requested belief/root configurations in the hybrid."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', type=Path, required=True)
    p.add_argument('--corpus', type=Path, required=True)
    p.add_argument('--model-archive', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--stride', type=int, default=1000)
    p.add_argument('--nodes', type=int, default=400000)
    p.add_argument('--particles', type=int, default=2048)
    p.add_argument('--priors', type=int, choices=(1, 2), nargs='+', default=[1, 2])
    p.add_argument('--prediction-modes', type=int, choices=(0, 1), nargs='+', default=[0, 1])
    p.add_argument('--root-modes', type=int, choices=(0, 1, 2), nargs='+', default=[0])
    p.add_argument('--frontier-capacities', type=int, nargs='+', default=[0])
    p.add_argument('--arm-prefix', default='')
    args = p.parse_args()
    if min(args.stride, args.nodes, args.particles) <= 0:
        p.error('stride, nodes and particles must be positive')
    if any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in args.arm_prefix):
        p.error('arm prefix must contain lowercase ASCII letters, digits, hyphens or underscores')
    if any(len(set(values)) != len(values) for values in
           (args.priors, args.prediction_modes, args.root_modes, args.frontier_capacities)):
        p.error('duplicate configurations')
    if any(not 0 <= cap <= 32768 for cap in args.frontier_capacities):
        p.error('frontier capacities must be 0..32768')
    if any(args.frontier_capacities) and b'FOW_FRONTIER_CAPACITY' not in args.binary.read_bytes():
        p.error('binary does not expose the frontier-capacity option')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    binary = out / 'benchmark'
    binary.write_bytes(args.binary.read_bytes()); binary.chmod(0o755)
    corpus = out / 'seats.txt'; corpus.write_bytes(args.corpus.read_bytes())
    model = out / 'model'; model.mkdir()
    with zipfile.ZipFile(args.model_archive) as z:
        for name in ('model_manifest.json', 'observe.onnx', 'score.onnx'):
            (model / name).write_bytes(z.read('model/' + name))
    inputs = {str(x): sha(x) for x in (binary, corpus, *sorted(model.iterdir()))}
    state = {'state': 'running', 'pid': os.getpid(), 'started_at': datetime.now(timezone.utc).isoformat(),
             'inputs': inputs, 'model_archive': str(args.model_archive.resolve()),
             'model_archive_sha256': sha(args.model_archive), 'runner_sha256': sha(Path(__file__)),
             'nodes': args.nodes, 'stride': args.stride, 'particles': args.particles, 'arms': {},
             'design': 'Requested root/prediction/opponent prior/frontier arms; history0, book0, seed777, one search thread, same hybrid model.',
             'limitations': ['Forced-history decisions, not games or Elo.',
                             'Stride1000 samples initial moves as well as terminal losing moves; report separately.']}
    def save():
        tmp = out / 'campaign.tmp'; tmp.write_text(json.dumps(state, indent=2) + '\n')
        tmp.replace(out / 'campaign.json')
    save()
    for prediction, prior, root_mode, capacity in ((m, p, r, c) for p in args.priors
            for m in args.prediction_modes for r in args.root_modes for c in args.frontier_capacities):
        root_label = '' if args.root_modes == [0] else f'root{root_mode}-'
        frontier_label = '' if args.frontier_capacities == [0] else f'frontier{capacity}-'
        name = args.arm_prefix + frontier_label + root_label + f'prediction{prediction}-prior{prior}'
        settings = dict(FOW_MODE='hybrid', FOW_MODEL_DIR=str(model), FOW_HISTORY_MODE='0',
                        FOW_PREDICTION_MODE=str(prediction), FOW_OPPONENT_PRIOR=str(prior),
                        FOW_ROOT_MODE=str(root_mode),
                        FOW_FRONTIER_CAPACITY=str(capacity),
                        FOW_PARTICLES=str(args.particles), FOW_CELL_THREADS='1', FOW_BOOK_PLIES='0')
        env = {k: v for k, v in os.environ.items() if not k.startswith(('FOW_', 'ASTRA_'))}
        env.update(settings)
        command = [str(binary), str(corpus), str(args.stride), str(args.nodes), 'verbose']
        arm = state['arms'][name] = {'state': 'running', 'command': command, 'settings': settings}
        save(); start = time.monotonic()
        try:
            with (out / (name + '.log')).open('w') as log:
                process = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=7200)
        except (OSError, subprocess.TimeoutExpired) as error:
            arm.update(state='failed', error=str(error), elapsed_seconds=time.monotonic()-start)
            state['state'] = 'failed'; save()
            raise
        rows = [json.loads(line.removeprefix('DECISION '))
                for line in (out / (name + '.log')).read_text().splitlines() if line.startswith('DECISION ')]
        terminal = [r for r in rows if r['terminal']]
        arm.update(state='complete' if process.returncode == 0 and rows else 'failed',
                   returncode=process.returncode, elapsed_seconds=time.monotonic()-start,
                   decisions=len(rows), king_losses=sum(r['king_loss'] for r in rows),
                   avoidable_losses=sum(r['king_loss'] and r['safe_alternatives'] > 0 for r in rows),
                   terminal_decisions=len(terminal), terminal_survived=sum(not r['king_loss'] for r in terminal),
                   log_sha256=sha(out / (name + '.log')))
        save(); print(json.dumps({name: arm}), flush=True)
        if arm['state'] != 'complete':
            state['state'] = 'failed'; save(); raise RuntimeError('benchmark failed')
    state['inputs_unchanged'] = all(sha(Path(path)) == digest for path, digest in inputs.items())
    state['state'] = 'complete' if state['inputs_unchanged'] else 'failed'
    state['completed_at'] = datetime.now(timezone.utc).isoformat(); save()


if __name__ == '__main__':
    main()
