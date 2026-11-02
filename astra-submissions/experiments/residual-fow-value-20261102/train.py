"""One matched development fit; never load either opened test for prediction."""
import json
import math
import os
import random
import time
import numpy as np
from scipy.special import expit
import torch
import torch.nn.functional as F
from common import HERE, ROOT, OUT, OLD, QUERY, OLDOUT, now, sha, write_new
from models import FlatResidual, QueryResidual, pack


def weights(g):
    _,inv,count=np.unique(g,return_inverse=True,return_counts=True);w=1/count[inv];return w/w.mean()


def metrics(y,p,g):
    original=np.asarray(p,dtype=np.float64);p=np.clip(original,1e-6,1-1e-6)
    return dict(logloss=float(np.average(-(y*np.log(p)+(1-y)*np.log1p(-p)),weights=weights(g))),
        brier=float(np.average((original-y)**2,weights=weights(g))),positions=len(y),games=len(np.unique(g)))


def freeze():
    pre=json.loads((OUT/'preflight.json').read_text());assert pre['passed']
    files=list(HERE.glob('*.py'))+[HERE/'README.md',OLD/'models.py',OLD/'student_infer.c',QUERY/'models.py',QUERY/'query_infer.c',
        OLD/'work/dataset/data.npz',OLDOUT/'selection.json',OLDOUT/'dataset-review.json',HERE/'build/flat.c',HERE/'build/query.c',HERE/'build/residual.so']
    p=dict(at=now(),name='239 bounded SF-residual development screen',dependencies={str(p):sha(p) for p in files},
        arms=['flat','query'],optimization=dict(seed=2391102,epochs=32,batch=512,learning_rate=.001,weight_decay=.0001,
            gradient_clip=1.,schedule='cosine',optimizer='AdamW',loss='equal-game outcome BCE',dtype='FP32; TF32 disabled',gpu_wall_cap_seconds=1200),
        residual=dict(bound_log_odds=2.,sf_condition_scale=4.,neutral_output_initialization=True,distillation=False),
        baseline='Fixed237 training-only two-parameter calibration; no refit.',selection='Minimum validation log loss over epochs, then arms.',
        gate=dict(relative_logloss_gain_min=.02,brier_difference_max=0.,hidden_threat_logloss_difference_max=0.,
            hidden_threat_min_positions=100,hidden_threat_min_games=30,native_max_bytes=1048576,
            native_max_median_microseconds=50,native_max_probability_error=2e-5),
        test_policy='Do not score237 or238 tests. Passing development gate earns a separately frozen fresh confirmation, not integration.',
        scope='Reused development validation; no unbiased generalization or strength inference. No Fable agreement assumed.')
    write_new(OUT/'plan.json',p);print(json.dumps({'plan_sha256':sha(OUT/'plan.json')}),flush=True)


