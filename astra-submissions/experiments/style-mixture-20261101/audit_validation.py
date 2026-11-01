#!/usr/bin/env python3
"""Post-fit audit: reproduce static scores and report all taxonomy slices."""
import gzip
import json
from collections import defaultdict
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from learning import move_taxonomy
from model import sha

OLD = ROOT/'astra-submissions/analysis/temporal-prior-20261101'
OUT = ROOT/'astra-submissions/analysis/style-mixture-20261101'


def rows(path):
    with gzip.open(path, 'rt') as f:
        return [json.loads(line) for line in f]


def key(r):
    return r['game_index'], r['ply'], r['side']


def main():
    current = rows(OUT/'validation-scores.jsonl.gz')
    previous = {key(r): r for r in rows(OLD/'fit/validation-scores.jsonl.gz')}
    assert len(current) == len(previous)
    assert len({key(r) for r in current}) == len(current)
    discrepancy = 0
    for r in current:
        prior = previous[key(r)]
        assert r['ambiguous'] == prior['ambiguous']
        for k in ('logp', 'conditional_logp', 'observation_logp'):
            if k == 'logp' or r['ambiguous']:
                discrepancy = max(discrepancy, abs(r['scores']['static'][k]-prior['static'][k]))
    assert discrepancy < 1e-9, discrepancy
    manifest = json.loads((OLD/'data-v2/manifest.json').read_text())
    wanted = {r['game_index'] for r in current}
    labels = {}
    hashes = {}
    for g in manifest['games']:
        if g['index'] not in wanted:
            continue
        p = ROOT/g['replay_path']
        assert sha(p) == g['replay_sha256']
        lab = move_taxonomy.label_game(json.loads(p.read_text()))
        hashes[g['id']] = g['replay_sha256']
        for m in lab['moves']:
            labels[g['index'], m['ply']-1, m['side']] = m['tags']
    groups = defaultdict(list)
    for r in current:
        tags = labels[key(r)]
        for tag in ['all'] + [t for t in move_taxonomy.KEYS if t in tags]:
            groups[tag].append(r)
    report = {'positions': len(current), 'games': len(hashes),
              'static_max_difference_from_original_implementation': discrepancy,
              'taxonomy_source_sha256': sha(ROOT/'learning/move_taxonomy.py'),
              'model_files': json.loads((OUT/'fit/frozen-models.json').read_text()),
              'replay_hashes': hashes, 'by_tag': {},
              'scope': 'Descriptive reused-development slices; tags can use truth and future moves. No tags enter prediction.'}
    for tag in ['all'] + move_taxonomy.KEYS:
        items = groups[tag]
        amb = [r for r in items if r['ambiguous']]
        out = {'moves': len(items), 'games': len({r['game_index'] for r in items}),
               'ambiguous_moves': len(amb), 'models': {}}
        for arm in current[0]['scores']:
            def gain(rs, field):
                return float(np.mean([r['scores'][arm][field]-r['scores']['static'][field] for r in rs])) if rs else None
            out['models'][arm] = {'all_move_gain_vs_static': gain(items, 'logp'),
                                  'ambiguous_conditional_gain_vs_static': gain(amb, 'conditional_logp')}
        report['by_tag'][tag] = out
    (OUT/'taxonomy-audit.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: report[k] for k in ['positions', 'games', 'static_max_difference_from_original_implementation']}))


if __name__ == '__main__':
    main()
