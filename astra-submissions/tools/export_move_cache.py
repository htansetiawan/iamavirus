#!/usr/bin/env python3
"""Export accepted moves through an SSD cache and publish complete generations.

The accepted journal is scanned sequentially; only missing move hashes require
random replay reads. Resolve PREFIX-current.json once before opening train/test.
Legacy PREFIX-{train,test}.txt files are conveniences, not a two-open snapshot.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shutil
import sqlite3
import time
import uuid

EXCLUDED = {"Uniform", "Baseline", "baseline.py"}
GAME_ID = re.compile(r"[a-z0-9]{8}\Z")
UCI = re.compile(r"[a-h][1-8][a-h][1-8][qrbn]?\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
FORMAT = 1


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def durable_json(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@contextmanager
def exclusive(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(f'another exporter owns {path}') from None
        yield


def journal_snapshot(path, check):
    """A finite, complete-line prefix; appends are allowed, replacement is not."""
    rows, digest, lines, duplicates = {}, hashlib.sha256(), 0, 0
    with path.open('rb') as handle:
        before = os.fstat(handle.fileno())
        remaining, trailing = before.st_size, 0
        while remaining:
            check()
            line = handle.readline(remaining)
            if not line:
                raise RuntimeError('accepted journal shrank during snapshot')
            remaining -= len(line)
            if not line.endswith(b'\n'):
                trailing = len(line)
                break
            digest.update(line)
            if not line.strip():
                continue
            row = json.loads(line)
            gid = row['id']
            if not isinstance(gid, str) or not GAME_ID.fullmatch(gid):
                raise ValueError(f'invalid accepted game ID {gid!r}')
            duplicates += gid in rows
            rows[gid] = row
            lines += 1
        after, current = os.fstat(handle.fileno()), path.stat()
        if (before.st_dev, before.st_ino) != (current.st_dev, current.st_ino) or after.st_size < before.st_size:
            raise RuntimeError('accepted journal replaced/truncated during snapshot')
    return rows, dict(path=str(path.resolve()), bytes=before.st_size - trailing,
                      sha256=digest.hexdigest(), accepted_lines=lines,
                      duplicate_lines=duplicates, unique_games=len(rows),
                      ignored_incomplete_tail_bytes=trailing,
                      device=before.st_dev, inode=before.st_ino)


def eligible_rows(rows, since):
    kept, exclusions = {}, {}
    for gid, row in rows.items():
        date = row.get('createdAt')
        reason = None
        if not isinstance(date, str) or date[:10] < since:
            reason = 'outside_date_or_undated'
        elif row.get('rulesVersion') != 'fow-v1':
            reason = 'other_or_unknown_rules'
        elif row.get('white') in EXCLUDED and row.get('black') in EXCLUDED:
            reason = 'both_excluded'
        elif row.get('plies', 0) < 4:
            reason = 'short_game'
        if reason:
            exclusions[reason] = exclusions.get(reason, 0) + 1
            continue
        if not SHA.fullmatch(row.get('moves_sha256') or ''):
            raise ValueError(f'missing move hash for eligible game {gid}')
        for side in ('white', 'black'):
            name = row.get(side)
            if not isinstance(name, str) or not name or any(c.isspace() and c != ' ' for c in name):
                raise ValueError(f'invalid {side} name for {gid}')
        kept[gid] = row
    return kept, exclusions


def checked_moves(text):
    moves = text.split()
    if len(moves) < 4 or not all(UCI.fullmatch(move) for move in moves):
        raise ValueError('invalid or short UCI move sequence')
    return ' '.join(moves)


def cache_open(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute('PRAGMA journal_mode=WAL')
    version = db.execute('PRAGMA user_version').fetchone()[0]
    if version not in (0, FORMAT):
        db.close()
        raise ValueError(f'unsupported move-cache format {version}')
    db.execute('CREATE TABLE IF NOT EXISTS moves (game_id TEXT NOT NULL, '
               'moves_sha256 TEXT NOT NULL, moves TEXT NOT NULL, '
               'PRIMARY KEY(game_id, moves_sha256)) WITHOUT ROWID')
    db.execute(f'PRAGMA user_version={FORMAT}')
    db.commit()
    return db


def seed_cache(db, rows, sources, check):
    counts = dict(records=0, matching=0, inserted=0, invalid=0, incomplete_tail=0)
    for source in sources:
        if not source.is_file():
            continue
        with source.open() as handle:
            for header in handle:
                check()
                tokens = header.split()
                if len(tokens) != 4 or tokens[0] != 'game':
                    counts['invalid'] += 1
                    continue
                line = next(handle, '')
                if not line.endswith('\n'):
                    counts['incomplete_tail'] += 1
                    break
                counts['records'] += 1
                row = rows.get(tokens[1])
                if row is None:
                    continue
                try:
                    text = checked_moves(line)
                except ValueError:
                    counts['invalid'] += 1
                    continue
                if sha(text.encode()) != row['moves_sha256']:
                    counts['invalid'] += 1
                    continue
                counts['matching'] += 1
                cursor = db.execute('INSERT OR IGNORE INTO moves VALUES (?,?,?)',
                                    (row['id'], row['moves_sha256'], text))
                counts['inserted'] += cursor.rowcount
                if counts['matching'] % 512 == 0:
                    db.commit()
        db.commit()
    return counts


def verify_generation(generation):
    manifest = json.loads((generation/'manifest.json').read_text())
    if manifest['format'] != FORMAT or not manifest['complete']:
        raise ValueError('generation is not complete')
    if set(manifest['files']) != {'train.txt', 'test.txt', 'games.jsonl'}:
        raise ValueError('unexpected generation members')
    for name, expected in manifest['files'].items():
        if (generation/name).stat().st_size != expected['bytes'] or file_sha(generation/name) != expected['sha256']:
            raise ValueError(f'generation file hash mismatch: {name}')
    return manifest


def resolve(prefix):
    """Resolve once: returned immutable paths remain valid across later exports."""
    pointer = Path(str(prefix) + '-current.json')
    if pointer.exists():
        current = json.loads(pointer.read_text())
        if current['format'] != FORMAT:
            raise ValueError('unsupported current-pointer format')
        generation = (pointer.parent/current['generation']).resolve(strict=True)
        if file_sha(generation/'manifest.json') != current['manifest_sha256']:
            raise ValueError('current generation manifest hash mismatch')
    else:
        # Read-only compatibility for early local fixtures; publication no longer
        # relies on symlink support (the bulk drive is exFAT).
        generation = Path(str(prefix) + '-current').resolve(strict=True)
    verify_generation(generation)
    return dict(generation=str(generation), train=str(generation/'train.txt'),
                test=str(generation/'test.txt'), manifest=str(generation/'manifest.json'))


def copy_atomic(source, path):
    temporary = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    try:
        with source.open('rb') as src, temporary.open('xb') as dest:
            shutil.copyfileobj(src, dest, length=1 << 20)
            dest.flush()
            os.fsync(dest.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def publish_generation(prefix, generation, legacy_files, check=lambda: None):
    """Caller owns the prefix lock. Works on filesystems without symlinks."""
    prefix, generation = prefix.absolute(), generation.resolve(strict=True)
    verify_generation(generation)
    pointer = Path(str(prefix) + '-current.json')
    temporary = pointer.with_name(pointer.name + '.tmp-' + uuid.uuid4().hex)
    try:
        durable_json(temporary, dict(format=FORMAT, generation=os.path.relpath(generation, pointer.parent.resolve()),
                     manifest_sha256=file_sha(generation/'manifest.json'), publisher_sha256=file_sha(Path(__file__))))
        check()
        os.replace(temporary, pointer)
        sync_dir(prefix.parent)
    finally:
        temporary.unlink(missing_ok=True)
    if legacy_files:
        for split in ('train', 'test'):
            copy_atomic(generation/f'{split}.txt', Path(str(prefix)+f'-{split}.txt'))
        sync_dir(prefix.parent)
    return dict(generation=str(generation), manifest=str(generation/'manifest.json'),
                manifest_sha256=file_sha(generation/'manifest.json'), current_pointer=str(pointer),
                legacy_files_updated=legacy_files)


def export(args):
    started = time.monotonic()
    deadline = started + args.wall_seconds
    def check():
        if time.monotonic() >= deadline:
            raise TimeoutError('export wall limit reached; previous generation retained')
    raw, prefix, cache = args.raw.absolute(), args.out_prefix.absolute(), args.cache.absolute()
    prefix.parent.mkdir(parents=True, exist_ok=True)
    with exclusive(Path(str(prefix) + '-export.lock')), exclusive(Path(str(cache) + '.lock')):
        rows, snapshot = journal_snapshot(raw/'accepted.jsonl', check)
        rows, exclusions = eligible_rows(rows, args.since)
        ids = sorted(rows)
        random.Random(args.seed).shuffle(ids)
        ids = ids[:args.games]
        selected = {gid: rows[gid] for gid in ids}
        db = cache_open(cache)
        staging = None
        try:
            seeds = seed_cache(db, selected, args.seed_export, check)
            generations = Path(str(prefix) + '-generations')
            generations.mkdir(exist_ok=True)
            staging = generations/('.tmp-' + uuid.uuid4().hex)
            staging.mkdir()
            counts = dict(train=0, test=0, replay_reads=0, cache_hits=0)
            files = {name: (staging/name).open('x') for name in ('train.txt', 'test.txt', 'games.jsonl')}
            try:
                for gid in ids:
                    check()
                    row = selected[gid]
                    cached = db.execute('SELECT moves FROM moves WHERE game_id=? AND moves_sha256=?',
                                        (gid, row['moves_sha256'])).fetchone()
                    if cached:
                        text = cached[0]
                        # Detect accidental cache corruption instead of silently training on it.
                        if sha(text.encode()) != row['moves_sha256']:
                            raise ValueError(f'cached move hash mismatch for {gid}')
                        counts['cache_hits'] += 1
                    else:
                        replay = json.loads((raw/'games'/gid/'replay.json').read_text())
                        counts['replay_reads'] += 1
                        if replay.get('id') != gid or replay.get('rulesVersion') != 'fow-v1':
                            raise ValueError(f'replay metadata mismatch for {gid}')
                        text = checked_moves(' '.join(f['move'] for f in replay['frames'] if f.get('move')))
                        if sha(text.encode()) != row['moves_sha256']:
                            raise ValueError(f'replay move hash mismatch for {gid}')
                        db.execute('INSERT INTO moves VALUES (?,?,?)', (gid, row['moves_sha256'], text))
                        if counts['replay_reads'] % 128 == 0:
                            db.commit()
                    split = 'test' if int(hashlib.sha1(gid.encode()).hexdigest(), 16) % 1000 < args.test_share * 1000 else 'train'
                    tags = [('-' if row[side] in EXCLUDED else row[side].replace(' ', '_')) for side in ('white', 'black')]
                    files[split+'.txt'].write(f"game {gid} {' '.join(tags)}\n{text}\n")
                    files['games.jsonl'].write(json.dumps(dict(id=gid, split=split, moves_sha256=row['moves_sha256'],
                                                             createdAt=row['createdAt'], white=row['white'], black=row['black']))+'\n')
                    counts[split] += 1
                if not ids:
                    raise ValueError('no eligible accepted games; previous generation retained')
                for handle in files.values():
                    handle.flush()
                    os.fsync(handle.fileno())
            finally:
                for handle in files.values():
                    handle.close()
            db.commit()
            check()
            manifest = dict(format=FORMAT, complete=True, at=datetime.now(timezone.utc).isoformat(),
                            journal=snapshot, exclusions=exclusions, eligible_games=len(rows),
                            requested_games=args.games, selected_games=len(ids), counts=counts, seed_sources=seeds,
                            since=args.since, test_share=args.test_share, seed=args.seed,
                            ordering='sorted accepted IDs then seeded shuffle; full eligible cohort when games >= eligible',
                            split='existing SHA1(game_id) mod 1000 < test_share*1000',
                            exporter_sha256=file_sha(Path(__file__)), elapsed_seconds=time.monotonic()-started,
                            files={name: dict(bytes=(staging/name).stat().st_size, sha256=file_sha(staging/name)) for name in files})
            durable_json(staging/'manifest.json', manifest)
            sync_dir(staging)
            generation = generations/('gen-' + uuid.uuid4().hex)
            staging.rename(generation)
            staging = None
            sync_dir(generations)
            publication = publish_generation(prefix, generation, args.legacy_files, check)
            result = dict(**publication, **counts,
                          elapsed_seconds=time.monotonic()-started)
            print(json.dumps(result), flush=True)
            return result
        finally:
            db.close()
            if staging is not None:
                shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', type=Path, default=Path('data/raw'))
    parser.add_argument('--out-prefix', type=Path, required=True)
    parser.add_argument('--cache', type=Path, default=Path('data/cache/move-export.sqlite'))
    parser.add_argument('--since', default='2026-09-30')
    parser.add_argument('--games', type=int, default=1000000)
    parser.add_argument('--test-share', type=float, default=.15)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--seed-export', type=Path, action='append', default=[])
    parser.add_argument('--wall-seconds', type=float, default=2400)
    parser.add_argument('--legacy-files', '--legacy-links', dest='legacy_files', action='store_true',
                        help='Atomically replace individual compatibility files; resolve current.json for a consistent pair')
    parser.add_argument('--resolve', action='store_true')
    parser.add_argument('--publish-generation', type=Path,
                        help='Recover publication of an already complete, hash-verified generation; no extraction')
    args = parser.parse_args()
    if args.games < 1 or args.wall_seconds <= 0 or not 0 <= args.test_share <= 1:
        parser.error('games/wall-seconds must be positive and test-share in [0,1]')
    if args.resolve:
        print(json.dumps(resolve(args.out_prefix)))
    elif args.publish_generation:
        with exclusive(Path(str(args.out_prefix)+'-export.lock')):
            print(json.dumps(publish_generation(args.out_prefix, args.publish_generation, args.legacy_files)), flush=True)
    else:
        export(args)


if __name__ == '__main__':
    main()
