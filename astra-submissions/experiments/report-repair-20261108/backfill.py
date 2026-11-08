"""Bounded catch-up of other teams' replays after the mounted-drive outage.

Uses the public GET client and existing rules validator. Excludes every game
involving IAmAVirus, which the independent arena watcher already maintains.
"""
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'astra-submissions/analysis/report-repair-20261108/backfill'
sys.path[:0] = [str(ROOT), str(ROOT/'astra-submissions/tools')]
from check_raw_available import check_raw_available
from learning import api_client, ingest
from learning.daily_report import accepted_rows

CUTOFF = datetime(2026, 11, 6, 9, 36, tzinfo=timezone.utc)
LIMIT = 12000
SECONDS = 4*60*60


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


def selection(row, known):
    date = datetime.fromisoformat(row['createdAt'].replace('Z', '+00:00'))
    if date < CUTOFF:
        return 'before_cutoff'
    if 'IAmAVirus' in (row.get('white'), row.get('black')):
        return 'our_watcher'
    if row['id'] in known:
        return 'known'
    return 'fetch'


def main():
    os.chdir(ROOT)
    os.sched_setaffinity(0, {4, 5})
    os.nice(10)
    # Avoid a competing scheduled all-team ingestion. The separate team-only
    # watcher may continue; its games are expressly excluded above.
    lock = open(ROOT/'data/logs/daily/.lock', 'a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    raw = ROOT/'data/raw'
    check_raw_available(raw, reports=True)
    OUT.mkdir(exist_ok=False)
    known = {r['id'] for r in accepted_rows(str(raw))}
    store = ingest.RawStore(raw)
    client = api_client.ApiClient(cache_dir=raw, min_interval=1.2)
    start = time.monotonic()
    write(OUT/'plan.json', dict(started=now(), pid=os.getpid(),
          proc_starttime=Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19],
          cores=[4,5], raw=str(raw.resolve()), known_before=len(known),
          cutoff=CUTOFF.isoformat(), listed_limit=LIMIT, wall_cap_seconds=SECONDS,
          source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          public_GET_only=True, minimum_request_interval=1.2, GPU=False,
          exclusions='All IAmAVirus games; no diagnostics, training, fitting, history rebuild or promotion.'))
    counts = Counter()
    reason = 'listing_limit_or_end'
    error = None
    consecutive_errors = 0
    try:
        params = dict(sort='played', order='desc', limit=100)
        cursor = None
        with (OUT/'accepted.jsonl').open('x') as accepted:
            while counts['listed'] < LIMIT:
                if time.monotonic()-start >= SECONDS:
                    reason = 'wall_cap'; break
                page, fetched = client.games_page(params, cursor)
                counts['pages'] += 1
                write(OUT/f"page-{counts['pages']:03}.json", dict(fetched=fetched.__dict__, payload=page))
                done = False
                for row in page.get('games', []):
                    if counts['listed'] >= LIMIT or time.monotonic()-start >= SECONDS:
                        reason = 'limit'; done = True; break
                    counts['listed'] += 1
                    choice = selection(row, known)
                    counts[choice] += 1
                    if choice == 'before_cutoff':
                        reason = 'cutoff_reached'; done = True; break
                    if choice != 'fetch':
                        continue
                    check_raw_available(raw, reports=True)
                    try:
                        replay, record, cached = client.replay(row['id'])
                    except (api_client.ApiError, OSError) as exc:
                        consecutive_errors += 1; counts['fetch_errors'] += 1
                        print(json.dumps(dict(at=now(), game=row['id'], error=str(exc))), flush=True)
                        if consecutive_errors >= 3:
                            raise RuntimeError('Three consecutive replay failures; stop instead of continuing requests') from exc
                        continue
                    consecutive_errors = 0
                    problems = ingest.ingest_replay(store, replay, row, dict(replay=record.__dict__, listing_source='/api/games'), None)
                    counts['quarantined' if problems else 'accepted'] += 1
                    counts['cached' if cached else 'downloaded'] += 1
                    if not problems:
                        known.add(row['id'])
                        accepted.write(json.dumps(dict(id=row['id'], createdAt=row['createdAt'], replay_fetch=record.__dict__))+'\n')
                        accepted.flush()
                print(json.dumps(dict(at=now(), counts=dict(counts), requests=client.requests_made)), flush=True)
                cursor = page.get('nextCursor')
                if done or not cursor:
                    break
    except BaseException as exc:
        error = repr(exc); reason = 'error'
        raise
    finally:
        write(OUT/'receipt.json', dict(finished=now(), counts=dict(counts), reason=reason, error=error,
              requests=client.requests_made, elapsed_seconds=time.monotonic()-start,
              historical_window_traversed=reason=='cutoff_reached',
              clean=reason=='cutoff_reached' and not counts['fetch_errors'] and not counts['quarantined'],
              limitation='A completed historical snapshot, not continuous synchronization; our watcher is separate.'))


if __name__ == '__main__':
    main()
