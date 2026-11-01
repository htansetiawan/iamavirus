#!/usr/bin/env python3
"""Recover an interrupted paired match by missing (pair, colour), never row count.

Uses the existing referee, ZIPs, seed convention and append-only game ledger.
Keeps the interrupted receipt intact and honours its ORIGINAL wall deadline.
No completed/failed recorded cell is replayed. Infrastructure interruptions
without a recorded outcome are reported separately, not scored as bot losses.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning import arena_local as arena, compare_archives as ca


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def missing_cells(match, rows, hashes):
    """Validate existing provenance before deriving the exact missing cells."""
    count = match['max_games']
    if count <= 0 or count % 2:
        raise ValueError('expected a positive even game cap')
    expected = [(p, c) for p in range(count // 2) for c in ('white', 'black')]
    occupied = set()
    for row in rows:
        cell = row['pair'], row['a_colour']
        if cell not in expected or cell in occupied:
            raise ValueError(f'duplicate or unexpected recorded cell: {cell}')
        if row['seed'] != int(match.get('seed', 20000)) + 2 * cell[0]:
            raise ValueError(f'seed mismatch: {cell}')
        for side in ('a', 'b'):
            if (row[side] != match[side] or row[side+'_sha'] != hashes[side][:12]
                    or row.get(side+'_env', []) != match.get(side+'_env', [])):
                raise ValueError(f'archive/environment mismatch: {cell} {side}')
        occupied.add(cell)
    return [cell for cell in expected if cell not in occupied]


def first_cells(match, rows, hashes):
    """An explicit audit view; never rewrite raw rows or choose the better result."""
    occupied = set(); retained = []; duplicates = []
    for row in rows:
        missing_cells(match, [row], hashes)  # validate even excluded-row provenance
        cell = row['pair'], row['a_colour']
        if cell in occupied:
            duplicates.append(row)
        else:
            occupied.add(cell); retained.append(row)
    return retained, duplicates


def unique_summary(match, hashes):
    raw = arena.ledger_games(match['id'])
    rows, duplicates = first_cells(match, raw, hashes)
    scores = [r['a_score'] for r in rows if r.get('a_score') is not None]
    wins = sum(s == 1 for s in scores); draws = sum(s == .5 for s in scores)
    counts = {}
    for r in rows:
        counts[r['pair']] = counts.get(r['pair'], 0)+1
    return {'raw_rows': len(raw), 'unique_cells': len(rows), 'duplicates_excluded': len(duplicates),
            'completed_pairs': sum(n == 2 for n in counts.values()), 'scored_games': len(scores),
            'failed': len(rows)-len(scores), 'w-d-l': f'{wins}-{draws}-{len(scores)-wins-draws}',
            'score': sum(scores)/len(scores) if scores else None}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--queue', type=Path, required=True)
    ap.add_argument('--original-receipt', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--slots', nargs='+', required=True)
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--reconcile-first', action='store_true',
                    help='explicitly retain the first recorded cell and preserve duplicates in the audit plan')
    args = ap.parse_args()
    os.chdir(ROOT)
    contaminated = [k for k in os.environ if k.startswith(('MIST_', 'FOW_'))]
    if contaminated:
        raise ValueError(f'undeclared experiment environment: {contaminated}')
    queue = json.loads(args.queue.read_text())
    if len(queue['matchups']) != 1:
        raise ValueError('recovery expects one immutable matchup')
    match = queue['matchups'][0]
    original = json.loads(args.original_receipt.read_text())
    if digest(args.queue) != original['queue_sha256']:
        raise ValueError('queue changed since original launch')
    if args.slots != original['slots']:
        raise ValueError('slots changed since original launch')
    deadline = (dt.datetime.fromisoformat(original['started_at'].replace('Z', '+00:00')).timestamp()
                + original['wall_hours'] * 3600)
    hashes = {s: digest(match[s]) for s in ('a', 'b')}
    raw_rows = arena.ledger_games(match['id'])
    rows, duplicates = first_cells(match, raw_rows, hashes) if args.reconcile_first else (raw_rows, [])
    cells = missing_cells(match, rows, hashes)
    receipt_start = dt.datetime.fromisoformat(original['started_at'].replace('Z', '+00:00'))
    since_receipt = [r for r in raw_rows if dt.datetime.fromisoformat(r['ts'].replace('Z', '+00:00')) >= receipt_start]
    if original['attempted_jobs'] < len(since_receipt):
        raise ValueError('receipt attempts cannot account for its recorded rows')
    plan = {'matchup': match['id'], 'queue_sha256': digest(args.queue), 'archives': hashes,
            'recorded_before': len(rows), 'missing_cells': cells,
            'raw_rows_before': len(raw_rows), 'duplicates_excluded': duplicates,
            'reconciliation': 'first recorded cell, never best score' if args.reconcile_first else None,
            'unrecorded_attempts_at_interruption': original['attempted_jobs'] - len(since_receipt),
            'original_deadline': dt.datetime.fromtimestamp(deadline, dt.timezone.utc).isoformat(),
            'slots': args.slots, 'original_receipt': original}
    print(json.dumps(plan, indent=2), flush=True)
    if not args.execute or not cells:
        return
    if time.time() + arena.GAME_BOUND_SECONDS >= deadline:
        raise ValueError('no complete game fits the original wall cap')
    # Reject a second runner, including the ordinary runner which uses no lock.
    for proc in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            argv = proc.read_bytes().split(b'\0')
        except OSError:
            continue
        if b'learning.arena_local' in argv and b'run' in argv:
            raise RuntimeError('another arena_local runner is live; recovery refused')
    args.out.mkdir(parents=True, exist_ok=True)
    lockfile = (args.out/'run.lock').open('w')
    fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
    # Never replace an earlier recovery receipt; a second recovery needs its own directory.
    with (args.out/'plan.json').open('x') as f:
        json.dump(plan, f, indent=2)
    (args.out/'ledger-before.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    status = {'state': 'building', 'pid': os.getpid(), 'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
              'started_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'original_deadline': plan['original_deadline'],
              'started_cells': [], 'completed_cells': [], 'failed_cells': [], 'slots': args.slots}
    mutex = threading.Lock()

    def save_status():
        temp = args.out/'status.tmp'
        temp.write_text(json.dumps(status, indent=2)+'\n')
        temp.replace(args.out/'status.json')

    save_status()
    binaries = {s: ca.build(Path(match[s]), args.out/'builds') for s in ('a', 'b')}
    pending = list(cells)
    status['state'] = 'running'; save_status()

    def worker(slot):
        while True:
            with mutex:
                if not pending or time.time() + arena.GAME_BOUND_SECONDS >= deadline:
                    return
                pair, color = pending.pop(0)
                # Also catches an unexpected outside ledger writer before scheduling.
                current = arena.ledger_games(match['id'])
                if args.reconcile_first:
                    current, extra = first_cells(match, current, hashes)
                    if len(extra) != len(duplicates):
                        raise RuntimeError('new duplicate from an outside writer; stopping recovery')
                still_missing = missing_cells(match, current, hashes)
                if (pair, color) not in still_missing:
                    raise RuntimeError('cell already recorded by another runner')
                status['started_cells'].append([pair, color]); save_status()
            seed = int(match.get('seed', 20000)) + 2 * pair
            white, black = ('a', 'b') if color == 'white' else ('b', 'a')
            replay = args.out/f'pair-{pair}-{color}.json'
            try:
                game = ca.play(binaries[white], binaries[black], seed, arena.KIT, replay, slot,
                               ' '.join(match.get(white+'_env', [])), ' '.join(match.get(black+'_env', [])),
                               timeout=deadline-time.time()-arena.CLEANUP_RESERVE_SECONDS)
            except Exception as exc:
                game = {'result': '*', 'reason': f'recovery runner error: {exc!r}', 'plies': 0, 'seconds': 0, 'clocks': None}
            score = {'1-0': 1., '0-1': 0., '1/2-1/2': .5}.get(game['result'])
            score = (score if color == 'white' else 1-score) if score is not None else None
            row = {'matchup': match['id'], 'pair': pair, 'seed': seed, 'a_colour': color,
                   'a_score': score, 'attempt': 'ok' if score is not None else 'failed',
                   'result': game['result'], 'reason': game['reason'], 'plies': game['plies'],
                   'seconds': round(game['seconds'], 1), 'clocks': game['clocks'], 'slot': slot,
                   'a': match['a'], 'b': match['b'], 'a_sha': hashes['a'][:12], 'b_sha': hashes['b'][:12],
                   'a_env': match.get('a_env', []), 'b_env': match.get('b_env', []),
                   'ts': dt.datetime.now(dt.timezone.utc).isoformat(), 'replay': str(replay),
                   'recovery_receipt': str(args.out/'plan.json')}
            with mutex:
                with arena.LEDGER.open('a') as f:
                    f.write(json.dumps(row)+'\n'); f.flush(); os.fsync(f.fileno())
                status['completed_cells'].append([pair, color])
                if score is None:
                    status['failed_cells'].append([pair, color])
                save_status()
                print(json.dumps(unique_summary(match, hashes)), flush=True)

    try:
        with ThreadPoolExecutor(max_workers=len(args.slots)) as pool:
            list(pool.map(worker, args.slots))
        current, excluded = first_cells(match, arena.ledger_games(match['id']), hashes)
        status['missing_cells'] = missing_cells(match, current, hashes)
        status['state'] = 'complete' if not status['missing_cells'] else 'wall_cap'
    except BaseException:
        status['state'] = 'error'
        raise
    finally:
        status['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        status['summary'] = unique_summary(match, hashes)
        save_status()


if __name__ == '__main__':
    main()
