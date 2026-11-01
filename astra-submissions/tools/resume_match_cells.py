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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--queue', type=Path, required=True)
    ap.add_argument('--original-receipt', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--slots', nargs='+', required=True)
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args()
    os.chdir(ROOT)
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
    rows = arena.ledger_games(match['id'])
    cells = missing_cells(match, rows, hashes)
    if original['attempted_jobs'] < len(rows):
        raise ValueError('receipt belongs to a later restart; supply the preserved original receipt')
    plan = {'matchup': match['id'], 'queue_sha256': digest(args.queue), 'archives': hashes,
            'recorded_before': len(rows), 'missing_cells': cells,
            'unrecorded_attempts_at_interruption': original['attempted_jobs'] - len(rows),
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
                still_missing = missing_cells(match, arena.ledger_games(match['id']), hashes)
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
                print(json.dumps(arena.summary(match)), flush=True)

    try:
        with ThreadPoolExecutor(max_workers=len(args.slots)) as pool:
            list(pool.map(worker, args.slots))
        status['missing_cells'] = missing_cells(match, arena.ledger_games(match['id']), hashes)
        status['state'] = 'complete' if not status['missing_cells'] else 'wall_cap'
    except BaseException:
        status['state'] = 'error'
        raise
    finally:
        status['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        status['summary'] = arena.summary(match)
        save_status()


if __name__ == '__main__':
    main()
