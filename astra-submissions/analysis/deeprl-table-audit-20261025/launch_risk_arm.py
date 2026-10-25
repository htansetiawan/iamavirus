"""Validate a pinned arm and print its command; --run explicitly starts it.

The human/committee plan review and CPU reservation happen before --run. This
wrapper enforces artifact identity, a free GPU/lease, fresh outputs and the
one-hour process-group deadline. It never stops another GPU service.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from prepare_risk_run import sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arm', required=True, choices=['control', 'auxiliary'])
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--output-root', type=Path, default=Path('/media/henrytan/seagate1/iamavirus/astra/rl-risk-20261025'))
    args = parser.parse_args()
    folder = HERE / 'risk-run-preflight'
    receipt = json.loads((folder / 'preflight.json').read_bytes())
    source = Path(receipt['source_root'])
    for name, digest in receipt['source_sha256'].items():
        if sha(source / name) != digest: raise RuntimeError('Prepared source changed: ' + name)
    checkpoints = list(receipt['actor_checkpoints'].values()) + [receipt['critic_checkpoint']]
    checked = set()
    for entry in checkpoints:
        if entry['path'] not in checked and sha(entry['path']) != entry['sha256']:
            raise RuntimeError('Checkpoint changed: ' + entry['path'])
        checked.add(entry['path'])
    config = folder / (args.arm + '.yaml')
    if sha(config) != receipt['configuration_sha256'][args.arm]: raise RuntimeError('Config changed')
    if sha(folder / 'validation-games.json') != receipt['validation_sha256']: raise RuntimeError('Validation manifest changed')
    output = args.output_root / args.arm
    command = [str(ROOT / '.venv/bin/python'), '-m', 'learning.rl_train',
               '--config', str(config), '--output', str(output), '--iterations', '60']
    plan = {'arm': args.arm, 'command': command, 'cwd': str(source),
            'wall_cap_seconds': receipt['limits']['wall_seconds_per_arm'],
            'preflight_sha256': sha(folder / 'preflight.json'), 'started': False}
    if not args.run:
        print(json.dumps(plan, indent=2)); return 0
    if output.exists(): raise RuntimeError('Output exists; this experiment does not resume or overwrite')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader,nounits'], text=True)
    if apps.strip(): raise RuntimeError('Another GPU process exists; leave it running and wait')
    gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader,nounits'], text=True)
    used, utilization = map(float, gpu.strip().split(','))
    if used > 4096 or utilization > 5: raise RuntimeError('GPU is not idle enough; wait without stopping services')
    subprocess.run([str(ROOT / '.venv/bin/python'), '-c',
                    'import torch; assert torch.cuda.is_available(), "CUDA required; no CPU fallback"'], check=True)
    lease = Path('/tmp/gpu_queue/claimed_by'); lease.parent.mkdir(exist_ok=True)
    owner = f'astra-risk-{args.arm}-pid{os.getpid()}'
    with lease.open('x') as stream: stream.write(owner)
    child = None; started = time.monotonic()
    try:
        output.mkdir(parents=True)
        env = dict(os.environ, OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='1',
                   PYTHONPATH=str(source))
        os.sched_setaffinity(0, {0, 1})
        plan.update(started=True, started_at=datetime.now(timezone.utc).isoformat(), gpu_before=gpu.strip())
        (output / 'launch.json').write_text(json.dumps(plan, indent=2) + '\n')
        with (output / 'process.log').open('w') as log:
            child = subprocess.Popen(command, cwd=source, env=env, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = child.wait(timeout=plan['wall_cap_seconds'])
                state = 'complete' if code == 0 else 'failed'
            except subprocess.TimeoutExpired:
                state = 'time_capped'; code = 124
            finally:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try: child.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL); child.wait()
        result = {'state': state, 'exit_code': code, 'wall_seconds': time.monotonic() - started,
                  'finished_at': datetime.now(timezone.utc).isoformat(),
                  'note': 'Use only complete, loadable common snapshots; no continuation beyond this cap.'}
        (output / 'completion.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result)); return code
    finally:
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try: child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL); child.wait()
        if lease.exists() and lease.read_text() == owner: lease.unlink()


if __name__ == '__main__': raise SystemExit(main())
