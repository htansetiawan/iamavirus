#!/usr/bin/env python3
"""Freeze recent reference-team games, reuse the shared cache, validate every replay.

Public GETs only. Splits are chronological by whole game across both teams.
External output stores new replays; cached replays stay in their original store.
"""
import argparse
import dataclasses
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning.api_client import ApiClient, utc_now  # noqa: E402
from learning.ingest import validate_replay  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--cache', type=Path, default=ROOT / 'data/raw')
    ap.add_argument('--per-team', type=int, default=1000)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    api = ApiClient()
    lb, fetched = api.leaderboard()
    (args.out / 'leaderboard.json').write_text(json.dumps({'fetched': dataclasses.asdict(fetched), 'leaderboard': lb}, indent=2))
    targets = {p['name']: p for p in lb['players'] if p['name'] in ('Instructors', 'duck')}
    if set(targets) != {'Instructors', 'duck'}:
        raise ValueError('Both reference teams must be present')
    listed = {}
    listings = {}
    for name, player in targets.items():
        params = {'white': f"{name} v{player['activeVersion']}", 'colors': 'any',
                  'sort': 'played', 'order': 'desc', 'limit': 100}
        rows = [g for g, _ in api.iter_games(params, args.per_team)]
        for g in rows:
            side = 'white' if g['whitePlayerId'] == player['id'] else 'black'
            assert g[side + 'PlayerId'] == player['id']
            assert g[side + 'Version'] == player['activeVersion']
            listed[g['id']] = g
        listings[name] = rows
        print(f'{name}: listed {len(rows)} current-version games', flush=True)
    (args.out / 'listings.json').write_text(json.dumps(listings, indent=2))
    rows, invalid = [], []
    downloaded = cached = 0
    for i, g in enumerate(sorted(listed.values(), key=lambda x: (x['createdAt'], x['id']))):
        source = args.cache / 'games' / g['id'] / 'replay.json'
        local = args.out / 'raw' / g['id'] / 'replay.json'
        if source.exists():
            data = source.read_bytes(); cached += 1
        elif local.exists():
            source = local; data = source.read_bytes(); cached += 1
        else:
            replay, record, _ = api.replay(g['id'])
            local.parent.mkdir(parents=True, exist_ok=True)
            data = json.dumps(replay, separators=(',', ':')).encode()
            local.write_bytes(data)
            (local.parent / 'fetch.json').write_text(json.dumps(dataclasses.asdict(record)))
            source = local; downloaded += 1
        replay = json.loads(data)
        _, problems = validate_replay(replay)
        if problems:
            invalid.append({'game': g['id'], 'problems': problems})
            continue
        rows.append({**g, 'replay_path': str(source.resolve()), 'replay_sha256': hashlib.sha256(data).hexdigest(),
                     'frames': len(replay['frames'])})
        if (i+1) % 100 == 0:
            print(f'validated {i+1}/{len(listed)}; downloaded={downloaded} cached={cached} invalid={len(invalid)}', flush=True)
    # Whole-game temporal splits shared by both teams; no result-based selection.
    n = len(rows)
    for i, row in enumerate(rows):
        row['split'] = 'train' if i < int(.7*n) else 'validation' if i < int(.85*n) else 'test'
    manifest = {'created_at': utc_now(), 'teams': {k: {'id': p['id'], 'version': p['activeVersion']} for k,p in targets.items()},
                'split_rule': 'chronological whole games: 70% train, 15% validation, 15% test; shared across teams',
                'games': rows, 'invalid': invalid, 'downloaded': downloaded, 'cached': cached,
                'requests': api.requests_made, 'counts': dict(Counter(r['split'] for r in rows))}
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({k: v for k,v in manifest.items() if k not in ('games', 'invalid')}, indent=2), flush=True)


if __name__ == '__main__':
    main()
