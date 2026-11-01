#!/usr/bin/env python3
"""Post-hoc expectation of the recorded root mixtures on the true boards.

This is not a new search, rollout, equilibrium certificate or strength test.
An action's limited tactical label is weighted by the already-recorded root
probability. No parameters are fitted and no live policy changes.
"""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'astra-submissions/tools')]
from learning import ingest
from fresh_taxonomy_gate import exchange_probe

OUT = ROOT/'astra-submissions/analysis/frozen-tree-20261101'
reports = []
for directory in [OUT, OUT/'early']:
    plan = json.loads((directory/'plan.json').read_text())
    rows = json.loads((directory/'labelled.json').read_text()); cases = {c['name']:c for c in plan['cases']}
    records = []
    for row in rows:
        case = cases[row['case']]
        replay = json.loads((ROOT/'data/raw/games'/case['game']/'replay.json').read_text())
        states, errors = ingest.validate_replay(replay); assert not errors
        state = states[case['ply']]; snapshot = row['snapshots'][0]
        actions = []
        for action in snapshot['actions']:
            if action['probability'] <= 1e-12:
                continue
            actions.append({**action, 'probe': exchange_probe(state, action['move'])})
        total = sum(a['probability'] for a in actions); assert total > 1-1e-9
        expected_fatal = sum(a['probability']*a['probe']['fatal'] for a in actions)
        expected_material = sum(a['probability']*(a['probe']['exchange_loss'] or 0) for a in actions)
        # Fatal outcomes are reported separately, not priced as zero overall loss.
        expected_material_event = sum(a['probability']*((a['probe']['exchange_loss'] or 0)>=2) for a in actions)
        records.append({'case': row['case'], 'original_move': snapshot['selected'],
                        'original_probe': snapshot['truth_probe'], 'mixed_fatal': expected_fatal,
                        'mixed_material_loss': expected_material, 'mixed_material_event': expected_material_event,
                        'actions': actions})
    reports.append({'panel': directory.name, 'cases': len(records),
                    'argmax_fatal': sum(r['original_probe']['fatal'] for r in records),
                    'mixed_expected_fatal': sum(r['mixed_fatal'] for r in records),
                    'argmax_material_events': sum((r['original_probe']['exchange_loss'] or 0)>=2 for r in records),
                    'mixed_expected_material_events': sum(r['mixed_material_event'] for r in records),
                    'argmax_material_points': sum(r['original_probe']['exchange_loss'] or 0 for r in records),
                    'mixed_expected_material_points': sum(r['mixed_material_loss'] for r in records),
                    'records': records})
(OUT/'mixture-diagnostic.json').write_text(json.dumps({'scope':__doc__,'panels':reports},indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k!='records'} for r in reports],indent=2))
