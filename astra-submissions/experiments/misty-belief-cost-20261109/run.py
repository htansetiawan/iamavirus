"""Two bounded belief-only diagnostics; no new game or strength comparison."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT/'astra-submissions/analysis/misty-belief-cost-20261109'
PREVIOUS = ROOT/'astra-submissions/analysis/guard-opponent-clock-20261109'
PY = '/home/henrytan/fable-persist/scratchpad/misty/venv/bin/python'
sys.path.insert(0, str(ROOT/'astra-submissions/tools'))
from local_turn_control import ProcessGroupControl, group_members, cleanup_registry


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def main():
    os.chdir(ROOT)
    os.sched_setaffinity(0, {6})
    os.nice(10)
    terminal = json.loads((PREVIOUS/'completion.json').read_text())
    assert not terminal['clean'] and terminal['completed'] == 5
    OUT.mkdir(exist_ok=False)
    replay = PREVIOUS/'jobs/p1-white-candidate/replay.json'
    plan = dict(at=datetime.now(timezone.utc).isoformat(), caps=['none', '200000'],
                replay=str(replay), replay_sha256=sha(replay), per_case_seconds=90,
                source_sha256={str(p): sha(p) for p in [Path(__file__), HERE/'trace.py']},
                scope='Observation/recorded-own-action belief replay with historical searches skipped and one final search; one core, 4GiB limit. '
                      'Not a strength game or exact timing/search reproduction. No model or arena action.')
    write(OUT/'plan.json', plan)
    rows = []
    env = {k: v for k, v in os.environ.items() if not k.startswith(('MIST_', 'MISTY_', 'FOW_', 'ASTRA_'))}
    env.update(FOW_REQUIRE_RUST='1', FOW_V2_CLOCK_TIME='1', OMP_NUM_THREADS='1',
               OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               PATH='/home/henrytan/fable-persist/scratchpad/misty/bin:/usr/bin:/bin')
    for cap in plan['caps']:
        folder = OUT/cap
        folder.mkdir()
        command = [PY, str(HERE/'trace.py'), '--replay', str(replay), '--side', 'black',
                   '--cap', cap, '--out', str(folder/'events.jsonl'), '--search-last']
        with (folder/'stdout.txt').open('x') as stdout, (folder/'stderr.txt').open('x') as stderr:
            proc = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=env, start_new_session=True)
            control = ProcessGroupControl(proc)
            start = time.monotonic()
            timed_out = False
            while proc.poll() is None:
                members = group_members(proc.pid)
                if members:
                    control.members = members
                if time.monotonic()-start > plan['per_case_seconds']:
                    timed_out = True
                    control._signal(signal.SIGKILL)
                    break
                try:
                    proc.wait(timeout=.25)
                except subprocess.TimeoutExpired:
                    pass
            proc.wait(timeout=5)
            write(folder/'processes.json', [control.record()])
            unverified = cleanup_registry(folder/'processes.json')
        events = [json.loads(line) for line in (folder/'events.jsonl').read_text().splitlines()] if (folder/'events.jsonl').exists() else []
        row = dict(cap=cap, exit_code=proc.returncode, timed_out=timed_out,
                   seconds=time.monotonic()-start, unverified_cleanup=unverified,
                   completed=any(e['kind'] == 'complete' for e in events),
                   max_positions=max((e.get('positions', 0) for e in events), default=0),
                   peak_rss_kib=max((e.get('peak_rss_kib', 0) for e in events), default=0),
                   last_event=events[-1] if events else None,
                   files={p.name: sha(p) for p in folder.iterdir() if p.is_file()})
        write(folder/'result.json', row)
        rows.append(row)
        print(json.dumps({k: v for k, v in row.items() if k != 'files'}), flush=True)
        assert not unverified
    write(OUT/'completion.json', dict(at=datetime.now(timezone.utc).isoformat(), rows=rows,
          scope=plan['scope']))


if __name__ == '__main__':
    main()
