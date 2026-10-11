from pathlib import Path
from datetime import datetime, timezone
import subprocess, os, json, time, signal, hashlib

root = Path('/media/henrytan/seagate/iamavirus/astra/ssl-transfer-20261011')
code = Path(__file__).parent
lease = Path('/tmp/gpu_queue/claimed_by')
owner = 'astra ssl-transfer fresh control ' + datetime.now(timezone.utc).isoformat()
reference = json.loads((root / 'ssl-plus-1000/run.json').read_text())
paths = list((code / 'learning').glob('*.py')) + list((code / 'astra-submissions/learning_experiments').glob('*.py'))
actual = {str(p.relative_to(code)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
assert actual == reference['source_sha256'], 'frozen source changed'
assert not (root / 'supervised-fresh-2500').exists(), 'fresh control already exists'
gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader,nounits'], text=True).strip()
mem, util = map(int, gpu.split(','))
assert mem < 2048 and util <= 5, 'GPU not idle: ' + gpu
with lease.open('x') as f:
    f.write(owner + '\n')
status = {'state': 'starting', 'owner': owner, 'pid': os.getpid(), 'started_at': datetime.now(timezone.utc).isoformat(),
          'reason': 'Fresh identical-source control after old checkpoint source guard rejected resume; failed arm retained.'}
def save():
    p = root / 'fresh-control-status.json'
    q = p.with_suffix('.tmp')
    q.write_text(json.dumps(status, indent=2) + '\n')
    os.replace(q, p)
child = None
started = time.monotonic()
try:
    (root / 'executed-fresh-control.py').write_bytes(Path(__file__).read_bytes())
    env = dict(os.environ, PYTHONPATH=str(code / 'astra-submissions') + ':' + str(code), OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
    cmd = ['taskset', '-c', '6,7', '/home/henrytan/git/iamavirus/.venv/bin/python', '-m', 'learning_experiments.run',
           '--manifest', str(code / 'manifest.json'), '--variant', 'attention', '--phase', 'supervised', '--device', 'cuda',
           '--threads', '2', '--seed', '253', '--window', '32', '--batch', '4', '--validation-games', '64',
           '--evaluate-every', '250', '--steps', '2500', '--output', str(root / 'supervised-fresh-2500')]
    status['command'] = cmd
    save()
    with (root / 'supervised-fresh-2500.log').open('x') as log:
        child = subprocess.Popen(cmd, cwd=code, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        status.update(state='running', child_pid=child.pid)
        save()
        result = child.wait(timeout=1800)
    status.update(state='complete' if result == 0 else 'failed', returncode=result)
except BaseException as exc:
    status.update(state='failed', error=str(exc))
    raise
finally:
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
    status.update(ended_at=datetime.now(timezone.utc).isoformat(), wall_seconds=time.monotonic()-started)
    save()
    if lease.exists() and lease.read_text().strip() == owner:
        lease.unlink()
print(json.dumps(status), flush=True)
