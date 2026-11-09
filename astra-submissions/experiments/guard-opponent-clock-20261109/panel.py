"""Fresh queue after an invalid opponent-clock setup; retain the failed run."""
from datetime import datetime, timezone, timedelta
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/guard-opponent-clock-20261109'
SOURCE = HERE.parent/'guard-opponent-20261109/panel.py'
CHECKED = HERE/'checked_adapter.py'
PREVIOUS = ROOT/'astra-submissions/analysis/guard-opponent-20261109'
spec = importlib.util.spec_from_file_location('clock_panel_base', SOURCE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.HERE, base.OUT, base.__file__ = HERE, OUT, str(Path(__file__))
original_command, original_inspect = base.command, base.inspect


def command(arm, seed):
    args = original_command(arm, seed)
    if arm == 'misty':
        assert args.count('FOW_V2_CLOCK_TIME=0') == 1
        assert args[-1] == str(base.ADAPTER)
        args = ['FOW_V2_CLOCK_TIME=1' if x == 'FOW_V2_CLOCK_TIME=0' else x for x in args]
        args[-1] = str(CHECKED)
    return args


def inspect(job, directory):
    result = original_inspect(job, directory)
    replay = json.loads((directory/'replay.json').read_text())
    side = 'black' if job['side'] == 'white' else 'white'
    text = replay.get('privateDiagnostics', {}).get(side, '')
    if 'misty-clock: enabled=1 fixed=none budget180=' not in text:
        result['faults'].append('Misty clock-configuration assertion missing')
    return result


base.command, base.inspect = command, inspect


def prepare():
    previous = json.loads((PREVIOUS/'completion.json').read_text())
    assert previous['completed'] == 3 and not previous['gate_pass'] and not previous['clean']
    assert json.loads((PREVIOUS/'technical-audit.json').read_text())['valid_strength_games'] == 0
    base.prepare()
    path = OUT/'plan.json'
    plan = json.loads(path.read_text())
    for job in plan['jobs']:
        job['engine_seed'] += 10000
        job['opponent_seed'] += 10000
    for source in [SOURCE, CHECKED, PREVIOUS/'completion.json', PREVIOUS/'technical-audit.json']:
        plan['dependencies'][str(source)] = base.sha(source)
    plan['opponent_clock'] = dict(enabled=True, fixed_budget=None, expected_initial_seconds=5,
                                  prior_invalid_flag='FOW_V2_CLOCK_TIME=0 with no fixed budget',
                                  prior_result='Three first-turn opponent timeouts, zero valid strength games; not resumed')
    plan['preflight'] = 'Full 180-second inputs, two actual Misty turns per color with its live clock manager; 30-second per-probe watchdog.'
    path.write_text(json.dumps(plan, indent=2)+'\n')
    base.module().load()
    print(json.dumps(dict(clock_plan_prepared=True, jobs=len(plan['jobs']), pins=len(plan['dependencies']))), flush=True)


def smoke():
    base.module().load()
    sys.path.insert(0, str(ROOT.parent/'fow-starter'))
    import referee
    from local_turn_control import group_members
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
                bot, row = None, dict(arm=arm, side='white' if side else 'black', turns=[])
                signal.setitimer(signal.ITIMER_REAL, 30)
                try:
                    args = command(arm, 2751000)
                    if arm != 'misty':
                        args = ['/usr/bin/env', 'MIST_MAX_SECONDS=.1', *args]
                    bot = referee.Bot(args, side, 180, 2, initialization_timeout=15)
                    board, remaining = referee.FowBoard(), 180.0
                    bot.observe(referee.observation(board, side), 0)
                    for _ in range(2 if arm == 'misty' else 1):
                        if board.turn != side:
                            legal = list(referee.fow_moves(board))
                            preferred = 'e2e4' if board.turn else 'e7e5'
                            other = next((m for m in legal if m.uci() == preferred), legal[0])
                            board.push(other)
                            bot.observe(referee.observation(board, side), len(board.move_stack))
                        uci, elapsed = bot.move(remaining)
                        assert referee.chess.Move.from_uci(uci) in referee.fow_moves(board)
                        if arm == 'misty':
                            assert elapsed < 15, 'clock manager did not bound the turn'
                        row['turns'].append(dict(move=uci, sent_clock=remaining, elapsed_seconds=elapsed))
                        remaining = remaining-elapsed+2
                        board.push_uci(uci)
                        bot.observe(referee.observation(board, side), len(board.move_stack))
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    if bot is not None:
                        bot.close()
                        row.update(stderr=bot.stderr_excerpt.decode(), failure=bot.failure,
                                   live_owned_members=[r for r in group_members(bot.proc.pid) if r['state'] not in ('Z', 'X')])
                    rows.append(row)
                assert bot is not None and bot.failure is None and not row['live_owned_members']
                assert 'inadmissible engine move' not in row['stderr']
                if arm == 'misty':
                    assert 'misty-clock: enabled=1 fixed=none budget180=5.000' in row['stderr']
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
        base.write(OUT/'smoke.json', dict(at=base.now(), passed=error is None, error=error, records=rows,
                                        scope='Protocol/runtime preflight with real full-clock opponent budgeting, not a playing-strength result'))
    print(json.dumps(dict(full_clock_smoke_passed=True, probes=len(rows), misty_turns=4)), flush=True)


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
