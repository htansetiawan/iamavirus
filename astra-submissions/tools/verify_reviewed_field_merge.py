"""Read-only post-import audit; never repairs or rewrites a shared source."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'astra-submissions/analysis/field-archive-merge-20261111'
STORE = ROOT / 'data/astra-spool/field-archive-merge-20261111'
FIELD = ROOT / 'data/astra-spool/field-snapshot-20261111'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    plan, result, execution = [read(OUT / name) for name in ['plan.json', 'result.json', 'execution.json']]
    assert execution['ended_at'] and execution['status'] == result['status'] == 'complete'
    assert execution['completed'] == result['processed'] == 6000
    assert execution['seconds'] <= plan['wall_seconds']
    assert execution['plan_sha256'] == sha(OUT / 'plan.json')
    assert execution['result_sha256'] == sha(OUT / 'result.json')
    for path, digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    assert sha(STORE / 'import-rows.jsonl') == result['import_journal_sha256']
    listing = read(FIELD / 'listing.json')
    rows = [json.loads(s) for s in (STORE / 'import-rows.jsonl').read_text().splitlines()]
    validation = [json.loads(s) for s in (FIELD / 'validation.jsonl').read_text().splitlines()]
    assert len(rows) == len(listing) == len(validation) == 6000
    assert [r['game'] for r in rows] == [r['id'] for r in listing] == [r['id'] for r in validation]
    counts, frames, clock_cases, metadata = Counter(), 0, Counter(), Counter()
    raw = Path(plan['raw_resolved'])
    assert Path(plan['raw_link']).resolve(strict=True) == raw
    for record, meta, checked in zip(rows, listing, validation, strict=True):
        source_path = FIELD / 'raw/games' / record['game'] / 'replay.json'
        dest_dir = raw / 'games' / record['game']
        dest_path = dest_dir / 'replay.json'
        assert sha(source_path) == record['source_sha256'] == checked['replay_sha256']
        assert sha(dest_path) == record['destination_sha256']
        source, target = read(source_path), read(dest_path)
        assert source['id'] == target['id'] == meta['id']
        assert source['result'] == target['result'] == meta['result']
        assert source['reason'] == target['reason'] == meta['reason']
        assert len(source['frames']) == len(target['frames']) == meta['plies'] + 1
        missing_clock = clock_diff = False
        for a, b in zip(source['frames'], target['frames'], strict=True):
            assert tuple(a[k] for k in ('ply', 'move', 'board', 'white', 'black')) == tuple(b[k] for k in ('ply', 'move', 'board', 'white', 'black'))
            missing_clock |= 'clocks' not in b
            clock_diff |= a.get('clocks') != b.get('clocks')
        clock_cases['missing_target_clock_fields'] += missing_clock
        clock_cases['different_clock_values'] += clock_diff
        clock_cases['equivalent_clock_values'] += not clock_diff
        if record['status'] == 'newly_accepted':
            # Newly imported source must preserve the full response contents,
            # including clocks, time control and optional metadata.
            assert source == target
        if record['accepted_original_preserved']:
            metadata['accepted_originals_preserved'] += 1
        old_listing = read(dest_dir / 'listing.json')
        assert old_listing['id'] == meta['id'] and old_listing['result'] == meta['result']
        fetch = read(dest_dir / 'fetch_metadata.json')
        if isinstance(fetch.get('replay'), dict) and fetch['replay'].get('sha256') == record['destination_sha256']:
            metadata['stored_fetch_hash_matches'] += 1
        else:
            metadata['legacy_or_missing_fetch_hash'] += 1
        frames += len(target['frames'])
        counts[record['status']] += 1
    assert frames == 459622
    assert dict(counts) == {k: v for k, v in result['counts'].items() if v}
    source = ROOT / 'astra-submissions/tools/merge_reviewed_field.py'
    spec = importlib.util.spec_from_file_location('verified_field_merge_reader', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ids, archive = module.archive_index()
    assert {r['id'] for r in listing} <= ids
    assert archive['duplicate_extra_lines'] == plan['before']['duplicate_extra_lines']
    assert result['final_unique_ids'] >= result['initial_unique_ids'] + counts['newly_accepted']
    assert result['atomic_writes']['bytes'] <= plan['maximum_atomic_write_bytes']
    assert not any(r['owner'] == 'astra-field-archive-merge-20261111' for r in read(ROOT / 'chatroom/cores.json')['allocation'])
    receipt = dict(at=datetime.now(timezone.utc).isoformat(), status='complete', games=6000, frames=frames,
                   transaction_counts=dict(counts), clocks=dict(clock_cases), stored_metadata=dict(metadata),
                   archive_index_at_review=archive, newly_imported_ids=counts['newly_accepted'],
                   old_duplicate_lines_retained=archive['duplicate_extra_lines'],
                   checks=['Original execution terminal within original cap; frozen inputs and importer source unchanged.',
                           'All 6000 ordered source and destination replay hashes match their transaction receipts.',
                           'Every board, both observations, move, result and frame index matches the already dual-validated source.',
                           'All newly imported response contents, including clocks and optional metadata, match the source.',
                           'Every source ID is accepted in the shared journal; no increase in duplicate journal lines.',
                           'Destination remains the original store; own core lease released.'],
                   result_sha256=sha(OUT / 'result.json'), import_journal_sha256=sha(STORE / 'import-rows.jsonl'),
                   review_source_sha256=sha(Path(__file__)),
                   scope='Read-only archive reconciliation, not a second rules walk, new collection, hardware certification, model fit or deployment.')
    with (OUT / 'review.json').open('x') as stream:
        stream.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
