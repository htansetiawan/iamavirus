"""Merge already-reviewed public replays into the recovered shared archive.

No HTTP client is called. Existing accepted replay bytes are preserved by
the existing RawStore transaction API. Source conflicts are reported rather
than overwritten; an I/O error stops the batch.
"""
from argparse import ArgumentParser
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning import _native, api_client, ingest

FIELD = ROOT / 'data/astra-spool/field-snapshot-20261111'
REVIEW = ROOT / 'astra-submissions/analysis/field-snapshot-20261111'
RAW = ROOT / 'data/raw'
OUT = ROOT / 'astra-submissions/analysis/field-archive-merge-20261111'
STORE = ROOT / 'data/astra-spool/field-archive-merge-20261111'
VALIDATOR = ROOT / 'astra-submissions/experiments/last-only-pilot-20261110/build/native-validator.so'
OWNER = 'astra-field-archive-merge-20261111'


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def atomic(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def archive_index():
    """Read complete journal bytes under the existing shared writer lock."""
    digest, ids, rows, latest = hashlib.sha256(), set(), 0, {}
    with (RAW / '.writer.lock').open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_SH)
        with (RAW / 'accepted.jsonl').open('rb') as stream:
            for line in stream:
                assert line.endswith(b'\n'), 'incomplete shared journal tail'
                digest.update(line)
                if not line.strip():
                    continue
                record = json.loads(line)
                rows += 1
                ids.add(record['id'])
                when = record.get('createdAt')
                if when:
                    stamp = datetime.fromisoformat(when.replace('Z', '+00:00'))
                    feed = 'ours' if 'IAmAVirus' in (record.get('white'), record.get('black')) else 'other_teams'
                    if feed not in latest or stamp > latest[feed][0]:
                        latest[feed] = (stamp, dict(id=record['id'], createdAt=when))
    return ids, dict(lines=rows, unique_ids=len(ids), duplicate_extra_lines=rows - len(ids),
                     journal_sha256=digest.hexdigest(), latest={k: v[1] for k, v in latest.items()})


def same_positions(a, b):
    assert a['id'] == b['id'] and a['result'] == b['result'] and a['reason'] == b['reason']
    assert len(a['frames']) == len(b['frames'])
    for x, y in zip(a['frames'], b['frames'], strict=True):
        assert all(x[k] == y[k] for k in ('ply', 'move', 'board', 'white', 'black'))


def transfer(store, replay, listing, fetch):
    """One transaction; never rewrite an accepted replay's original bytes."""
    with store.writer():
        store._refresh_accepted()
        accepted = replay['id'] in store._accepted_ids
        target = store.games / replay['id'] / 'replay.json'
        before = target.read_bytes() if target.is_file() else None
        if before is not None:
            if accepted:
                same_positions(json.loads(before), replay)
            elif before != json.dumps(replay, indent=1, sort_keys=True).encode():
                return dict(status='unaccepted_source_conflict', destination_sha256=hashlib.sha256(before).hexdigest())
        problems = ingest.ingest_replay(store, replay, listing, fetch, None)
        assert not problems, (replay['id'], list(problems))
        after = target.read_bytes()
        if accepted and before is not None:
            assert after == before, ('accepted original changed', replay['id'])
        same_positions(json.loads(after), replay)
        store._refresh_accepted()
        assert replay['id'] in store._accepted_ids
        return dict(status='cached' if problems.cached else 'repaired_missing_files' if problems.recovered else 'newly_accepted',
                    destination_sha256=hashlib.sha256(after).hexdigest(), accepted_original_preserved=accepted and before is not None,
                    source_and_destination_bytes_identical=after == json.dumps(replay, indent=1, sort_keys=True).encode())


