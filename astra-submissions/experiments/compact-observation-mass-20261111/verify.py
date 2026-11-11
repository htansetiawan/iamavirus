"""Audit the ablation from stored rows and the paired timing controls."""
from collections import defaultdict
from datetime import datetime, timezone
import json
import math

import numpy as np

from build import OUT, PREVIOUS, ROOT, STORE, read, save, sha, stable

RISK = ('king1','kingt','queen1','queent')
ARMS = ('original','learned')  # Public legacy aggregate calls the preserved arm learned.


def read_rows(path,digest):
    assert sha(path)==digest,path
    return [json.loads(line) for line in path.read_text().splitlines()]


def check_close(observed,expected):
    assert abs(observed-expected)<1e-10,(observed,expected)


def main():
    plan, status, result = read(STORE/'plan.json'),read(OUT/'execution.json'),read(OUT/'result.json')
    assert status['status']=='complete' and status['result_sha256']==sha(OUT/'result.json')
    assert result['plan_sha256']==status['plan_sha256']==sha(STORE/'plan.json')
    assert all(sha(path)==digest for path,digest in plan['dependencies'].items())
    assert not any(row['owner']=='astra-'+OUT.name for row in read(ROOT/'chatroom/cores.json')['allocation'])
    assert result['calls_sha256']==sha(STORE/'calls.json')
    calls = read(STORE/'calls.json')
    assert len(calls)==len(plan['jobs'])==160
    current = {}
    for row,job in zip(calls,plan['jobs']):
        assert row['code']==0 and all(row[key]==value for key,value in job.items())
        label = f"{job['game']}-s{job['seed_index']}-{job['arm']}"
        assert sha(STORE/(label+'.stderr'))==row['stderr_sha256']
        current[label] = read_rows(STORE/(label+'.stdout'),row['stdout_sha256'])
    old = {row['name']:row for row in read(PREVIOUS/'calls.json')}
    observations = []
    times = defaultdict(list)
    collapses = defaultdict(int)
    full = defaultdict(int)
    large = set()
    measured_pairs = verified_rows = 0
    for game in plan['games']:
        for seed in range(len(plan['seeds'])):
            key = f"{game['game']}-s{seed}"
            native,unrestricted = (read_rows(PREVIOUS/(key+'-'+arm+'.stdout'),old[key+'-'+arm]['stdout_sha256'])
                                   for arm in ARMS)
            preserved = current[key+'-preserved']
            assert len(native)==len(unrestricted)==len(preserved)==game['rows']
            verified_rows += len(preserved)
            for name,rows in zip(ARMS,(native,preserved)):
                assert not any(r['guard_bad_moves'] or not r['matches'] and not r['ever_capped'] for r in rows)
                collapses[name] += int(any(not r['worlds'] for r in rows))
                full[name] += sum(r['full_update'] for r in rows)
            if any(row['decision'] and row['parents']>10000 for row in native):
                large.add(game['game'])
            if key+'-baseline' in current:
                paired = current[key+'-baseline']
                assert stable(paired)==stable(native)
                times['original'].extend(r['update_seconds'] for r in paired)
                times['preserved'].extend(r['update_seconds'] for r in preserved)
                measured_pairs+=1
            for a,b,c in zip(native,preserved,unrestricted):
                for field in ('ply','decision','guard_applicable','king_label','queen_label'):
                    assert a[field]==b[field]==c[field]
                if a['decision'] and a['ply']>=16:
                    observations.append((game,a,b,c))
    assert measured_pairs==32==result['paired_timing_calls']
    assert len(observations)==result['primary'] and len(large)==result['large_regime_games']
    distinct = len({(game['game'],base['ply']) for game,base,_,_ in observations})
    assert distinct==result['distinct_primary']
    assert dict(full)=={arm:result['full_updates'][arm] for arm in ARMS}
    assert dict(collapses)=={arm:result['collapsed_case_seeds'][arm] for arm in ARMS}
    gains = {floor:[math.log(max(new['truth_share'],floor))-math.log(max(base['truth_share'],floor))
                    for _,base,new,_ in observations] for floor in (1e-9,1e-12,1e-15)}
    n = len(observations)
    for i,arm in enumerate(ARMS,1):
        check_close(-math.fsum(math.log(max(row[i]['truth_share'],1e-12)) for row in observations)/n,result['mean_truth_nll'][arm])
        assert sum(row[i]['matches']>0 for row in observations)==result['support'][arm]
    for floor,values in gains.items():
        check_close(math.fsum(values)/n,result['sensitivity'][str(floor)])
    check_close(math.fsum(gains[1e-12])/n,result['gain'])
    game_totals = defaultdict(list)
    for (game,*_),value in zip(observations,gains[1e-12]):
        game_totals[game['game']].append(value)
    grouped = [np.array([(math.fsum(game_totals[g['game']]),len(game_totals[g['game']]))
                         for g in plan['games'] if g['team']==team]) for team in plan['teams']]
    rng = np.random.default_rng(plan['seed'])
    draws = []
    for _ in range(plan['bootstrap_draws']):
        samples = np.concatenate([rows[rng.integers(len(rows),size=len(rows))] for rows in grouped])
        gain,count = samples.sum(0)
        draws.append(gain/count)
    interval = np.quantile(draws,[.025,.975])
    for x,y in zip(interval,result['interval95']):
        check_close(float(x),y)
    for team in plan['teams']:
        rows = [row for row in observations if row[0]['team']==team]
        unrestricted = math.fsum(math.log(max(new['truth_share'],1e-12))-math.log(max(old['truth_share'],1e-12))
                                 for _,_,new,old in rows)/len(rows)
        check_close(unrestricted,result['gain_vs_unconstrained'][team])
        assert len(rows)==result['by_team'][team]['decisions']
        check_close(math.fsum(value for (game,*_),value in zip(observations,gains[1e-12]) if game['team']==team)/len(rows),
                    result['by_team'][team]['gain'])
    risk_rows = [row for row in observations if row[1]['guard_applicable']]
    assert len(risk_rows)==result['risk_rows']
    positives = {label:len({(game['game'],base['ply']) for game,base,_,_ in risk_rows if base[label]})
                 for label in ('king_label','queen_label')}
    assert positives==result['unique_positive_guard_events']
    brier = {}
    for kind in RISK:
        label = 'king_label' if kind.startswith('king') else 'queen_label'
        brier[kind] = []
        for i,arm in enumerate(ARMS,1):
            score = math.fsum((row[i][kind]-row[i][label])**2 for row in risk_rows)/len(risk_rows)
            check_close(score,result['native_guard_brier'][kind][arm])
            brier[kind].append(score)
        check_close(brier[kind][1]-brier[kind][0],result['native_guard_brier'][kind]['delta'])
    available = {arm:sum(row[i]['guard_available'] for row in risk_rows) for i,arm in enumerate(ARMS,1)}
    assert available==result['risk_available']
    for arm,values in times.items():
        check_close(math.fsum(values),result['paired_time'][arm]['total'])
        check_close(float(np.quantile(values,.95)),result['paired_time'][arm]['p95'])
    g = plan['gate']
    metrics = result['by_team']
    base,preserved = (result['paired_time'][arm] for arm in ('original','preserved'))
    expected = dict(primary_coverage=n>=g['primary_min'] and distinct>=g['distinct_min'],
                    truth_support=result['support']['learned']>=result['support']['original'],
                    gain=result['gain']>=g['gain'],confidence=bool(interval[0]>0),
                    floor_sensitivity=all(math.fsum(values)>=0 for values in gains.values()),
                    no_extra_collapse=collapses['learned']<=collapses['original'],
                    regime_coverage=len(large)>=g['large_games'] and full['original']>=g['full_updates'],
                    priority_coverage=all(metrics[team]['games']>=g['priority_games'] for team in plan['priority']),
                    priority_nonregression=all(metrics[team]['gain']>=0 for team in plan['priority']),
                    total_cost=preserved['total']<=g['total_ratio']*base['total'],
                    p95_cost=preserved['p95']<=max(g['p95_floor'],g['p95_ratio']*base['p95']),
                    guard_coverage=len(risk_rows)>=g['risk_rows'] and min(positives.values())>=g['positive_events'],
                    guard_availability=available['learned']>=available['original'],
                    guard_nonregression=all(new-old<=g['brier_tolerance'] for old,new in brier.values()))
    assert expected==result['conditions']
    assert result['decision']==('fresh_confirmation_design_allowed' if all(expected.values()) else 'close_observed_mass_configuration')
    receipt = dict(at=datetime.now(timezone.utc).isoformat(),session=12604,exit_code=0,scored_calls=len(calls),
                   preserved_rows_verified=verified_rows,paired_timing_calls=measured_pairs,dependencies=len(plan['dependencies']),
                   source_commit='f6a1de129e0848f50efe6ebf6cd2189aad0adc68',both_mirrors_verified_before_launch=True,
                   plan_sha256=sha(STORE/'plan.json'),result_sha256=sha(OUT/'result.json'),core_released=True,
                   decision=result['decision'],failed_conditions=[k for k,v in result['conditions'].items() if not v])
    save(OUT/'terminal-verification.json',receipt)
    print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    main()
