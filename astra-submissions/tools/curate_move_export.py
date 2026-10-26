#!/usr/bin/env python3
"""Build dated, duplicate-grouped move-model splits with opponent/version coverage.

Inputs are an existing C-engine move export and the public listing cache.
Output must be a new directory: frozen exports are never overwritten.
"""
import argparse
import collections
import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning.dataset import assign_splits
from learning.daily_insights import parse_utc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-prefix', type=Path, required=True)
    ap.add_argument('--raw', type=Path, default=ROOT / 'data/raw/games')
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--receipt', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    records = {}
    rejected = collections.Counter()
    source_hashes = {}
    for split in ('train', 'test'):
        path = Path(str(args.source_prefix) + f'-{split}.txt')
        source_hashes[split] = hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open() as source:
            for header in source:
                moves = next(source, None)
                if moves is None or not header.startswith('game '):
                    raise ValueError(f'malformed export in {path}')
                game_id = header.split()[1]
                assert game_id not in records, game_id
                listing = json.loads((args.raw / game_id / 'listing.json').read_text())
                at = parse_utc(listing.get('createdAt'))
                if at is None:
                    rejected['missing_or_invalid_date'] += 1
                    continue
                sequence = ' '.join(moves.split())
                records[game_id] = {'id': game_id, 'createdAt': at.isoformat(),
                                    'moves_sha256': hashlib.sha256(sequence.encode()).hexdigest(),
                                    'header': header.strip(), 'moves': sequence, 'listing': listing}
    rows = list(records.values())
    assignment = assign_splits(rows, fractions=(.8, .1, .1), seed=20261026)
    groups = collections.defaultdict(set)
    original_groups = collections.defaultdict(set)
    for split in ('train', 'test'):
        with Path(str(args.source_prefix) + f'-{split}.txt').open() as source:
            for header in source:
                moves = next(source)
                original_groups[hashlib.sha256(' '.join(moves.split()).encode()).hexdigest()].add(split)
    coverage = {s: collections.Counter() for s in ('train', 'validation', 'test')}
    paths = {}; counts = {}; dates = {}; hashes = {}
    with (args.output / 'games.jsonl').open('w') as index:
        for split in coverage:
            selected = sorted((r for r in rows if assignment[r['id']] == split), key=lambda r: (r['createdAt'], r['id']))
            path = args.output / f'arena-{split}.txt'
            with path.open('w') as out:
                for row in selected:
                    out.write(row['header'] + '\n' + row['moves'] + '\n')
                    groups[row['moves_sha256']].add(split)
                    listing = row['listing']
                    for side in ('white', 'black'):
                        coverage[split][f"{listing[side]}@v{listing.get(side + 'Version')}"] += 1
                    index.write(json.dumps({'id': row['id'], 'createdAt': row['createdAt'],
                                            'moves_sha256': row['moves_sha256'], 'split': split,
                                            'white': listing['white'], 'black': listing['black'],
                                            'whiteVersion': listing.get('whiteVersion'),
                                            'blackVersion': listing.get('blackVersion')}, separators=(',', ':')) + '\n')
            paths[split] = str(path)
            counts[split] = len(selected)
            dates[split] = {'earliest': selected[0]['createdAt'] if selected else None,
                            'latest': selected[-1]['createdAt'] if selected else None}
            hashes[split] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert all(len(splits) == 1 for splits in groups.values())
    latest_by_group = collections.defaultdict(str)
    for row in rows:
        latest_by_group[row['moves_sha256']] = max(latest_by_group[row['moves_sha256']], row['createdAt'])
    bounds = {s: sorted(latest_by_group[g] for g, splits in groups.items() if s in splits) for s in coverage}
    assert bounds['train'][-1] <= bounds['validation'][0] <= bounds['validation'][-1] <= bounds['test'][0]
    manifest = {'classification': 'curated modelling data; no fit or strength result',
                'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'source_sha256': source_hashes, 'source_prefix': str(args.source_prefix),
                'files': paths, 'sha256': hashes, 'counts': counts, 'dates': dates,
                'split_method': '80/10/10 whole move-sequence groups ordered by latest completion',
                'unique_sequences': len(groups), 'cross_split_duplicate_sequences': 0,
                'source_cross_split_duplicate_sequences': sum(len(x) > 1 for x in original_groups.values()),
                'rejected': dict(rejected), 'opponent_version_seats': {s: dict(c) for s, c in coverage.items()},
                'limits': 'Older members of a repeated sequence follow its newest member into the same split. Held-out opponent versions require a separate declared filter.'}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    args.receipt.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: manifest[k] for k in ('counts', 'unique_sequences', 'source_cross_split_duplicate_sequences', 'cross_split_duplicate_sequences', 'rejected')}, indent=2))


if __name__ == '__main__':
    main()
