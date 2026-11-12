"""Reconcile complete field-cache files, cache hits and HTTP attempt budgets.

Reads existing local evidence only; original HTTP response bodies are not
retained independently and are not claimed to be rehashed here.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'astra-submissions/analysis/field-snapshot-20261111'
STORE = ROOT / 'data/astra-spool/field-snapshot-20261111'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    plan, result, execution = read(OUT / 'plan.json'), read(OUT / 'result.json'), read(OUT / 'execution.json')
    assert execution['status'] == 'complete' and execution['result_sha256'] == sha(OUT / 'result.json')
    assert result['plan_sha256'] == sha(OUT / 'plan.json')
    assert result['listing_sha256'] == sha(STORE / 'listing.json')
    assert result['validation_sha256'] == sha(STORE / 'validation.jsonl')
    listing = read(STORE / 'listing.json')
    sources, cache_roots = Counter(), Counter()
    attempts, replay_bytes, maximum_replay, cached_verified, raw_files_bytes = 0, 0, 0, 0, 0
    for row in listing:
        directory = STORE / 'raw/games' / row['id']
        path = directory / 'replay.json'
        fetch = read(directory / 'fetch_metadata.json')['replay']
        assert sha(path) == fetch['sha256']
        size = path.stat().st_size
        assert size <= plan['replay_bytes_cap']
        replay_bytes += size
        maximum_replay = max(maximum_replay, size)
        for name in ['replay.json', 'listing.json', 'fetch_metadata.json']:
            raw_files_bytes += (directory / name).stat().st_size
        sources[fetch['source']] += 1
        assert fetch['url'] == 'https://6s890.lids.mit.edu/api/games/' + row['id']
        if fetch['source'] == 'public API':
            assert fetch['status'] == 200 and fetch['attempts'] >= 1
            attempts += fetch['attempts']
        elif fetch['source'] == 'shared cache':
            origin = Path(fetch['path']).resolve()
            roots = [Path(c).resolve() for c in plan['caches']]
            matched = [p for p in roots if origin.is_relative_to(p)]
            assert len(matched) == 1 and origin.parent.name == row['id'] and origin.name == 'replay.json'
            assert sha(origin) == fetch['source_bytes_sha256']
            cached_verified += 1
            cache_roots[str(matched[0])] += 1
        else:
            raise AssertionError('Unexpected source: ' + fetch['source'])
    pages = sorted((STORE / 'pages').glob('*.json'))
    for page in pages:
        fetch = read(page)['fetch']
        assert fetch['status'] == 200
        attempts += fetch['attempts']
    leaderboard = read(STORE / 'leaderboard.json')['fetch']
    attempts += leaderboard['attempts']
    assert attempts == result['requests'] <= plan['request_limit']
    assert dict(sources) == result['sources']
    total_json = sum(p.stat().st_size for p in STORE.rglob('*.json'))
    assert total_json < plan['raw_json_bytes_cap']
    report = dict(at=datetime.now(timezone.utc).isoformat(), source_result_sha256=sha(OUT / 'result.json'),
                  audit_source_sha256=sha(Path(__file__)), games=len(listing), sources=dict(sources),
                  cached_source_hashes_verified=cached_verified, cache_root_counts=dict(cache_roots),
                  metadata_http_attempts=attempts, reported_http_attempts=result['requests'], request_limit=plan['request_limit'],
                  attempts_beyond_one_per_success=attempts - sources['public API'] - len(pages) - 1,
                  saved_replay_bytes=replay_bytes, maximum_saved_replay_bytes=maximum_replay,
                  original_raw_json_files_bytes=raw_files_bytes, reported_growth_counter=result['raw_json_bytes'],
                  saved_json_bytes=total_json, raw_json_bound=plan['raw_json_bytes_cap'],
                  scope='Local byte/source/request-budget reconciliation. No new HTTP request, replay inference, fit, split, game or deployment.',
                  limitations=['Saved wrapper/replay bytes are verified; original public HTTP response bodies were not retained independently.',
                               'Start-time pacing follows the pinned client implementation; this is not a transport-start timestamp audit.',
                               'Reused cached data is not automatically an untouched holdout.'])
    with (OUT / 'transport-review.json').open('x') as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: report[k] for k in ['games', 'sources', 'cached_source_hashes_verified', 'metadata_http_attempts', 'attempts_beyond_one_per_success', 'saved_json_bytes']}, indent=2))


if __name__ == '__main__':
    main()
