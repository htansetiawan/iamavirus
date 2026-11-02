"""Recompute the selected test scores, CPU teacher and native student outputs."""
from datetime import datetime,timezone
import ctypes
import json
from pathlib import Path
import sys
import time

import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'astra-submissions/experiments/native-fow-value-20261102'
sys.path.insert(0,str(SOURCE))
from data import load,sha,OUT,write_new
from models import Teacher,Student
from native_check import ORDER


def evaluate(y,p,g):
    raw=p.astype(np.float64);p=np.clip(raw,1e-6,1-1e-6)
    losses=-(y*np.log(p)+(1-y)*np.log1p(-p));squares=(raw-y)**2
    ids=np.unique(g)
    ll=np.array([losses[g==k].mean() for k in ids]);br=np.array([squares[g==k].mean() for k in ids])
    return dict(logloss=float(ll.mean()),brier=float(br.mean()),positions=len(y),games=len(ids)),ll


def main():
    begin=time.monotonic();load();target=SOURCE/'work/training'
    terminal=json.loads((OUT/'training-terminal.json').read_text());result=json.loads((OUT/'result.json').read_text())
    selection=json.loads((OUT/'selection.json').read_text());assert terminal['status']=='complete'
    assert terminal['result_sha256']==sha(OUT/'result.json') and result['selection']==selection
    assert terminal['predictions_sha256']==sha(target/'test-predictions.npz')
    for k,h in terminal['checkpoints'].items():assert sha(target/k)==h
    with np.load(SOURCE/'work/dataset/data.npz') as archive:d={k:archive[k] for k in archive.files}
    with np.load(target/'test-predictions.npz') as archive:pred={k:archive[k] for k in archive.files}
    ii=np.flatnonzero(d['fold']==2);assert np.array_equal(ii,pred.pop('indices'))
    y=d['y'][ii].astype(np.float64);g=d['game'][ii];x=np.ascontiguousarray(d['x'][ii]);half=np.ascontiguousarray(d['half'][ii])
    assert np.array_equal(pred['raw_sf'],d['sf'][ii].astype(np.float64))
    slope=selection['calibration'][1];offset=selection['calibration'][0]
    sf=d['sf'][ii].astype(np.float64);z=np.log(np.clip(sf,1e-6,1-1e-6)/np.clip(1-sf,1e-6,1-1e-6))
    expected=1/(1+np.exp(-(offset+slope*z)));assert np.max(np.abs(expected-pred['calibrated_sf']))<1e-12
    curves={name:json.loads((target/(name+'-curve.json')).read_text()) for name in ('teacher','direct_student','distilled_student')}
    for name,rows in curves.items():
        assert len(rows)==8
        best=min(rows,key=lambda row:row['validation']['logloss'])
        assert selection[name]['epoch']==best['epoch'] and selection[name]['validation_logloss']==best['validation']['logloss']
    chosen=min(('direct_student','distilled_student'),key=lambda n:selection[n]['validation_logloss'])
    assert selection['chosen_student']==chosen
    assert selection['at']<result['at']
    base=selection['chosen_control'];metrics={};ll={};pairs={}
    for name,p in pred.items():
        metrics[name],ll[name]=evaluate(y,p,g)
        for key in ('logloss','brier'):assert abs(metrics[name][key]-result['test'][name][key])<1e-12,(name,key)
    for name in ('teacher','direct_student','distilled_student'):
        diff=ll[name]-ll[base];rng=np.random.default_rng(2371103)
        draws=diff[rng.integers(0,len(diff),size=(2000,len(diff)))].mean(axis=1)
        q=np.quantile(draws,[.025,.975]);assert np.max(np.abs(q-result['paired_differences'][name]['bootstrap_95']))<1e-12
        pairs[name]=dict(mean=float(diff.mean()),interval=q.tolist())
    subgroup=d['hidden_threat'][ii];slices={}
    for name,p in pred.items():
        slices[name],_=evaluate(y[subgroup],p[subgroup],g[subgroup])
        for key in ('logloss','brier'):assert abs(slices[name][key]-result['hidden_threat'][name][key])<1e-12
    # CPU re-inference of the teacher independently checks saved CUDA outputs.
    torch.set_num_threads(2);teacher=Teacher().eval()
    teacher.load_state_dict(torch.load(target/'teacher.pt',map_location='cpu',weights_only=True))
    values=[]
    with torch.no_grad():
        for i in range(0,len(x),128):
            values.extend(torch.sigmoid(teacher(torch.tensor(x[i:i+128],dtype=torch.long),torch.tensor(half[i:i+128],dtype=torch.float32))).numpy())
    teacher_error=float(np.max(np.abs(np.array(values)-pred['teacher'])));assert teacher_error<2e-5,teacher_error
    # Native arithmetic of both trained students; no Python model execution.
    lib=ctypes.CDLL(str(SOURCE/'build/student.so'));fp=ctypes.POINTER(ctypes.c_float);bp=ctypes.POINTER(ctypes.c_uint8)
    lib.fow_student_logit.argtypes=[fp,bp,ctypes.c_uint8];lib.fow_student_logit.restype=ctypes.c_float
    native={}
    for name in ('direct_student','distilled_student'):
        state=torch.load(target/(name+'.pt'),map_location='cpu',weights_only=True)
        packed=np.concatenate([state[k].numpy().reshape(-1) for k in ORDER]).astype(np.float32)
        assert len(packed)==160065;wp=packed.ctypes.data_as(fp)
        logits=np.array([lib.fow_student_logit(wp,row.ctypes.data_as(bp),int(h)) for row,h in zip(x,half)])
        probability=1/(1+np.exp(-logits));error=float(np.max(np.abs(probability-pred[name])));assert error<2e-5,error
        export=target/(name+'.fp32.bin');assert not export.exists();packed.tofile(export)
        native[name]=dict(bytes=packed.nbytes,export_sha256=sha(export),max_probability_error=error)
    b=metrics[base];s=metrics[chosen];t=metrics['teacher']
    gate={'teacher_gain':t['logloss']<=.98*b['logloss'],'student_gain':s['logloss']<=.98*b['logloss'],
          'student_interval':pairs[chosen]['interval'][1]<0,'student_brier':s['brier']<=b['brier'],
          'hidden_king_threat':slices[chosen]['logloss']<=slices[base]['logloss']}
    assert gate==result['gates'] and not result['pass_overall']
    report=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,seconds=time.monotonic()-begin,
        test_positions=len(x),games=len(np.unique(g)),metrics=metrics,paired=pairs,hidden_threat=slices,
        cpu_teacher_max_probability_error=teacher_error,native_students=native,gates=gate,
        result_sha256=sha(OUT/'result.json'),source_sha256=sha(__file__),
        scope='Recomputed game-weighted metrics/intervals and epoch selection, CPU teacher and native trained-student parity on all test inputs. Confirms prediction result; no additional training, test tuning, search integration or playing-strength evidence.')
    write_new(OUT/'training-review.json',report);print(json.dumps(report))


if __name__=='__main__':main()