def prepare():
    closure = read(REVIEW / 'closure-review.json')
    assert closure['status'] == 'complete' and closure['games'] == 6000
    for path, digest in closure['artifact_sha256'].items():
        assert sha(ROOT / path) == digest, path
    listing = read(FIELD / 'listing.json')
    indexed, before = archive_index()
    resolved = RAW.resolve(strict=True)
    mount = subprocess.check_output(['findmnt', '-rn', '-o', 'TARGET,SOURCE,FSTYPE', '--target', str(resolved)], text=True).strip()
    assert mount.startswith('/media/henrytan/seagate '), mount
    assert shutil.disk_usage(resolved).free >= 2 * 1024**3
    assert _native._library is None
    _native.ensure_built = lambda verbose=True: VALIDATOR
    with tempfile.TemporaryDirectory(prefix='iamavirus-field-import-') as temporary:
        store = ingest.RawStore(Path(temporary) / 'raw')
        meta = listing[0]
        directory = FIELD / 'raw/games' / meta['id']
        replay, fetch = read(directory / 'replay.json'), read(directory / 'fetch_metadata.json')
        first = transfer(store, replay, meta, fetch)
        assert first['status'] == 'newly_accepted'
        target = store.games / meta['id'] / 'replay.json'
        original = target.read_bytes()
        second = transfer(store, {**replay, 'whiteCurrentVersion': 9999}, meta, fetch)
        assert second['status'] == 'cached' and target.read_bytes() == original
        (target.parent / 'listing.json').unlink()
        repaired = transfer(store, replay, meta, fetch)
        assert repaired['status'] == 'repaired_missing_files' and target.read_bytes() == original
        assert len(store.accepted_ids()) == 1
        assert len(store.accepted.read_text().splitlines()) == 1
        orphan = ingest.RawStore(Path(temporary) / 'orphan')
        conflict_path = orphan.games / meta['id'] / 'replay.json'
        conflict_path.parent.mkdir()
        conflict_path.write_text('{}')
        conflict = transfer(orphan, replay, meta, fetch)
        assert conflict['status'] == 'unaccepted_source_conflict' and conflict_path.read_text() == '{}'
    dependencies = [Path(__file__), REVIEW / 'closure-review.json', REVIEW / 'review-result.json', FIELD / 'listing.json',
                    FIELD / 'validation.jsonl', ROOT / 'learning/ingest.py', ROOT / 'learning/api_client.py',
                    ROOT / 'learning/rules.py', ROOT / 'learning/_native.py', ROOT / 'learning/histories.py', VALIDATOR]
    OUT.mkdir(exist_ok=False)
    plan = dict(at=now(), games=6000, raw_link=str(RAW), raw_resolved=str(resolved), raw_device=os.stat(resolved).st_dev, mount=mount,
                core=6, wall_seconds=1800, maximum_atomic_write_bytes=512 * 1024**2, min_destination_free_bytes=2 * 1024**3,
                before=before, initially_indexed=len(indexed & {r['id'] for r in listing}),
                initially_missing_ids=[r['id'] for r in listing if r['id'] not in indexed],
                dependencies={str(p): sha(p) for p in dependencies},
                preservation='Existing accepted replay bytes unchanged; source conflicts recorded without overwrite. Missing files use the existing RawStore recovery path. Stop at first I/O error.',
                concurrency='One RawStore instance with per-game reentrant writer transactions and incremental journal tail reads; no batch lock or duplicate HTTP client.',
                scope='Offline shared-archive data import only. No new HTTP requests, bot search/game, model fit, history rebuild, training split, GPU, report publication, commit, push or deployment.')
    save(OUT / 'plan.json', plan)
    save(OUT / 'preflight.json', dict(at=now(), checks=['new valid replay accepted', 'repeat cached without rewriting original',
         'missing listing repaired without replay rewrite or duplicate journal row', 'unaccepted conflicting source preserved'], first=first, second=second, repaired=repaired, conflict=conflict))
    print(json.dumps(dict(plan_sha256=sha(OUT / 'plan.json'), initial_missing=len(plan['initially_missing_ids']), before=before), indent=2), flush=True)


