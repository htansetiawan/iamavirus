"""Audit completed historical catch-up against its saved API snapshot.

No network or writes to the corpus. This checks coverage and stored content;
the existing ingest validator already checks the rules before acceptance.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from learning.daily_report import accepted_rows


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def instant(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('timestamp lacks timezone')
    return result


def snapshot_rows(pages, cutoff):
    """Require the original filter/cursor chain, not just recent timestamps."""
    previous_cursor = None
    previous_time = None
    seen = set()
    rows = []
    crossed = False
    for index, page in enumerate(pages):
        if crossed:
            raise ValueError('pages recorded after crossing the cutoff')
        fetched, payload = page['fetched'], page['payload']
        url = urlparse(fetched['url'])
        query = parse_qs(url.query, keep_blank_values=True)
        expected = dict(sort=['played'], order=['desc'], limit=['100'])
        if index:
            if not previous_cursor:
                raise ValueError('page follows an exhausted cursor')
            expected['cursor'] = [previous_cursor]
        if (url.scheme != 'https' or url.netloc != '6s890.lids.mit.edu'
                or url.path != '/api/games' or query != expected
                or fetched['status'] != 200):
            raise ValueError('changed filters, endpoint, status or cursor')
        if payload['sort'] != 'played' or payload['order'] != 'desc':
            raise ValueError('unexpected effective sort')
        if not payload['games'] or len(payload['games']) > 100:
            raise ValueError('unexpected page size before cutoff')
        for row in payload['games']:
            at = instant(row['createdAt'])
            if previous_time is not None and at > previous_time:
                raise ValueError('completion order is not descending')
            if row['id'] in seen:
                raise ValueError('duplicate game in cursor snapshot')
            seen.add(row['id']); previous_time = at
            rows.append(row)
            if at < cutoff:
                crossed = True
                break
        previous_cursor = payload['nextCursor']
    if not crossed:
        raise ValueError('saved snapshot has not reached the historical cutoff')
    return rows


def check_metadata(listed, stored):
    for field in ('id', 'white', 'black', 'result', 'plies', 'whiteVersion', 'blackVersion'):
        if listed.get(field) != stored.get(field):
            raise ValueError(f"{listed['id']}: archive differs on {field}")
    if instant(listed['createdAt']) != instant(stored['createdAt']):
        raise ValueError(f"{listed['id']}: completion time differs")


def audit(directory, raw):
    plan_path, receipt_path = directory/'plan.json', directory/'receipt.json'
    plan, receipt = json.loads(plan_path.read_text()), json.loads(receipt_path.read_text())
    if not (receipt['clean'] and receipt['historical_window_traversed']
            and receipt['reason'] == 'cutoff_reached' and receipt['error'] is None):
        raise ValueError('collector did not finish a clean historical window')
    if digest(Path(__file__).with_name('backfill.py')) != plan['source_sha256']:
        raise ValueError('collector source changed')
    paths = sorted(directory.glob('page-*.json'))
    if [p.name for p in paths] != [f'page-{i:03}.json' for i in range(1, len(paths)+1)]:
        raise ValueError('missing page file')
    cutoff = instant(plan['cutoff'])
    listed = snapshot_rows([json.loads(p.read_text()) for p in paths], cutoff)
    journal_path = directory/'accepted.jsonl'
    downloaded = [json.loads(line) for line in journal_path.read_text().splitlines()]
    fetched_ids = {r['id'] for r in downloaded}
    if len(fetched_ids) != len(downloaded):
        raise ValueError('duplicate backfill acceptance')
    expected = {r['id']: r for r in listed[:-1]
                if 'IAmAVirus' not in (r['white'], r['black'])}
    if not fetched_ids <= expected.keys():
        raise ValueError('backfill accepted an excluded or unlisted game')
    counts = receipt['counts']
    expected_counts = dict(pages=len(paths), listed=len(listed),
                           accepted=len(downloaded), fetch=len(downloaded),
                           our_watcher=len(listed)-1-len(expected),
                           known=len(expected)-len(downloaded), before_cutoff=1)
    for key, value in expected_counts.items():
        if counts.get(key, 0) != value:
            raise ValueError(f'collector count disagrees: {key}')
    if counts.get('fetch_errors', 0) or counts.get('quarantined', 0):
        raise ValueError('collector reported errors or quarantine')
    if counts.get('downloaded', 0)+counts.get('cached', 0) != len(downloaded):
        raise ValueError('download/cache counts differ from acceptances')
    index = {r['id']: r for r in accepted_rows(str(raw))}
    missing = sorted(expected.keys()-index.keys())
    if missing:
        raise ValueError(f'{len(missing)} listed other-team games absent from index: {missing[:5]}')
    days = Counter()
    frames = 0
    for game_id, listing in expected.items():
        row = index[game_id]
        check_metadata(listing, row)
        replay = json.loads((raw/'games'/game_id/'replay.json').read_text())
        stored = dict(replay, plies=len(replay['frames'])-1)
        check_metadata(listing, stored)
        moves = ' '.join(f['move'] for f in replay['frames'] if f.get('move'))
        if hashlib.sha256(moves.encode()).hexdigest() != row['moves_sha256']:
            raise ValueError(f'{game_id}: replay differs from accepted move hash')
        frames += len(replay['frames'])
        days[instant(listing['createdAt']).astimezone(timezone.utc).date().isoformat()] += 1
    return dict(at=datetime.now(timezone.utc).isoformat(), passed=True,
                source_sha256=digest(Path(__file__)), plan_sha256=digest(plan_path),
                receipt_sha256=digest(receipt_path), accepted_sha256=digest(journal_path),
                page_sha256={p.name: digest(p) for p in paths}, counts=expected_counts,
                other_team_games=len(expected), frames_content_checked=frames,
                by_completion_day=dict(sorted(days.items())),
                oldest_included=min(r['createdAt'] for r in expected.values()),
                newest_included=max(r['createdAt'] for r in expected.values()),
                cutoff=plan['cutoff'], snapshot_started=plan['started'],
                limitation='Coverage of other-team games in this historical API snapshot only. '
                'Our watcher is separate. Newer games remain outside this snapshot. '
                'This audit compares stored replay content and acceptance hashes; '
                'rules validation was performed by ingestion, not rerun here.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backfill', type=Path, default=ROOT/'astra-submissions/analysis/report-repair-20261108/backfill')
    parser.add_argument('--raw', type=Path, default=ROOT/'data/raw')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.backfill, args.raw)
    with args.out.open('x') as handle:
        json.dump(result, handle, indent=2); handle.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'page_sha256'}), flush=True)


if __name__ == '__main__':
    main()
