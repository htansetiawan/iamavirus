#!/usr/bin/env python3
"""Freeze, cache and validate a bounded all-outcome public replay snapshot.

Existing shared raw data is read only. New raw files and exact rules receipts
belong in an independent output directory. No training split is changed here.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'astra-submissions'), str(ROOT)]

from learning import ingest
from learning_experiments.run import isolate_rules
from monitor_arena import Client, Deferred, write_json


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cache', type=Path, default=ROOT / 'data/raw/games')
    parser.add_argument('--limit', type=int, default=500)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('limit must be positive')
    output = args.output.resolve()
    if output.exists() and not args.resume:
        parser.error('output exists; use --resume or a new snapshot directory')
    output.mkdir(parents=True, exist_ok=True)
    source_paths = [Path(__file__), Path(__file__).with_name('monitor_arena.py'),
                    ROOT / 'astra-submissions/learning_experiments/run.py',
                    ROOT / 'learning/ingest.py', ROOT / 'learning/rules.py',
                    ROOT / 'learning/histories.py', ROOT / 'learning/_native.py']
    source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in source_paths}
    identity = {'limit': args.limit, 'cache': str(args.cache.resolve()), 'source_sha256': source_hashes}
    receipt_path = output / 'collection.json'
    if receipt_path.exists():
        previous = json.loads(receipt_path.read_text())
        if previous['identity'] != identity:
            parser.error('collection source/options changed; use a fresh output directory')
        if previous['state'] == 'complete':
            parser.error('snapshot already completed')
    native = isolate_rules(output)
    client = Client()
    receipt = {'state': 'running', 'started_at': now(), 'pid': os.getpid(), 'identity': identity,
               'native': native, 'selection': 'newest completed games, all teams and outcomes',
               'training_split_changed': False, 'requests_paced': 'sequential, at least one second apart',
               'completed': 0}
    write_json(receipt_path, receipt)
    try:
        listing_path = output / 'listing.json'
        if listing_path.exists():
            listing = json.loads(listing_path.read_text())
        else:
            leaderboard, lb_fetch = client.get('/api/leaderboard')
            write_json(output / 'leaderboard.json', {'data': leaderboard, 'fetch': lb_fetch})
            listing, cursor, page_index = [], None, 0
            while len(listing) < args.limit:
                params = {'sort': 'played', 'order': 'desc', 'limit': 100}
                if cursor:
                    params['cursor'] = cursor
                page, fetch = client.get('/api/games', params)
                write_json(output / 'pages' / f'{page_index:04d}.json', {'data': page, 'fetch': fetch})
                listing.extend(page['games'][:args.limit-len(listing)])
                cursor = page['nextCursor']
                page_index += 1
                if cursor is None:
                    break
            if len({row['id'] for row in listing}) != len(listing):
                raise ValueError('duplicate game id in snapshot')
            write_json(listing_path, listing)
        store = ingest.RawStore(output / 'raw')
        known = store.accepted_ids()
        journal = output / 'validation.jsonl'
        journal.touch(exist_ok=True)
        records = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
        processed = {row['id'] for row in records}
        if len(processed) != len(records):
            raise ValueError('duplicate validation record')
        receipt.update(completed=len(records), accepted=sum(r['accepted'] for r in records),
                       quarantined=sum(not r['accepted'] for r in records))
        for row in listing:
            game = row['id']
            if not re.fullmatch('[a-z0-9]{8}', game) or row['result'] not in ('1-0','0-1','1/2-1/2'):
                raise ValueError('malformed completed listing row')
            if game in processed:
                continue
            saved = store.games / game / 'replay.json'
            cached = args.cache / game / 'replay.json'
            if saved.exists():
                replay = json.loads(saved.read_text())
                fetch = {'source': 'resumed snapshot', 'path': str(saved), 'sha256': sha(saved)}
            elif cached.exists():
                replay = json.loads(cached.read_text())
                fetch = {'source': 'shared cache', 'path': str(cached), 'sha256': sha(cached)}
            else:
                replay, fetch = client.get('/api/games/' + game)
                fetch['source'] = 'public API'
            if replay.get('id') != game:
                raise ValueError('replay id does not match request')
            problems = []
            for key in ('result', 'whitePlayerId', 'blackPlayerId', 'whiteVersion', 'blackVersion'):
                if replay.get(key) != row.get(key):
                    problems.append('listing/replay disagreement: ' + key)
            # Cache metadata hashes the bytes actually stored, while keeping the
            # fetched/source bytes separately. Preserve the normal RawStore API
            # cache contract without claiming a new network fetch for a cache hit.
            fetch.setdefault('url', 'https://6s890.lids.mit.edu/api/games/' + game)
            fetch.setdefault('fetched_at', now())
            fetch['source_bytes_sha256'] = fetch.pop('sha256')
            store.save_game(replay, row, {'replay': fetch}, None)
            fetch['sha256'] = sha(saved)
            store.write_json(saved.parent / 'fetch_metadata.json', {'replay': fetch})
            states, rule_problems = ingest.validate_replay(replay)
            problems += rule_problems
            if not problems and row.get('plies') != len(states)-1:
                problems.append('listing/replay ply-count disagreement')
            if problems:
                store.record_quarantine(game, problems, replay)
            elif game not in known:
                store.record_accepted(replay)
                known.add(game)
            record = {'id': game, 'accepted': not problems, 'problems': problems,
                      'source': fetch['source'], 'frames_checked': len(states),
                      'replay_sha256': sha(saved),
                      'moves_sha256': ingest.replay_hash(replay) if isinstance(replay.get('frames'),list) else None,
                      'createdAt': replay.get('createdAt'), 'result': replay['result'],
                      'whitePlayerId': replay.get('whitePlayerId'), 'blackPlayerId': replay.get('blackPlayerId'),
                      'whiteVersion': replay.get('whiteVersion'), 'blackVersion': replay.get('blackVersion')}
            with journal.open('a') as handle:
                handle.write(json.dumps(record) + '\n')
            records.append(record)
            processed.add(game)
            receipt.update(completed=len(records), accepted=sum(r['accepted'] for r in records),
                           quarantined=sum(not r['accepted'] for r in records))
            write_json(receipt_path, receipt)
            if len(records) % 25 == 0:
                print(json.dumps({k: receipt[k] for k in ('completed', 'accepted', 'quarantined')}), flush=True)
        receipt.update(state='complete', completed_at=now(), listing_sha256=sha(listing_path),
                       validation_sha256=sha(journal), sources=dict(Counter(r['source'] for r in records)),
                       outcomes=dict(Counter(r['result'] for r in records)),
                       frames_checked=sum(r['frames_checked'] for r in records),
                       unique_move_sequences=len({r['moves_sha256'] for r in records}),
                       limitations=['Recent all-outcome snapshot, not uniform sampling across opponents.',
                                    'Train/validation overlap not yet audited; no held-out strength claim.',
                                    'Accepted means exact replay agreement with pinned rules, not good play.'])
    except Deferred as error:
        receipt.update(state='deferred', retry_after_seconds=error.wait, error=str(error))
        raise
    except BaseException as error:
        receipt.update(state='failed', error=repr(error))
        raise
    finally:
        write_json(receipt_path, receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('native','identity')},indent=2),flush=True)


if __name__ == '__main__':
    main()
