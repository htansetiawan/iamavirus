"""One multi-world teaching decision using the unchanged 375 binaries.

Selection uses population size only, before searching a move. This is not a
new candidate, speed test, arena reconstruction or strength comparison.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
NAME = 'presentation-multistate-20261111'
OUT = ROOT / 'astra-submissions/analysis' / NAME
STORE = ROOT / 'data/astra-spool' / NAME
OLD_BUILD = ROOT / 'astra-submissions/experiments/presentation-real-decision-20261111'
OLD_PLAN = ROOT / 'astra-submissions/analysis/presentation-real-decision-20261111/plan.json'
SHIP = ROOT / 'astra-submissions/experiments/guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
REPLAY = ROOT / 'data/astra-spool/v38-mist-wins-20261111/c8ozqj0m.json'


def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def save(p, value):
    with p.open('x') as stream: stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')
def update(p, value):
    temporary = p.with_suffix(p.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n'); temporary.replace(p)


def feed(frames, last_ply):
    result = ['fow', 'w 180 2', frames[0]['white'], str(frames[0]['clocks'][0])]
    for ply in range(2, last_ply + 1, 2):
        result += [frames[ply - 1]['white'], frames[ply]['white'], str(frames[ply]['clocks'][0])]
    return '\n'.join(result) + '\n'


@contextmanager
def lease():
    path = ROOT / 'chatroom/cores.json'
    owner = 'astra-' + NAME
    def change(take):
        with open('/tmp/iamavirus-cores-json.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX); state = read(path)
            if take:
                assert not any(set(r['cores']) & {2, 3} for r in state['allocation'])
                state['allocation'].append(dict(owner=owner, cores=[2, 3], pid=os.getpid(), at=now(), purpose='fixed multi-world teaching trace'))
            else:
                state['allocation'] = [r for r in state['allocation'] if not (r['owner'] == owner and r.get('pid') == os.getpid())]
            state['updated'] = now(); update(path, state)
    change(True)
    try: yield
    finally: change(False)


def prepare():
    prior = read(OLD_PLAN)
    for p, h in prior['dependencies'].items():
        assert sha(p) == h, p
    replay = read(REPLAY)
    assert replay['white'] == 'IAmAVirus' and replay['whiteVersion'] == 38
    OUT.mkdir(exist_ok=False); STORE.mkdir(exist_ok=False)
    frames = replay['frames']
    (STORE / 'probe-input.txt').write_text(feed(frames, 14))
    paths = [Path(__file__), OLD_PLAN, REPLAY, STORE / 'probe-input.txt', SHIP / 'data/history.bin', SHIP / 'bin/stockfish']
    paths += [p for arm in ('control', 'trace') for p in (OLD_BUILD / arm).rglob('*') if p.is_file()]
    plan = dict(at=now(), seed=3831111, probe_last_ply=14, earliest_ply=6, minimum_worlds=33, maximum_worlds=4096,
                selection='First White decision at ply6..14 in the already selected c8ozqj0m win with33..4096 retained worlds. Size-only selection before any searched action output. No replacement game or parameter sweep.',
                forced_probe=[frames[p + 1]['move'] for p in range(0, 15, 2)],
                search_seconds=2.0, call_timeout=90, output_byte_cap=16 * 1024**2, cores=[2, 3],
                dependencies={str(p): sha(p) for p in paths},
                scope='One all-forced inference probe, then one unchanged control and one output-only annotated search. Teaching only: no candidate, performance/strength gate, fit, model change, match, GPU, commit, push or deployment.',
                information_boundary='The bot receives only recorded White views/clocks and its own forced past actions. Truth and actual opponent moves are used in independent review, not engine input.',
                limitations=['Shortened two-second search, fixed local seed, and forced past moves do not recover the arena tree or probabilities.',
                             'Logging affects finite wall-clock search; control/trace differences are not a speed or strength measurement.',
                             'Only a selected prefix. No general coverage, calibration, Nash or safety guarantee.'])
    save(OUT / 'plan.json', plan)
    print(json.dumps(dict(plan_sha256=sha(OUT / 'plan.json'), selection=plan['selection'])), flush=True)


def call(arm, input_path, forced, plan, scorer):
    env = {k: v for k, v in os.environ.items() if not k.startswith(('MIST_', 'ASTRA_', 'FOW_', 'OMP_', 'MKL_', 'OPENBLAS_'))}
    env.update(MIST_HISTORY_TABLE=str(SHIP / 'data/history.bin'), MIST_FORCE_MOVES=','.join(forced),
               MIST_TIMING='1', MIST_RISK='1', MIST_MAX_SECONDS=str(plan['search_seconds']),
               FOW_SEED=str(plan['seed']), OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    if scorer:
        env.update(MIST_STOCKFISH=str(SHIP / 'bin/stockfish'), ASTRA_SF_ALLCHILDREN='1')
    binary = OLD_BUILD / ('control' if arm == 'probe' else arm) / 'mist'
    started = time.monotonic()
    process = subprocess.Popen(['taskset', '-c', '2,3', str(binary)], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, start_new_session=True)
    state = dict(at=now(), status='running', arm=arm, pid=process.pid, plan_sha256=sha(OUT / 'plan.json'))
    save(OUT / (arm + '-execution.json'), state)
    try:
        stdout, stderr = process.communicate(input_path.read_text(), timeout=plan['call_timeout'])
    except BaseException as error:
        os.killpg(process.pid, signal.SIGKILL); stdout, stderr = process.communicate()
        (STORE / (arm + '.stdout')).write_text(stdout); (STORE / (arm + '.stderr')).write_text(stderr)
        state.update(status='failed', error=repr(error), code=process.returncode, ended_at=now(), seconds=time.monotonic() - started)
        update(OUT / (arm + '-execution.json'), state)
        raise
    (STORE / (arm + '.stdout')).write_text(stdout); (STORE / (arm + '.stderr')).write_text(stderr)
    state.update(status='complete' if process.returncode == 0 else 'failed', code=process.returncode,
                 ended_at=now(), seconds=time.monotonic() - started,
                 stdout_sha256=sha(STORE / (arm + '.stdout')), stderr_sha256=sha(STORE / (arm + '.stderr')))
    update(OUT / (arm + '-execution.json'), state)
    assert process.returncode == 0 and len(stdout.encode()) + len(stderr.encode()) <= plan['output_byte_cap']
    assert 'forced move' not in stderr and 'belief empty' not in stderr
    if scorer: assert 'mist: stockfish ready' in stderr and 'failed to start' not in stderr
    return stdout, stderr


def probe():
    plan = read(OUT / 'plan.json')
    for p, h in plan['dependencies'].items(): assert sha(p) == h, p
    with lease():
        stdout, stderr = call('probe', STORE / 'probe-input.txt', plan['forced_probe'], plan, False)
    expected = ['ready'] + ['move ' + m for m in plan['forced_probe']]
    assert stdout.splitlines() == expected
    count_rows = list(re.finditer(r'^mist: played \S+ risk [\d.]+ least [\d.]+ \|P\|=(\d+).*$', stderr, re.MULTILINE))
    counts = [int(row[1]) for row in count_rows]
    assert len(counts) == len(plan['forced_probe']) == 8
    choices = [(2 * i, n) for i, n in enumerate(counts) if 2 * i >= plan['earliest_ply'] and plan['minimum_worlds'] <= n <= plan['maximum_worlds']]
    assert choices, 'no eligible multi-world teaching prefix; no replacement search authorized by this plan'
    ply, count = choices[0]
    # Capping after the selected prefix is irrelevant; reject it before selection.
    prefix = stderr[:count_rows[ply // 2].end()]
    assert 'thinned' not in prefix and '(capped)' not in prefix
    frames = read(REPLAY)['frames']
    (STORE / 'input.txt').write_text(feed(frames, ply))
    selection = dict(at=now(), observed_population_counts=counts, selected_ply=ply, selected_count=count,
                     decision=ply // 2 + 1, forced=[frames[p + 1]['move'] for p in range(0, ply, 2)],
                     recorded_move=frames[ply + 1]['move'], input_sha256=sha(STORE / 'input.txt'),
                     plan_sha256=sha(OUT / 'plan.json'), probe_stdout_sha256=sha(STORE / 'probe.stdout'),
                     probe_stderr_sha256=sha(STORE / 'probe.stderr'))
    save(OUT / 'selection.json', selection)
    print(json.dumps(selection), flush=True)


def run():
    plan = read(OUT / 'plan.json'); selection = read(OUT / 'selection.json')
    for p, h in plan['dependencies'].items(): assert sha(p) == h, p
    assert sha(STORE / 'input.txt') == selection['input_sha256']
    with lease():
        for arm in ('control', 'trace'):
            stdout, stderr = call(arm, STORE / 'input.txt', selection['forced'], plan, True)
            print(json.dumps(dict(arm=arm, last_output=stdout.splitlines()[-1], source_rows=len(stderr.splitlines()))), flush=True)


if __name__ == '__main__':
    {'prepare': prepare, 'probe': probe, 'run': run}[sys.argv[1]]()
