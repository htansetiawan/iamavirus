"""Independently audit the collector's already-frozen listing, without HTTP.

The listing and its pages are complete before replay downloads start. This
checks their selection/provenance and reports descriptive metadata only.
It does not certify missing replays, fit a model or assign a training split.
"""
from argparse import ArgumentParser
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def at_ns(value):
    match = re.fullmatch(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?(Z|[+-]\d\d:\d\d)', value)
    assert match, value
    whole, fraction, offset = match.groups()
    stamp = datetime.fromisoformat(whole + ('+00:00' if offset == 'Z' else offset))
    return int(stamp.timestamp()) * 1000000000 + int((fraction or '').ljust(9, '0'))


def audit(store, plan_path):
    plan = read(plan_path)
    assert store.resolve() == Path(plan['store']).resolve()
    for name, expected in plan['dependencies'].items():
        assert sha(Path(name)) == expected, name
    listing_path = store / 'listing.json'
    listing = read(listing_path)
    assert isinstance(listing, list) and len(listing) == plan['limit'] == 6000
    pages = sorted((store / 'pages').glob('*.json'))
    assert [p.name for p in pages] == [f'{i:04d}.json' for i in range(60)]
    joined, cursor = [], None
    source_hashes = {str(listing_path): sha(listing_path), str(plan_path): sha(plan_path), str(Path(__file__)): sha(Path(__file__))}
    for i, path in enumerate(pages):
        record = read(path)
        data, fetch = record['data'], record['fetch']
        url = urlparse(fetch['url'])
        query = parse_qs(url.query)
        expected = dict(sort=['played'], order=['desc'], limit=['100'])
        if cursor is not None:
            expected['cursor'] = [cursor]
        assert url.scheme == 'https' and url.netloc == '6s890.lids.mit.edu' and url.path == '/api/games'
        assert query == expected, (path, query)
        assert fetch['status'] == 200 and fetch['attempts'] >= 1
        assert data['sort'] == 'played' and data['order'] == 'desc'
        assert len(data['games']) == 100
        if i == 0:
            summary = data['summary']
            assert summary['total'] >= len(listing)
            assert sum(summary['white'].values()) == summary['total']
        else:
            assert data['summary'] is None
        joined.extend(data['games'])
        cursor = data['nextCursor']
        source_hashes[str(path)] = sha(path)
    assert joined == listing
    ids = [row['id'] for row in listing]
    assert len(set(ids)) == len(ids) and all(re.fullmatch('[a-z0-9]{8}', value) for value in ids)
    dates = [at_ns(row['createdAt']) for row in listing]
    assert dates == sorted(dates, reverse=True)
    assert all(row['result'] in ('1-0', '0-1', '1/2-1/2') and isinstance(row['plies'], int) and row['plies'] >= 0 for row in listing)
    leaderboard_path = store / 'leaderboard.json'
    leaderboard = read(leaderboard_path)
    source_hashes[str(leaderboard_path)] = sha(leaderboard_path)
    own = [p for p in leaderboard['data']['players'] if p['name'] == 'IAmAVirus']
    assert len(own) == 1
    player = own[0]
    cells, own_games = defaultdict(Counter), []
    seen_names = defaultdict(set)
    for row in listing:
        for color, opponent in [('white', 'black'), ('black', 'white')]:
            seen_names[row[color + 'PlayerId']].add(row[color])
            if row[color + 'PlayerId'] != player['id']:
                continue
            score = .5 if row['result'] == '1/2-1/2' else float((row['result'] == '1-0') == (color == 'white'))
            result = 'draws' if score == .5 else 'wins' if score == 1 else 'losses'
            key = (row[color + 'Version'], row[opponent + 'PlayerId'], row[opponent + 'Version'], color)
            cells[key][result] += 1
            own_games.append(dict(game=row['id'], own_version=row[color + 'Version'], opponent_id=row[opponent + 'PlayerId'],
                                  opponent_name=row[opponent], opponent_version=row[opponent + 'Version'], color=color,
                                  score=score, plies=row['plies'], reason=row['reason']))
    outcomes = Counter(row['result'] for row in listing)
    reasons = Counter(row['reason'] for row in listing)
    versions = Counter()
    for row in own_games:
        versions[row['own_version']] += 1
    own_versions = []
    for version, count in sorted(versions.items()):
        rows = [r for r in own_games if r['own_version'] == version]
        own_versions.append(dict(version=version, games=count, wins=sum(r['score'] == 1 for r in rows),
                                 draws=sum(r['score'] == .5 for r in rows), losses=sum(r['score'] == 0 for r in rows),
                                 points=sum(r['score'] for r in rows), white_games=sum(r['color'] == 'white' for r in rows)))
    cell_rows = []
    for (version, opponent, their_version, color), counts in sorted(cells.items(), key=lambda x: repr(x[0])):
        cell_rows.append(dict(own_version=version, opponent_id=opponent, played_names=sorted(seen_names[opponent]),
                              opponent_version=their_version, own_color=color, **counts))
    return dict(at=datetime.now(timezone.utc).isoformat(), selection='All 6000 newest completed IDs from one fixed-cursor snapshot; no outcome/team filter.',
                source_hashes=source_hashes, pages_verified=len(pages), distinct_game_ids=len(ids),
                newest=listing[0]['createdAt'], oldest=listing[-1]['createdAt'], span_hours=(dates[0] - dates[-1]) / 3.6e12,
                total_archive_snapshot_games=summary['total'], timestamp_precision='nanoseconds',
                outcome_counts=dict(outcomes), termination_reasons=dict(reasons),
                distinct_team_ids=len(seen_names), final_cursor_nonnull=cursor is not None,
                own_leaderboard_snapshot=dict(fetched_at=leaderboard['fetch']['fetched_at'], team_id=player['id'],
                                              active_version=player['activeVersion'], elo=player['rating'],
                                              wins=player['wins'], draws=player['draws'], losses=player['losses']),
                own_window_versions=own_versions, own_opponent_version_color_cells=cell_rows,
                own_window_games=own_games,
                limitations=['Metadata-only selection audit; replay collection is a separate, potentially running job.',
                             'The 6000-game limit is a recent window, not the full archive or a balanced opponent sample.',
                             'No replay-frame, taxonomy, training-readiness, independence or strength claim.',
                             'Hashes verify saved wrapper files, not independently retained original HTTP response bytes.',
                             'Leaderboard values describe its saved fetch time; played versions/colors define matchup cells.'])


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--store', type=Path, default=ROOT / 'data/astra-spool/field-snapshot-20261111')
    parser.add_argument('--plan', type=Path, default=ROOT / 'astra-submissions/analysis/field-snapshot-20261111/plan.json')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = audit(args.store, args.plan)
    if args.out:
        with args.out.open('x') as stream:
            stream.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ['pages_verified', 'distinct_game_ids', 'newest', 'oldest', 'span_hours', 'own_window_versions']}, indent=2))