def main():
    plan=json.loads((OUT/'plan.json').read_text())
    for name,h in plan['dependencies'].items():assert sha(ROOT/name)==h,name
    permit=json.loads((OUT/'gpu-start.json').read_text());assert permit['free_compute_device'] and permit['plan_sha256']==sha(OUT/'plan.json')
    target=HERE/'work/training';target.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    write_new(target/'started.json',dict(at=now(),pid=os.getpid(),plan_sha256=sha(OUT/'plan.json')))
    torch.set_num_threads(2);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    seed=plan['optimization']['seed'];random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    assert torch.cuda.is_available()
    with np.load(OLD/'work/dataset/data.npz') as a:
        masks=[np.flatnonzero(a['fold']==k) for k in (0,1)]
        xs=a['x'];halves=a['half'];ys=a['y'];games=a['game'];sfs=a['sf'];hidden=a['hidden_threat']
    # Only train and validation rows are transferred/scored. Opened tests never enter an arm.
    ab=json.loads((OLDOUT/'selection.json').read_text())['calibration'];cpu={};gpu={}
    for k,ii in enumerate(masks):
        sf=sfs[ii].astype(np.float64);z=ab[0]+ab[1]*np.log(np.clip(sf,1e-6,1-1e-6)/np.clip(1-sf,1e-6,1-1e-6))
        cpu[k]=dict(y=ys[ii].astype(np.float64),game=games[ii],sf=sf,z=z,hidden=hidden[ii])
        gpu[k]=(torch.tensor(xs[ii],device='cuda',dtype=torch.long),torch.tensor(halves[ii],device='cuda',dtype=torch.float32),
            torch.tensor(z,device='cuda',dtype=torch.float32),torch.tensor(ys[ii],device='cuda'),
            torch.tensor(weights(games[ii]),device='cuda',dtype=torch.float32))
    @torch.no_grad()
    def predict(model,t):
        model.eval();x,h,z=t[:3]
        return torch.cat([torch.sigmoid(model(x[i:i+512],h[i:i+512],z[i:i+512])) for i in range(0,len(x),512)]).cpu().numpy().astype(np.float64)
    val=cpu[1];base=expit(val['z']);pred={'calibrated_sf':base,'raw_sf':val['sf']};selection={};trained={}
    try:
        for name,klass in [('flat',FlatResidual),('query',QueryResidual)]:
            torch.manual_seed(seed);torch.cuda.manual_seed_all(seed);model=klass().cuda()
            # Neutral model should preserve the fixed baseline before any update.
            initial=predict(model,gpu[1]);assert np.max(abs(initial-base))<2e-7
            opt=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0001)
            schedule=torch.optim.lr_scheduler.CosineAnnealingLR(opt,T_max=32)
            x,h,z,y,w=gpu[0];best=math.inf;curve=[];chosen=None
            for epoch in range(32):
                model.train();order=torch.randperm(len(x),device='cuda');total=0
                for j in range(0,len(x),512):
                    if time.monotonic()-start>1200:raise TimeoutError('20-minute GPU cap')
                    ii=order[j:j+512];opt.zero_grad(set_to_none=True)
                    l=(F.binary_cross_entropy_with_logits(model(x[ii],h[ii],z[ii]),y[ii],reduction='none')*w[ii]).mean()
                    assert torch.isfinite(l),name
                    l.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1);opt.step();total+=float(l.detach())*len(ii)
                schedule.step();vp=predict(model,gpu[1]);m=metrics(val['y'],vp,val['game'])
                row=dict(arm=name,epoch=epoch+1,train_loss=total/len(x),validation=m,elapsed=time.monotonic()-start)
                curve.append(row);print(json.dumps(row),flush=True)
                if m['logloss']<best:
                    best=m['logloss'];chosen=epoch+1;torch.save(model.state_dict(),target/(name+'.pt'))
            write_new(target/(name+'-curve.json'),curve)
            model.load_state_dict(torch.load(target/(name+'.pt'),weights_only=True));model.eval();trained[name]=model
            pred[name]=predict(model,gpu[1]);selection[name]=dict(epoch=chosen,validation_logloss=best,
                sha256=sha(target/(name+'.pt')),parameters=sum(p.numel() for p in model.parameters()))
        chosen=min(selection,key=lambda n:selection[n]['validation_logloss'])
        results={n:metrics(val['y'],p,val['game']) for n,p in pred.items()}
        hidden=val['hidden'];slices={n:metrics(val['y'][hidden],p[hidden],val['game'][hidden]) for n,p in pred.items()}
        b=results['calibrated_sf'];s=results[chosen]
        sufficient=slices[chosen]['positions']>=100 and slices[chosen]['games']>=30
        gates=dict(logloss_gain=s['logloss']<=.98*b['logloss'],brier=s['brier']<=b['brier'],
            hidden_threat=slices[chosen]['logloss']<=slices['calibrated_sf']['logloss'] if sufficient else None)
        result=dict(at=now(),selection=selection,chosen=chosen,validation=results,hidden_threat=slices,
            gates=gates,pass_development=all(v is True for v in gates.values()),seconds=time.monotonic()-start,
            calibration=ab,scope='Reused development validation only. No test or strength result; pass earns fresh confirmation, not integration.')
        np.savez(target/'validation-predictions.npz',indices=masks[1],**pred)
        write_new(OUT/'result.json',result)
        for name,model in trained.items():pack(model,name).tofile(target/(name+'.fp32.bin'))
        write_new(OUT/'training-terminal.json',dict(at=now(),status='complete',seconds=time.monotonic()-start,
            result_sha256=sha(OUT/'result.json'),predictions_sha256=sha(target/'validation-predictions.npz'),
            checkpoints={p.name:sha(p) for p in target.glob('*.pt')}))
        print(json.dumps(result),flush=True)
    except BaseException as e:
        write_new(target/'failure.json',dict(at=now(),error=repr(e),seconds=time.monotonic()-start));raise


if __name__=='__main__':
    import sys
    freeze() if len(sys.argv)>1 and sys.argv[1]=='freeze' else main()
