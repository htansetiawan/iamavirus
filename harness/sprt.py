#!/usr/bin/env python3
"""Sequential A/B testing between two engine configurations.

Three things make this trustworthy where the earlier harness was not.

Node budgets instead of a clock. A time-limited engine's strength depends on how
busy the machine is, so the number of parallel games was a hidden variable in
every previous result, and running more games to cut noise introduced a bias
instead. Counting nodes makes each decision reproducible and lets every core be
used.

A sequential test instead of a fixed batch. A fixed batch invites reading a 1-sigma
result as a direction, which is what happened repeatedly: three changes measured
+33, -47 and +51 and none of them was conclusive. The SPRT decides between two
explicit hypotheses with bounded error rates and stops as soon as the evidence
justifies it, so an unclear result is reported as unclear rather than squinted at.

Distinct-game accounting. Repeated games are not independent samples; the honest
confidence interval follows the number of distinct games, so they are counted.

Usage: sprt.py NAME_A NAME_B [options] -- A_ENV... -- B_ENV...
"""
import argparse
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


def log_likelihood_ratio(wins, draws, losses, elo0, elo1):
    """Normal-approximation LLR over a trinomial result, as used for engine tests.

    Positive values favour "the difference is at least elo1", negative favour
    "it is at most elo0".
    """
    total = wins + draws + losses
    if total == 0:
        return 0.0
    w, d = wins / total, draws / total
    score = w + d / 2.0
    variance = (w + d / 4.0) - score * score
    if variance <= 1e-12:
        return 0.0
    def expected(elo):
        return 1.0 / (1.0 + 10.0 ** (-elo / 400.0))
    s0, s1 = expected(elo0), expected(elo1)
    return total * (s1 - s0) * (2.0 * score - s0 - s1) / (2.0 * variance)


def play(binary, seed, a_white, env_a, env_b, node_budget, base, inc):
    out = tempfile.mktemp(suffix='.json')
    def command(env, bot_seed):
        settings = dict(pair.split('=', 1) for pair in env)
        settings['FOW_SEED'] = str(bot_seed)
        settings['FOW_NODE_BUDGET'] = str(node_budget)
        assignments = ' '.join(f'{k}={v}' for k, v in sorted(settings.items()))
        return f'/usr/bin/env {assignments} {binary}'
    a = command(env_a, seed)
    b = command(env_b, seed + 7777)
    cmd = [PYTHON, os.path.join(KIT, 'referee.py'), '--trusted-local',
           '--white', a if a_white else b, '--black', b if a_white else a,
           '--white-name', 'A' if a_white else 'B',
           '--black-name', 'B' if a_white else 'A',
           '--base-time', base, '--increment', inc,
           '--max-plies', '1000', '--output', out]
    try:
        subprocess.run(cmd, capture_output=True, timeout=3600, cwd=KIT)
        replay = json.load(open(out))
    except Exception as error:
        return None, None, f'{type(error).__name__}: {error}'
    finally:
        if os.path.exists(out):
            os.unlink(out)
    problems = []
    for side in ('white', 'black'):
        log = (replay.get('privateDiagnostics') or {}).get(side) or ''
        problems += [l for l in log.splitlines()
                     if 'error' in l.lower() or 'fatal' in l.lower()]
    moves = [f['move'] for f in replay['frames'] if f.get('move')]
    signature = hashlib.sha1(' '.join(moves).encode()).hexdigest()[:10]
    result = replay['result']
    if result == '1/2-1/2':
        score = 0.5
    else:
        score = 1.0 if (result == '1-0') == a_white else 0.0
    return score, signature, (problems[0][:70] if problems else None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name_a')
    parser.add_argument('name_b')
    parser.add_argument('--binary', default='/tmp/bot_nodes')
    parser.add_argument('--nodes', type=int, default=4000000)
    parser.add_argument('--elo0', type=float, default=0.0)
    parser.add_argument('--elo1', type=float, default=15.0)
    parser.add_argument('--alpha', type=float, default=0.05)
    parser.add_argument('--beta', type=float, default=0.05)
    parser.add_argument('--max-games', type=int, default=600)
    parser.add_argument('--workers', type=int, default=10)
    parser.add_argument('--base', default='300')
    parser.add_argument('--inc', default='0')
    parser.add_argument('rest', nargs=argparse.REMAINDER)
    args = parser.parse_args()

    splits = [i for i, a in enumerate(args.rest) if a == '--']
    env_a = args.rest[splits[0] + 1:splits[1]] if len(splits) > 1 else []
    env_b = args.rest[splits[1] + 1:] if len(splits) > 1 else []

    lower = math.log(args.beta / (1 - args.alpha))
    upper = math.log((1 - args.beta) / args.alpha)
    print(f'{args.name_a} vs {args.name_b}')
    print(f'  H0: <= {args.elo0:+.0f} Elo   H1: >= {args.elo1:+.0f} Elo   '
          f'bounds [{lower:.2f}, {upper:.2f}]   nodes/move {args.nodes:,}')

    wins = draws = losses = 0
    signatures = []
    problems = []
    seed = 0
    verdict = 'inconclusive (hit the game cap)'
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        while wins + draws + losses < args.max_games:
            batch = []
            for _ in range(max(2, args.workers)):
                seed += 1
                batch.append((seed, True))
                batch.append((seed, False))
            for score, sig, problem in pool.map(
                    lambda j: play(args.binary, j[0], j[1], env_a, env_b,
                                   args.nodes, args.base, args.inc), batch):
                if problem:
                    problems.append(problem)
                if score is None:
                    continue
                signatures.append(sig)
                if score == 1.0:
                    wins += 1
                elif score == 0.5:
                    draws += 1
                else:
                    losses += 1
            total = wins + draws + losses
            llr = log_likelihood_ratio(wins, draws, losses, args.elo0, args.elo1)
            rate = (wins + 0.5 * draws) / total
            elo = -400 * math.log10(1 / rate - 1) if 0 < rate < 1 else float('nan')
            print(f'  {total:4} games  {wins}W {losses}L {draws}D  '
                  f'score {rate:.3f}  ~{elo:+6.1f} Elo  LLR {llr:+.2f}')
            if llr >= upper:
                verdict = f'ACCEPT H1: better than {args.elo1:+.0f} Elo'
                break
            if llr <= lower:
                verdict = f'ACCEPT H0: not better than {args.elo0:+.0f} Elo'
                break

    total = wins + draws + losses
    rate = (wins + 0.5 * draws) / total if total else 0.0
    err = math.sqrt(rate * (1 - rate) / total) if 0 < rate < 1 else 0.0
    distinct = len(collections.Counter(signatures))
    print(f'  verdict: {verdict}')
    print(f'  final: {rate:.3f} +/- {err:.3f} over {total} games '
          f'({distinct} distinct)')
    if problems:
        print(f'  !! {len(problems)} internal errors: {problems[0]}')


if __name__ == '__main__':
    main()
