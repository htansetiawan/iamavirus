from collections import defaultdict
import ctypes
import gzip
import json
import os
from pathlib import Path
import numpy as np
from settings import HERE,OUT,ROOT,exporter,now,sha,unique
from quadratic import mask_array


def lse(x):
    if not len(x):return -np.inf
    m=x.max();return float(m+np.log(np.exp(x-m).sum()))


def score(row,linear,q,floor):
    x=row['x'].astype(float);z=row['base'].astype(float)+x@linear+np.einsum('ni,ij,nj->n',x,q,x)
    logp=np.empty(len(z));offsets=np.r_[0,np.cumsum(np.bincount(row['a_parent'],minlength=len(row['u'])))]
    for i,(a,b) in enumerate(zip(offsets[:-1],offsets[1:])):
        v=z[a:b]-lse(z[a:b])
        if row['hn'][i]>=3:
            with np.errstate(divide='ignore'):v=np.logaddexp(np.log(row['counts'][a:b].astype(float)),np.log(4.)+v)-np.log(row['hn'][i]+4.)
        logp[a:b]=v
    u=row['u'].astype(float);edge=u[row['a_parent']]+2*logp
    if not row['meta']['natural_support']:return (np.log(floor),)*2,z
    post=lse(edge[row['positive']])-lse(edge[row['valid']])
    act=lse((u[row['a_parent']]+logp)[row['actor_edge']])-lse(u[row['actor_parent']])
    return tuple(float(np.clip(v,np.log(floor),0)) for v in (post,act)),z


def main():
    os.sched_setaffinity(0,{2,3});plan=json.loads((OUT/'plan.json').read_text())
    assert all(g['split']!='test' for g in plan['games'])
    for p,h in plan['dependencies'].items():assert sha(Path(p))==h,p
    selected=json.loads((OUT/'selection.json').read_text());result=json.loads((OUT/'result.json').read_text())
    assert sha(OUT/'selection.json')==result['selection_sha256'] and sha(OUT/'plan.json')==result['plan_sha256']
    for key,record in selected.items():
        candidates=[]
        for ridge in plan['ridges']:
            name=f'{key}-{ridge:g}';curve=json.loads((OUT/(name+'-curve.json')).read_text());best=min(curve,key=lambda r:r['validation_nll'])
            saved=json.loads((OUT/(name+'-model.json')).read_text())
            assert saved==dict(form=record['form'],objective=record['objective'],ridge=ridge,**best);candidates.append(saved)
        assert record==min(candidates,key=lambda r:(r['validation_nll'],r['ridge']))
        assert np.max(np.abs(np.array(record['quadratic'])*(1-mask_array())))==0
    cases=exporter.collect(plan,'validation',receipt_name='review-validation-data.json')
    original=json.loads((OUT/'validation-data.json').read_text());reviewed=json.loads((OUT/'review-validation-data.json').read_text())
    assert original['features_sha256']==reviewed['features_sha256'] and original['games']==reviewed['games']
    records=[json.loads(s) for s in gzip.open(OUT/'validation-scores.jsonl.gz','rt')]
    assert len(records)==len(cases) and sha(OUT/'validation-scores.jsonl.gz')==result['scores_sha256']
    models={k:(np.array(v['linear']),np.array(v['quadratic'])) for k,v in selected.items()};models['baseline']=(np.zeros(26),np.zeros((26,26)))
    errors={k:0. for k in models};native_error=0.;lib=ctypes.CDLL(str(HERE/'build/residual.so'))
    ptr=np.ctypeslib.ndpointer(dtype=np.float32,flags='C_CONTIGUOUS');lib.residual_logits.argtypes=[ptr,ptr,ctypes.c_int,ptr,ptr,ptr]
    for row,record in zip(cases,records):
        assert row['meta']==record['metadata']
        for key,(linear,q) in models.items():
            values,z=score(row,linear,q,plan['probability_floor'])
            got=record['predictions'][key]
            errors[key]=max(errors[key],abs(values[0]-got['posterior_logp']),abs(values[1]-got['actor_logp']))
            if key=='quadratic-posterior':
                out=np.empty(len(z),np.float32)
                lib.residual_logits(row['x'],row['base'],len(z),linear.astype(np.float32),q.astype(np.float32),out)
                native_error=max(native_error,float(np.max(np.abs(out-z))))
    assert max(errors.values())<1e-8,errors
    assert native_error<2e-5,native_error
    for name,select in {'primary':lambda r:r['primary'],'all':lambda r:True,'late':lambda r:r['primary'] and r['late'],'surprise':lambda r:r['primary'] and r['surprise']}.items():
        grouped=defaultdict(list)
        for r in records:
            if select(r['metadata']):grouped[r['metadata']['game']].append(r)
        expected=result['metrics'][name];assert len(grouped)==expected['games']
        if not grouped:continue
        for key in models:
            nll=float(np.mean([-np.mean([r['predictions'][key]['posterior_logp'] for r in v]) for v in grouped.values()]))
            assert abs(nll-expected['nll'][key])<1e-8
        assert abs(expected['nll']['baseline']-expected['nll']['quadratic-posterior']-expected['gain'])<1e-10
        for key in ('linear-posterior','quadratic-actor'):
            assert abs(expected['nll'][key]-expected['nll']['quadratic-posterior']-expected['gain_over_'+key])<1e-10
    p=result['metrics']['primary'];s=result['metrics']['surprise'];l=result['metrics']['late'];a=result['metrics']['all'];g=plan['gate']
    checks=dict(baseline_gain=p['gain']>=g['baseline_gain'],linear_posterior=p['gain_over_linear-posterior']>=g['linear_posterior_gain'],
                quadratic_actor=p['gain_over_quadratic-actor']>=g['quadratic_actor_gain'],
                late=l['gain'] is not None and l['gain']>=g['late_min_gain'],surprise_count=s['cases']>=g['min_surprise'],
                surprise=s['gain'] is not None and s['gain']>=g['surprise_min_gain'],all=a['gain']>=g['all_min_gain'],
                support=a['unsupported']<=g['max_support_failures'])
    assert checks==result['checks'] and all(checks.values())==result['passed']
    unique(OUT/'independent-review.json',dict(at=now(),cases=len(cases),probability_errors=errors,native_float_logit_error=native_error,
        feature_reconstruction_exact=True,selection_verified=True,old_test_not_exported=True,
        result_sha256=sha(OUT/'result.json'),scope=plan['scope']))
    print(json.dumps(dict(cases=len(cases),probability_errors=errors,native_error=native_error)),flush=True)


if __name__=='__main__':main()
