"""Independently reduce the frozen confirmation outputs and verify the verdict."""

from collections import Counter, defaultdict
import json
import math

import numpy as np

from confirm import ARMS, HERE, OUT, ROOT, STORE, now, read, save, sha

RISK = ('king1', 'kingt', 'queen1', 'queent')
FLOORS = (1e-9, 1e-12, 1e-15)


def audit_calls(plan):
    expected = read(STORE/'calls.json')
    assert len(expected) == len(plan['jobs']) == 4*len(plan['games'])
    paired = defaultdict(dict)
    for row, job in zip(expected, plan['jobs']):
        assert row['code'] == 0 and all(row[key] == value for key, value in job.items())
        tag = f"{job['game']}-s{job['seed_index']}-{job['arm']}"
        for name in ('stdout', 'stderr'):
            assert sha(STORE/(tag+'.'+name)) == row[name+'_sha256']
        lines = (STORE/(tag+'.stdout')).read_text().splitlines()
        paired[job['game'], job['seed_index']][job['arm']] = [json.loads(line) for line in lines]
    return paired


def reduce(plan, paired):
    statistics = defaultdict(list)
    support, collapse, full, available = (Counter() for _ in range(4))
    duration, errors = defaultdict(list), defaultdict(list)
    positive = defaultdict(set)
    large = set()
    risk_rows = 0
    audited_rows = 0
    for game in plan['games']:
        for seed in range(len(plan['seeds'])):
            cases = paired[game['game'], seed]
            assert set(cases) == set(ARMS)
            for arm, rows in cases.items():
                assert [row['ply'] for row in rows] == list(range(1, game['rows']+1))
                assert all((row['ever_capped'] or row['matches']) and not row['guard_bad_moves'] for row in rows)
                assert all(0 <= row['truth_share'] <= 1 and 0 <= row['update_seconds'] for row in rows)
                duration[arm].extend(row['update_seconds'] for row in rows)
                collapse[arm] += any(not row['worlds'] for row in rows)
                full[arm] += sum(row['full_update'] for row in rows)
                audited_rows += len(rows)
            for old, new in zip(*(cases[arm] for arm in ARMS)):
                for field in ('ply', 'decision', 'guard_applicable', 'king_label', 'queen_label'):
                    assert old[field] == new[field]
                if not old['decision']:
                    continue
                if old['parents'] > 10000:
                    large.add(game['game'])
                if old['ply'] < 16:
                    continue
                gain = [math.log(max(new['truth_share'], floor))-math.log(max(old['truth_share'], floor)) for floor in FLOORS]
                statistics[game['game']].append((old['ply'], gain))
                for arm, row in zip(ARMS, (old, new)):
                    support[arm] += row['matches'] > 0
                if not old['guard_applicable']:
                    continue
                risk_rows += 1
                for kind in RISK:
                    label = kind[:4]+'_label' if kind.startswith('king') else 'queen_label'
                    if old[label]:
                        positive[label].add((game['game'], old['ply']))
                    for arm, row in zip(ARMS, (old, new)):
                        assert 0 <= row[kind] <= 1
                        errors[kind, arm].append((row[kind]-row[label])**2)
                for arm, row in zip(ARMS, (old, new)):
                    available[arm] += row['guard_available']
    return dict(statistics=statistics, support=support, collapse=collapse, full=full,
                available=available, duration=duration, errors=errors, large=large,
                positive={label:len(positive[label]) for label in ('king_label','queen_label')},
                risk_rows=risk_rows, audited_rows=audited_rows)


