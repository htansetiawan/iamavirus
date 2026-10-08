#!/usr/bin/env python3
"""Freeze a model and compare grouped belief prediction in the actual hybrid."""
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
    args = p.parse_args()
    if min(args.stride, args.nodes) <= 0:
        p.error('stride and nodes must be positive')
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
             'nodes': args.nodes, 'stride': args.stride, 'arms': {},
             'design': '2x2 grouped prediction and opponent prior; history0, book0, seed777, one search thread, same hybrid model.',
             'limitations': ['Forced-history decisions, not games or Elo.',
                             'Stride1000 samples initial moves as well as terminal losing moves; report separately.']}
    def save():
        tmp = out / 'campaign.tmp'; tmp.write_text(json.dumps(state, indent=2) + '\n')
        tmp.replace(out / 'campaign.json')
    save()
    for prediction, prior in ((0, 1), (1, 1), (0, 2), (1, 2)):
        name = f'prediction{prediction}-prior{prior}'
        settings = dict(FOW_MODE='hybrid', FOW_MODEL_DIR=str(model), FOW_HISTORY_MODE='0',
                        FOW_PREDICTION_MODE=str(prediction), FOW_OPPONENT_PRIOR=str(prior),
                        FOW_PARTICLES='2048', FOW_CELL_THREADS='1', FOW_BOOK_PLIES='0')
        env = {k: v for k, v in os.environ.items() if not k.startswith(('FOW_', 'ASTRA_'))}
        env.update(settings)
        command = [str(binary), str(corpus), str(args.stride), str(args.nodes), 'verbose']
        arm = state['arms'][name] = {'state': 'running', 'command': command, 'settings': settings}
        save(); start = time.monotonic()
        with (out / (name + '.log')).open('w') as log:
            process = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=7200)
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
