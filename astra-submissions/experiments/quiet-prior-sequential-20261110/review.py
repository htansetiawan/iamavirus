"""Independent raw-row arithmetic, source and native-control verification."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'astra-submissions/analysis/quiet-prior-sequential-20261110'


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    plan = json.loads((OUT / 'plan.json').read_text()); result = json.loads((OUT / 'result.json').read_text())
    assert json.loads((OUT / 'execution.json').read_text())['status'] == 'complete'
    for path, expected in plan['dependencies'].items(): assert sha(path) == expected, path
    calls = json.loads((OUT / 'calls.json').read_text())
    assert len(calls) == len(plan['jobs']) == 288
    assert [r['name'] for r in calls] == [r['name'] for r in plan['jobs']]
    assert result['calls_sha256'] == sha(OUT / 'calls.json') and result['plan_sha256'] == sha(OUT / 'plan.json')
    raw = {}; rows_verified = 0
    for call in calls:
        assert call['code'] == 0
        for suffix in ('stdout', 'stderr'):
            assert sha(OUT / (call['name'] + '.' + suffix)) == call[suffix + '_sha256']
        raw[call['name']] = [json.loads(s) for s in (OUT / (call['name'] + '.stdout')).read_text().splitlines()]
        rows_verified += len(raw[call['name']])
    records = []; timing = {'original': [], 'zero': [], 'learned': []}; collapses = {k: 0 for k in timing}
    exposure = {k: 0 for k in timing}; large = set()
    for game in plan['games']:
        for seed in range(len(plan['seeds'])):
            rows = {arm: raw[f"{game['game']}-s{seed}-{arm}"] for arm in timing}
            for arm, values in rows.items():
                assert len(values) == game['rows']
                assert not any(r['guard_bad_moves'] or (not r['ever_capped'] and not r['matches']) for r in values)
                timing[arm].extend(r['update_seconds'] for r in values)
                collapses[arm] += int(any(r['worlds'] == 0 for r in values))
                exposure[arm] += sum(r['full_update'] for r in values)
            for a, b in zip(rows['original'], rows['zero']):
                assert {k: v for k, v in a.items() if k not in ('update_seconds', 'guard_seconds')} == {
                    k: v for k, v in b.items() if k not in ('update_seconds', 'guard_seconds')}
            if any(r['decision'] and r['parents'] > 10000 for r in rows['original']): large.add(game['game'])
            for old, new in zip(rows['original'], rows['learned']):
                assert all(old[k] == new[k] for k in ('ply', 'decision', 'guard_applicable', 'king_label', 'queen_label'))
                if old['decision'] and old['ply'] >= 16:
                    records.append((game['game'], game['team'], old, new))
    assert len(records) == result['primary']
    unique = len({(g, a['ply']) for g, _, a, _ in records}); assert unique == result['distinct_primary']
    gains = {}
    for floor in (1e-9, 1e-12, 1e-15):
        gains[floor] = [math.log(max(new['truth_share'], floor)) - math.log(max(old['truth_share'], floor))
                        for _, _, old, new in records]
        assert abs(math.fsum(gains[floor]) / len(records) - result['sensitivity'][str(floor)]) < 1e-12
    for arm, position in (('original', 2), ('learned', 3)):
        nll = -math.fsum(math.log(max(r[position]['truth_share'], 1e-12)) for r in records) / len(records)
        support = sum(r[position]['matches'] > 0 for r in records)
        assert abs(nll - result['mean_truth_nll'][arm]) < 1e-12 and support == result['support'][arm]
    for arm, values in timing.items():
        assert abs(math.fsum(values) - result['time'][arm]['total']) < 1e-10
        assert abs(float(np.quantile(values, .95)) - result['time'][arm]['p95']) < 1e-12
    assert collapses == result['collapsed_case_seeds'] and exposure == result['full_updates']
    assert len(large) == result['large_regime_games']

    def bootstrap(selected, delta, seed):
        group_ids = [[g['game'] for g in plan['games'] if g['team'] == t] for t in plan['teams']]
        sums = {g['game']: [0., 0] for g in plan['games']}
        for row, value in zip(selected, delta):
            sums[row[0]][0] += value; sums[row[0]][1] += 1
        rng = np.random.default_rng(seed); estimates = []
        for _ in range(plan['bootstrap_draws']):
            chosen = [ids[i] for ids in group_ids for i in rng.integers(0, len(ids), len(ids))]
            estimates.append(sum(sums[g][0] for g in chosen) / sum(sums[g][1] for g in chosen))
        return np.quantile(estimates, [.025, .975])

    confidence = bootstrap(records, gains[1e-12], plan['seed'])
    assert abs(math.fsum(gains[1e-12]) / len(records) - result['gain']) < 1e-12
    assert max(abs(confidence - result['interval95'])) < 1e-10
    risk_rows = [r for r in records if r[2]['guard_applicable']]
    assert len(risk_rows) == result['risk_rows']
    for index, kind in enumerate(('king1', 'kingt', 'queen1', 'queent')):
        label = 'king_label' if kind.startswith('king') else 'queen_label'
        old = [(r[2][kind] - r[2][label]) ** 2 for r in risk_rows]
        new = [(r[3][kind] - r[3][label]) ** 2 for r in risk_rows]
        delta = [b - a for a, b in zip(old, new)]; m = result['native_guard_brier'][kind]
        assert abs(math.fsum(old) / len(old) - m['original']) < 1e-12
        assert abs(math.fsum(new) / len(new) - m['learned']) < 1e-12
        assert abs(math.fsum(delta) / len(delta) - m['delta']) < 1e-12
        assert max(abs(bootstrap(risk_rows, delta, plan['seed'] + 10 + index) - m['interval95'])) < 1e-10
        count = len({(r[0], r[2]['ply']) for r in risk_rows if r[2][label]})
        assert count == result['unique_positive_guard_events'][label]
    for arm, position in (('original', 2), ('learned', 3)):
        assert sum(r[position]['guard_available'] for r in risk_rows) == result['risk_available'][arm]
    for team in plan['teams']:
        values = [(row, delta) for row, delta in zip(records, gains[1e-12]) if row[1] == team]
        m = result['by_team'][team]
        assert len(values) == m['decisions'] and len({r[0] for r, _ in values}) == m['games']
        assert abs(math.fsum(v for _, v in values) / len(values) - m['gain']) < 1e-12
    g = plan['gate']; t = result['time']; r = result
    expected = dict(primary_coverage=r['primary'] >= g['primary_min'] and unique >= g['distinct_min'],
                    truth_support=r['support']['learned'] >= r['support']['original'],
                    gain=r['gain'] >= g['gain'], confidence=bool(confidence[0] > 0),
                    floor_sensitivity=all(v >= 0 for v in r['sensitivity'].values()),
                    no_extra_collapse=collapses['learned'] <= collapses['original'],
                    regime_coverage=len(large) >= g['large_games'] and exposure['original'] >= g['full_updates'],
                    priority_coverage=all(r['by_team'][n]['games'] >= g['priority_games'] for n in plan['priority']),
                    priority_nonregression=all(r['by_team'][n]['gain'] >= 0 for n in plan['priority']),
                    total_cost=t['learned']['total'] <= g['total_ratio'] * t['original']['total'],
                    p95_cost=t['learned']['p95'] <= max(g['p95_floor'], g['p95_ratio'] * t['original']['p95']),
                    guard_coverage=len(risk_rows) >= g['risk_rows'] and all(v >= g['positive_events'] for v in r['unique_positive_guard_events'].values()),
                    guard_availability=r['risk_available']['learned'] >= r['risk_available']['original'],
                    guard_nonregression=all(v['delta'] <= g['brier_tolerance'] for v in r['native_guard_brier'].values()))
    assert expected == r['conditions']
    expected_decision = 'real_clock_decision_design_allowed' if all(expected.values()) else 'close_frozen_full_head_sequential'
    assert expected_decision == r['decision']
    report = dict(at=datetime.now(timezone.utc).isoformat(), passed=True, calls=len(calls), raw_rows=rows_verified,
                  primary=len(records), distinct_primary=unique, conditions=expected,
                  result_sha256=sha(OUT / 'result.json'), calls_sha256=sha(OUT / 'calls.json'),
                  limitation='Independent source hashes/raw arithmetic/bootstrap/control audit. Does not rerun C or independently enumerate every emitted population. Guard targets are native approximations, not actual future outcomes.')
    with (OUT / 'independent-review.json').open('x') as stream: json.dump(report, stream, indent=2); stream.write('\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__': main()
