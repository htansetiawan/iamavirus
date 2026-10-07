#!/usr/bin/env python3
"""Validate the measurement apparatus before trusting it to measure anything.

Two things are checked, neither of which was ever checked before:

1. A configuration played against *itself* must score 0.5. Anything else means
   the harness has a colour, scoring or scheduling bias, and every A/B run
   through it inherits that bias.
2. How many of the games are actually distinct. The engine is nearly
   deterministic -- 64% of its decisions are taken with probability above 0.99 --
   so seeds may be producing the same game repeatedly. Repeated games are not
   independent samples: the true confidence interval is set by the number of
   distinct games, not the number played, so duplicates make the reported error
   bars too narrow and the conclusions too confident.
"""
import collections
import concurrent.futures
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile

KIT = os.path.dirname(os.path.abspath(__file__))
PYTHON = os.path.join(KIT, '.venv', 'bin', 'python')
BOT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/bot_v4'
SEEDS = int(sys.argv[2]) if len(sys.argv) > 2 else 16
BASE = sys.argv[3] if len(sys.argv) > 3 else '20'
INC = sys.argv[4] if len(sys.argv) > 4 else '0.3'
WORKERS = int(sys.argv[5]) if len(sys.argv) > 5 else 4


def play(seed, a_white):
    out = tempfile.mktemp(suffix='.json')
    a = f'/usr/bin/env FOW_SEED={seed} {BOT}'
    b = f'/usr/bin/env FOW_SEED={seed + 7777} {BOT}'
    cmd = [PYTHON, os.path.join(KIT, 'referee.py'), '--trusted-local',
           '--white', a if a_white else b, '--black', b if a_white else a,
           '--white-name', 'A' if a_white else 'B',
           '--black-name', 'B' if a_white else 'A',
           '--base-time', BASE, '--increment', INC,
           '--max-plies', '1000', '--output', out]
    try:
        subprocess.run(cmd, capture_output=True, timeout=1800, cwd=KIT)
        replay = json.load(open(out))
    except Exception as error:
        return None, None, str(error)
    finally:
        if os.path.exists(out):
            os.unlink(out)
    moves = [f['move'] for f in replay['frames'] if f.get('move')]
    signature = hashlib.sha1(' '.join(moves).encode()).hexdigest()[:10]
    result = replay['result']
    score = 0.5 if result == '1/2-1/2' else (1.0 if (result == '1-0') == a_white else 0.0)
    return score, (signature, len(moves)), None


jobs = [(s, w) for s in range(1, SEEDS + 1) for w in (True, False)]
scores, signatures, errors = [], [], []
with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
    for score, sig, err in pool.map(lambda j: play(*j), jobs):
        if err:
            errors.append(err)
            continue
        scores.append(score)
        signatures.append(sig)

n = len(scores)
rate = sum(scores) / n
counts = collections.Counter(s for s, _ in signatures)
distinct = len(counts)
# Binomial standard error if every game were independent, versus the honest one
# based on the number of distinct games actually produced.
naive = math.sqrt(rate * (1 - rate) / n) if 0 < rate < 1 else 0.0
honest = math.sqrt(rate * (1 - rate) / distinct) if 0 < rate < 1 and distinct else 0.0
print(f'self-test of {os.path.basename(BOT)} against itself, {BASE}+{INC}, '
      f'{WORKERS} workers')
print(f'  games played          : {n}')
print(f'  score (must be ~0.500): {rate:.3f}')
print(f'  distinct games        : {distinct} / {n}')
print(f'  most repeated game    : {counts.most_common(1)[0][1]} times')
print(f'  plies: min {min(p for _, p in signatures)} '
      f'median {sorted(p for _, p in signatures)[n//2]} '
      f'max {max(p for _, p in signatures)}')
print(f'  standard error if independent : +/- {naive:.3f}')
print(f'  standard error, distinct only : +/- {honest:.3f}')
if errors:
    print(f'  !! {len(errors)} errors: {errors[0][:70]}')
