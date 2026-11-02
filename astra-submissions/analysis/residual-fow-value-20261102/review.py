"""Independent review of a development screen, with native export checks."""
import ctypes
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'astra-submissions/experiments/residual-fow-value-20261102'
sys.path.insert(0,str(SOURCE))
from common import HERE, OUT, OLD, OLDOUT, now, sha, write_new
from models import FlatResidual, QueryResidual, pack


def metrics(y,p,g):
    p=np.asarray(p,dtype=np.float64);c=np.clip(p,1e-6,1-1e-6)
    l=-(y*np.log(c)+(1-y)*np.log1p(-c));b=(p-y)**2;ids=np.unique(g)
    return dict(logloss=float(np.mean([l[g==k].mean() for k in ids])),
        brier=float(np.mean([b[g==k].mean() for k in ids])),positions=len(y),games=len(ids))


def main():
    start=time.monotonic();os.sched_setaffinity(0,{0});torch.set_num_threads(1)
    plan=json.loads((OUT/'plan.json').read_text())
    for path,h in plan['dependencies'].items():assert sha(ROOT/path)==h,path
    terminal=json.loads((OUT/'training-terminal.json').read_text());assert terminal['status']=='complete'
    r=json.loads((OUT/'result.json').read_text());target=HERE/'work/training'
    assert terminal['result_sha256']==sha(OUT/'result.json')
    assert terminal['predictions_sha256']==sha(target/'validation-predictions.npz')
    for name,h in terminal['checkpoints'].items():assert sha(target/name)==h
    with np.load(OLD/'work/dataset/data.npz') as a:
        ii=np.flatnonzero(a['fold']==1);x=np.ascontiguousarray(a['x'][ii]);half=np.ascontiguousarray(a['half'][ii])
        y=a['y'][ii].astype(np.float64);g=a['game'][ii];sf=a['sf'][ii].astype(np.float64);hidden=a['hidden_threat'][ii]
    with np.load(target/'validation-predictions.npz') as a:pred={k:a[k] for k in a.files}
    assert np.array_equal(pred.pop('indices'),ii);assert set(pred)=={'raw_sf','calibrated_sf','flat','query'}
    assert np.array_equal(pred['raw_sf'],sf)
    ab=json.loads((OLDOUT/'selection.json').read_text())['calibration'];assert ab==r['calibration']
    z=ab[0]+ab[1]*np.log(np.clip(sf,1e-6,1-1e-6)/np.clip(1-sf,1e-6,1-1e-6))
    assert np.max(abs(1/(1+np.exp(-z))-pred['calibrated_sf']))<1e-12
    for name in ('flat','query'):
        curve=json.loads((target/(name+'-curve.json')).read_text());assert len(curve)==32
        best=min(curve,key=lambda v:v['validation']['logloss']);s=r['selection'][name]
        assert best['epoch']==s['epoch'] and best['validation']['logloss']==s['validation_logloss']
    chosen=min(r['selection'],key=lambda n:r['selection'][n]['validation_logloss']);assert chosen==r['chosen']
    scores={};slices={}
    for name,p in pred.items():
        assert np.isfinite(p).all() and np.all((p>=0)&(p<=1))
        scores[name]=metrics(y,p,g);slices[name]=metrics(y[hidden],p[hidden],g[hidden])
        for k in ('logloss','brier'):
            assert abs(scores[name][k]-r['validation'][name][k])<1e-12,(name,k)
            assert abs(slices[name][k]-r['hidden_threat'][name][k])<1e-12,(name,k)
    b=scores['calibrated_sf'];s=scores[chosen]
    enough=slices[chosen]['positions']>=100 and slices[chosen]['games']>=30
    gates=dict(logloss_gain=s['logloss']<=.98*b['logloss'],brier=s['brier']<=b['brier'],
        hidden_threat=slices[chosen]['logloss']<=slices['calibrated_sf']['logloss'] if enough else None)
    assert gates==r['gates'] and all(v is True for v in gates.values())==r['pass_development']
    lib=ctypes.CDLL(str(HERE/'build/residual.so'));fp=ctypes.POINTER(ctypes.c_float);bp=ctypes.POINTER(ctypes.c_uint8)
    z32=z.astype(np.float32);native={}
    for name,klass in [('flat',FlatResidual),('query',QueryResidual)]:
        model=klass().eval();model.load_state_dict(torch.load(target/(name+'.pt'),map_location='cpu',weights_only=True))
        logits=[]
        with torch.no_grad():
            for i in range(0,len(x),128):
                logits.extend(model(torch.tensor(x[i:i+128],dtype=torch.long),torch.tensor(half[i:i+128],dtype=torch.float32),torch.tensor(z32[i:i+128])).numpy())
        logits=np.asarray(logits,dtype=np.float64);cpu=1/(1+np.exp(-logits));assert np.max(abs(logits-z32))<=2+2e-6
        cpu_error=float(np.max(abs(cpu-pred[name])));assert cpu_error<2e-5,(name,cpu_error)
        # Reproduce original two-thread embedding folding, then return to one core.
        torch.set_num_threads(2);packed=pack(model,name);torch.set_num_threads(1)
        assert packed.tobytes()==(target/(name+'.fp32.bin')).read_bytes()
        single=getattr(lib,'fow_residual_'+name+'_logit');single.argtypes=[fp,bp,ctypes.c_uint8,ctypes.c_float];single.restype=ctypes.c_float
        batch=getattr(lib,'fow_residual_'+name+'_batch');batch.argtypes=[fp,bp,bp,fp,ctypes.c_int,ctypes.c_int];batch.restype=ctypes.c_double
        wp=packed.ctypes.data_as(fp)
        value=np.array([single(wp,row.ctypes.data_as(bp),int(h),float(a)) for row,h,a in zip(x,half,z32)])
        assert np.max(abs(value-z32))<=2+2e-6
        probability=1/(1+np.exp(-value));error=float(np.max(abs(probability-pred[name])));assert error<2e-5
        xx=x[:256].copy();hh=half[:256].copy();zz=z32[:256].copy();samples=[]
        args=(wp,xx.ctypes.data_as(bp),hh.ctypes.data_as(bp),zz.ctypes.data_as(fp),256)
        batch(*args,3)
        for _ in range(7):
            begin=time.perf_counter();batch(*args,20);samples.append(1e6*(time.perf_counter()-begin)/5120)
        native[name]=dict(cpu_cuda_probability_error=cpu_error,native_cuda_probability_error=error,
            bounded_residual_max=float(np.max(abs(value-z32))),export_bytes=packed.nbytes,
            export_sha256=sha(target/(name+'.fp32.bin')),microseconds=samples,median_microseconds=float(np.median(samples)),
            passes=bool(packed.nbytes<=1048576 and np.median(samples)<=50))
    report=dict(at=now(),passed=True,seconds=time.monotonic()-start,chosen=chosen,development_gate_pass=r['pass_development'],
        native=native,native_gate_pass=native[chosen]['passes'],fresh_confirmation_eligible=r['pass_development'] and native[chosen]['passes'],
        source_sha256=sha(__file__),scope='Independent reused-validation metrics/selection/gates and all native predictions; no fresh test, search or Elo evaluation.')
    write_new(OUT/'review.json',report);print(json.dumps(report),flush=True)


if __name__=='__main__':main()
