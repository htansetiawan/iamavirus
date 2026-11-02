"""Matched-budget compact students; frozen fresh test opened after selection."""
import importlib.util
import json
import math
import os
import random
import time
import numpy as np
from scipy.special import expit
import torch
import torch.nn.functional as F

from common import HERE, ROOT, OUT, OLD, OLDOUT, now, sha, write_new
from models import QueryStudent, pack_native

spec=importlib.util.spec_from_file_location('old_models',OLD/'models.py')
old_models=importlib.util.module_from_spec(spec);spec.loader.exec_module(old_models)
ARMS=('flat_distilled','query_direct','query_distilled')


def weights(g):
    _,inv,n=np.unique(g,return_inverse=True,return_counts=True);w=1/n[inv];return w/w.mean()


def loss(y,p):
    p=np.clip(np.asarray(p,dtype=np.float64),1e-6,1-1e-6)
    return -(y*np.log(p)+(1-y)*np.log1p(-p))


def metrics(y,p,g):
    return dict(logloss=float(np.average(loss(y,p),weights=weights(g))),
        brier=float(np.average((p-y)**2,weights=weights(g))),positions=len(y),games=len(np.unique(g)))


def difference(y,p,q,g):
    _,inv,n=np.unique(g,return_inverse=True,return_counts=True)
    v=np.bincount(inv,weights=loss(y,p)-loss(y,q))/n
    rng=np.random.default_rng(2381103)
    draws=v[rng.integers(len(v),size=(2000,len(v)))].mean(axis=1)
    return dict(mean=float(v.mean()),bootstrap_95=np.quantile(draws,[.025,.975]).tolist(),games=len(v))


def freeze():
    assert not (OUT/'plan.json').exists()
    pre=json.loads((OUT/'native-preflight.json').read_text());assert all(pre['gates'].values())
    assert json.loads((OUT/'holdout-review.json').read_text())['passed']
    paths=list(HERE.glob('*.py'))+list(HERE.glob('*.c'))+[HERE/'README.md',HERE/'build/query.so',
        OLD/'models.py',OLD/'work/training/teacher.pt',OLD/'work/training/direct_student.pt',
        OLD/'work/training/distilled_student.pt',OLD/'work/dataset/data.npz',OLDOUT/'selection.json',
        OLDOUT/'training-review.json',HERE/'work/holdout/data.npz',OUT/'games.json',OUT/'holdout-selection.json',
        OUT/'holdout-review.json',OUT/'native-preflight.json']
    plan=dict(at=now(),name='238 matched-budget query value compression',
        dependencies={str(p):sha(p) for p in paths},arms=list(ARMS),
        optimization=dict(seed=2381102,epochs_per_arm=32,batch=512,learning_rate=.001,weight_decay=.0001,
            optimizer='AdamW',schedule='cosine',gradient_clip=1.,dtype='FP32; TF32 disabled',
            distillation_teacher_weight=.5,loss='equal-game weighted binary cross entropy',gpu_wall_cap_seconds=1800),
        model_selection='Minimum equal-game validation log loss among all epochs and all three arms; freeze before fresh-test predictions.',
        baseline='Frozen237 train-fitted SF calibration; no new calibration fitting.',
        gate=dict(relative_logloss_gain_min=.02,game_bootstrap_upper_difference_max=0.,brier_difference_max=0.,
            new_date_point_logloss_difference_max=0.,hidden_threat_point_logloss_difference_max=0.,
            hidden_threat_min_positions=100,hidden_threat_min_games=30,
            hidden_threat_insufficient='Quality gate incomplete; no deployment inferred from missing subgroup.',
            native_max_probability_error=2e-5,native_max_bytes=1048576,native_max_median_microseconds=50),
        scope='Outcome prediction on unused older/new-date game cohorts. Not self-play equilibrium values or arena Elo. No decision integration unless quality/native gates pass, followed by independent decision and full-game validation.')
    write_new(OUT/'plan.json',plan);print(json.dumps({'plan_sha256':sha(OUT/'plan.json')}),flush=True)


