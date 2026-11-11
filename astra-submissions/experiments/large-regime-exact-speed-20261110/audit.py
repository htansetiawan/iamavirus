"""Recheck the stress gate from immutable trace outputs."""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median, quantiles
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def audit(experiment, arms, session, source_commit, pass_decision, fail_decision):
    out = ROOT/'astra-submissions/analysis'/experiment
    private = ROOT/'data/astra-spool'/experiment
    plan = read(private/'plan.json')
    result, execution, summary = (read(out/name) for name in ('result.json','execution.json','plan-summary.json'))
    assert execution['status']=='complete' and execution['result_sha256']==sha(out/'result.json')
    assert sha(private/'plan.json')==summary['plan_sha256']==result['plan_sha256']==execution['plan_sha256']
    assert all(sha(path)==digest for path,digest in plan['dependencies'].items())
    assert not any(row['owner']=='astra-'+experiment for row in read(ROOT/'chatroom/cores.json')['allocation'])
    calls = read(private/'calls.json')
    assert len(calls)==len(plan['jobs'])==72 and sha(private/'calls.json')==result['calls_sha256']
    by_game = defaultdict(dict)
    for call,job in zip(calls,plan['jobs']):
        assert call['code']==0 and all(call[key]==value for key,value in job.items())
        path = private/(call['game']+'-'+call['arm'])
        for suffix in ('stdout','stderr'):
            assert sha(path.with_suffix('.'+suffix))==call[suffix+'_sha256']
        by_game[call['game']][call['arm']] = [json.loads(line) for line in path.with_suffix('.stdout').read_text().splitlines()]
    timing = {arm:defaultdict(list) for arm in arms}
    game_ratios = {arm:[] for arm in arms[1:]}
    for game in plan['panel']:
        rows = by_game[game['game']]
        assert all(len(rows[arm])==game['rows'] for arm in arms)
        stable = lambda row: {k:v for k,v in row.items() if k not in ('update_seconds','guard_seconds')}
        for triple in zip(*(rows[arm] for arm in arms)):
            assert stable(triple[0])==stable(triple[1])==stable(triple[2])
            for arm,row in zip(arms,triple):
                timing[arm]['all'].append(row['update_seconds'])
                if row['decision'] and row['full_update']:
                    timing[arm]['full'].append(row['update_seconds'])
                if row['decision'] and row['parents']>10000:
                    timing[arm]['large'].append(row['update_seconds'])
                if row['guard_applicable']:
                    timing[arm]['guard'].append(row['guard_seconds'])
        baseline = math.fsum(row['update_seconds'] for row in rows['original'])
        for arm in arms[1:]:
            game_ratios[arm].append(math.fsum(row['update_seconds'] for row in rows[arm])/baseline)
    reference = timing['original']
    for key in ('full','large','guard'):
        assert len(reference[key])==result['counts'][key]
    assert len(reference['all'])==result['counts']['updates']==sum(row['rows'] for row in plan['panel'])
    for arm,values in timing.items():
        m = result['metrics'][arm]
        for key,times in values.items():
            seconds = math.fsum(times)
            assert abs(seconds-m['seconds'][key])<1e-10
            assert abs(seconds/math.fsum(reference[key])-m['ratio'][key])<1e-12
        assert abs(quantiles(values['all'],n=20,method='inclusive')[18]-m['p95'])<1e-12
        if arm!='original':
            assert abs(median(game_ratios[arm])-m['median_game_ratio'])<1e-12
            assert sum(r<1 for r in game_ratios[arm])==m['faster_games']
    combined = result['metrics']['combined']
    conditions = dict(parity=True,coverage=len(reference['all'])>=plan['update_min'] and
                      min(len(reference['full']),len(reference['large']))>=plan['cutoff_updates_min'],
                      aggregate_cost=combined['ratio']['all']<=plan['total_cost_max'],
                      median_game_cost=combined['median_game_ratio']<=plan['game_median_max'],
                      tail_cost=combined['p95']<=plan['tail_ratio_max']*result['metrics']['original']['p95'])
    if 'incremental_ratio_max' in plan:
        incremental = {key:math.fsum(timing['combined'][key])/math.fsum(timing['eager'][key]) for key in ('all','large')}
        assert all(abs(value-result['incremental_ratio_vs_eager'][key])<1e-12 for key,value in incremental.items())
        conditions['incremental_cost'] = all(value<=plan['incremental_ratio_max'] for value in incremental.values())
    assert conditions==result['conditions']
    assert result['decision']==(pass_decision if all(conditions.values()) else fail_decision)
    receipt = dict(at=datetime.now(timezone.utc).isoformat(), original_session=session, exit_code=0,
                 source_commit=source_commit,both_mirrors_verified_before_launch=True,
                 plan_sha256=execution['plan_sha256'], result_sha256=execution['result_sha256'], calls=len(calls),
                 checked_rows=len(reference['all'])*len(arms), dependencies=len(plan['dependencies']), core_released=True,
                 conditions=conditions, elapsed_seconds=execution['seconds'])
    with (out/'terminal-verification.json').open('x') as stream:
        json.dump(receipt,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    audit(HERE.name,('original','reverse','combined'),84426,'e9eed3486493f2c03ae1d0bf8fece3782481ada1',
          'exact_speed_full_clock_design_allowed','close_exact_speed_gate')
