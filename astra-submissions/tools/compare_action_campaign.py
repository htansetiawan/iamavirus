#!/usr/bin/env python3
"""Compare two completed fixed-node arms, keeping initial/fatal decisions separate."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(root, control, candidate, replays=None, candidate_root=None):
    campaign = json.loads((root / 'campaign.json').read_text())
    candidate_root = root if candidate_root is None else candidate_root
    other_campaign = json.loads((candidate_root / 'campaign.json').read_text())
    if any(campaign[k] != other_campaign[k] for k in ('nodes', 'stride')):
        raise ValueError('node budget or decision sampling differs')
    for name in ('benchmark', 'seats.txt', 'model_manifest.json', 'observe.onnx', 'score.onnx'):
        identities = [[v for k, v in c['inputs'].items() if Path(k).name == name]
                      for c in (campaign, other_campaign)]
        if any(len(v) != 1 for v in identities) or identities[0] != identities[1]:
            raise ValueError('cross-campaign frozen input differs: ' + name)
    arms = []
    for name, directory, c in ((control, root, campaign), (candidate, candidate_root, other_campaign)):
        state = c['arms'][name]
        if state['state'] != 'complete':
            raise ValueError('requested arm is not complete: ' + name)
        log = directory / (name + '.log')
        if sha(log) != state['log_sha256']:
            raise ValueError('completed arm log changed')
        rows = [json.loads(line.removeprefix('DECISION '))
                for line in log.read_text().splitlines() if line.startswith('DECISION ')]
        keyed = {(r['game'], r['side'], r['ply']): r for r in rows}
        if len(keyed) != len(rows) or len(rows) != state['decisions']:
            raise ValueError('duplicate or missing decisions')
        arms.append(keyed)
    a, b = arms
    if a.keys() != b.keys():
        raise ValueError('arms evaluated different decisions')
    for k in a:
        if any(a[k][f] != b[k][f] for f in ('sampled', 'terminal', 'safe_alternatives', 'legal_moves')):
            raise ValueError('truth/candidate labels differ: ' + repr(k))
    for c in (campaign, other_campaign):
        for name, digest in c['inputs'].items():
            if sha(Path(name)) != digest:
                raise ValueError('frozen input changed: ' + name)
    replay_cache, replay_hashes = {}, {}
    groups = defaultdict(list)
    for k, row in a.items():
        groups['all'].append(k)
        phase = 'terminal' if row['terminal'] else 'sampled_nonterminal'
        groups[phase].append(k)
        groups[phase + ('_white' if row['side'] == 0 else '_black')].append(k)
        if row['safe_alternatives'] > 0:
            groups[phase + '_avoidable'].append(k)
        if replays is not None:
            if row['game'] not in replay_cache:
                path = replays / row['game'] / 'replay.json'
                replay_cache[row['game']] = json.loads(path.read_text())
                replay_hashes[row['game']] = sha(path)
            replay = replay_cache[row['game']]
            actor = replay['white' if row['side'] == 0 else 'black']
            opponent = replay['black' if row['side'] == 0 else 'white']
            if actor == 'IAmAVirus':
                groups['IAmAVirus_' + phase].append(k)
                groups['IAmAVirus_' + phase + '_vs_' + opponent].append(k)
    results = {}
    for label, keys in groups.items():
        by_game = defaultdict(Counter)
        for k in keys:
            x, y = a[k], b[k]
            by_game[k[0]].update(decisions=1, control_fatal=int(x['king_loss']), candidate_fatal=int(y['king_loss']))
        names = sorted(by_game)
        sizes = np.array([by_game[n]['decisions'] for n in names])
        delta = np.array([by_game[n]['candidate_fatal'] - by_game[n]['control_fatal'] for n in names])
        indices = np.random.default_rng(253).integers(len(names), size=(10000, len(names)))
        sampled = delta[indices].sum(1) / sizes[indices].sum(1)
        results[label] = {'decisions': len(keys), 'games': len(names),
                          'control_fatal': sum(a[k]['king_loss'] for k in keys),
                          'candidate_fatal': sum(b[k]['king_loss'] for k in keys),
                          'changed_moves': sum(a[k]['move'] != b[k]['move'] for k in keys),
                          'saved': sum(a[k]['king_loss'] and not b[k]['king_loss'] for k in keys),
                          'new_fatal': sum(not a[k]['king_loss'] and b[k]['king_loss'] for k in keys),
                          'fatal_rate_candidate_minus_control': float(delta.sum() / sizes.sum()),
                          'paired_game_bootstrap_95': np.percentile(sampled, [2.5, 97.5]).tolist()}
    changes = [{'game': k[0], 'side': k[1], 'ply': k[2], 'control': a[k], 'candidate': b[k]}
               for k in sorted(a) if a[k]['king_loss'] != b[k]['king_loss']]
    return {'recorded_at': datetime.now(timezone.utc).isoformat(), 'root': str(root),
            'candidate_root': str(candidate_root),
            'campaign_state_at_read': campaign['state'], 'control': control, 'candidate': candidate,
            'candidate_campaign_state_at_read': other_campaign['state'],
            'arms': {control: campaign['arms'][control], candidate: other_campaign['arms'][candidate]},
            'inputs': campaign['inputs'], 'candidate_inputs': other_campaign['inputs'],
            'game_metadata_sha256': replay_hashes, 'groups': results, 'fatal_changes': changes,
            'limitations': ['Only requested completed arms are compared; other campaign arms may still run.',
                            'One seed; intervals cover games, not seed variability. Subgroups are exploratory.',
                            'Terminal decision is primary; repeated initial positions do not add terminal evidence.',
                            'Forced-history move safety, not a game outcome or Elo estimate.',
                            'Recorded wall times are not isolated CPU performance measurements.']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--control', required=True)
    p.add_argument('--candidate', required=True)
    p.add_argument('--candidate-root', type=Path)
    p.add_argument('--replays', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    report = compare(args.root, args.control, args.candidate, args.replays, args.candidate_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['groups'], indent=2))


if __name__ == '__main__':
    main()
