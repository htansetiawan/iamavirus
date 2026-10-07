#!/usr/bin/env python3
"""Run a bot configuration against the baseline over many seeds, both colours.

Usage: arena.py LABEL SEEDS [KEY=VALUE ...]

Games run in parallel at a shortened time control so a configuration can be
measured in a couple of minutes. Any line containing "error" in our own stderr
makes the run fail outright: a bot whose every move throws still plays legal
fallback moves, so a silent exception is indistinguishable from weak play.
"""
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import tempfile

KIT = os.path.dirname(os.path.abspath(__file__))
PYTHON = os.path.join(KIT, '.venv', 'bin', 'python')
BOT = '/Users/henrytan/Documents/git/MIT-6.7980-Topics-in-Multiagent-Learning/fog/bot/bot.py'
BASE_TIME = os.environ.get('FOW_ARENA_BASE', '40')
INCREMENT = os.environ.get('FOW_ARENA_INCREMENT', '0.5')


def play(seed, mine_is_white, env):
    out = tempfile.mktemp(suffix='.json', dir=tempfile.gettempdir())
    mine = f'{PYTHON} -u {BOT}'
    base = f'{PYTHON} -u {os.path.join(KIT, "baseline.py")} --seed {seed}'
    cmd = [PYTHON, os.path.join(KIT, 'referee.py'), '--trusted-local',
           '--white', mine if mine_is_white else base,
           '--black', base if mine_is_white else mine,
           '--white-name', 'Mine' if mine_is_white else 'Base',
           '--black-name', 'Base' if mine_is_white else 'Mine',
           '--base-time', BASE_TIME, '--increment', INCREMENT,
           '--max-plies', '1000', '--output', out]
    merged = dict(os.environ, **env)
    try:
        subprocess.run(cmd, capture_output=True, timeout=900, env=merged, cwd=KIT)
        replay = json.load(open(out))
    except Exception as error:
        return {'verdict': 'ERROR', 'problems': [f'{type(error).__name__}: {error}'],
                'plies': 0, 'depths': [], 'clock': 0.0}
    finally:
        if os.path.exists(out):
            os.unlink(out)
    side = 'white' if mine_is_white else 'black'
    result = replay['result']
    if result == '1/2-1/2':
        verdict = 'DRAW'
    else:
        verdict = 'WIN' if (result == '1-0') == mine_is_white else 'LOSS'
    log = (replay.get('privateDiagnostics') or {}).get(side) or ''
    problems = [line for line in log.splitlines() if 'error' in line.lower()]
    return {'verdict': verdict, 'problems': problems,
            'plies': len(replay['frames']) - 1,
            'depths': [int(d) for d in re.findall(r'depth=(\d+)', log)],
            'clock': replay['frames'][-1]['clocks'][0 if mine_is_white else 1],
            'reason': replay['reason']}


def main():
    label, seeds = sys.argv[1], int(sys.argv[2])
    env = dict(pair.split('=', 1) for pair in sys.argv[3:])
    jobs = [(seed, white) for seed in range(1, seeds + 1) for white in (True, False)]
    tally = {'WIN': 0, 'LOSS': 0, 'DRAW': 0, 'ERROR': 0}
    problems, depths, plies, clocks = [], [], [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        for outcome in pool.map(lambda job: play(job[0], job[1], env), jobs):
            tally[outcome['verdict']] += 1
            problems += outcome['problems']
            depths += outcome['depths']
            plies.append(outcome['plies'])
            clocks.append(outcome['clock'])
    total = tally['WIN'] + tally['LOSS'] + tally['DRAW']
    score = (tally['WIN'] + 0.5 * tally['DRAW']) / total if total else 0.0
    print(f"{label:28} {tally['WIN']:3}W {tally['LOSS']:3}L {tally['DRAW']:3}D "
          f"score={score:.3f} depth~{sorted(depths)[len(depths)//2] if depths else 0} "
          f"plies~{sorted(plies)[len(plies)//2] if plies else 0} "
          f"minclock={min(clocks) if clocks else 0:.1f}"
          + (f"  !! {len(problems)} ERRORS: {problems[0][:60]}" if problems else ""))
    return 1 if problems or tally['ERROR'] else 0


if __name__ == '__main__':
    sys.exit(main())
