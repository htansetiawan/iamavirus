#!/usr/bin/env python3
"""Prepare current-version, whole-game holdouts for opponent-policy calibration.

Uses the project's existing validated actor/target separation and feature cache.
Only the named reference team's seat becomes an imitation episode.
"""
import argparse
import gzip
import hashlib
import json
import sys
import yaml
from collections import Counter
from contextlib import ExitStack
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning import dataset, features, histories, ingest, feature_cache  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source', type=Path)
    args = ap.parse_args()
    source = json.loads(args.source.read_text())
    out = args.source.parent / 'dataset'; out.mkdir(exist_ok=True)
    if (out/'manifest.json').exists():
        raise FileExistsError('Prepared dataset already exists; use a new collection directory')
    rows = source['games']
    for row in rows:
        rp = json.loads(Path(row['replay_path']).read_text())
        row['moves_sha256'] = ingest.replay_hash(rp)
    splits = dataset.assign_splits(rows, (.7, .15, .15), chronological=True)
    stats = {s: Counter() for s in dataset.SPLITS}
    digest = hashlib.sha256(); mismatches = []
    with ExitStack() as stack:
        writers = {s: stack.enter_context(gzip.open(out / f'{s}.jsonl.gz', 'wt')) for s in dataset.SPLITS}
        for i, row in enumerate(rows):
            data = Path(row['replay_path']).read_bytes()
            assert hashlib.sha256(data).hexdigest() == row['replay_sha256']
            rp = json.loads(data); states, problems = ingest.validate_replay(rp)
            assert not problems, (row['id'], problems)
            split = splits[row['id']]
            row['split'] = split
            for side, key in enumerate(('white', 'black')):
                team = source['teams'].get(rp[key])
                if not team or rp.get(key+'Version') != team['version']:
                    continue
                ep = histories.build_episode(rp, states, side, ingest.RULES_FINGERPRINT, row['replay_sha256'])
                ep.metadata.split = split
                if ep.metadata.candidate_mismatches:
                    mismatches.append({'id': row['id'], 'side': side, 'cases': ep.metadata.candidate_mismatches})
                line = json.dumps(ep.to_dict(), separators=(',', ':'))
                writers[split].write(line+'\n'); digest.update(line.encode())
                stats[split]['episodes'] += 1; stats[split]['decisions'] += ep.num_decisions
                stats[split][rp[key]] += 1
            if (i+1) % 200 == 0: print('episodes prepared', i+1, '/', len(rows), flush=True)
    if mismatches:
        (out/'candidate-mismatches.json').write_text(json.dumps(mismatches,indent=2))
        raise ValueError('Actor-derived move sets disagree with the referee; do not train')
    manifest = {'version': 'references-20261030', 'feature_version': features.FEATURE_VERSION,
                'action_version': features.ACTION_VERSION, 'rules_fingerprint': ingest.RULES_FINGERPRINT,
                'content_sha256': digest.hexdigest(), 'counts': {s:dict(v) for s,v in stats.items()},
                'shards': {s:str(out/f'{s}.jsonl.gz') for s in dataset.SPLITS},
                'source_manifest': str(args.source), 'source_games': len(rows),
                'split_method': 'chronological_duplicate_groups', 'candidate_mismatches': []}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'game-splits.json').write_text(json.dumps(rows,indent=2)+'\n')
    for split in dataset.SPLITS:
        cached=feature_cache.build_split(Path(manifest['shards'][split]),out/'cache'/split)
        print('cache',split,{k:v for k,v in cached.items() if k!='players'},flush=True)
    feature_cache.verify(out/'manifest.json',out/'cache',trials=5)
    for name, team in source['teams'].items():
        label=name.lower()
        config={'pretrain': {'init_checkpoint': str(ROOT/f'checkpoints/replica-{label}/best.pt'),
                            'players': [team['id']], 'feature_cache': str(out/'cache'),
                            'window':64, 'sequences_per_batch':8, 'accumulation_steps':1,
                            'learning_rate': 0.00005, 'weight_decay':0.0001, 'grad_clip':1.0,
                            'epochs':3, 'select_on':'policy', 'loss_weights':{'policy':1.0,'belief':0.0,'danger':0.0,'value':0.0},
                            'mixed_precision':True, 'seed':730, 'validation_sequences':128,
                            'device':'cuda'}}
        (out/f'{label}-config.yaml').write_text(yaml.safe_dump(config))
    print('READY',str(out/'manifest.json'),manifest['counts'],flush=True)


if __name__ == '__main__': main()
