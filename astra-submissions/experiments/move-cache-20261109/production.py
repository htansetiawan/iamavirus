"""One bounded production export; publish only the exporter's complete generation."""
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'astra-submissions/analysis/move-cache-20261109'
HERE = Path(__file__).resolve().parent
EXPORTER = ROOT/'astra-submissions/tools/export_move_cache.py'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def prepare():
    parity = json.loads((OUT/'real-parity.json').read_text())
    assert parity['passed'] and parity['games'] == 128 and parity['exporter_sha256'] == digest(EXPORTER)
    prefix = ROOT/'data/derived/moves/arena-latest'
    seeds = [Path(str(prefix)+f'-{name}.txt') for name in ('train', 'test')]
    since = (datetime.now(timezone.utc)-timedelta(days=21)).date().isoformat()
    command = [sys.executable, str(EXPORTER), '--raw', str(ROOT/'data/raw'),
               '--cache', str(ROOT/'data/cache/move-export.sqlite'), '--out-prefix', str(prefix),
               '--since', since, '--games', '1000000', '--wall-seconds', '2400', '--legacy-links']
    for source in seeds:
        if source.is_file():
            command += ['--seed-export', str(source)]
    write(OUT/'production-plan.json', dict(at=datetime.now(timezone.utc).isoformat(),
          cores=[6], wall_seconds=2430, command=command, exporter_sha256=digest(EXPORTER),
          launcher_sha256=digest(Path(__file__)), parity_sha256=digest(OUT/'real-parity.json'),
          seeds={str(p): dict(bytes=p.stat().st_size, sha256=digest(p)) for p in seeds if p.is_file()},
          scope='One bounded cache/bootstrap/full-recent move export. No model fit, dataset episode rebuild or arena action.'))
    print(json.dumps(dict(prepared=True, since=since)), flush=True)


def main():
    os.chdir(ROOT)
    os.sched_setaffinity(0, {6})
    os.nice(10)
    plan = json.loads((OUT/'production-plan.json').read_text())
    assert digest(EXPORTER) == plan['exporter_sha256']
    assert digest(Path(__file__)) == plan['launcher_sha256']
    for name, item in plan['seeds'].items():
        assert digest(Path(name)) == item['sha256'], name
    before = time.monotonic()
    with (OUT/'production.stdout').open('x') as stdout, (OUT/'production.stderr').open('x') as stderr:
        process = subprocess.Popen(plan['command'], stdout=stdout, stderr=stderr, start_new_session=True)
        write(OUT/'production-handle.json', dict(at=datetime.now(timezone.utc).isoformat(),
              pid=process.pid, pid_namespace=os.readlink('/proc/self/ns/pid'),
              start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        timed_out = False
        try:
            code = process.wait(timeout=plan['wall_seconds'])
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                code = process.wait(timeout=5)
    write(OUT/'production-terminal.json', dict(at=datetime.now(timezone.utc).isoformat(),
          exit_code=code, timed_out=timed_out, elapsed_seconds=time.monotonic()-before,
          stdout_sha256=digest(OUT/'production.stdout'), stderr_sha256=digest(OUT/'production.stderr')))
    print(json.dumps(dict(exit_code=code, timed_out=timed_out, seconds=time.monotonic()-before)), flush=True)
    return code


if __name__ == '__main__':
    if '--prepare' in sys.argv:
        prepare()
    else:
        raise SystemExit(main())
