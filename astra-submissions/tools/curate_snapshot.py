#!/usr/bin/env python3
"""Audit replay overlap and build separate actor-only and labelled history pools.

No existing split changes. Test shards are read only for membership metadata;
their actor/target records are never deserialized or scored.
"""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'astra-submissions'), str(ROOT)]

from learning import _native, features, histories, ingest
from learning_experiments.ssl import ActorHistory


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def membership(path):
    """Read the known shard format's final metadata object, not its labels."""
    counts = Counter()
    decoder = json.JSONDecoder()
    with gzip.open(path, 'rt') as handle:
        for line in handle:
            _, marker, suffix = line.rpartition(',"metadata":')
            if not marker:
                raise ValueError('unexpected shard format; refusing to parse sealed targets')
            meta, end = decoder.raw_decode(suffix)
            if suffix[end:].strip() != '}':
                raise ValueError('metadata is not the final shard object')
            counts[meta['game_id']] += 1
    if any(n != 2 for n in counts.values()):
        raise ValueError('expected both player histories exactly once per game')
    return set(counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--known-raw', type=Path, default=ROOT / 'data/raw')
    parser.add_argument('--manifests', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.snapshot.resolve()
    collection = json.loads((source / 'collection.json').read_text())
    if collection['state'] != 'complete':
        parser.error('collection must finish first')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    native = source / 'native-source'
    native_sources = json.loads((native / 'sources.json').read_text())
    if any(sha(native / name) != digest for name, digest in native_sources.items()):
        raise ValueError('collector native snapshot changed')
    _native.ROOT, _native.BUILD_DIR = native, native / 'build'
    _native.LIBRARY = _native.BUILD_DIR / 'librules.so'
    if sha(_native.LIBRARY) != collection['native']['library_sha256']:
        raise ValueError('collector native library changed')
    known_rows = [json.loads(line) for line in (args.known_raw / 'accepted.jsonl').read_text().splitlines()]
    known_moves = {}
    for row in known_rows:
        if row['id'] in known_moves and known_moves[row['id']] != row['moves_sha256']:
            raise ValueError('conflicting recorded moves for known game')
        known_moves[row['id']] = row['moves_sha256']
    id_splits, move_splits = defaultdict(set), defaultdict(set)
    split_receipts = {}
    for path in args.manifests:
        manifest = json.loads(path.read_text())
        seen = set()
        for split, relative in manifest['shards'].items():
            shard = Path(relative)
            shard = shard if shard.is_absolute() else ROOT / shard
            ids = membership(shard)
            if seen & ids:
                raise ValueError('existing manifest contains overlapping game splits')
            seen.update(ids)
            key = manifest['version'] + ':' + split
            split_receipts[key] = {'games': len(ids), 'shard_sha256': sha(shard), 'manifest_sha256': sha(path)}
            for game in ids:
                if game not in known_moves:
                    raise ValueError('cannot audit duplicate move sequences for ' + game)
                id_splits[game].add(key)
                move_splits[known_moves[game]].add(key)
    journal = [json.loads(line) for line in (source / 'validation.jsonl').read_text().splitlines()]
    if sha(source / 'validation.jsonl') != collection['validation_sha256']:
        raise ValueError('collection journal changed')
    totals, overlaps = Counter(), Counter()
    index = []
    actor_fields = ('side', 'observations', 'phases', 'plies', 'decision_event_indices', 'own_actions')
    with gzip.open(output / 'episodes.jsonl.gz', 'wt') as labelled, \
         gzip.open(output / 'actor-observations.jsonl.gz', 'wt') as actors, \
         gzip.open(output / 'new-games.jsonl.gz', 'wt') as novel:
        for record in journal:
            if not record['accepted']:
                continue
            path = source / 'raw/games' / record['id'] / 'replay.json'
            if sha(path) != record['replay_sha256']:
                raise ValueError('accepted replay changed')
            replay = json.loads(path.read_text())
            states, problems = ingest.validate_replay(replay)
            if problems:
                raise ValueError('accepted replay no longer validates: ' + record['id'])
            known = id_splits[record['id']] | move_splits[record['moves_sha256']]
            overlaps.update(known)
            item = {'game': record['id'], 'moves_sha256': record['moves_sha256'],
                    'replay_sha256': record['replay_sha256'], 'known_splits': sorted(known),
                    'new_to_listed_splits': not known, 'created_at': record['createdAt'], 'decisions': 0}
            for side in (0, 1):
                episode = histories.build_episode(replay, states, side, ingest.RULES_FINGERPRINT, record['replay_sha256'])
                episode.metadata.split = 'unassigned-development'
                if episode.metadata.candidate_mismatches:
                    raise ValueError('actor-derived move candidates differ from truth: ' + record['id'])
                text = json.dumps(episode.to_dict(), separators=(',', ':')) + '\n'
                labelled.write(text)
                if not known:
                    novel.write(text)
                # Explicit whitelist: no true board, outcome, opponent's moves,
                # danger targets, legal truth, or expert target enters this file.
                actor = asdict(episode.actor)
                actor_only = {'actor': {k: actor[k] for k in actor_fields},
                              'metadata': {'game_id': record['id'], 'feature_version': features.FEATURE_VERSION,
                                           'action_version': features.ACTION_VERSION}}
                parsed = ActorHistory.from_record(actor_only)
                assert parsed.game_id == record['id'] and parsed.side == side
                actors.write(json.dumps(actor_only, separators=(',', ':')) + '\n')
                totals.update(episodes=1, decisions=episode.num_decisions,
                              observation_events=len(episode.actor.observations),
                              new_game_decisions=episode.num_decisions if not known else 0)
                item['decisions'] += episode.num_decisions
            totals.update(games=1, new_games=int(not known))
            index.append(item)
            if totals['games'] % 100 == 0:
                print(json.dumps(dict(totals)), flush=True)
    (output / 'index.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in index))
    receipt = {'completed_at': datetime.now(timezone.utc).isoformat(), 'state': 'complete',
               'snapshot': str(source), 'collection_sha256': sha(source / 'collection.json'),
               'feature_version': features.FEATURE_VERSION, 'native_library_sha256': sha(_native.LIBRARY),
               'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in
                                 (Path(__file__), ROOT / 'learning/histories.py', ROOT / 'learning/features.py',
                                  ROOT / 'learning/ingest.py', ROOT / 'learning/labels.py')},
               'counts': dict(totals), 'overlap_games': dict(overlaps), 'existing_splits': split_receipts,
               'artifacts_sha256': {p.name: sha(p) for p in output.iterdir() if p.is_file()},
               'test_membership_metadata_read': True, 'test_targets_deserialized': False,
               'training_split_changed': False,
               'limitations': ['New means absent by game ID and complete move hash from the listed manifests.',
                               'Shared openings and partial histories can still overlap.',
                               'All pools are development data; no sealed performance test or Elo claim.',
                               'Keep the game index when assigning splits, including for actor-only SSL.']}
    (output / 'curation.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'state': 'complete', 'counts': receipt['counts'], 'overlap_games': receipt['overlap_games']}), flush=True)


if __name__ == '__main__':
    main()
