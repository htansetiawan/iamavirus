"""Independent fresh-test metrics, bootstrap, gate and CPU/native parity."""
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
DATA=ROOT/'astra-submissions/experiments/residual-confirmation-20261102'
RESIDUAL=ROOT/'astra-submissions/experiments/residual-fow-value-20261102'
sys.path.insert(0,str(RESIDUAL))
from common import OLDOUT, now, sha, write_new
from models import FlatResidual,QueryResidual


def metrics(y,p,g):
    p=np.asarray(p,dtype=np.float64);c=np.clip(p,1e-6,1-1e-6)
    l=-(y*np.log(c)+(1-y)*np.log1p(-c));b=(p-y)**2;ids=np.unique(g)
    ll=np.array([l[g==k].mean() for k in ids]);bb=np.array([b[g==k].mean() for k in ids])
    return dict(logloss=float(ll.mean()),brier=float(bb.mean()),positions=len(y),games=len(ids)),ll


def main():
    start=time.monotonic();os.sched_setaffinity(0,{0,1});torch.set_num_threads(2)
    contract=json.loads((OUT/'contract.json').read_text());assert contract['primary']=='flat'
    for path,h in contract['dependencies'].items():assert sha(ROOT/path)==h,path
    r=json.loads((OUT/'result.json').read_text());assert r['primary']=='flat'
    data_review=json.loads((OUT/'holdout-review.json').read_text());assert data_review['passed']
    assert r['data_sha256']==data_review['data_sha256']==sha(DATA/'work/holdout/data.npz')
    assert r['contract_sha256']==sha(OUT/'contract.json') and contract['at']<r['at']
    with np.load(DATA/'work/holdout/data.npz') as a:d={k:a[k] for k in a.files}
    with np.load(DATA/'work/predictions.npz') as a:pred={k:a[k] for k in a.files}
    logits={n:pred.pop(n+'_logit') for n in ('flat','query')}
    y=d['y'].astype(np.float64);g=d['game'];sf=d['sf'].astype(np.float64)
    assert np.array_equal(sf,pred['raw_sf']);assert set(pred)=={'flat','query','raw_sf','calibrated_sf'}
    ab=json.loads((OLDOUT/'selection.json').read_text())['calibration']
    z=ab[0]+ab[1]*np.log(np.clip(sf,1e-6,1-1e-6)/np.clip(1-sf,1e-6,1-1e-6))
    assert np.max(abs(1/(1+np.exp(-z))-pred['calibrated_sf']))<1e-12
    scores={};ll={};slices={}
    for n,p in pred.items():
        assert np.isfinite(p).all() and np.all((p>=0)&(p<=1))
        scores[n],ll[n]=metrics(y,p,g)
        for k in ('logloss','brier'):assert abs(scores[n][k]-r['test'][n][k])<1e-12
    for n in ('flat','query'):
        delta=ll[n]-ll['calibrated_sf'];rng=np.random.default_rng(2401103)
        boot=delta[rng.integers(len(delta),size=(2000,len(delta)))].mean(1)
        pair=r['paired_differences'][n]
        assert abs(delta.mean()-pair['mean'])<1e-12
        assert np.max(abs(np.quantile(boot,[.025,.975])-pair['bootstrap_95']))<1e-12
    for tag,mask in [('older_unused',d['group']==0),('new_date',d['group']==1),('hidden_threat',d['hidden_threat']),('ordinary',~d['hidden_threat'])]:
        slices[tag]={}
        for n,p in pred.items():
            m,_=metrics(y[mask],p[mask],g[mask]);slices[tag][n]=m
            for k in ('logloss','brier'):assert abs(m[k]-r['slices'][tag][n][k])<1e-12
    b=scores['calibrated_sf'];s=scores['flat'];nd=slices['new_date'];ht=slices['hidden_threat'];ordinary=slices['ordinary']
    nd_enough=nd['flat']['games']>=30 and nd['flat']['positions']>=200
    ht_enough=ht['flat']['games']>=30 and ht['flat']['positions']>=100
    gates=dict(logloss_gain=s['logloss']<=.98*b['logloss'],game_interval=r['paired_differences']['flat']['bootstrap_95'][1]<0,
        brier=s['brier']<=b['brier'],new_date_logloss=nd['flat']['logloss']<=nd['calibrated_sf']['logloss'] if nd_enough else None,
        new_date_brier=nd['flat']['brier']<=nd['calibrated_sf']['brier'] if nd_enough else None,
        hidden_threat=ht['flat']['logloss']<=ht['calibrated_sf']['logloss'] if ht_enough else None,
        ordinary=ordinary['flat']['logloss']<=ordinary['calibrated_sf']['logloss'])
    assert gates==r['gates'] and all(v is True for v in gates.values())==r['pass_confirmation']
    parity={}
    for n,klass in [('flat',FlatResidual),('query',QueryResidual)]:
        model=klass().eval();model.load_state_dict(torch.load(RESIDUAL/'work/training'/(n+'.pt'),map_location='cpu',weights_only=True))
        value=[]
        with torch.no_grad():
            for i in range(0,len(y),128):
                value.extend(model(torch.tensor(d['x'][i:i+128],dtype=torch.long),torch.tensor(d['half'][i:i+128],dtype=torch.float32),torch.tensor(z[i:i+128],dtype=torch.float32)).numpy())
        value=np.asarray(value,dtype=np.float64);p=1/(1+np.exp(-value));error=float(np.max(abs(p-pred[n])))
        assert error<2e-5,(n,error)
        assert np.max(abs(logits[n]-z.astype(np.float32)))<=2+2e-6
        assert np.max(abs(1/(1+np.exp(-logits[n]))-pred[n]))<1e-12
        parity[n]=dict(cpu_native_max_probability_error=error,positions=len(y))
    report=dict(at=now(),passed=True,primary='flat',confirmation_gate_pass=r['pass_confirmation'],
        independent_gates=gates,native_cpu_parity=parity,seconds=time.monotonic()-start,
        result_sha256=sha(OUT/'result.json'),predictions_sha256=sha(DATA/'work/predictions.npz'),source_sha256=sha(__file__),
        scope='Every score/subgroup/bootstrap/gate and CPU check of all native predictions. No fitting or arm selection; no policy/Elo claim.')
    write_new(OUT/'review.json',report);print(json.dumps(report),flush=True)


if __name__=='__main__':main()
