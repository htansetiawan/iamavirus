"""Bounded cost diagnostic on historical own observations; no search or truth input."""
from datetime import datetime, timedelta, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/belief-sort-cost-20261110'
BUILD = HERE/'build'
CONTROLS = ROOT/'astra-submissions/analysis/guard-controls-20261109'
SOURCES = ['board', 'belief', 'movemodel', 'cfr', 'eval', 'search', 'gtcfr', 'front', 'sfeval', 'main']


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def env(parent, moves):
    result = {k: v for k, v in os.environ.items() if not k.startswith(('MIST_', 'FOW_', 'ASTRA_'))}
    result.update(MIST_HISTORY_TABLE=str(parent/'data/history.bin'), MIST_FORCE_MOVES=','.join(moves),
                  MIST_TIMING='1', FOW_SEED='2791000', MIST_MAX_SECONDS='10', MIST_THREADS='2')
    # No evaluator process: all decisions, including the last, are forced.
    return result


def feed(case):
    replay = json.loads(Path(case['replay_path']).read_text())
    assert sha(case['replay_path']) == case['replay_sha256']
    side = ['white', 'black'].index(case['side'])
    lines = ['fow', f"{'w' if side == 0 else 'b'} 180 2"]
    moves = []
    for ply, frame in enumerate(replay['frames'][:case['ply']+1]):
        lines.append(frame[case['side']])
        if ply % 2 == side:
            lines.append(str(frame['clocks'][side]))
            moves.append(replay['frames'][ply+1]['move'])
    return '\n'.join(lines)+'\n', moves


def prepare():
    OUT.mkdir(exist_ok=False)
    BUILD.mkdir(exist_ok=False)
    pilot = json.loads((CONTROLS/'full-games/plan.json').read_text())
    parent = Path(pilot['parent_build'])
    shutil.copytree(parent/'src', BUILD/'src')
    flags = ['-O2', '-std=c11', '-pthread', '-D_POSIX_C_SOURCE=199309L']
    commands = []
    for name in SOURCES:
        cmd = ['gcc', *flags, *(['-Dqsort=astra_qsort'] if name == 'belief' else []),
               '-c', str(BUILD/'src'/f'{name}.c'), '-o', str(BUILD/f'{name}.o')]
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        commands.append(cmd)
    cmd = ['gcc', *flags, str(HERE/'profile.c'), *[str(BUILD/f'{n}.o') for n in SOURCES],
           '-lm', '-o', str(BUILD/'mist-profile')]
    subprocess.run(cmd, check=True, capture_output=True, timeout=60)
    commands.append(cmd)
    original = json.loads((CONTROLS/'plan.json').read_text())
    pool = []
    for case in original['cases']:
        result = CONTROLS/'jobs'/case['id']/'result.json'
        target = json.loads(result.read_text())['arms']['base'].get('target')
        if target:
            pool.append(dict(case, selection_population=target['belief_count'], selection_receipt=str(result),
                             selection_receipt_sha256=sha(result)))
    high = sorted(pool, key=lambda c: (-c['selection_population'], c['id']))[:6]
    medium = sorted([c for c in pool if c not in high],
                    key=lambda c: (abs(c['selection_population']-1000), c['id']))[:2]
    cases = high+medium
    smoke = []
    for side in ('white', 'black'):
        c = dict(next(c for c in original['cases'] if c['side'] == side))
        c['ply'] = 0 if side == 'white' else 1
        text, moves = feed(c)
        r = subprocess.run([str(BUILD/'mist-profile')], input=text, capture_output=True, text=True,
                           env=env(parent, moves), timeout=10)
        assert r.returncode == 0 and re.findall(r'^move (\S+)$', r.stdout, re.M) == moves
        profile = json.loads(re.findall(r'^astra-sort-profile: (.*)$', r.stderr, re.M)[0])
        smoke.append(dict(side=side, move=moves[0], profile=profile))
    deps = [Path(__file__), HERE/'profile.c', BUILD/'mist-profile', parent/'mist', parent/'data/history.bin',
            ROOT/'astra-submissions/iamavirus-v38-mist-c-allchildren.zip', CONTROLS/'plan.json']
    deps += list((BUILD/'src').glob('*'))
    deps += [parent/'src'/p.name for p in (BUILD/'src').iterdir()]
    for case in cases:
        deps += [Path(case['replay_path']), Path(case['selection_receipt'])]
    write(OUT/'preflight.json', dict(passed=True, checks=smoke, commands=commands,
          delegated_sort='Only belief.c qsort symbol redirects; wrapper calls the same libc qsort, comparator and array.'))
    plan = dict(at=now(), parent=str(parent), cases=cases, core=6, per_case_seconds=120, total_seconds=1020,
                dependencies={str(p): sha(p) for p in deps},
                selection='Six largest prior control populations, then two nearest 1000; no outcome or speed selection.',
                scope='Forced whole prefixes with no search/SF, native paid thinning retained; one core, two belief threads. '
                      'Instrumentation and wall-time thinning can alter populations. Not full-turn performance or strength.',
                interpretation='Report qsort thread CPU / engine process CPU, with max serial saving 1/(1-share). '
                               'Do not interpret this as a whole-decision bound; profile excludes search.',
                next_step='Only a material measured sort share earns a bounded semantics-preserving kernel experiment. '
                          'No candidate or arena change from this profile.')
    write(OUT/'plan.json', plan)
    print(json.dumps(dict(prepared=True, cases=len(cases), pins=len(plan['dependencies']))), flush=True)


