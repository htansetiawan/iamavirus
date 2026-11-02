"""Freeze the confirmation contract; later score only pinned native models."""
import ctypes
import json
import os
import sys
import time
import numpy as np
from common import HERE, ROOT, OUT, OLD, OLDOUT, QUERY, QUERYOUT, RESIDUAL, RESIDUALOUT, REFRESH, now, sha, write_new


def freeze():
    review=json.loads((RESIDUALOUT/'review.json').read_text());assert review['fresh_confirmation_eligible'] and review['chosen']=='flat'
    development=json.loads((RESIDUALOUT/'result.json').read_text());assert development['chosen']=='flat'
    files=list(HERE.glob('*.py'))+[HERE/'README.md',OLD/'data.py',OLD/'build/leaf_collect',
        RESIDUAL/'build/residual.so',RESIDUAL/'work/training/flat.fp32.bin',RESIDUAL/'work/training/query.fp32.bin',
        RESIDUAL/'work/training/flat.pt',RESIDUAL/'work/training/query.pt',RESIDUALOUT/'result.json',RESIDUALOUT/'review.json',
        OLDOUT/'selection.json',QUERY/'work/holdout/data.npz',QUERYOUT/'games.json',OLDOUT/'games.json',REFRESH/'refresh.py']
    contract=dict(at=now(),primary='flat',secondary=['query'],candidate_selection='Frozen239 development choice; no alternative selection on test.',
        dependencies={str(p):sha(p) for p in files},development_plan_sha256=sha(RESIDUALOUT/'plan.json'),
        selection=dict(older_dates=['2026-10-10','2026-10-31'],older_max=2000,new_max=500,
            new_source='Newly accepted2November games in one completed bounded600-game refresh; existing canonical states excluded.',
            required_new_source_games=30,required_total_source_games=1500,team_cohort='237 pinned top12',
            game_order='SHA256(240-holdout:game_id)',max_positions_per_game=8,all_prior_237_238_features_excluded=True),
        gate=dict(relative_logloss_gain_min=.02,game_bootstrap_upper_difference_max=0.,brier_difference_max=0.,
            new_date_logloss_difference_max=0.,new_date_brier_difference_max=0.,new_date_min_games=30,new_date_min_positions=200,
            hidden_threat_logloss_difference_max=0.,hidden_threat_min_games=30,hidden_threat_min_positions=100,
            ordinary_logloss_difference_max=0.,bootstrap_replicates=2000,bootstrap_seed=2401103),
        scope='Fresh prediction confirmation; older-unused plus separately checked new-date cohort. No training, search integration or Elo claim.')
    write_new(OUT/'contract.json',contract);print(json.dumps({'contract_sha256':sha(OUT/'contract.json')}),flush=True)


def metrics(y,p,g):
    original=np.asarray(p,dtype=np.float64);p=np.clip(original,1e-6,1-1e-6)
    _,inv,n=np.unique(g,return_inverse=True,return_counts=True)
    l=-(y*np.log(p)+(1-y)*np.log1p(-p));b=(original-y)**2
    return dict(logloss=float((np.bincount(inv,weights=l)/n).mean()),brier=float((np.bincount(inv,weights=b)/n).mean()),
        positions=len(y),games=len(n))


def difference(y,p,q,g):
    p=np.clip(p,1e-6,1-1e-6);q=np.clip(q,1e-6,1-1e-6)
    loss=-y*np.log(p/q)-(1-y)*np.log((1-p)/(1-q))
    _,inv,n=np.unique(g,return_inverse=True,return_counts=True);delta=np.bincount(inv,weights=loss)/n
    rng=np.random.default_rng(2401103);samples=delta[rng.integers(len(delta),size=(2000,len(delta)))].mean(1)
    return dict(mean=float(delta.mean()),bootstrap_95=np.quantile(samples,[.025,.975]).tolist(),games=len(delta))