def check(plan, result, data):
    rows = data['statistics']
    flattened = [delta for game in plan['games'] for _, delta in rows[game['game']]]
    primary = len(flattened)
    distinct = sum(len({ply for ply, _ in game}) for game in rows.values())
    assert primary == result['primary'] and distinct == result['distinct_primary']
    gains = {str(floor): math.fsum(row[i] for row in flattened)/primary for i, floor in enumerate(FLOORS)}
    close = lambda a, b: math.isclose(a, b, abs_tol=1e-10, rel_tol=0)
    assert all(close(value, result['sensitivity'][key]) for key, value in gains.items())
    assert close(gains['1e-12'], result['gain'])
    assert data['large'] and len(data['large']) == result['large_regime_games']
    for key, label in (('support', 'support'), ('collapse','collapsed_case_seeds'),
                       ('full','full_updates'), ('available','risk_available')):
        assert all(data[key][arm] == result[label][arm] for arm in ARMS)
    assert data['positive'] == result['unique_positive_guard_events'] and data['risk_rows'] == result['risk_rows']
    blocks = []
    for team in plan['teams']:
        games = [rows[g['game']] for g in plan['games'] if g['team'] == team]
        block = np.array([(math.fsum(value[1] for _,value in game),len(game)) for game in games])
        blocks.append(block)
        numer, denom = block.sum(0)
        measured = result['by_team'][team]
        assert measured['games'] == sum(bool(game) for game in games) and measured['decisions'] == denom
        assert close(numer/denom, measured['gain'])
    rng = np.random.default_rng(plan['seed'])
    estimates = []
    for _ in range(plan['bootstrap_draws']):
        draws = np.concatenate([block[rng.integers(len(block),size=len(block))] for block in blocks])
        num, den = draws.sum(0)
        estimates.append(num/den)
    interval = np.quantile(estimates, [.025,.975])
    assert all(close(a,b) for a,b in zip(interval, result['interval95']))
    for kind in RISK:
        by_arm = result['native_guard_brier'][kind]
        old, new = (math.fsum(data['errors'][kind,arm])/data['risk_rows'] for arm in ARMS)
        assert close(by_arm['original'],old) and close(by_arm['learned'],new) and close(by_arm['delta'],new-old)
    for arm in ARMS:
        t = data['duration'][arm]
        assert close(math.fsum(t),result['time'][arm]['total'])
        assert close(float(np.quantile(t,.95)),result['time'][arm]['p95'])
    g, d = plan['gate'], result['by_team']
    base, learned = (result['time'][arm] for arm in ARMS)
    expected = dict(
        primary_coverage=primary>=g['primary_min'] and distinct>=g['distinct_min'],
        truth_support=data['support']['learned']>=data['support']['original'],
        gain=gains['1e-12']>=g['gain'], confidence=bool(interval[0]>0),
        floor_sensitivity=min(gains.values())>=0,
        no_extra_collapse=data['collapse']['learned']<=data['collapse']['original'],
        regime_coverage=len(data['large'])>=g['large_games'] and data['full']['original']>=g['full_updates'],
        priority_coverage=all(d[team]['games']>=g['priority_games'] for team in plan['priority']),
        priority_nonregression=all(d[team]['gain']>=0 for team in plan['priority']),
        total_cost=learned['total']<=g['total_ratio']*base['total'],
        p95_cost=learned['p95']<=max(g['p95_floor'],g['p95_ratio']*base['p95']),
        guard_coverage=data['risk_rows']>=g['risk_rows'] and min(data['positive'].values())>=g['positive_events'],
        guard_availability=data['available']['learned']>=data['available']['original'],
        guard_nonregression=all(result['native_guard_brier'][kind]['delta']<=g['brier_tolerance'] for kind in RISK))
    assert expected == result['conditions']
    return expected


def main():
    plan, state, result = (read(path) for path in (STORE/'plan.json', OUT/'execution.json', OUT/'result.json'))
    assert state['status'] == 'complete'
    assert sha(STORE/'plan.json') == state['plan_sha256'] == result['plan_sha256']
    assert sha(OUT/'result.json') == state['result_sha256']
    assert sha(STORE/'calls.json') == result['calls_sha256']
    assert all(sha(path) == digest for path, digest in plan['dependencies'].items())
    assert not any(row['owner'] == 'astra-'+HERE.name for row in read(ROOT/'chatroom/cores.json')['allocation'])
    paired = audit_calls(plan)
    audited = reduce(plan, paired)
    conditions = check(plan, result, audited)
    expected = 'full_clock_integration_design_allowed' if all(conditions.values()) else 'close_fixed_mass_prior_confirmation'
    assert expected == result['decision']
    receipt = dict(at=now(), plan_sha256=state['plan_sha256'], result_sha256=state['result_sha256'],
                   calls=2*len(paired), paired_calls=len(paired), rows=audited['audited_rows'],
                   dependencies=len(plan['dependencies']), core_released=True,
                   failed=[key for key,value in conditions.items() if not value], decision=expected)
    save(OUT/'terminal-verification.json',receipt)
    print(json.dumps(receipt),flush=True)


if __name__ == '__main__':
    main()
