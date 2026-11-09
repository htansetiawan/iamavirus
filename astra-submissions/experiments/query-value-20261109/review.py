"""Independent CPU checkpoint prediction and game-aggregated metric audit."""
import json
from pathlib import Path
import os
import numpy as np
import torch
from scipy.special import expit
from model import QueryValue
from prepare import HERE,OLD,OUT,sha,write


def scores(y,p,g):
    clipped=np.clip(p,1e-6,1-1e-6);ll=-y*np.log(clipped)-(1-y)*np.log1p(-clipped);br=(p-y)**2
    groups={}
    for game,a,b in zip(g,ll,br):
        count,x,z=groups.get(int(game),(0,0.,0.));groups[int(game)]=(count+1,x+a,z+b)
    return dict(logloss=float(np.mean([a/n for n,a,b in groups.values()])),
                brier=float(np.mean([b/n for n,a,b in groups.values()])))


def main():
    os.sched_setaffinity(0,{4,5});torch.set_num_threads(2);torch.backends.mha.set_fastpath_enabled(False)
    result=json.loads((OUT/'result.json').read_text());plan=json.loads((OUT/'plan.json').read_text())
    assert sha(HERE/'work/selected.pt')==result['checkpoint_sha256']
    assert sha(HERE/'work/validation-predictions.npz')==result['prediction_sha256']
    assert sha(OUT/'plan.json')==result['plan_sha256']
    curve=json.loads((OUT/'curve.json').read_text());assert len(curve)==8
    assert result['selected_epoch']==min(curve,key=lambda r:r['validation']['logloss'])['epoch']
    old=np.load(OLD/'work/dataset/data.npz');ii=np.flatnonzero(old['fold']==1);assert len(ii)==8746
    saved=np.load(HERE/'work/validation-predictions.npz');y=old['y'][ii];game=old['game'][ii]
    assert np.array_equal(saved['y'],y) and np.array_equal(saved['game'],game)
    m=QueryValue().eval();m.load_state_dict(torch.load(HERE/'work/selected.pt',map_location='cpu',weights_only=True))
    x=torch.from_numpy(old['x'][ii].astype(np.int64));half=torch.from_numpy(old['half'][ii].astype(np.float32))
    with torch.no_grad():p=torch.cat([torch.sigmoid(m(x[i:i+64],half[i:i+64])) for i in range(0,len(x),64)]).numpy().astype(np.float64)
    gpu=saved['prediction'];error=float(np.max(np.abs(gpu-p)));assert error<2e-4
    original=scores(y,gpu,game);cpu=scores(y,p,game)
    for name in original:assert abs(original[name]-result['validation'][name])<1e-12 and abs(cpu[name]-original[name])<1e-5
    sf=old['sf'][ii].astype(np.float64);a,b=plan['baseline_calibration'];cal=expit(a+b*np.log(np.clip(sf,1e-6,1-1e-6)/np.clip(1-sf,1e-6,1-1e-6)))
    control=scores(y,cal,game)
    for name in control:assert abs(control[name]-result['controls']['calibrated_sf'][name])<1e-12
    checks=dict(logloss=original['logloss']<=.98*control['logloss'],brier=original['brier']<=control['brier'],
                flat_student=original['logloss']<=result['controls']['flat_student']['logloss'],parameters=sum(v.numel() for v in m.parameters())<=160065)
    assert checks==result['checks'] and all(checks.values())==result['development_gate_pass']
    write(OUT/'review.json',dict(passed=True,development_gate_pass=result['development_gate_pass'],checks=checks,
          cpu_validation=cpu,max_cpu_gpu_probability_difference=error,validation_games=len(np.unique(game)),
          old_test_evaluated=False,script_sha256=sha(Path(__file__)),result_sha256=sha(OUT/'result.json')))
    print(json.dumps(dict(audit_pass=True,development_gate_pass=result['development_gate_pass'],cpu_validation=cpu,max_difference=error)))


if __name__=='__main__':main()
