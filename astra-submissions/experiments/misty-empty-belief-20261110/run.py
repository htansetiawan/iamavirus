"""Two bounded component cases; not another game comparison."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/misty-empty-belief-20261110'
PANEL = ROOT/'astra-submissions/analysis/guard-opponent-bounded-20261110'
PY = '/home/henrytan/fable-persist/scratchpad/misty/venv/bin/python'
sys.path.insert(0, str(ROOT/'astra-submissions/tools'))
from local_turn_control import ProcessGroupControl, group_members, cleanup_registry


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def prepare():
    audit = json.loads((PANEL/'audit.json').read_text())
    assert audit['completed'] == 23 and audit['technical_games'] == 1 and not audit['gate_pass']
    OUT.mkdir(exist_ok=False)
    case = PANEL/'jobs/p3-black-candidate/replay.json'
    replay = json.loads(case.read_text())
    seed = json.loads((PANEL/'jobs/p3-black-candidate/result.json').read_text())['job']['opponent_seed']
    assert replay['failedSide'] == 'white' and replay['frames'][23]['move'] == 'd1a4'
    observations = [dict(ply=f['ply'], view=f['white'],
                    own_move_after=replay['frames'][i+1]['move'] if i % 2 == 0 else None)
                    for i, f in enumerate(replay['frames'][:24])]
    write(OUT/'redacted-input.json', dict(side='white', seed=seed, observations=observations))
    previous = json.loads((PANEL/'plan.json').read_text())
    deps = {k: v for k, v in previous['dependencies'].items()
            if '/scratchpad/misty/' in k or '/fow-starter/' in k or k.endswith('misty_adapter.py')}
    for p in [Path(__file__), HERE/'trace.py', OUT/'redacted-input.json', case, PANEL/'audit.json',
              ROOT/'astra-submissions/tools/local_turn_control.py']:
        deps[str(p)] = sha(p)
    write(OUT/'plan.json', dict(at=datetime.now(timezone.utc).isoformat(), dependencies=deps,
          cases=['200000', 'none'], seed=seed, core=6, case_wall_seconds=60, address_space_limit=4 << 30,
          scope='Observation/own-action component trace, historical searches skipped. Same seed/capture inference. '
                'Compare bounded and uncapped own-view consistency at ply23, not strength or exact search/carryover. '
                '4GiB address space is a diagnostic bound, not the arena RSS limit. No package changes or fourth match batch.'))
    print(json.dumps(dict(prepared=True, caps=['200000', 'none'], pins=len(deps))), flush=True)


def run():
    plan = json.loads((OUT/'plan.json').read_text())
    for path, digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    os.sched_setaffinity(0, {6}); os.nice(10)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('MIST_', 'MISTY_', 'FOW_', 'ASTRA_'))}
    env.update(FOW_REQUIRE_RUST='1', FOW_V2_CLOCK_TIME='1', OMP_NUM_THREADS='1',
               OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               PATH='/home/henrytan/fable-persist/scratchpad/misty/bin:/usr/bin:/bin')
    rows = []
    for cap in plan['cases']:
        folder = OUT/cap; folder.mkdir()
        command = [PY, str(HERE/'trace.py'), '--input', str(OUT/'redacted-input.json'),
                   '--cap', cap, '--out', str(folder/'events.jsonl')]
        with (folder/'stdout.txt').open('x') as stdout, (folder/'stderr.txt').open('x') as stderr:
            proc = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=env, start_new_session=True)
            control = ProcessGroupControl(proc); start = time.monotonic(); timed_out = False
            while proc.poll() is None:
                members = group_members(proc.pid)
                if members: control.members = members
                if time.monotonic()-start > plan['case_wall_seconds']:
                    timed_out = True; control._signal(signal.SIGKILL); break
                try: proc.wait(timeout=.25)
                except subprocess.TimeoutExpired: pass
            proc.wait(timeout=5)
            write(folder/'processes.json', [control.record()])
            unverified = cleanup_registry(folder/'processes.json')
        events = [json.loads(line) for line in (folder/'events.jsonl').read_text().splitlines()]
        row = dict(cap=cap, exit_code=proc.returncode, timed_out=timed_out,
                   seconds=time.monotonic()-start, completed=any(e['kind'] == 'complete' for e in events),
                   max_positions=max((e.get('positions', 0) for e in events), default=0),
                   peak_rss_kib=max(e['peak_rss_kib'] for e in events), last_event=events[-1],
                   unverified_cleanup=unverified, files={p.name: sha(p) for p in folder.iterdir() if p.is_file()})
        write(folder/'result.json', row); rows.append(row)
        print(json.dumps({k: v for k, v in row.items() if k != 'files'}), flush=True)
        assert not unverified
    write(OUT/'completion.json', dict(at=datetime.now(timezone.utc).isoformat(), rows=rows, scope=plan['scope']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'run'))
    globals()[parser.parse_args().action]()
