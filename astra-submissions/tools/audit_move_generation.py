#!/usr/bin/env python3
"""Independently check a full-cohort move generation against its accepted prefix."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            result.update(block)
    return result.hexdigest()


def audit(prefix, plan=None, generation=None):
    # One resolution; never follow the mutable pointer again during this audit.
    if generation is None:
        pointer = Path(str(prefix)+'-current.json')
        if pointer.exists():
            current = json.loads(pointer.read_text())
            generation = (pointer.parent/current['generation']).resolve(strict=True)
            assert digest(generation/'manifest.json') == current['manifest_sha256']
        else:
            generation = Path(str(prefix)+'-current').resolve(strict=True)
    else:
        generation = generation.resolve(strict=True)
    manifest_path = generation/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    assert manifest['format'] == 1 and manifest['complete'] is True
    if plan:
        frozen = json.loads(plan.read_text())
        assert manifest['exporter_sha256'] == frozen['exporter_sha256']
    assert set(manifest['files']) == {'train.txt', 'test.txt', 'games.jsonl'}
    for name, expected in manifest['files'].items():
        path = generation/name
        assert path.stat().st_size == expected['bytes'], name
        assert digest(path) == expected['sha256'], name
    source = manifest['journal']
    remaining, rows, journal_hash, lines = source['bytes'], {}, hashlib.sha256(), 0
    with Path(source['path']).open('rb') as handle:
        while remaining:
            line = handle.readline(remaining)
            assert line and line.endswith(b'\n'), 'source prefix unavailable/incomplete'
            remaining -= len(line)
            journal_hash.update(line)
            if line.strip():
                row = json.loads(line)
                rows[row['id']] = row
                lines += 1
    assert journal_hash.hexdigest() == source['sha256']
    assert lines == source['accepted_lines'] and len(rows) == source['unique_games']
    expected = {}
    for gid, row in rows.items():
        date = row.get('createdAt')
        if not isinstance(date, str) or date[:10] < manifest['since']:
            continue
        if row.get('rulesVersion') != 'fow-v1' or row.get('plies', 0) < 4:
            continue
        if all(row.get(side) in {'Uniform', 'Baseline', 'baseline.py'} for side in ('white', 'black')):
            continue
        expected[gid] = row
    assert len(expected) == manifest['eligible_games']
    assert manifest['requested_games'] >= len(expected), 'audit is for a full eligible cohort'
    assert len(expected) == manifest['selected_games']
    cohort = {}
    with (generation/'games.jsonl').open() as handle:
        for line in handle:
            row = json.loads(line)
            gid = row['id']
            assert gid not in cohort and gid in expected
            for field in ('createdAt', 'white', 'black', 'moves_sha256'):
                assert row[field] == expected[gid][field], (gid, field)
            cohort[gid] = row
    assert set(cohort) == set(expected)
    seen, counts, moves_count, long_names = set(), {}, 0, set()
    uci = re.compile(r'[a-h][1-8][a-h][1-8][qrbn]?\Z')
    for split in ('train', 'test'):
        count = 0
        with (generation/f'{split}.txt').open() as handle:
            while header := handle.readline():
                tag, gid, white, black = header.split()
                assert tag == 'game' and gid not in seen and gid in cohort
                seen.add(gid)
                row = expected[gid]
                tags = tuple('-' if row[s] in {'Uniform', 'Baseline', 'baseline.py'} else row[s].replace(' ', '_')
                             for s in ('white', 'black'))
                assert (white, black) == tags
                for name in tags:
                    if len(name.encode()) > 63:
                        long_names.add(name)
                target = 'test' if int(hashlib.sha1(gid.encode()).hexdigest(), 16) % 1000 < manifest['test_share']*1000 else 'train'
                assert target == split == cohort[gid]['split']
                line = handle.readline()
                assert line.endswith('\n')
                moves = line.split()
                assert len(moves) >= 4 and all(uci.fullmatch(move) for move in moves)
                assert len(moves) == row['plies'], (gid, 'move/ply mismatch')
                assert hashlib.sha256(' '.join(moves).encode()).hexdigest() == row['moves_sha256'], gid
                moves_count += len(moves)
                count += 1
        counts[split] = count
        assert manifest['counts'][split] == count
    assert seen == set(expected)
    return dict(at=datetime.now(timezone.utc).isoformat(), passed=True, generation=str(generation),
                manifest_sha256=digest(manifest_path), cohort_games=len(expected), counts=counts,
                moves=moves_count, source_prefix_bytes=source['bytes'], source_prefix_sha256=source['sha256'],
                legacy_aliases_match={s: Path(str(prefix)+f'-{s}.txt').exists() and
                                      digest(Path(str(prefix)+f'-{s}.txt')) == manifest['files'][f'{s}.txt']['sha256']
                                      for s in ('train', 'test')},
                names_exceeding_existing_c_parser_63byte_limit=sorted(long_names),
                auditor_sha256=digest(Path(__file__)),
                limitation='Verifies the accepted move sequence and complete cohort, not a new rules replay '
                'or model-quality/playing-strength test. The accepted journal is the ingest authority.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-prefix', type=Path, required=True)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--generation', type=Path, help='Audit an unpublished completed generation directly')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.out_prefix, args.plan, args.generation)
    with args.out.open('x') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