def run():
    start=time.monotonic();os.sched_setaffinity(0,{0,1});contract=json.loads((OUT/'contract.json').read_text())
    for path,h in contract['dependencies'].items():assert sha(ROOT/path)==h,path
    review=json.loads((OUT/'holdout-review.json').read_text());assert review['passed']
    data=HERE/'work/holdout/data.npz';assert sha(data)==review['data_sha256']
    with np.load(data) as a:d={k:a[k] for k in a.files}
    x=np.ascontiguousarray(d['x']);half=np.ascontiguousarray(d['half']);sf=d['sf'].astype(np.float64)
    ab=json.loads((OLDOUT/'selection.json').read_text())['calibration']
    z=ab[0]+ab[1]*np.log(np.clip(sf,1e-6,1-1e-6)/np.clip(1-sf,1e-6,1-1e-6));z32=z.astype(np.float32)
    pred={'raw_sf':sf,'calibrated_sf':1/(1+np.exp(-z))};logits={}
    lib=ctypes.CDLL(str(RESIDUAL/'build/residual.so'));fp=ctypes.POINTER(ctypes.c_float);bp=ctypes.POINTER(ctypes.c_uint8)
    for name in ('flat','query'):
        weights=np.fromfile(RESIDUAL/'work/training'/(name+'.fp32.bin'),dtype=np.float32);wp=weights.ctypes.data_as(fp)
        fn=getattr(lib,'fow_residual_'+name+'_logit');fn.argtypes=[fp,bp,ctypes.c_uint8,ctypes.c_float];fn.restype=ctypes.c_float
        value=np.array([fn(wp,row.ctypes.data_as(bp),int(h),float(v)) for row,h,v in zip(x,half,z32)])
        assert np.isfinite(value).all() and np.max(abs(value-z32))<=2+2e-6
        logits[name]=value;pred[name]=1/(1+np.exp(-value))
    # All predictions are complete before labels are used in any calculation.
    y=d['y'].astype(np.float64);g=d['game'];scores={n:metrics(y,p,g) for n,p in pred.items()}
    diffs={n:difference(y,p,pred['calibrated_sf'],g) for n,p in pred.items() if n in ('flat','query')}
    slices={}
    for name,mask in [('older_unused',d['group']==0),('new_date',d['group']==1),('hidden_threat',d['hidden_threat']),('ordinary',~d['hidden_threat'])]:
        slices[name]={n:metrics(y[mask],p[mask],g[mask]) for n,p in pred.items()} if mask.any() else {}
    b=scores['calibrated_sf'];s=scores['flat'];nd=slices['new_date'];ht=slices['hidden_threat'];ordinary=slices['ordinary']
    nd_enough=bool(nd and nd['flat']['games']>=30 and nd['flat']['positions']>=200)
    ht_enough=bool(ht and ht['flat']['games']>=30 and ht['flat']['positions']>=100)
    gates=dict(logloss_gain=s['logloss']<=.98*b['logloss'],game_interval=diffs['flat']['bootstrap_95'][1]<0,
        brier=s['brier']<=b['brier'],new_date_logloss=nd['flat']['logloss']<=nd['calibrated_sf']['logloss'] if nd_enough else None,
        new_date_brier=nd['flat']['brier']<=nd['calibrated_sf']['brier'] if nd_enough else None,
        hidden_threat=ht['flat']['logloss']<=ht['calibrated_sf']['logloss'] if ht_enough else None,
        ordinary=ordinary['flat']['logloss']<=ordinary['calibrated_sf']['logloss'] if ordinary else None)
    result=dict(at=now(),primary='flat',test=scores,paired_differences=diffs,slices=slices,gates=gates,
        pass_confirmation=all(v is True for v in gates.values()),seconds=time.monotonic()-start,
        contract_sha256=sha(OUT/'contract.json'),data_sha256=sha(data),
        scope='Pinned native predictions on disjoint played positions. No model selection, test fitting, policy or playing-strength conclusion.')
    np.savez(HERE/'work/predictions.npz',**pred,flat_logit=logits['flat'],query_logit=logits['query'])
    write_new(OUT/'result.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':freeze() if sys.argv[1]=='freeze' else run()
