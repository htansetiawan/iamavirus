#!/usr/bin/env python3
"""Post-hoc component attribution on the fresh gate's three regression cases.

The existing MIST_TRUTH_SEQ hook prints support/weight only; these diagnostic
runs are kept separate from the observation-only comparison and its scores.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning import ingest, compare_archives as ca
from fresh_taxonomy_gate import protocol, exchange_probe


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('directory', type=Path)
    args = ap.parse_args(); out = args.directory.resolve()
    rows = [json.loads(l) for l in (out/'results.jsonl').read_text().splitlines()]
    cases = []
    for row in rows:
        a, b = row['arms']['v35'], row['arms']['v37']
        if ('error' in a or 'error' in b):
            continue
        if (b.get('fatal', False) and not a.get('fatal', False)) or ((b.get('exchange_loss') or 0) >= 2 > (a.get('exchange_loss') or 0)):
            cases.append(row['case'])
    builds = {35: out/'builds/iamavirus-v35-mist-c-v14', 37: out/'builds/iamavirus-v37-mist-c-v14-allfit'}
    arms = {'v35': (35,35), 'new_weights_only': (37,35), 'new_table_only': (35,37), 'v37': (37,37)}
    plan = {'cases': cases, 'arms': arms, 'base_seed': 11012026,
            'extra_policy_seeds': [11012027,11012028], 'seconds': 2.5,
            'post_hoc': True, 'truth_hook': 'diagnostic print-only MIST_TRUTH_SEQ, component arms only',
            'source_results_sha256': hashlib.sha256((out/'results.jsonl').read_bytes()).hexdigest()}
    for version, directory in builds.items():
        plan[f'v{version}_hashes'] = {name: hashlib.sha256((directory/name).read_bytes()).hexdigest()
                                    for name in ('mist', 'data/history.bin', 'bin/stockfish', 'src/main.c')}
    with (out/'diagnostic-plan.json').open('x') as f:
        json.dump(plan, f, indent=2)
    results = []
    with (out/'diagnostics.jsonl').open('x') as sink:
        for case in cases:
            payload = Path(case['replay_path']).read_bytes()
            assert hashlib.sha256(payload).hexdigest() == case['replay_sha256']
            rp = json.loads(payload); states, problems = ingest.validate_replay(rp); assert not problems
            ply = case['ply']; side = ('white','black').index(case['side'])
            feed, forced = protocol(rp, ply, side)
            jobs = [(name, 11012026, True) for name in arms]
            jobs += [(name, seed, False) for seed in plan['extra_policy_seeds'] for name in ('v35', 'v37')]
            for name, seed, trace in jobs:
                model, table = arms[name]; directory = builds[model]
                env = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_', 'FOW_'))}
                env.update(FOW_SEED=str(seed), MIST_FORCE_MOVES=','.join(forced), MIST_MAX_SECONDS='2.5',
                           MIST_STOCKFISH=str(directory/'bin/stockfish'), MIST_HISTORY_TABLE=str(builds[table]/'data/history.bin'))
                if trace:
                    env['MIST_TRUTH_SEQ'] = ','.join(f['board'] for f in rp['frames'][:ply+1])
                proc = subprocess.Popen(['taskset', '-c', '0,1', str(directory/'mist')], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
                try:
                    stdout, stderr = proc.communicate(feed, timeout=180)
                except subprocess.TimeoutExpired:
                    ca.kill_tree(proc.pid); proc.wait(); raise
                moves = [s[5:].strip() for s in stdout.splitlines() if s.startswith('move ')]
                assert proc.returncode == 0 and len(moves) == len(forced)+1 and moves[:-1] == forced
                truth = [s for s in stderr.splitlines() if s.startswith('mist: truth')]
                result = {'game': case['game'], 'ply': ply, 'arm': name, 'seed': seed, 'truth_diagnostic': trace,
                          'move': moves[-1], 'truth': truth[-1] if truth else None, **exchange_probe(states[ply], moves[-1])}
                log = out/'logs'/f"diagnostic-{case['game']}-{ply}-{name}-{seed}.stderr"
                log.write_text(stderr)
                result['last_search'] = next((s for s in reversed(stderr.splitlines()) if s.startswith('mist: n=')), None)
                sink.write(json.dumps(result)+'\n'); sink.flush(); results.append(result)
                print(result, flush=True)
    (out/'diagnostic-summary.json').write_text(json.dumps(results, indent=2)+'\n')


if __name__ == '__main__':
    main()
