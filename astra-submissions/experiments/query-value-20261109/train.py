"""Single bounded GPU development fit; never score the opened old test fold."""
from datetime import datetime,timezone
import json
import math
import os
from pathlib import Path
import random
import time
import importlib.util

import numpy as np
import torch
import torch.nn.functional as F
from scipy.special import expit
from model import QueryValue
from prepare import HERE,ROOT,OUT,OLD,EVIDENCE,sha,write


def game_weights(game):
    _,index,count=np.unique(game,return_inverse=True,return_counts=True)
    w=1/count[index];return w/w.mean()


def metrics(y,p,game):
    w=game_weights(game);clipped=np.clip(p,1e-6,1-1e-6)
    return dict(logloss=float(np.average(-y*np.log(clipped)-(1-y)*np.log1p(-clipped),weights=w)),
                brier=float(np.average((y-p)**2,weights=w)))


def main():
    plan=json.loads((OUT/'plan.json').read_text());permit=json.loads((OUT/'gpu-start.json').read_text())
    assert permit['plan_sha256']==sha(OUT/'plan.json') and permit['free_compute_device']
    for p,digest in plan['dependencies'].items():assert sha(Path(p))==digest,p
    os.sched_setaffinity(0,set(plan['resource']['cores']));torch.set_num_threads(2)
    assert torch.cuda.is_available()
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    seed=plan['optimization']['seed'];random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    work=HERE/'work';work.mkdir(exist_ok=False)
    started=time.monotonic();write(work/'started.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),plan_sha256=sha(OUT/'plan.json')))
    spec=importlib.util.spec_from_file_location('retained_value_models',OLD/'models.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    teacher=mod.Teacher().cuda().eval();teacher.load_state_dict(torch.load(OLD/'work/training/teacher.pt',weights_only=True,map_location='cuda'))
    flat=mod.Student().cuda().eval();flat.load_state_dict(torch.load(OLD/'work/training/distilled_student.pt',weights_only=True,map_location='cuda'))
    arrays=np.load(OLD/'work/dataset/data.npz');fold=arrays['fold'];ii={k:np.flatnonzero(fold==k) for k in (0,1)}
    assert len(ii[0])==193517 and len(ii[1])==8746
    # The old fold2 is deliberately never indexed, predicted or scored.
    data={}
    for k in (0,1):
        sel=ii[k];g=arrays['game'][sel];y=arrays['y'][sel];sf=arrays['sf'][sel].astype(np.float64)
        data[k]=dict(x=torch.as_tensor(arrays['x'][sel],device='cuda',dtype=torch.long),
                     half=torch.as_tensor(arrays['half'][sel],device='cuda',dtype=torch.float32),
                     y=torch.as_tensor(y,device='cuda'),w=torch.as_tensor(game_weights(g),device='cuda',dtype=torch.float32),
                     labels=y,games=g,sf=sf)
    @torch.no_grad()
    def predict(m,k):
        m.eval();d=data[k]
        return torch.cat([torch.sigmoid(m(d['x'][i:i+512],d['half'][i:i+512])) for i in range(0,len(d['x']),512)]).cpu().numpy().astype(np.float64)
    va=data[1];a,b=plan['baseline_calibration'];z=np.log(np.clip(va['sf'],1e-6,1-1e-6)/np.clip(1-va['sf'],1e-6,1-1e-6))
    controls={'raw_sf':metrics(va['labels'],va['sf'],va['games']),
              'calibrated_sf':metrics(va['labels'],expit(a+b*z),va['games']),
              'teacher':metrics(va['labels'],predict(teacher,1),va['games']),
              'flat_student':metrics(va['labels'],predict(flat,1),va['games'])}
    assert abs(controls['flat_student']['logloss']-plan['baseline_flat_validation_logloss'])<1e-5
    best_control=min(('raw_sf','calibrated_sf'),key=lambda k:controls[k]['logloss'])
    soft=torch.as_tensor(predict(teacher,0),device='cuda',dtype=torch.float32)
    del teacher,flat;torch.cuda.empty_cache();torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    m=QueryValue().cuda();opt=torch.optim.AdamW(m.parameters(),lr=.001,weight_decay=.0001)
    schedule=torch.optim.lr_scheduler.CosineAnnealingLR(opt,T_max=8);best=math.inf;chosen=0;history=[]
    d=data[0]
    for epoch in range(8):
        m.train();order=torch.randperm(len(d['x']),device='cuda');total=0
        for start in range(0,len(order),512):
            if time.monotonic()-started>1800:raise TimeoutError('fixed30min GPU bound')
            j=order[start:start+512];opt.zero_grad(set_to_none=True)
            logits=m(d['x'][j],d['half'][j]);target=.5*d['y'][j]+.5*soft[j]
            loss=(F.binary_cross_entropy_with_logits(logits,target,reduction='none')*d['w'][j]).mean()
            assert torch.isfinite(loss);loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),1);opt.step()
            total+=float(loss.detach())*len(j)
        schedule.step();p=predict(m,1);stats=metrics(va['labels'],p,va['games'])
        row=dict(epoch=epoch+1,train_loss=total/len(order),validation=stats,elapsed=time.monotonic()-started);history.append(row);print(json.dumps(row),flush=True)
        if stats['logloss']<best:
            best=stats['logloss'];chosen=epoch+1;torch.save(m.state_dict(),work/'selected.pt')
    m.load_state_dict(torch.load(work/'selected.pt',weights_only=True));pred=predict(m,1);stats=metrics(va['labels'],pred,va['games']);control=controls[best_control]
    checks=dict(logloss=stats['logloss']<=.98*control['logloss'],brier=stats['brier']<=control['brier'],
                flat_student=stats['logloss']<=controls['flat_student']['logloss'],parameters=sum(p.numel() for p in m.parameters())<=160065)
    np.savez_compressed(work/'validation-predictions.npz',prediction=pred,y=va['labels'],game=va['games'])
    write(OUT/'curve.json',history)
    write(OUT/'result.json',dict(at=datetime.now(timezone.utc).isoformat(),development_gate_pass=all(checks.values()),checks=checks,
         selected_epoch=chosen,validation=stats,controls=controls,best_sf_control=best_control,
         parameters=sum(p.numel() for p in m.parameters()),elapsed=time.monotonic()-started,
         checkpoint_sha256=sha(work/'selected.pt'),prediction_sha256=sha(work/'validation-predictions.npz'),
         old_test_evaluated=False,plan_sha256=sha(OUT/'plan.json'),
         scope='Development compression only; validation selects the checkpoint. No fresh test, inference-speed or playing-strength result.'))
    print(json.dumps(dict(development_gate_pass=all(checks.values()),checks=checks,validation=stats)),flush=True)


if __name__=='__main__':main()