def main():
    plan=json.loads((OUT/'plan.json').read_text())
    for name,h in plan['dependencies'].items():assert sha(ROOT/name)==h,name
    permit=json.loads((OUT/'gpu-start.json').read_text());assert permit['free_compute_device'] and permit['plan_sha256']==sha(OUT/'plan.json')
    target=HERE/'work/training';target.mkdir(exist_ok=False);begin=time.monotonic()
    write_new(target/'started.json',dict(at=now(),pid=os.getpid(),plan_sha256=sha(OUT/'plan.json')))
    seed=plan['optimization']['seed'];torch.set_num_threads(2)
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    assert torch.cuda.is_available()
    with np.load(OLD/'work/dataset/data.npz') as source:
        fold=source['fold'];ii=np.flatnonzero(fold==0);vi=np.flatnonzero(fold==1)
        features=source['x'];half=source['half'];ys=source['y'];games=source['game']
    tensors={}
    for k,jj in enumerate((ii,vi)):
        tensors[k]=(torch.tensor(features[jj],device='cuda',dtype=torch.long),torch.tensor(half[jj],device='cuda',dtype=torch.float32),
            torch.tensor(ys[jj],device='cuda'),torch.tensor(weights(games[jj]),device='cuda',dtype=torch.float32))
    @torch.no_grad()
    def predict(model,x,h):
        model.eval();return torch.cat([torch.sigmoid(model(x[j:j+512],h[j:j+512])) for j in range(0,len(x),512)]).cpu().numpy().astype(np.float64)
    def checktime():
        if time.monotonic()-begin>1800:raise TimeoutError('30-minute GPU cap')
    try:
        teacher=old_models.Teacher().cuda().eval()
        teacher.load_state_dict(torch.load(OLD/'work/training/teacher.pt',weights_only=True,map_location='cuda'))
        soft=torch.tensor(predict(teacher,*tensors[0][:2]),device='cuda',dtype=torch.float32)
        trained={};selections={}
        for name in ARMS:
            torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
            model=(old_models.Student() if name=='flat_distilled' else QueryStudent()).cuda()
            opt=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0001)
            schedule=torch.optim.lr_scheduler.CosineAnnealingLR(opt,T_max=32)
            x,h,y,w=tensors[0];target_y=y if name=='query_direct' else .5*y+.5*soft
            best=math.inf;chosen=None;curve=[]
            for epoch in range(32):
                model.train();order=torch.randperm(len(x),device='cuda');total=0
                for start in range(0,len(x),512):
                    checktime();jj=order[start:start+512];opt.zero_grad(set_to_none=True)
                    l=(F.binary_cross_entropy_with_logits(model(x[jj],h[jj]),target_y[jj],reduction='none')*w[jj]).mean()
                    assert torch.isfinite(l),name
                    l.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1);opt.step();total+=float(l.detach())*len(jj)
                schedule.step();vp=predict(model,*tensors[1][:2]);m=metrics(ys[vi],vp,games[vi])
                row=dict(model=name,epoch=epoch+1,train_loss=total/len(x),validation=m,elapsed=time.monotonic()-begin)
                curve.append(row);print(json.dumps(row),flush=True)
                if m['logloss']<best:
                    best=m['logloss'];chosen=epoch+1;torch.save(model.state_dict(),target/(name+'.pt'))
            write_new(target/(name+'-curve.json'),curve)
            model.load_state_dict(torch.load(target/(name+'.pt'),weights_only=True));model.eval();trained[name]=model
            selections[name]=dict(epoch=chosen,validation_logloss=best,sha256=sha(target/(name+'.pt')),
                parameters=sum(p.numel() for p in model.parameters()))
        selected=min(ARMS,key=lambda name:selections[name]['validation_logloss'])
        selection=dict(at=now(),arms=selections,chosen_student=selected,plan_sha256=sha(OUT/'plan.json'))
        write_new(OUT/'selection.json',selection)
        # The independent fresh holdout is first opened for prediction here.
        with np.load(HERE/'work/holdout/data.npz') as source:d={k:source[k] for k in source.files}
        x=torch.tensor(d['x'],device='cuda',dtype=torch.long);h=torch.tensor(d['half'],device='cuda',dtype=torch.float32)
        y=d['y'].astype(np.float64);g=d['game'];sf=d['sf'].astype(np.float64)
        ab=json.loads((OLDOUT/'selection.json').read_text())['calibration']
        z=np.log(np.clip(sf,1e-6,1-1e-6)/np.clip(1-sf,1e-6,1-1e-6))
        pred={'raw_sf':sf,'calibrated_sf':expit(ab[0]+ab[1]*z),'teacher':predict(teacher,x,h)}
        for name,model in trained.items():pred[name]=predict(model,x,h)
        for name in ('direct_student','distilled_student'):
            model=old_models.Student().cuda().eval();model.load_state_dict(torch.load(OLD/'work/training'/(name+'.pt'),weights_only=True,map_location='cuda'))
            pred['old_'+name]=predict(model,x,h)
        tests={name:metrics(y,p,g) for name,p in pred.items()};base=pred['calibrated_sf']
        diffs={name:difference(y,p,base,g) for name,p in pred.items() if name not in ('raw_sf','calibrated_sf')}
        slices={}
        for tag,mask in [('older_unused',d['group']==0),('new_date',d['group']==1),('hidden_threat',d['hidden_threat'])]:
            slices[tag]={name:metrics(y[mask],p[mask],g[mask]) for name,p in pred.items()} if mask.any() else {}
        b=tests['calibrated_sf'];s=tests[selected];th=slices['hidden_threat']
        sufficient=bool(th and th[selected]['positions']>=100 and th[selected]['games']>=30)
        gates=dict(logloss_gain=s['logloss']<=.98*b['logloss'],game_interval=diffs[selected]['bootstrap_95'][1]<0,
            brier=s['brier']<=b['brier'],new_date=slices['new_date'][selected]['logloss']<=slices['new_date']['calibrated_sf']['logloss'],
            hidden_threat=th[selected]['logloss']<=th['calibrated_sf']['logloss'] if sufficient else None)
        result=dict(at=now(),selection=selection,test=tests,paired_differences=diffs,slices=slices,gates=gates,
            pass_quality=all(v is True for v in gates.values()),seconds=time.monotonic()-begin,
            scope='Fresh-disjoint off-policy outcome prediction. A native trained-weight check and actual policy evaluation remain necessary.')
        np.savez(target/'test-predictions.npz',**pred)
        write_new(OUT/'result.json',result)
        for name in ('query_direct','query_distilled'):
            packed=pack_native(trained[name]);packed.tofile(target/(name+'.fp32.bin'))
        write_new(OUT/'training-terminal.json',dict(at=now(),status='complete',seconds=time.monotonic()-begin,
            result_sha256=sha(OUT/'result.json'),checkpoints={p.name:sha(p) for p in target.glob('*.pt')},
            predictions_sha256=sha(target/'test-predictions.npz')))
        print(json.dumps(result),flush=True)
    except BaseException as e:
        write_new(target/'failure.json',dict(at=now(),error=repr(e),seconds=time.monotonic()-begin));raise


if __name__=='__main__':
    import sys
    freeze() if len(sys.argv)>1 and sys.argv[1]=='freeze' else main()
