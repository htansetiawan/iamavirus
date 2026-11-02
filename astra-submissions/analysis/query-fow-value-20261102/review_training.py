"""Independent metric, checkpoint-selection and native-export verification."""
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'astra-submissions/experiments/query-fow-value-20261102'
sys.path.insert(0,str(SOURCE))
from common import HERE, OUT, OLD, OLDOUT, now, sha, write_new
from models import QueryStudent,pack_native

spec=importlib.util.spec_from_file_location('reference_models',OLD/'models.py')
reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)


def score(y,p,g):
    p=np.asarray(p,dtype=np.float64);clipped=np.clip(p,1e-6,1-1e-6)
    per_row=-(y*np.log(clipped)+(1-y)*np.log1p(-clipped))
    sq=(p-y)**2;ids=np.unique(g)
    ll=np.array([per_row[g==v].mean() for v in ids]);bb=np.array([sq[g==v].mean() for v in ids])
    return dict(logloss=float(ll.mean()),brier=float(bb.mean()),positions=len(y),games=len(ids)),ll


def main():
    start=time.monotonic();os.sched_setaffinity(0,{0});torch.set_num_threads(1)
    plan=json.loads((OUT/'plan.json').read_text())
    for name,h in plan['dependencies'].items():assert sha(ROOT/name)==h,name
    terminal=json.loads((OUT/'training-terminal.json').read_text());assert terminal['status']=='complete'
    selection=json.loads((OUT/'selection.json').read_text());r=json.loads((OUT/'result.json').read_text())
    target=HERE/'work/training';assert terminal['result_sha256']==sha(OUT/'result.json')
    assert terminal['predictions_sha256']==sha(target/'test-predictions.npz') and r['selection']==selection
    assert selection['at']<r['at']
    for name,h in terminal['checkpoints'].items():assert sha(target/name)==h
    for name,s in selection['arms'].items():
        curve=json.loads((target/(name+'-curve.json')).read_text());assert len(curve)==32
        best=min(curve,key=lambda v:v['validation']['logloss'])
        assert best['epoch']==s['epoch'] and best['validation']['logloss']==s['validation_logloss']
    chosen=min(selection['arms'],key=lambda name:selection['arms'][name]['validation_logloss'])
    assert chosen==selection['chosen_student']
    with np.load(HERE/'work/holdout/data.npz') as f:d={k:f[k] for k in f.files}
    with np.load(target/'test-predictions.npz') as f:pred={k:f[k] for k in f.files}
    y=d['y'].astype(np.float64);g=d['game'];x=np.ascontiguousarray(d['x']);h=np.ascontiguousarray(d['half'])
    assert np.array_equal(pred['raw_sf'],d['sf'].astype(np.float64))
    ab=json.loads((OLDOUT/'selection.json').read_text())['calibration'];sf=pred['raw_sf']
    z=np.log(np.clip(sf,1e-6,1-1e-6)/np.clip(1-sf,1e-6,1-1e-6))
    expected=1/(1+np.exp(-(ab[0]+ab[1]*z)));assert np.max(abs(expected-pred['calibrated_sf']))<1e-12
    scores={};pergame={}
    for name,p in pred.items():
        assert len(p)==len(y) and np.isfinite(p).all() and np.all((p>=0)&(p<=1))
        scores[name],pergame[name]=score(y,p,g)
        for k in ('logloss','brier'):assert abs(scores[name][k]-r['test'][name][k])<1e-12,(name,k)
    for name,pair in r['paired_differences'].items():
        diff=pergame[name]-pergame['calibrated_sf'];rng=np.random.default_rng(2381103)
        boot=diff[rng.integers(len(diff),size=(2000,len(diff)))].mean(axis=1)
        assert abs(diff.mean()-pair['mean'])<1e-12
        assert np.max(abs(np.quantile(boot,[.025,.975])-pair['bootstrap_95']))<1e-12
    for tag,mask in [('older_unused',d['group']==0),('new_date',d['group']==1),('hidden_threat',d['hidden_threat'])]:
        for name,p in pred.items():
            m,_=score(y[mask],p[mask],g[mask])
            for k in ('logloss','brier'):assert abs(m[k]-r['slices'][tag][name][k])<1e-12,(tag,name,k)
    b=scores['calibrated_sf'];s=scores[chosen];th=r['slices']['hidden_threat']
    sufficient=th[chosen]['positions']>=100 and th[chosen]['games']>=30
    gates=dict(logloss_gain=s['logloss']<=.98*b['logloss'],game_interval=r['paired_differences'][chosen]['bootstrap_95'][1]<0,
        brier=s['brier']<=b['brier'],new_date=r['slices']['new_date'][chosen]['logloss']<=r['slices']['new_date']['calibrated_sf']['logloss'],
        hidden_threat=th[chosen]['logloss']<=th['calibrated_sf']['logloss'] if sufficient else None)
    assert gates==r['gates'] and all(v is True for v in gates.values())==r['pass_quality']
    native={};fp=ctypes.POINTER(ctypes.c_float);bp=ctypes.POINTER(ctypes.c_uint8)
    flat_order=('piece.weight','vision.weight','castle.weight','ep.weight','bias','half_weight',
        'hidden.weight','hidden.bias','output.weight','output.bias')
    for name in plan['arms']:
        flat=name=='flat_distilled';model=reference.Student() if flat else QueryStudent()
        model.load_state_dict(torch.load(target/(name+'.pt'),map_location='cpu',weights_only=True));model.eval()
        cpu=[]
        with torch.no_grad():
            for i in range(0,len(x),128):
                cpu.extend(torch.sigmoid(model(torch.tensor(x[i:i+128],dtype=torch.long),torch.tensor(h[i:i+128],dtype=torch.float32))).numpy())
        cpu=np.array(cpu,dtype=np.float64)
        cpu_error=float(np.max(abs(cpu-pred[name])));assert cpu_error<2e-5,(name,'CPU/CUDA',cpu_error)
        if flat:
            state=model.state_dict();packed=np.concatenate([state[k].numpy().reshape(-1) for k in flat_order]).astype(np.float32)
            library=OLD/'build/student.so';stem='fow_student'
        else:
            # Reproduce the training export's two-thread BLAS reduction. The
            # preceding one-thread exact-byte check failed on <2.4e-7 rounding
            # differences in folded tables; source and failed receipt retained.
            torch.set_num_threads(2)
            packed=pack_native(model)
            torch.set_num_threads(1)
            library=HERE/'build/query.so';stem='fow_query'
            assert packed.tobytes()==(target/(name+'.fp32.bin')).read_bytes()
        lib=ctypes.CDLL(str(library));single=getattr(lib,stem+'_logit');batch=getattr(lib,stem+'_batch')
        single.argtypes=[fp,bp,ctypes.c_uint8];single.restype=ctypes.c_float
        batch.argtypes=[fp,bp,bp,ctypes.c_int,ctypes.c_int];batch.restype=ctypes.c_double
        wp=packed.ctypes.data_as(fp);logits=np.array([single(wp,row.ctypes.data_as(bp),int(v)) for row,v in zip(x,h)])
        actual=1/(1+np.exp(-logits));error=float(np.max(abs(actual-pred[name])))
        assert error<2e-5,(name,'native/CUDA',error)
        samples=[];xx=x[:320].copy();hh=h[:320].copy();xp=xx.ctypes.data_as(bp);hp=hh.ctypes.data_as(bp)
        batch(wp,xp,hp,320,3)
        for _ in range(7):
            begin=time.perf_counter();batch(wp,xp,hp,320,10);samples.append(1e6*(time.perf_counter()-begin)/3200)
        if flat:packed.tofile(target/(name+'.fp32.bin'))
        native[name]=dict(cpu_cuda_max_probability_error=cpu_error,native_cuda_max_probability_error=error,
            export_bytes=packed.nbytes,export_sha256=sha(target/(name+'.fp32.bin')),library_sha256=sha(library),
            microseconds=samples,median_microseconds=float(np.median(samples)),
            passes=bool(packed.nbytes<=1048576 and np.median(samples)<=50))
    # Frozen teacher is a reference, not the compact model's export. Experiment
    # 237 documented CPU/CUDA differences around9e-5, so test metric stability
    # separately rather than asserting native-style2e-5 parity for that model.
    teacher=reference.Teacher().eval()
    teacher.load_state_dict(torch.load(OLD/'work/training/teacher.pt',map_location='cpu',weights_only=True))
    tp=[]
    with torch.no_grad():
        for i in range(0,len(x),128):
            tp.extend(torch.sigmoid(teacher(torch.tensor(x[i:i+128],dtype=torch.long),torch.tensor(h[i:i+128],dtype=torch.float32))).numpy())
    tp=np.asarray(tp,dtype=np.float64);teacher_error=float(np.max(abs(tp-pred['teacher'])))
    teacher_metrics,_=score(y,tp,g)
    assert teacher_error<2e-4,teacher_error
    for k in ('logloss','brier'):assert abs(teacher_metrics[k]-scores['teacher'][k])<1e-5
    report=dict(at=now(),passed=True,seconds=time.monotonic()-start,chosen_student=chosen,
        quality_gate_pass=r['pass_quality'],native=native,native_gate_pass=native[chosen]['passes'],
        teacher_cpu_reference=dict(max_probability_difference=teacher_error,metrics=teacher_metrics,
            scope='CPU/CUDA probability tolerance2e-4, aggregate metric tolerance1e-5; not native compact export parity.'),
        next_gate_eligible=r['pass_quality'] and native[chosen]['passes'],source_sha256=sha(__file__),
        scope='Independent metrics/bootstrap/selection, every held-out CPU and native prediction for three compact arms, trained native one-core timing. Teacher remains frozen reference; no Elo or search strength conclusion.')
    write_new(OUT/'training-review.json',report);print(json.dumps(report),flush=True)


if __name__=='__main__':main()
