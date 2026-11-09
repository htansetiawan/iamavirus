"""Conditional, matched 32-game panel using the repaired local Misty adapter."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/guard-opponent-20261109'
PILOT = ROOT/'astra-submissions/analysis/guard-controls-20261109/full-games'
RUNNER = HERE.parent/'persistent-response-20261101/bench.py'
ADAPTER = HERE.parent/'obscuro-fidelity-20261108/misty_adapter.py'
MISTY_PY = Path('/home/henrytan/fable-persist/scratchpad/misty/venv/bin/python')
MISTY_BIN = Path('/home/henrytan/fable-persist/scratchpad/misty/bin')
sys.path[:0] = [str(ROOT), str(ROOT/'astra-submissions/tools')]
from learning import ingest
from local_turn_control import cleanup_registry, group_members


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def clean_env():
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('MIST_', 'MISTY_', 'ASTRA_', 'FOW_', 'OMP_', 'OPENBLAS_', 'MKL_'))}
    env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    return env


def command(arm, seed):
    if arm == 'misty':
        return ['/usr/bin/env', f'FOW_SEED={seed}', 'FOW_REQUIRE_RUST=1', 'FOW_V2_CLOCK_TIME=0',
                'MISTY_PROFILE=v1.6', 'MISTY_BUDGET=0', f'PATH={MISTY_BIN}:/usr/bin:/bin',
                str(MISTY_PY), str(ADAPTER)]
    assert arm in ('base', 'candidate')
    parent = json.loads((PILOT/'plan.json').read_text())
    folder = parent['parent_build'] if arm == 'base' else parent['candidate_build']
    return ['/usr/bin/env', f'FOW_SEED={seed}', '/bin/bash', str(Path(folder)/'run.sh')]


def module():
    spec = importlib.util.spec_from_file_location('guard_opponent_runner', RUNNER)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    result.HERE, result.OUT, result.command = HERE, OUT, command
    return result


def prepare():
    audit = json.loads((PILOT/'audit.json').read_text())
    assert audit['completed'] == 16 and audit['gate_pass']
    parent = json.loads((PILOT/'plan.json').read_text())
    for name, value in parent['dependencies'].items():
        assert sha(name) == value, name
    prior_smoke_path = ROOT/'astra-submissions/analysis/obscuro-fidelity-20261108/adapter-smoke.json'
    prior_smoke = json.loads(prior_smoke_path.read_text())
    assert prior_smoke['passed']
    deps = dict(prior_smoke['dependencies'])
    for name, value in deps.items():
        assert sha(name) == value, ('Misty smoke dependency changed', name)
    assert prior_smoke['dependencies'][str(ADAPTER)] == sha(ADAPTER)
    version = subprocess.check_output([str(MISTY_PY), '-c',
        'import importlib.metadata; print(importlib.metadata.version("misty-chess"))'], text=True).strip()
    assert version == '0.1.3'
    OUT.mkdir(exist_ok=False)
    (HERE/'build').mkdir(exist_ok=False)
    shutil.copy2(ROOT.parent/'fow-starter/referee.py', HERE/'build/referee.py')
    for name, value in parent['dependencies'].items():
        # Pin playing files directly; do not inherit the earlier runner code.
        if '/build/pilot/' in name:
            deps[name] = value
    paths = [Path(__file__), RUNNER, HERE/'build/referee.py',
             ROOT/'astra-submissions/tools/local_turn_control.py', ROOT/'learning/ingest.py',
             ROOT/'learning/rules.py', ROOT/'learning/_native.py', ROOT.parent/'fow-starter/uniform_random.py',
             PILOT/'audit.json', PILOT/'plan.json', prior_smoke_path, ADAPTER]
    packages = MISTY_PY.parent.parent/'lib/python3.13/site-packages'
    paths += list((packages/'fow_rust').glob('*.so')) + list((packages/'fow_rust').glob('*.py'))
    paths += [packages/'chess/__init__.py', packages/'chess/engine.py', packages/'chess/variant.py']
    assert list((packages/'fow_rust').glob('*.so')), 'native library must be pinned'
    deps.update({str(p): sha(p) for p in paths})
    jobs = []
    for pair in range(8):
        for side in ('white', 'black'):
            order = ('base', 'candidate') if (pair+(side == 'black')) % 2 == 0 else ('candidate', 'base')
            for arm in order:
                jobs.append(dict(id=f'p{pair}-{side}-{arm}', phase='misty', pair=pair, lane=pair % 3,
                                 arm=arm, side=side, opponent='misty',
                                 engine_seed=2742000+2*pair, opponent_seed=2742001+2*pair))
    plan = dict(at=now(), dependencies=deps, jobs=jobs, lanes={'0': '0,1', '1': '2,3', '2': '4,5'},
                game_wall_cap=2450, batch_wall_cap=14400, time_control=dict(base=180, increment=2, max_plies=1000),
                misty_version=version, misty_profile='v1.6', native_required=True,
                gate=dict(games=32, per_arm=16, candidate_min_points=8, candidate_min_advantage_points=2,
                          technical_faults=0),
                resume='No started first attempt is repeated. A technical fault stops all new games; in-flight games may finish.',
                order='Eight seed blocks, both colors and arms; alternate first arm; same seeds within matched cells.',
                scope='Local Misty package with repaired course-action adapter; not verified current arena bytes or original Obscuro. '
                      'Passing earns candidate review, not an Elo claim or automatic upload. All attempts count.',
                fairness='Two reserved cores per lane; process groups frozen off turn; buffered observations charged on turn.')
    write(OUT/'plan.json', plan)
    module().load()
    print(json.dumps(dict(prepared=True, games=len(jobs), pins=len(deps))), flush=True)


def smoke():
    module().load()
    sys.path.insert(0, str(ROOT.parent/'fow-starter'))
    import referee
    os.sched_setaffinity(0, {4, 5})
    fresh = clean_env()
    os.environ.clear()
    os.environ.update(fresh)
    records = []
    for arm in ('base', 'candidate', 'misty'):
        for side in (True, False):
            board = referee.FowBoard()
            args = command(arm, 2741000)
            if arm == 'misty':
                args = [s.replace('MISTY_BUDGET=0', 'MISTY_BUDGET=.05') for s in args]
            else:
                args = ['/usr/bin/env', 'MIST_MAX_SECONDS=.1', *args]
            bot = referee.Bot(args, side, 180, 2, initialization_timeout=15)
            moves = []
            try:
                bot.observe(referee.observation(board, side), 0)
                if not side:
                    board.push_uci('d2d4')
                    bot.observe(referee.observation(board, side), 1)
                move, elapsed = bot.move(2)
                assert referee.chess.Move.from_uci(move) in referee.fow_moves(board)
                moves.append(dict(move=move, seconds=elapsed))
            finally:
                bot.close()
            error = bot.stderr_excerpt.decode()
            live = [p for p in group_members(bot.proc.pid) if p['state'] not in ('Z', 'X')]
            assert not live and bot.failure is None
            assert 'inadmissible engine move' not in error
            if arm != 'misty':
                assert 'mist: stockfish ready' in error
            records.append(dict(arm=arm, side='white' if side else 'black', turns=moves,
                                stderr=error, failure=bot.failure, live_owned_members=live))
    write(OUT/'smoke.json', dict(at=now(), passed=True, records=records))
    print(json.dumps(dict(smoke_passed=True, calls=len(records))), flush=True)


def inspect(job, directory):
    replay = json.loads((directory/'replay.json').read_text())
    states, faults = ingest.validate_replay(replay)
    if 'failedSide' in replay:
        faults.append('bot failure: '+replay['failedSide']+' '+replay['reason'])
    if replay.get('warnings'):
        faults.append('capture warning')
    if replay['result'] not in ('1-0', '0-1', '1/2-1/2'):
        faults.append('non-game result')
    ours = replay.get('privateDiagnostics', {}).get(job['side'], '')
    other_side = 'black' if job['side'] == 'white' else 'white'
    theirs = replay.get('privateDiagnostics', {}).get(other_side, '')
    if 'mist: stockfish ready' not in ours:
        faults.append('our Stockfish initialization missing')
    if 'inadmissible engine move' in theirs:
        faults.append('Misty adapter legal fallback used')
    controls = replay.get('localTurnControl', {}).get('controls', [])
    if len(controls) != 2 or any(not any(e['op'] == 'freeze' for e in c['events']) for c in controls):
        faults.append('missing turn isolation')
    result = replay['result']
    score = .5 if result == '1/2-1/2' else float((result == '1-0') == (job['side'] == 'white')) if result in ('1-0', '0-1') else None
    return dict(job=job, score=score, result=result, reason=replay['reason'], faults=faults,
                plies=len(replay['frames'])-1, validated_frames=len(states),
                replay_sha256=sha(directory/'replay.json'), final_clocks=replay['frames'][-1]['clocks'])


def run():
    runner = module()
    plan = runner.load()
    assert json.loads((OUT/'smoke.json').read_text())['passed']
    started = time.monotonic()
    write(OUT/'started.json', dict(at=now(), pid=os.getpid(), plan_sha256=sha(OUT/'plan.json')))
    stop = threading.Event()
    def lane(number):
        with (OUT/f'lane{number}.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            count = 0
            try:
                for job in [j for j in plan['jobs'] if j['lane'] == number]:
                    if stop.is_set() or time.monotonic()-started+plan['game_wall_cap'] > plan['batch_wall_cap']:
                        break
                    directory = OUT/'jobs'/job['id']
                    directory.mkdir(parents=True, exist_ok=False)
                    write(directory/'started.json', dict(at=now(), job=job))
                    process = subprocess.Popen(['taskset', '-c', plan['lanes'][str(number)], sys.executable,
                                                str(Path(__file__)), 'worker', '--job', job['id']],
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                               env=clean_env(), start_new_session=True)
                    write(directory/'handle.json', dict(pid=process.pid,
                          start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
                    clock = time.monotonic()
                    try:
                        stdout, stderr = process.communicate(timeout=plan['game_wall_cap'])
                        timed_out = False
                    except subprocess.TimeoutExpired:
                        timed_out = True
                        process.kill()
                        stdout, stderr = process.communicate()
                    unverified = cleanup_registry(directory/'processes.json')
                    (directory/'stdout.txt').write_text(stdout)
                    (directory/'stderr.txt').write_text(stderr)
                    if process.returncode or timed_out or unverified or not (directory/'replay.json').exists():
                        result = dict(job=job, score=None, faults=[f'worker_exit={process.returncode};timeout={timed_out};unverified={unverified}'])
                    else:
                        result = inspect(job, directory)
                    result.update(exit_code=process.returncode, elapsed_seconds=time.monotonic()-clock,
                                  finished=now(), files={p.name: sha(p) for p in directory.iterdir() if p.is_file()})
                    write(directory/'result.json', result)
                    count += 1
                    print(json.dumps({k: v for k, v in result.items() if k != 'files'}), flush=True)
                    if result['faults']:
                        stop.set()
                        break
            except BaseException as error:
                stop.set()
                write(OUT/f'lane{number}-failure.json', dict(at=now(), error=repr(error)))
                raise
            finally:
                write(OUT/f'lane{number}-completion.json', dict(at=now(), completed=count, stopped=stop.is_set()))
    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(lane, (0, 1, 2)))
        rows = [json.loads(p.read_text()) for p in OUT.glob('jobs/*/result.json')]
        clean = not any(r['faults'] for r in rows)
        stats = {}
        for arm in ('base', 'candidate'):
            scores = [r['score'] for r in rows if r['job']['arm'] == arm and r['score'] is not None]
            stats[arm] = dict(games=len(scores), wins=scores.count(1), draws=scores.count(.5),
                              losses=scores.count(0), points=sum(scores))
        g = plan['gate']
        passed = clean and len(rows) == 32 and stats['candidate']['points'] >= g['candidate_min_points'] and stats['candidate']['points']-stats['base']['points'] >= g['candidate_min_advantage_points']
        write(OUT/'completion.json', dict(at=now(), completed=len(rows), clean=clean, stats=stats, gate_pass=passed,
              elapsed_seconds=time.monotonic()-started,
              unstarted=[j['id'] for j in plan['jobs'] if not (OUT/'jobs'/j['id']/'started.json').exists()]))
    except BaseException as error:
        write(OUT/'failure.json', dict(at=now(), error=repr(error)))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'smoke', 'run', 'worker'))
    parser.add_argument('--job')
    args = parser.parse_args()
    if args.action == 'worker':
        module().worker(args.job)
    else:
        globals()[args.action]()
