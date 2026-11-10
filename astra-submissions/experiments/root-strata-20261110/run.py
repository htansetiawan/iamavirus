"""Execute exactly four frozen seeds, retaining every first attempt."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/root-strata-20261110'
BUILD = HERE/'build'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def members(group):
    found = []
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            fields = (path/'stat').read_text().rsplit(')', 1)[1].split()
            if int(fields[2]) == group and fields[0] not in ('Z', 'X'):
                found.append(int(path.name))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            pass
    return found


def main():
    plan = json.loads((OUT/'plan.json').read_text())
    assert json.loads((OUT/'preflight.json').read_text())['passed']
    for path, digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    os.sched_setaffinity(0, set(plan['cores']))
    write(OUT/'started.json', dict(at=datetime.now(timezone.utc).isoformat(), pid=os.getpid(),
                                  plan_sha256=sha(OUT/'plan.json')))
    started = time.monotonic()
    rows, error = [], None
    try:
        for index, seed in enumerate(plan['seeds']):
            assert time.monotonic()-started+plan['process_seconds'] < plan['total_seconds']
            folder = OUT/f'seed-{seed}'
            folder.mkdir(exist_ok=False)
            env = {k: v for k, v in os.environ.items() if not k.startswith(('MIST_', 'FOW_', 'ASTRA_'))}
            sf = HERE.parent/'guard-controls-20261109/build/bin/stockfish'
            env.update(MIST_STOCKFISH=str(sf), ASTRA_SF_ALLCHILDREN='1', MIST_SF_WORKERS='2',
                       MIST_SF_MULTIPV='256', MIST_ASYNC='0', MIST_BEST_INIT='1', MIST_MODEL_TEMP='2',
                       MIST_TEACHER_OUT=str(folder/'targets.jsonl'), OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
            cmd = [str(BUILD/'driver'), 'search', str(OUT/'population.txt'), str(seed),
                   str(plan['seconds_per_arm']), str(index)]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, env=env, start_new_session=True)
            ticks = Path(f'/proc/{proc.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
            write(folder/'started.json', dict(at=datetime.now(timezone.utc).isoformat(), command=cmd,
                                             pid=proc.pid, pgid=proc.pid, start_ticks=ticks))
            timeout = False
            try:
                stdout, stderr = proc.communicate(timeout=plan['process_seconds'])
            except subprocess.TimeoutExpired:
                timeout = True
                os.killpg(proc.pid, signal.SIGKILL)  # This runner's freshly created child group.
                stdout, stderr = proc.communicate()
            (folder/'stdout.json').write_text(stdout)
            (folder/'stderr.txt').write_text(stderr)
            live = members(proc.pid)
            result = dict(seed=seed, order=index, exit_code=proc.returncode, timed_out=timeout, live_members=live,
                          files={p.name: sha(p) for p in folder.iterdir() if p.is_file()})
            write(folder/'result.json', result)
            rows.append(result)
            assert proc.returncode == 0 and not timeout and not live, result
            data = json.loads(stdout)
            assert data['belief_unchanged'] and data['eligible'] and len(data['searches']) == 4
            print(json.dumps(dict(seed=seed, moves={r['arm']: r['move'] for r in data['searches']})), flush=True)
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        write(OUT/'completion.json', dict(at=datetime.now(timezone.utc).isoformat(), error=error,
              completed=len(rows), elapsed_seconds=time.monotonic()-started, rows=rows, scope=plan['scope']))


if __name__ == '__main__':
    main()
