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
OUT = ROOT/'astra-submissions/analysis'/HERE.name
PRIVATE = ROOT/'data/astra-spool'/HERE.name
ARMS = ('original','reverse','combined')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    plan = read(PRIVATE/'plan.json')
    result, execution, summary = (read(OUT/name) for name in ('result.json','execution.json','plan-summary.json'))
    assert execution['status']=='complete' and execution['result_sha256']==sha(OUT/'result.json')
    assert sha(PRIVATE/'plan.json')==summary['plan_sha256']==result['plan_sha256']==execution['plan_sha256']
    assert all(sha(path)==digest for path,digest in plan['dependencies'].items())
    assert not any(row['owner']=='astra-'+HERE.name for row in read(ROOT/'chatroom/cores.json')['allocation'])
    calls = read(PRIVATE/'calls.json')
    assert len(calls)==len(plan['jobs'])==72 and sha(PRIVATE/'calls.json')==result['calls_sha256']
    by_game = defaultdict(dict)
    for call,job in zip(calls,plan['jobs']):
        assert call['code']==0 and all(call[key]==value for key,value in job.items())
        path = PRIVATE/(call['game']+'-'+call['arm'])
        for suffix in ('stdout','stderr'):
            assert sha(path.with_suffix('.'+suffix))==call[suffix+'_sha256']
        by_game[call['game']][call['arm']] = [json.loads(line) for line in path.with_suffix('.stdout').read_text().splitlines()]
    timing = {arm:defaultdict(list) for arm in ARMS}
    game_ratios = {arm:[] for arm in ARMS[1:]}
    for game in plan['panel']:
        rows = by_game[game['game']]
        assert all(len(rows[arm])==game['rows'] for arm in ARMS)
        stable = lambda row: {k:v for k,v in row.items() if k not in ('update_seconds','guard_seconds')}
        for triple in zip(*(rows[arm] for arm in ARMS)):
            assert stable(triple[0])==stable(triple[1])==stable(triple[2])
            for arm,row in zip(ARMS,triple):
                timing[arm]['all'].append(row['update_seconds'])
                if row['decision'] and row['full_update']:
                    timing[arm]['full'].append(row['update_seconds'])
                if row['decision'] and row['parents']>10000:
                    timing[arm]['large'].append(row['update_seconds'])
                if row['guard_applicable']:
                    timing[arm]['guard'].append(row['guard_seconds'])
        baseline = math.fsum(row['update_seconds'] for row in rows['original'])
        for arm in ARMS[1:]:
            game_ratios[arm].append(math.fsum(row['update_seconds'] for row in rows[arm])/baseline)
    reference = timing['original']
    for key in ('full','large','guard'):
        assert len(reference[key])==result['counts'][key]
    assert len(reference['all'])==result['counts']['updates']==summary['historical_frames']
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
    assert conditions==result['conditions']
    assert result['decision']==('exact_speed_full_clock_design_allowed' if all(conditions.values()) else 'close_exact_speed_gate')
    audit = dict(at=datetime.now(timezone.utc).isoformat(), original_session=84426, exit_code=0,
                 source_commit='e9eed3486493f2c03ae1d0bf8fece3782481ada1',both_mirrors_verified_before_launch=True,
                 plan_sha256=execution['plan_sha256'], result_sha256=execution['result_sha256'], calls=len(calls),
                 checked_rows=len(reference['all'])*len(ARMS), dependencies=len(plan['dependencies']), core_released=True,
                 conditions=conditions, elapsed_seconds=execution['seconds'])
    with (OUT/'terminal-verification.json').open('x') as stream:
        json.dump(audit,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps(audit),flush=True)


if __name__=='__main__':
    main()
