"""One bounded, staged intelligence refresh; never edits a bot or publishes reports."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'astra-submissions/analysis/report-repair-20261108'
STAGE = OUT/'reports'
PY = str(ROOT/'.venv/bin/python')


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    with path.open('x') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


def main():
    os.chdir(ROOT)
    os.sched_setaffinity(0, {4, 5})
    os.nice(10)
    STAGE.mkdir(exist_ok=False)
    previous = ROOT/'data/reports/daily/2026-11-02.json'
    shutil.copy2(previous, STAGE/previous.name)
    commands = [
        ('daily', [PY, '-m', 'learning.daily_report', '--raw', 'data/raw', '--out', str(STAGE)], 1200),
        ('insights', [PY, '-m', 'learning.daily_insights', '--raw', 'data/raw', '--out', str(STAGE)], 300),
        ('scorecard', [PY, '-m', 'learning.scorecard', '--raw', 'data/raw', '--out', str(STAGE), '--days', '3'], 1200),
        ('intel', [PY, 'astra-submissions/tools/daily_intel_status.py', '--raw', 'data/raw', '--out', str(STAGE)], 180),
    ]
    write(OUT/'refresh-plan.json', dict(at=now(), cores=[4, 5], commands=commands,
          raw_resolved=str((ROOT/'data/raw').resolve()), previous_sha256=digest(previous),
          limitation='Rolling read-only view of a live mirror; not a frozen experiment or a model refresh.'))
    records = []
    for name, command, timeout in commands:
        subprocess.run([PY, 'astra-submissions/tools/check_raw_available.py', '--reports'], check=True)
        start = time.monotonic()
        with (OUT/f'{name}.stdout').open('x') as stdout, (OUT/f'{name}.stderr').open('x') as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
            write(OUT/f'{name}-handle.json', dict(at=now(), pid=process.pid, command=command,
                  proc_starttime=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
            timed_out = False
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    code = process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    code = process.wait(timeout=5)
        row = dict(name=name, finished=now(), exit_code=code, timed_out=timed_out,
                   elapsed_seconds=time.monotonic()-start)
        write(OUT/f'{name}-receipt.json', row)
        records.append(row)
        print(json.dumps(row), flush=True)
        if code or timed_out:
            break
    write(OUT/'refresh-receipt.json', dict(at=now(), steps=records,
          passed=len(records)==len(commands) and all(r['exit_code']==0 and not r['timed_out'] for r in records),
          staged_files={p.name: digest(p) for p in STAGE.iterdir() if p.is_file()},
          published=False))


if __name__ == '__main__':
    main()
