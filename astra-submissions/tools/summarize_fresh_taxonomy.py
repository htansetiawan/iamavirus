#!/usr/bin/env python3
"""Read a finished fresh gate; separate paired changes, controls and repetitions."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning import ingest


def paired(rows, arm, field, threshold=None):
    good = [r for r in rows if 'error' not in r['arms']['v35'] and 'error' not in r['arms'][arm]]
    def event(v):
        if field == 'fatal_or_exchange':
            return (v.get('legal') is False or v.get('fatal', False)
                    or v.get('forced_king_loss_after_capture', False)
                    or (v.get('exchange_loss') or 0) >= 2)
        value = v.get(field)
        return bool(value) if threshold is None else value is not None and value >= threshold
    fixed = []; broken = []
    for r in good:
        old, new = event(r['arms']['v35']), event(r['arms'][arm])
        key = f"{r['case']['game']}:{r['case']['ply']}"
        if old and not new:
            fixed.append(key)
        if new and not old:
            broken.append(key)
    return {'n': len(good), 'fixed': fixed, 'broken': broken, 'net_fixed': len(fixed)-len(broken)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('directory', type=Path)
    args = ap.parse_args(); out = args.directory
    frozen = json.loads((out/'cases.json').read_text())
    rows = [json.loads(l) for l in (out/'results.jsonl').read_text().splitlines()]
    expected = {(c['game'], c['ply']) for c in frozen['cases']}
    actual = [(r['case']['game'], r['case']['ply']) for r in rows]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError('run incomplete or duplicated; no final report')
    states_by_game = {}; safe_cases = []; labels = []
    for r in rows:
        c = r['case']; gid = c['game']
        if gid not in states_by_game:
            payload = Path(c['replay_path']).read_bytes()
            assert hashlib.sha256(payload).hexdigest() == c['replay_sha256']
            states, errors = ingest.validate_replay(json.loads(payload)); assert not errors
            states_by_game[gid] = states
        state = states_by_game[gid][c['ply']]
        safe = [m for m in state.board.legal_moves() if not state.board.move_loses_king(m)]
        labels.append({'game': gid, 'ply': c['ply'], 'safe_moves': safe})
        if safe:
            safe_cases.append(r)
    report = {'cases': len(rows), 'games': len(states_by_game), 'with_safe_alternative': len(safe_cases),
              'paired_vs_v35': {}, 'by_opponent': {}, 'by_cohort': {}}
    for arm in ('v37', 'v35_repeat'):
        report['paired_vs_v35'][arm] = {
            'fatal_where_safe_exists': paired(safe_cases, arm, 'fatal'),
            'exchange_loss_ge2': paired(rows, arm, 'exchange_loss', 2),
            'queen_exchange_loss_ge4': paired(rows, arm, 'queen_exchange_loss', 4),
            'fatal_or_exchange_loss_ge2': paired(rows, arm, 'fatal_or_exchange'),
            'forced_king_loss_after_capture': paired(rows, arm, 'forced_king_loss_after_capture')}
    for dim in ('opponent', 'cohort'):
        groups = defaultdict(list)
        for r in rows:
            values = [r['case']['opponent']] if dim == 'opponent' else r['case']['cohorts']
            for key in values:
                groups[key].append(r)
        for key, group in groups.items():
            report['by_'+dim][key] = {'cases': len(group), 'v37': {
                'fatal': paired(group, 'v37', 'fatal'),
                'exchange_loss_ge2': paired(group, 'v37', 'exchange_loss', 2)}}
    report['limitations'] = ['Small deliberately stratified diagnostic sample; not a win-rate or Elo estimate.',
                             'King fatal is immediate. Exchange labels use an omniscient single capture then our best safe response, not the opponent policy or a full tactical search.',
                             'No recorded replies after divergence. Truth never supplied to either bot.',
                             'No significance claim from treating correlated decisions as independent games.']
    (out/'case-labels.json').write_text(json.dumps(labels, indent=2)+'\n')
    (out/'paired-summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
