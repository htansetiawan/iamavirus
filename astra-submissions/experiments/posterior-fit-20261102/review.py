"""Reconstruct held-out cases; independently check rules, probability sums and selection."""
from collections import defaultdict
import gzip
import json
import os
from pathlib import Path
import time
import numpy as np
from config import ROOT, OUT, sha, now, unique
from extract import collect


def lse(values):
    values=np.asarray(values,dtype=float)
    if not len(values):return -np.inf
    maximum=values.max()
    return float(maximum+np.log(np.exp(values-maximum).sum()))


def numpy_scores(row,theta,floor):
    z=row['base'].astype(float)+row['x'].astype(float)@theta
    logp=np.empty(len(z),float)
    offsets=np.r_[0,np.cumsum(np.bincount(row['a_parent'],minlength=len(row['u'])))]
    for i,(lo,hi) in enumerate(zip(offsets[:-1],offsets[1:])):
        part=z[lo:hi]-lse(z[lo:hi])
        if row['hn'][i]>=3:
            h=row['counts'][lo:hi].astype(float)
            with np.errstate(divide='ignore'):
                part=np.logaddexp(np.log(h),np.log(4)+part)-np.log(row['hn'][i]+4.)
        logp[lo:hi]=part
    u=row['u'].astype(float); edge=u[row['a_parent']]+2*logp
    if not row['meta']['natural_support']:return np.log(floor),np.log(floor)
    post=lse(edge[row['positive']])-lse(edge[row['valid']])
    actor=lse((u[row['a_parent']]+logp)[row['actor_edge']])-lse(u[row['actor_parent']])
    return tuple(float(np.clip(v,np.log(floor),0)) for v in (post,actor))


def main():
    started=time.monotonic(); os.sched_setaffinity(0,{2,3})
    plan=json.loads((OUT/'plan.json').read_text()); result=json.loads((OUT/'result.json').read_text())
    for path,digest in plan['dependencies'].items():assert sha(Path(path))==digest,path
    assert sha(OUT/'plan.json')==result['plan_sha256']
    selection=json.loads((OUT/'selection.json').read_text()); lock=json.loads((OUT/'selection-lock.json').read_text())
    assert sha(OUT/'selection.json')==lock['sha256']==result['selection_sha256']
    candidates=[]
    for kind in ('actor','posterior'):
        for ridge in plan['ridges']:
            name=f'{kind}-{ridge:g}'
            assert sha(OUT/(name+'-curve.json'))==lock['curves'][name+'-curve.json']
            curve=json.loads((OUT/(name+'-curve.json')).read_text())
            assert [r['step'] for r in curve]==list(range(5,61,5))
            best=min(curve,key=lambda r:r['validation_nll'])
            model=json.loads((OUT/(name+'-model.json')).read_text())
            assert model==dict(kind=kind,ridge=ridge,**best); candidates.append(model)
        assert selection[kind]==min((c for c in candidates if c['kind']==kind),key=lambda c:(c['validation_nll'],c['ridge']))
    scored=[json.loads(line) for line in gzip.open(OUT/'test-scores.jsonl.gz','rt')]
    assert sha(OUT/'test-scores.jsonl.gz')==result['scores_sha256']
    assert (OUT/'selection-lock.json').stat().st_mtime_ns < (OUT/'test-data.json').stat().st_mtime_ns
    cases=collect(plan,'test',receipt_name='review-test-data.json',audit_rules=True)
    original=json.loads((OUT/'test-data.json').read_text()); reviewed=json.loads((OUT/'review-test-data.json').read_text())
    assert original['features_sha256']==reviewed['features_sha256']
    assert original['games']==reviewed['games'] and len(cases)==len(scored)
    errors={kind:0. for kind in ('baseline','actor','posterior')}
    for row,record in zip(cases,scored):
        assert all(record[k]==v for k,v in row['meta'].items())
        for kind in errors:
            theta=np.zeros(26) if kind=='baseline' else np.array(selection[kind]['coefficients'])
            post,act=numpy_scores(row,theta,plan['probability_floor'])
            errors[kind]=max(errors[kind],abs(post-record[kind]['posterior_logp']),abs(act-record[kind]['actor_logp']))
    assert max(errors.values())<1e-8,errors
    masks={'primary':lambda r:r['primary'],'all':lambda r:True,
           'late':lambda r:r['primary'] and r['late'],'surprise':lambda r:r['primary'] and r['surprise']}
    for name,mask in masks.items():
        rows=[r for r in scored if mask(r)]; recorded=result['metrics'][name]
        assert recorded['cases']==len(rows) and recorded['games']==len({r['game'] for r in rows})
        grouped=defaultdict(list)
        for r in rows:grouped[r['game']].append(r)
        if not rows:continue
        for kind in errors:
            for metric,key in [('nll','posterior_logp'),('actor_nll','actor_logp')]:
                value=np.mean([-np.mean([r[kind][key] for r in group]) for group in grouped.values()])
                assert abs(value-recorded[kind+'_'+metric])<1e-10
        gains=np.array([np.mean([r['posterior']['posterior_logp']-r['baseline']['posterior_logp'] for r in grouped[g]]) for g in sorted(grouped)])
        assert abs(gains.mean()-recorded['gain'])<1e-10
        if name=='primary':
            rng=np.random.default_rng(plan['seed'])
            interval=np.quantile([rng.choice(gains,len(gains),replace=True).mean() for _ in range(plan['bootstrap_samples'])],[.025,.975])
            assert np.max(np.abs(interval-recorded['gain_ci95']))<1e-10
    p=result['metrics']['primary']; a=result['metrics']['all']; l=result['metrics']['late']; s=result['metrics']['surprise']; g=plan['gate']
    expected=dict(baseline_gain=p['gain']>=g['baseline_gain'],baseline_ci=p['gain_ci95'][0]>g['baseline_ci_lower'],
                  matched_actor=p['gain_over_actor']>=g['actor_comparator_gain'],
                  late=l['gain'] is not None and l['gain']>=g['late_min_gain'],
                  surprise_count=s['cases']>=g['min_surprise'],surprise=s['gain'] is not None and s['gain']>=g['surprise_min_gain'],
                  all=a['gain']>=g['all_min_gain'],support=a['unsupported']<=g['max_support_failures'])
    assert expected==result['checks'] and all(expected.values())==result['passed']
    checked=dict(at=now(),elapsed=time.monotonic()-started,cases=len(cases),numpy_log_probability_errors=errors,
                 independent_rules=reviewed['independent_rules'],all_source_pins_verified=True,
                 selection_before_test_verified=True,feature_reconstruction_exact=True,gate_recomputed=True,
                 plan_sha256=sha(OUT/'plan.json'),result_sha256=sha(OUT/'result.json'))
    unique(OUT/'independent-review.json',checked); print(json.dumps(checked),flush=True)


if __name__=='__main__':main()
