#!/usr/bin/env python3
"""Seeded belief diagnostics, with durable per-run completion and failure records.

This does not measure playing strength: every arm receives the same recorded
actor observations and own moves. Hidden truth is used only for labels.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', type=Path, required=True)
    parser.add_argument('--release-probe', type=Path)
    parser.add_argument('--moves-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--seeds', type=int, nargs='+', default=[1, 2, 3, 777])
    parser.add_argument('--cases', nargs='+', default=['xidde3fz:1', 'ea9ds6vw:1', 'al0xlrqe:0'])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    binaries = {'control': args.probe.resolve(), 'history': args.probe.resolve()}
    if args.release_probe:
        binaries['deployed'] = args.release_probe.resolve()
    hashes = {arm: sha(path) for arm, path in binaries.items()}
    jobs = []
    for case in args.cases:
        game, side = case.split(':')
        moves = (args.moves_dir / f'{game}-moves.txt').resolve()
        for arm in binaries:
            if arm == 'deployed' and game != 'xidde3fz':
                continue
            for seed in args.seeds:
                command = [str(binaries[arm]), str(moves), side, str(seed), '2048']
                if arm != 'deployed':
                    command += ['1', '1', '1', '1', str(int(arm == 'history'))]
                jobs.append(dict(game=game, side=int(side), arm=arm, seed=seed,
                                 command=command, binary_sha256=hashes[arm],
                                 moves_sha256=sha(moves), expected_updates=len(moves.read_text().split()),
                                 deductions=True, grouped=arm != 'deployed',
                                 continuation=arm != 'deployed', history=arm == 'history'))
    manifest = dict(started_at=datetime.now(timezone.utc).isoformat(), status='running',
                    interpretation='Controlled replay diagnostics, not actual arena internals or strength evidence',
                    tracked_squares=[18], jobs=jobs, runs=[])

    def save():
        tmp = args.output / 'state.tmp'
        tmp.write_text(json.dumps(manifest, indent=2) + '\n')
        tmp.replace(args.output / 'state.json')

    save()

    def run(job):
        name = f"{job['game']}-{job['arm']}-{job['seed']}"
        path = args.output / (name + '.jsonl')
        log = args.output / (name + '.stderr')
        start = time.monotonic()
        with path.open('w') as out, log.open('w') as err:
            proc = subprocess.run(job['command'], stdout=out, stderr=err,
                                  env={**os.environ, 'ASTRA_PROBE_SQUARES': '18'}, timeout=600)
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        actor = [r for r in rows if 'actual_move' in r]
        bad_views = [r['ply'] for r in rows if r['exact_observation_matches'] != r['particles']]
        collapsed = [r for r in rows if r['collapsed']]
        hidden = sum(r['hidden_squares'] for r in rows)
        result = dict(job, trace=str(path), trace_sha256=sha(path), returncode=proc.returncode,
                      elapsed_seconds=time.monotonic() - start, updates=len(rows),
                      complete=proc.returncode == 0 and len(rows) == job['expected_updates'],
                      view_mismatch_plies=bad_views,
                      collapses=len(collapsed), random_rebuilds=sum(not r.get('history_recovered', False) for r in collapsed),
                      history_rescues=sum(r.get('history_recovered', False) for r in rows),
                      full_certified_updates=sum(r.get('history_full_certified', False) for r in rows),
                      history_budget_exhausted_updates=sum(r.get('history_budget_exhausted', False) for r in rows),
                      history_transitions=sum(r.get('history_transitions', 0) for r in rows),
                      truth_held_updates=sum(r['truth_board_matches'] > 0 for r in rows),
                      hidden_brier=sum(r['hidden_brier_sum'] for r in rows) / max(1, hidden),
                      hidden_log_loss=sum(r['hidden_log_loss_sum'] for r in rows) / max(1, hidden),
                      continuation_invalid_updates=sum(r['continuation_invalid_particles'] > 0 for r in rows),
                      max_observe_ms=max((r['observe_ms'] for r in rows), default=0),
                      final_actor=actor[-1] if actor else None)
        return result

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run, job): job for job in jobs}
        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception as exc:
                result = dict(futures[future], complete=False, error=repr(exc))
            manifest['runs'].append(result)
            save()
            print(json.dumps({k: result.get(k) for k in ('game', 'arm', 'seed', 'complete', 'collapses', 'random_rebuilds', 'history_rescues', 'truth_held_updates', 'view_mismatch_plies')}), flush=True)
    unchanged = all(sha(binaries[arm]) == value for arm, value in hashes.items())
    manifest['binaries_unchanged'] = unchanged
    manifest['status'] = 'complete' if unchanged and all(r['complete'] for r in manifest['runs']) else 'failed'
    manifest['completed_at'] = datetime.now(timezone.utc).isoformat()
    save()
    if manifest['status'] != 'complete':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
