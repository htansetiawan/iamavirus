"""One bounded GPU run; validation selects, later test is evaluated once."""
import json
import math
import os
from pathlib import Path
import random
import time

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
import torch
import torch.nn.functional as F

from data import HERE,OUT,load,now,sha,write_new
from models import Teacher,Student


def weights(g):
    _,inv,count=np.unique(g,return_inverse=True,return_counts=True)
    w=1/count[inv];return w/w.mean()


def loss_rows(y,p):
    p=np.clip(np.asarray(p,dtype=np.float64),1e-6,1-1e-6)
    return -(y*np.log(p)+(1-y)*np.log1p(-p))


def metrics(y,p,g):
    w=weights(g);return dict(logloss=float(np.average(loss_rows(y,p),weights=w)),
                            brier=float(np.average((p-y)**2,weights=w)),positions=len(y),games=len(np.unique(g)))


def grouped_diff(y,p,q,g):
    ids,inv,count=np.unique(g,return_inverse=True,return_counts=True)
    diff=loss_rows(y,p)-loss_rows(y,q)
    vals=np.bincount(inv,weights=diff)/count
    rng=np.random.default_rng(2371103);samples=[]
    for _ in range(2000):samples.append(float(vals[rng.integers(len(vals),size=len(vals))].mean()))
    return {'mean':float(vals.mean()),'bootstrap_95':np.quantile(samples,[.025,.975]).tolist(),'games':len(ids)}