def run():
    plan = json.loads((OUT/'plan.json').read_text())
    for path, value in plan['dependencies'].items():
        assert sha(path) == value, path
    os.sched_setaffinity(0, {plan['core']})
    start = time.monotonic()
    write(OUT/'started.json', dict(at=now(), pid=os.getpid(), plan_sha256=sha(OUT/'plan.json')))
    rows = []
    try:
        for case in plan['cases']:
            assert time.monotonic()-start+plan['per_case_seconds'] < plan['total_seconds']
            folder = OUT/case['id']
            folder.mkdir(exist_ok=False)
            text, moves = feed(case)
            (folder/'input.txt').write_text(text)
            clock = time.monotonic()
            proc = subprocess.Popen([str(BUILD/'mist-profile')], stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                    env=env(Path(plan['parent']), moves), start_new_session=True)
            write(folder/'process.json', dict(pid=proc.pid,
                  start_ticks=Path(f'/proc/{proc.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
            try:
                stdout, stderr = proc.communicate(text, timeout=plan['per_case_seconds'])
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                stdout, stderr = proc.communicate()
                (folder/'stdout.txt').write_text(stdout)
                (folder/'stderr.txt').write_text(stderr)
                raise
            (folder/'stdout.txt').write_text(stdout)
            (folder/'stderr.txt').write_text(stderr)
            assert proc.returncode == 0, (case['id'], proc.returncode, stderr[-1000:])
            assert re.findall(r'^move (\S+)$', stdout, re.M) == moves
            assert 'nodes=' not in stderr and 'stockfish ready' not in stderr, 'Unexpected unforced search'
            profiles = re.findall(r'^astra-sort-profile: (.*)$', stderr, re.M)
            assert len(profiles) == 1
            profile = json.loads(profiles[0])
            total_sort = sum(b['thread_cpu_ns'] for b in profile['buckets'])
            row = dict(case=case, elapsed_seconds=time.monotonic()-clock, exit_code=proc.returncode,
                       forced_moves=len(moves), profile=profile,
                       sort_cpu_share=total_sort/profile['process_cpu_ns'],
                       timing_updates=re.findall(r'mist: timing (own|opp) update ([\d.]+) s \|P\| (\d+) -> (\d+)', stderr),
                       files={p.name: sha(p) for p in folder.iterdir() if p.is_file()})
            write(folder/'result.json', row)
            rows.append(row)
            print(json.dumps(dict(case=case['id'], seconds=row['elapsed_seconds'], sort_share=row['sort_cpu_share'])), flush=True)
        write(OUT/'completion.json', dict(at=now(), completed=len(rows), state='complete',
              elapsed_seconds=time.monotonic()-start, rows=[r['case']['id'] for r in rows]))
    except BaseException as error:
        write(OUT/'failure.json', dict(at=now(), completed=len(rows), error=repr(error)))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'run'))
    args = parser.parse_args()
    globals()[args.action]()
