"""Reconstruct all aggregate decisions from immutable per-decision receipts."""
import json
import math
from collections import defaultdict
import numpy as np
from collect import OUT
from protocol import check_pins,sha,write,now


def main():
    p=json.loads((OUT/'plan.json').read_text());check_pins(p)
    result=json.loads((OUT/'result.json').read_text())
    assert result['cases_sha256']==sha(OUT/'cases.json')
    rows=json.loads((OUT/'cases.json').read_text())
    cohort=json.loads((OUT/'cohort.json').read_text())['games']
    wanted={g['game']:g for g in cohort}; bygame=defaultdict(list)
    assert len(rows)==sum(len(g['moves']) for g in cohort)
    for r in rows:
        g=wanted[r['game']];side=('white','black')[r['ply']%2]
        assert r['team_id']==g[side+'_id'] and r['team']==g[side]
        reference=r['team_id'] in p['teams']
        assert r['reference']==reference
        assert r['primary']==(reference and r['ply']//2>=8 and r['target_survives'])
        if r['capture']:
            assert r['eligible']==0 and r['old']==r['ranked']['linear']==r['ranked']['quadratic']
        bygame[r['game']].append(r['ply'])
    for game,plies in bygame.items(): assert plies==list(range(len(wanted[game]['moves'])))
    primary=[r for r in rows if r['primary']]
    gain=lambda r,k:2*(r['ranked'][k]-r['old'])
    value=math.fsum(gain(r,'quadratic') for r in primary)/len(primary)
    linear=math.fsum(gain(r,'quadratic')-gain(r,'linear') for r in primary)/len(primary)
    sums=defaultdict(lambda:[0.,0])
    for r in primary:
        sums[r['game']][0]+=gain(r,'quadratic');sums[r['game']][1]+=1
    groups=list(sums)
    rng=np.random.default_rng(p['seed']);boot=[]
    for _ in range(p['bootstrap_draws']):
        draw=rng.integers(0,len(groups),len(groups))
        boot.append(sum(sums[groups[i]][0] for i in draw)/sum(sums[groups[i]][1] for i in draw))
    ci=np.quantile(boot,[.025,.975]).tolist()
    assert np.allclose(ci,result['interval95_game_bootstrap'],rtol=0,atol=1e-12)
    assert abs(value-result['primary']['tempered_log_gain']['quadratic'])<1e-12
    assert abs(linear-result['primary']['quadratic_vs_linear'])<1e-12
    priority={t:[r for r in primary if r['team_id']==t] for t in p['priority']}
    gate=p['gate'];allrefs=[r for r in rows if r['reference']]
    conditions=dict(primary_count=len(primary)>=gate['primary_min'],
        changed=sum(r['changed']['quadratic']>0 for r in primary)>=gate['changed_min'],
        changed_games=len({r['game'] for r in primary if r['changed']['quadratic']>0})>=gate['changed_games_min'],
        gain=value>=gate['gain'],confidence=ci[0]>0,over_linear=linear>=gate['over_linear'],
        all_reference_nonregression=math.fsum(gain(r,'quadratic') for r in allrefs)>=0,
        priority_coverage=all(len({r['game'] for r in v})>=gate['priority_games_min'] for v in priority.values()),
        priority_nonregression=all(v and math.fsum(gain(r,'quadratic') for r in v)>=0 for v in priority.values()),
        mask_capture_multiset_and_scalar_checks=True)
    assert conditions==result['conditions']
    decision='separate_sequential_posterior_design_only' if all(conditions.values()) else 'close_frozen_rank_configuration'
    assert decision==result['decision']
    write(OUT/'independent-review.json',dict(at=now(),passed=True,rows=len(rows),games=len(cohort),
          reconstructed_conditions=conditions,decision=decision,result_sha256=sha(OUT/'result.json'),
          note='Aggregate reconstruction plus source/course/scalar/invariant audits; no second native model run.'),exclusive=True)
    print('independent aggregate review passed',decision,flush=True)


if __name__=='__main__':main()
