"""Qualify bounded local Misty in two v38 games; candidate scores are absent."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/misty-bounded-health-20261110'
SOURCE = HERE.parent/'persistent-response-20261101/bench.py'
PILOT = ROOT/'astra-submissions/analysis/guard-controls-20261109/full-games'
PREVIOUS = ROOT/'astra-submissions/analysis/guard-opponent-clock-20261109'
PY = '/home/henrytan/fable-persist/scratchpad/misty/venv/bin/python'
sys.path[:0] = [str(ROOT), str(ROOT/'astra-submissions/tools')]
from learning import ingest, rules
from local_turn_control import cleanup_registry


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def now():
    return datetime.now(timezone.utc).isoformat()


def command(arm, seed):
    if arm == 'misty':
        return ['/usr/bin/env', f'FOW_SEED={seed}', 'FOW_REQUIRE_RUST=1', 'FOW_V2_CLOCK_TIME=1',
                'MISTY_PROFILE=v1.6', 'MISTY_BUDGET=0', f'ASTRA_MISTY_TELEMETRY_DIR={OUT}',
                'PATH=/home/henrytan/fable-persist/scratchpad/misty/bin:/usr/bin:/bin', PY, str(HERE/'adapter.py')]
    assert arm == 'base'
    base = json.loads((PILOT/'plan.json').read_text())['parent_build']
    return ['/usr/bin/env', f'FOW_SEED={seed}', '/bin/bash', str(Path(base)/'run.sh')]


def module():
    spec = importlib.util.spec_from_file_location('bounded_health_worker', SOURCE)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    result.HERE, result.OUT, result.command = HERE, OUT, command
    return result


def prepare():
    old = json.loads((PREVIOUS/'plan.json').read_text())
    stopped = json.loads((PREVIOUS/'audit-stopped.json').read_text())
    diagnostic = json.loads((ROOT/'astra-submissions/analysis/misty-belief-cost-20261109/200000/result.json').read_text())
    assert stopped['decision'] == 'technical_stop_inconclusive'
    assert diagnostic['completed'] and diagnostic['exit_code'] == 0 and diagnostic['max_positions'] == 200000
    for path, value in old['dependencies'].items():
        assert sha(path) == value, path
    OUT.mkdir(exist_ok=False)
    (HERE/'build').mkdir(exist_ok=False)
    shutil.copy2(ROOT.parent/'fow-starter/referee.py', HERE/'build/referee.py')
    deps = dict(old['dependencies'])
    paths = [Path(__file__), HERE/'adapter.py', HERE/'build/referee.py', SOURCE,
             PREVIOUS/'audit-stopped.json', ROOT/'astra-submissions/analysis/misty-belief-cost-20261109/200000/result.json']
    deps.update({str(p): sha(p) for p in paths})
    jobs = [dict(id=f'health-{side}', phase='health', lane=i, pair=i, side=side,
                 arm='base', opponent='misty', engine_seed=2771000+2*i, opponent_seed=2771001+2*i)
            for i, side in enumerate(('white', 'black'))]
    plan = dict(at=now(), dependencies=deps, jobs=jobs, lanes={'0': '0,1', '1': '2,3'},
                game_wall_cap=2450, batch_wall_cap=2700, cap=200000,
                gate='Both games normal and fault-free, clock/cap markers present, telemetry post-update population <=200000. '
                     'Scores do not determine qualification. No candidate games or release approval.',
                scope='Local deployment qualification, not a replica of current arena Misty. Finite cap changes the approximation; '
                      'no speed-only or playing-strength equivalence claim. Telemetry enabled only for this health check.')
    write(OUT/'plan.json', plan)
    module().load()
    print(json.dumps(dict(prepared=True, games=2, pins=len(deps))), flush=True)


def run():
    runner = module()
    plan = runner.load()
    started = time.monotonic()
    write(OUT/'started.json', dict(at=now(), pid=os.getpid(), plan_sha256=sha(OUT/'plan.json')))
    def execute(job):
        folder = OUT/'jobs'/job['id']
        folder.mkdir(parents=True, exist_ok=False)
        write(folder/'started.json', dict(at=now(), job=job))
        process = subprocess.Popen(['taskset', '-c', plan['lanes'][str(job['lane'])], sys.executable,
                                    str(Path(__file__)), 'worker', '--job', job['id']],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   env=runner.clean_env(), start_new_session=True)
        write(folder/'handle.json', dict(pid=process.pid,
              start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        clock = time.monotonic()
        try:
            stdout, stderr = process.communicate(timeout=plan['game_wall_cap'])
            timed_out = False
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            stdout, stderr = process.communicate()
        unverified = cleanup_registry(folder/'processes.json')
        (folder/'stdout.txt').write_text(stdout)
        (folder/'stderr.txt').write_text(stderr)
        faults = []
        game, stats = None, {}
        if process.returncode or timed_out or unverified or not (folder/'replay.json').exists():
            faults.append(f'worker_exit={process.returncode};timeout={timed_out};unverified={unverified}')
        else:
            game = json.loads((folder/'replay.json').read_text())
            _, errors = ingest.validate_replay(game)
            faults.extend(errors)
            if game.get('result') not in ('1-0', '0-1', '1/2-1/2') or game.get('reason') not in rules.NORMAL_REASONS:
                faults.append('non-normal result')
            if game.get('failedSide') or game.get('warnings'):
                faults.append('technical failure or capture warning')
            own = game['privateDiagnostics'].get(job['side'], '')
            other = 'black' if job['side'] == 'white' else 'white'
            theirs = game['privateDiagnostics'].get(other, '')
            if 'mist: stockfish ready' not in own:
                faults.append('native Stockfish initialization missing')
            if 'misty-clock: enabled=1 fixed=none budget180=5.000' not in theirs or 'misty-cap: states=200000' not in theirs:
                faults.append('Misty deployment assertion missing')
            if 'inadmissible engine move' in theirs:
                faults.append('adapter fallback used')
            controls = game.get('localTurnControl', {}).get('controls', [])
            if len(controls) != 2 or any(not any(e['op'] == 'freeze' for e in c['events']) for c in controls):
                faults.append('turn control missing')
            else:
                pid = controls[1 if job['side'] == 'white' else 0]['pid']
                telemetry = OUT/f'misty-{pid}.jsonl'
                if not telemetry.exists():
                    faults.append('Misty telemetry missing')
                else:
                    events = [json.loads(line) for line in telemetry.read_text().splitlines()]
                    stats = dict(events=len(events), max_post_positions=max((e['p_post'] for e in events), default=0),
                                 max_phase_ms=max((e['wall_ms'] for e in events), default=0),
                                 capped_updates=sum(bool(e.get('downsampled')) for e in events),
                                 path=str(telemetry), sha256=sha(telemetry))
                    if not events or stats['max_post_positions'] > 200000:
                        faults.append('population cap not observed/enforced')
        result = dict(at=now(), job=job, exit_code=process.returncode, timed_out=timed_out,
                      faults=faults, passed=not faults, elapsed_seconds=time.monotonic()-clock,
                      result=game['result'] if game else None, reason=game['reason'] if game else None,
                      plies=len(game['frames'])-1 if game else None, telemetry=stats,
                      files={p.name: sha(p) for p in folder.iterdir() if p.is_file()})
        write(folder/'result.json', result)
        print(json.dumps({k: v for k, v in result.items() if k != 'files'}), flush=True)
        return result
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(execute, plan['jobs']))
    write(OUT/'completion.json', dict(at=now(), qualified=len(rows) == 2 and all(r['passed'] for r in rows),
          completed=len(rows), elapsed_seconds=time.monotonic()-started,
          scope=plan['gate']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'run', 'worker'))
    parser.add_argument('--job')
    args = parser.parse_args()
    if args.action == 'worker':
        module().worker(args.job)
    else:
        globals()[args.action]()