@contextmanager
def lease():
    path = ROOT / 'chatroom/cores.json'
    def update(take):
        with open('/tmp/iamavirus-cores-json.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = read(path)
            if take:
                assert not any(6 in r['cores'] for r in state['allocation'])
                state['allocation'].append(dict(owner=OWNER, cores=[6], pid=os.getpid(), at=now(), purpose='offline reviewed replay import'))
            else:
                state['allocation'] = [r for r in state['allocation'] if not (r['owner'] == OWNER and r.get('pid') == os.getpid())]
            state['updated'] = now()
            atomic(path, state)
    update(True)
    try:
        yield
    finally:
        update(False)


def run():
    plan = read(OUT / 'plan.json')
    for path, digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    assert str(RAW.resolve(strict=True)) == plan['raw_resolved'] and os.stat(RAW).st_dev == plan['raw_device']
    _native.ensure_built = lambda verbose=True: VALIDATOR
    assert _native._library is None
    listing = read(FIELD / 'listing.json')
    validation = [json.loads(s) for s in (FIELD / 'validation.jsonl').read_text().splitlines()]
    assert len(listing) == len(validation) == 6000 and [r['id'] for r in listing] == [r['id'] for r in validation]
    STORE.mkdir(exist_ok=False)
    state = dict(at=now(), status='running', completed=0, plan_sha256=sha(OUT / 'plan.json'))
    save(OUT / 'execution.json', state)
    writes = dict(bytes=0, files=0)
    original_write = api_client.atomic_write
    def bounded_write(path, data):
        assert Path(path).resolve().is_relative_to(Path(plan['raw_resolved'])), path
        assert os.stat(RAW).st_dev == plan['raw_device']
        assert shutil.disk_usage(RAW).free >= plan['min_destination_free_bytes']
        assert writes['bytes'] + len(data) <= plan['maximum_atomic_write_bytes']
        value = original_write(path, data)
        writes['bytes'] += len(data); writes['files'] += 1
        return value
    def timeout(*_):
        raise TimeoutError('reviewed archive import reached original wall cap')
    signal.signal(signal.SIGALRM, timeout)
    signal.signal(signal.SIGTERM, timeout)
    signal.alarm(plan['wall_seconds'])
    started = time.monotonic()
    counts = Counter()
    try:
        with lease(), (STORE / 'import-rows.jsonl').open('x') as journal:
            api_client.atomic_write = bounded_write
            store = ingest.RawStore(RAW)
            initial_count = len(store.accepted_ids())
            for meta, checked in zip(listing, validation, strict=True):
                assert os.stat(RAW).st_dev == plan['raw_device']
                directory = FIELD / 'raw/games' / meta['id']
                path = directory / 'replay.json'
                assert sha(path) == checked['replay_sha256'] and checked['accepted'] and not checked['problems']
                replay, fetch = read(path), read(directory / 'fetch_metadata.json')
                result = transfer(store, replay, meta, fetch)
                counts[result['status']] += 1
                journal.write(json.dumps(dict(game=meta['id'], source_sha256=checked['replay_sha256'], **result)) + '\n')
                state['completed'] += 1
                if state['completed'] % 250 == 0:
                    journal.flush()
                    atomic(OUT / 'execution.json', state)
                    print(json.dumps(dict(completed=state['completed'], counts=dict(counts), atomic_bytes=writes['bytes'])), flush=True)
            final_count = len(store.accepted_ids())
            index_bytes_read = store._index_bytes_read
        for path, digest in plan['dependencies'].items():
            assert sha(path) == digest, path
        result = dict(at=now(), status='complete' if not counts['unaccepted_source_conflict'] else 'partial_source_conflicts',
                      processed=state['completed'], counts=dict(counts), initial_unique_ids=initial_count, final_unique_ids=final_count,
                      rawstore_index_bytes_read=index_bytes_read, atomic_writes=writes, import_journal_sha256=sha(STORE / 'import-rows.jsonl'),
                      final_archive_index=archive_index()[1], scope=plan['scope'],
                      limitations=['Archive additions do not refit or deploy a model or regenerate the shared reports.',
                                   'The old 31 duplicate journal rows are retained as evidence; new ingestion uses the existing deduplicating transaction API.',
                                   'Current source equality checks cover boards/views/moves/result, not a recertification of every historical clock or mutable metadata field.',
                                   'The global corpus count can also include another writer; per-ID transaction statuses provide our attribution.',
                                   'A successful bounded import does not certify the hardware or the next daily job.'])
        save(OUT / 'result.json', result)
        state.update(status=result['status'], result_sha256=sha(OUT / 'result.json'))
        print(json.dumps(result, indent=2), flush=True)
    except BaseException as exc:
        state.update(status='failed', error=repr(exc), counts=dict(counts), writes=writes)
        raise
    finally:
        api_client.atomic_write = original_write
        signal.alarm(0)
        state.update(ended_at=now(), seconds=time.monotonic() - started)
        atomic(OUT / 'execution.json', state)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'run'])
    args = parser.parse_args()
    {'prepare': prepare, 'run': run}[args.command]()
