"""Verify target replicas' recorded dataset and eligible version coverage.

Read-only: no model inference, fitting, or corpus changes. Eligibility describes
the recorded dataset/filter, not proof that every eligible example was sampled.
"""
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'deeprl-table-audit-20261025'))
from prepare_risk_run import dataset_identity


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    provenance = json.loads((HERE / 'target-replica-provenance.json').read_bytes())
    manifest_path = ROOT / 'data/manifests/v4.json'
    manifest = json.loads(manifest_path.read_bytes())
    for replica in provenance:
        assert sha(Path(replica['checkpoint'])) == replica['checkpoint_sha256']
        assert replica['dataset_content_sha256'] == manifest['content_sha256']
    eligible = {r['name']: {} for r in provenance}
    chosen_games = set()
    for split, filename in manifest['shards'].items():
        with gzip.open(ROOT / filename, 'rt') as stream:
            for line in stream:
                episode = json.loads(line); meta = episode['metadata']; actor = episode['actor']
                decisions = len(actor['decision_event_indices'])
                for replica in provenance:
                    if meta['player_id'] not in replica['config']['players']:
                        continue
                    if split == 'train' and decisions == 0:
                        continue
                    selected = eligible[replica['name']].setdefault(split, [])
                    selected.append({'game': meta['game_id'], 'side': actor['side'],
                                     'played_version': meta['played_version'], 'decisions': decisions})
                    chosen_games.add(meta['game_id'])
    accepted, dates = [], {}
    accepted_path = ROOT / 'data/raw/accepted.jsonl'
    with accepted_path.open() as stream:
        for line in stream:
            row = json.loads(line); accepted.append({'id': row['id']})
            if row['id'] in chosen_games and row.get('createdAt'):
                dates[row['id']] = row['createdAt']
    _, verified = dataset_identity(manifest, accepted)
    latest = json.loads((HERE / 'latest.json').read_bytes())
    leaderboard = json.loads((Path(latest['snapshot']) / 'leaderboard.json').read_bytes())
    players = {p['name'].lower(): p for p in leaderboard['players']}
    results = []
    for replica in provenance:
        name = replica['name'].removeprefix('replica-')
        active = players[name]['activeVersion']
        splits = {}
        for split, rows in eligible[replica['name']].items():
            timestamps = [datetime.fromisoformat(dates[r['game']]) for r in rows if r['game'] in dates]
            splits[split] = {'eligible_episodes': len(rows), 'unique_games': len({r['game'] for r in rows}),
                             'decisions': sum(r['decisions'] for r in rows),
                             'episodes_by_played_version': dict(Counter(str(r['played_version']) for r in rows)),
                             'current_version_episodes': sum(r['played_version'] == active for r in rows),
                             'dated_episodes': len(timestamps),
                             'earliest_completion': min(timestamps).isoformat() if timestamps else None,
                             'latest_completion': max(timestamps).isoformat() if timestamps else None,
                             'episodes': rows}
        results.append({'name': name, 'current_arena_version': active,
                        'checkpoint_sha256': replica['checkpoint_sha256'],
                        'checkpoint_step': replica['step'], 'checkpoint_epoch': replica['epoch'],
                        'splits': splits})
    result = {'audited_at': datetime.now(timezone.utc).isoformat(), 'auditor_sha256': sha(Path(__file__)),
              'provenance_sha256': sha(HERE / 'target-replica-provenance.json'),
              'accepted_metadata_sha256': sha(accepted_path), 'manifest_sha256': sha(manifest_path),
              'dataset_verified': verified, 'arena_snapshot_at': latest['at'], 'replicas': results,
              'limits': ['Counts describe eligible fine-tuning episodes under the recorded player filter; unknown CLI limits or sampling are not reconstructed.',
                         'Version coverage is not a measurement of imitation fidelity or simulated playing strength.',
                         'Matching current version numbers alone would not prove a replica matches a live bot.',
                         'A replica may generalize across versions; absent version coverage is not proof of uselessness.']}
    (HERE / 'target-replica-data-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'dataset_verified': verified,
                     'replicas': [{**{k: v for k, v in r.items() if k != 'splits'},
                                   'splits': {s: {k: v for k, v in d.items() if k != 'episodes'} for s, d in r['splits'].items()}}
                                  for r in results]}, indent=2))


if __name__ == '__main__':
    main()
