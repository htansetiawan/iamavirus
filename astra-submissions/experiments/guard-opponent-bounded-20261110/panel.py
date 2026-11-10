"""Fresh matched comparison, conditional on score-independent deployment health."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/guard-opponent-bounded-20261110'
HEALTH = ROOT/'astra-submissions/analysis/misty-bounded-health-20261110'
SOURCE = HERE.parent/'guard-opponent-20261109/panel.py'
ADAPTER = HERE.parent/'misty-bounded-health-20261110/adapter.py'
spec = importlib.util.spec_from_file_location('bounded_guard_panel', SOURCE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.HERE, base.OUT, base.__file__ = HERE, OUT, str(Path(__file__))
original_command, original_inspect = base.command, base.inspect


def command(arm, seed):
    if arm == 'misty':
        return ['/usr/bin/env', f'FOW_SEED={seed}', 'FOW_REQUIRE_RUST=1', 'FOW_V2_CLOCK_TIME=1',
                'MISTY_PROFILE=v1.6', 'MISTY_BUDGET=0', f'ASTRA_MISTY_TELEMETRY_DIR={OUT / "telemetry"}',
                f'PATH={base.MISTY_BIN}:/usr/bin:/bin', str(base.MISTY_PY), str(ADAPTER)]
    return original_command(arm, seed)


def inspect(job, directory):
    result = original_inspect(job, directory)
    game = json.loads((directory/'replay.json').read_text())
    side = 'black' if job['side'] == 'white' else 'white'
    diag = game['privateDiagnostics'].get(side, '')
    if ('misty-clock: enabled=1 fixed=none budget180=5.000' not in diag
            or 'misty-cap: states=200000' not in diag):
        result['faults'].append('Misty deployment assertion missing')
    controls = game.get('localTurnControl', {}).get('controls', [])
    if len(controls) == 2:
        pid = controls[1 if job['side'] == 'white' else 0]['pid']
        path = OUT/'telemetry'/f'misty-{pid}.jsonl'
        if not path.exists():
            result['faults'].append('Misty telemetry missing')
        else:
            events = [json.loads(line) for line in path.read_text().splitlines()]
            result['telemetry'] = dict(path=str(path), sha256=base.sha(path), events=len(events),
                max_post_positions=max((e['p_post'] for e in events), default=0),
                capped_updates=sum(bool(e.get('downsampled')) for e in events),
                max_raw_positions=max((e.get('p_raw', 0) or 0 for e in events), default=0),
                max_phase_ms=max((e['wall_ms'] for e in events), default=0))
            if not events or result['telemetry']['max_post_positions'] > 200000:
                result['faults'].append('Misty population cap not observed/enforced')
    return result


base.command, base.inspect = command, inspect


def prepare():
    audit = json.loads((HEALTH/'audit.json').read_text())
    cleanup = json.loads((HEALTH/'cleanup.json').read_text())
    assert audit['qualified'] and audit['completed'] == 2
    assert cleanup['live_owned_actors'] == []
    old = json.loads((HEALTH/'plan.json').read_text())
    for path, value in old['dependencies'].items():
        assert base.sha(path) == value, path
    OUT.mkdir(exist_ok=False)
    (OUT/'telemetry').mkdir()
    (OUT/'preflight-telemetry').mkdir()
    (HERE/'build').mkdir(exist_ok=False)
    import shutil
    shutil.copy2(ROOT.parent/'fow-starter/referee.py', HERE/'build/referee.py')
    deps = dict(old['dependencies'])
    deps.update({str(p): base.sha(p) for p in [Path(__file__), SOURCE, ADAPTER,
        HERE/'build/referee.py', HEALTH/'audit.json', HEALTH/'cleanup.json', HEALTH/'preflight/result.json']})
    jobs = []
    for pair in range(8):
        for side in ('white', 'black'):
            order = ('base', 'candidate') if (pair+(side == 'black')) % 2 == 0 else ('candidate', 'base')
            for arm in order:
                jobs.append(dict(id=f'p{pair}-{side}-{arm}', phase='misty', pair=pair, lane=pair % 3,
                                 arm=arm, side=side, opponent='misty',
                                 engine_seed=2802000+2*pair, opponent_seed=2802001+2*pair))
    plan = dict(at=base.now(), dependencies=deps, jobs=jobs, lanes={'0': '0,1', '1': '2,3', '2': '4,5'},
                game_wall_cap=2450, batch_wall_cap=14400, time_control=dict(base=180, increment=2, max_plies=1000),
                misty_version='0.1.3', misty_profile='v1.6', native_required=True,
                misty_deployment=dict(clock_time=True, fixed_budget=None, population_cap=200000,
                                      telemetry=True, health_audit_sha256=base.sha(HEALTH/'audit.json')),
                gate=dict(games=32, per_arm=16, candidate_min_points=8, candidate_min_advantage_points=2,
                          technical_faults=0),
                resume='No started first attempt is repeated. Technical fault stops new games; in-flight may finish.',
                order='Eight fresh seed blocks, both colors and arms; alternate first arm; same seeds in matched cells.',
                scope='Bounded local Brian Liou Misty, qualified without using scores. Not exact current arena bytes '
                      'or Brian Hu Zhang Obscuro. Pass earns review only, no Elo proof or automatic upload.',
                fairness='Two reserved cores per lane; groups frozen off turn; buffered observations charged on turn.',
                prior_attempts='274 wrong clock closed; 275 late uncapped resource fault closed. '
                               'Their original results remain; neither run is resumed or counted here.')
    base.write(OUT/'plan.json', plan)
    base.module().load()
    print(json.dumps(dict(prepared=True, jobs=32, pins=len(deps))), flush=True)


def smoke():
    base.module().load()
    sys.path.insert(0, str(ROOT.parent/'fow-starter'))
    import referee
    os.sched_setaffinity(0, {4, 5})
    fresh = base.clean_env()
    os.environ.clear()
    os.environ.update(fresh)
    def expired(*_):
        raise TimeoutError('Full-clock protocol probe exceeded 30 seconds')
    old_handler = signal.signal(signal.SIGALRM, expired)
    rows, error = [], None
    try:
        for arm in ('base', 'candidate', 'misty'):
            for side in (True, False):
                bot, row = None, dict(arm=arm, side='white' if side else 'black')
                signal.setitimer(signal.ITIMER_REAL, 30)
                try:
                    args = command(arm, 2801000)
                    if arm == 'misty':
                        args = [f'ASTRA_MISTY_TELEMETRY_DIR={OUT / "preflight-telemetry"}'
                                if x.startswith('ASTRA_MISTY_TELEMETRY_DIR=') else x for x in args]
                    if arm != 'misty':
                        args = ['/usr/bin/env', 'MIST_MAX_SECONDS=.1', *args]
                    bot = referee.Bot(args, side, 180, 2, initialization_timeout=15)
                    board = referee.FowBoard()
                    bot.observe(referee.observation(board, side), 0)
                    if not side:
                        board.push_uci('d2d4')
                        bot.observe(referee.observation(board, side), 1)
                    move, elapsed = bot.move(180)
                    assert referee.chess.Move.from_uci(move) in referee.fow_moves(board)
                    row.update(move=move, elapsed_seconds=elapsed)
                    if arm == 'misty':
                        assert elapsed < 15
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    if bot is not None:
                        bot.close()
                        row.update(stderr=bot.stderr_excerpt.decode(), failure=bot.failure,
                                   live_owned_members=[r for r in base.group_members(bot.proc.pid) if r['state'] not in ('Z', 'X')])
                    rows.append(row)
                assert bot is not None and bot.failure is None and not row['live_owned_members']
                assert 'inadmissible engine move' not in row['stderr']
                if arm == 'misty':
                    assert 'misty-clock: enabled=1 fixed=none budget180=5.000' in row['stderr']
                    assert 'misty-cap: states=200000' in row['stderr']
                else:
                    assert 'mist: stockfish ready' in row['stderr']
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
        base.write(OUT/'smoke.json', dict(at=base.now(), passed=error is None, error=error, records=rows,
                   scope='Actual new commands in both colors, full-clock Misty; protocol/runtime only.'))
    print(json.dumps(dict(smoke_passed=True, probes=len(rows))), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'smoke', 'run', 'worker'))
    parser.add_argument('--job')
    args = parser.parse_args()
    if args.action == 'worker':
        base.module().worker(args.job)
    elif args.action == 'run':
        base.run()
    else:
        globals()[args.action]()