def main():
    plan,_=load();droot=HERE/'work/dataset';receipt=json.loads((OUT/'dataset-receipt.json').read_text())
    assert receipt['status']=='complete' and sha(droot/'data.npz')==receipt['artifacts']['data.npz']
    assert json.loads((OUT/'pilot-review.json').read_text())['passed']
    # Require an explicit host free-device receipt immediately preceding this launch.
    permit=json.loads((OUT/'gpu-start.json').read_text());assert permit['free_compute_device'] and permit['plan_sha256']==sha(OUT/'plan.json')
    target=HERE/'work/training';target.mkdir(exist_ok=False)
    started=time.monotonic();write_new(target/'started.json',dict(at=now(),pid=os.getpid(),plan_sha256=sha(OUT/'plan.json')))
    seed=plan['optimization']['seed'];random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    torch.set_num_threads(2);torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    assert torch.cuda.is_available()
    d=np.load(droot/'data.npz');fold=d['fold'];ys=d['y'];games=d['game'];sf=d['sf'].astype(np.float64)
    masks=[np.flatnonzero(fold==k) for k in range(3)];assert all(len(i)>0 for i in masks)
    # Test features remain on CPU until validation selection is saved.
    tensors={}
    for k in (0,1):
        ii=masks[k];tensors[k]=(torch.as_tensor(d['x'][ii],device='cuda',dtype=torch.long),
            torch.as_tensor(d['half'][ii],device='cuda',dtype=torch.float32),
            torch.as_tensor(ys[ii],device='cuda'),torch.as_tensor(weights(games[ii]),device='cuda',dtype=torch.float32))
    def checktime():
        if time.monotonic()-started>3600:raise TimeoutError('one GPU-hour cap')
    @torch.no_grad()
    def predict(model,x,h):
        model.eval();return torch.cat([torch.sigmoid(model(x[i:i+512],h[i:i+512])) for i in range(0,len(x),512)]).cpu().numpy().astype(np.float64)
    def fit(name,klass,soft=None):
        torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
        model=klass().cuda();opt=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0001)
        schedule=torch.optim.lr_scheduler.CosineAnnealingLR(opt,T_max=8)
        x,h,y,w=tensors[0];best=math.inf;chosen=None;history=[]
        for epoch in range(8):
            model.train();order=torch.randperm(len(x),device='cuda');tot=0.;n=0
            for i in range(0,len(x),512):
                checktime();jj=order[i:i+512];opt.zero_grad(set_to_none=True)
                pred=model(x[jj],h[jj]);target_=y[jj] if soft is None else .5*y[jj]+.5*soft[jj]
                loss=(F.binary_cross_entropy_with_logits(pred,target_,reduction='none')*w[jj]).mean()
                if not torch.isfinite(loss):raise RuntimeError('nonfinite loss')
                loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1);opt.step()
                tot+=float(loss.detach())*len(jj);n+=len(jj)
            schedule.step();vp=predict(model,*tensors[1][:2]);m=metrics(ys[masks[1]],vp,games[masks[1]])
            row=dict(model=name,epoch=epoch+1,train_loss=tot/n,validation=m,elapsed=time.monotonic()-started)
            history.append(row);print(json.dumps(row),flush=True)
            if m['logloss']<best:
                best=m['logloss'];chosen=epoch+1;torch.save(model.state_dict(),target/(name+'.pt'))
        write_new(target/(name+'-curve.json'),history)
        model.load_state_dict(torch.load(target/(name+'.pt'),weights_only=True));model.eval()
        return model,dict(epoch=chosen,validation_logloss=best,sha256=sha(target/(name+'.pt')),
                          parameters=sum(p.numel() for p in model.parameters()))
    try:
        tr=masks[0];va=masks[1]
        z=np.log(np.clip(sf[tr],1e-6,1-1e-6)/np.clip(1-sf[tr],1e-6,1-1e-6));w=weights(games[tr]);y=ys[tr]
        def objective(ab):
            v=ab[0]+ab[1]*z;p=expit(v)
            loss=np.average(np.logaddexp(0,v)-y*v,weights=w)
            grad=np.array([np.average(p-y,weights=w),np.average((p-y)*z,weights=w)])
            return loss,grad
        cal=minimize(objective,[0.,1.],jac=True,method='L-BFGS-B',bounds=[(-5,5),(.05,5)])
        assert cal.success,cal.message
        logit_sf=np.log(np.clip(sf,1e-6,1-1e-6)/np.clip(1-sf,1e-6,1-1e-6));calp=expit(cal.x[0]+cal.x[1]*logit_sf)
        controls={'raw_sf':sf,'calibrated_sf':calp}
        selected_control=min(controls,key=lambda k:metrics(ys[va],controls[k][va],games[va])['logloss'])
        teacher,tsel=fit('teacher',Teacher)
        direct,dsel=fit('direct_student',Student)
        soft=torch.as_tensor(predict(teacher,*tensors[0][:2]),device='cuda',dtype=torch.float32)
        distilled,ssel=fit('distilled_student',Student,soft)
        chosen_student='direct_student' if dsel['validation_logloss']<=ssel['validation_logloss'] else 'distilled_student'
        selection=dict(at=now(),teacher=tsel,direct_student=dsel,distilled_student=ssel,chosen_student=chosen_student,
                       chosen_control=selected_control,calibration=cal.x.tolist(),plan_sha256=sha(OUT/'plan.json'),
                       data_sha256=sha(droot/'data.npz'))
        write_new(OUT/'selection.json',selection)
        # Selection is immutable before loading test features to the GPU.
        te=masks[2];tx=torch.as_tensor(d['x'][te],device='cuda',dtype=torch.long);th=torch.as_tensor(d['half'][te],device='cuda',dtype=torch.float32)
        pred={k:v[te] for k,v in controls.items()}
        for name,model in [('teacher',teacher),('direct_student',direct),('distilled_student',distilled)]:pred[name]=predict(model,tx,th)
        test={name:metrics(ys[te],p,games[te]) for name,p in pred.items()};base=pred[selected_control]
        ci={name:grouped_diff(ys[te],pred[name],base,games[te]) for name in ('teacher','direct_student','distilled_student')}
        threat=d['hidden_threat'][te];slices={name:metrics(ys[te][threat],p[threat],games[te][threat]) for name,p in pred.items()} if threat.any() else {}
        b=test[selected_control];s=test[chosen_student];t=test['teacher']
        gates={'teacher_gain':t['logloss']<=.98*b['logloss'],'student_gain':s['logloss']<=.98*b['logloss'],
            'student_interval':ci[chosen_student]['bootstrap_95'][1]<0,'student_brier':s['brier']<=b['brier']}
        if slices and slices[selected_control]['positions']>=100 and slices[selected_control]['games']>=30:
            gates['hidden_king_threat']=slices[chosen_student]['logloss']<=slices[selected_control]['logloss']
        else:gates['hidden_king_threat']=None
        result=dict(at=now(),test=test,paired_differences=ci,hidden_threat=slices,selection=selection,gates=gates,
            pass_overall=all(v for v in gates.values() if v is not None),seconds=time.monotonic()-started,
            scope='Temporal off-policy outcome prediction, not playing strength. Insufficient threat subgroup is reported, not interpreted as a passed safety check.')
        np.savez(target/'test-predictions.npz',indices=te,**pred)
        write_new(OUT/'result.json',result);print(json.dumps(result),flush=True)
        write_new(OUT/'training-terminal.json',dict(at=now(),status='complete',seconds=time.monotonic()-started,
            result_sha256=sha(OUT/'result.json'),checkpoints={p.name:sha(p) for p in target.glob('*.pt')},
            predictions_sha256=sha(target/'test-predictions.npz')))
    except BaseException as e:
        write_new(target/'failure.json',dict(at=now(),error=repr(e),seconds=time.monotonic()-started));raise


if __name__=='__main__':main()
