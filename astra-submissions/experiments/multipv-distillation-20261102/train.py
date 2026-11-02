"""One bounded fit on existing teacher values; never load the old TEST fold."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np
import torch
from torch.nn import functional as F

from data import HERE,ROOT,OUT,sha,write
from model import MultiPVStudent


def game_average(values,games):
    _,inverse,counts=np.unique(games,return_inverse=True,return_counts=True)
    return float(np.sum(np.asarray(values)/counts[inverse])/len(counts))


def metrics(pred,target,mask,games):
    counts=mask.sum(1)
    mse=(((pred-target)**2)*mask).sum(1)/counts
    mae=(np.abs(pred-target)*mask).sum(1)/counts
    choice=np.where(mask,pred,-np.inf).argmax(1)
    regret=np.where(mask,target,-np.inf).max(1)-target[np.arange(len(target)),choice]
    return dict(mse=game_average(mse,games),mae=game_average(mae,games),
                teacher_regret=game_average(regret,games),regret_over_half_rate=game_average(regret>.5,games),
                parents=len(pred),games=len(np.unique(games)),actions=int(mask.sum()))


def main():
    os.sched_setaffinity(0,{0,1});torch.set_num_threads(2)
    receipt=json.loads((OUT/'data-receipt.json').read_text());assert receipt['passed']
    assert sha(HERE/'work/data.npz')==receipt['data_sha256']
    plan=json.loads((OUT/'plan.json').read_text());assert sha(OUT/'plan.json')==receipt['plan_sha256']
    for p,h in plan['sources'].items():assert sha(ROOT/p)==h,p
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True).strip()
    assert not apps,'GPU occupied; leave existing work running'
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip()
    target=HERE/'work/training';target.mkdir(exist_ok=False)
    start=time.monotonic();settings=plan['optimization'];seed=settings['seed']
    record=dict(startedAt=datetime.now(timezone.utc).isoformat(),state='running',gpu=gpu,competing_apps=apps,
                no_existing_service_stopped=True,plan_sha256=sha(OUT/'plan.json'),data_sha256=receipt['data_sha256'],
                training_source_sha256=sha(__file__),model_source_sha256=sha(HERE/'model.py'),epochs_completed=0)
    write(OUT/'training-receipt.json',record)
    torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    try:
        data=np.load(HERE/'work/data.npz');assert set(data['fold'].tolist())=={0,1}
        tensors={}
        for fold in (0,1):
            ix=np.flatnonzero(data['fold']==fold)
            tensors[fold]=[torch.tensor(data[n][ix],device='cuda',dtype=torch.float32 if n in ('half','y') else torch.bool if n=='mask' else torch.long)
                           for n in ('piece','castle','ep','half','actions','y','mask')]
        train_games=data['game'][data['fold']==0];valid_games=data['game'][data['fold']==1]
        assert not set(train_games)&set(valid_games)
        _,inv,cnt=np.unique(train_games,return_inverse=True,return_counts=True)
        weights=torch.tensor(len(train_games)/len(cnt)/cnt[inv],device='cuda',dtype=torch.float32)
        model=MultiPVStudent().cuda();opt=torch.optim.AdamW(model.parameters(),lr=settings['lr'],weight_decay=settings['decay'])
        scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(opt,T_max=settings['epochs'])
        @torch.no_grad()
        def predict(inputs):
            model.eval()
            return np.concatenate([model(*[x[i:i+256] for x in inputs[:5]]).cpu().numpy() for i in range(0,len(inputs[0]),256)])
        ty=data['y'][data['fold']==1];tm=data['mask'][data['fold']==1]
        before=metrics(predict(tensors[1]),ty,tm,valid_games)
        write(OUT/'untrained-control.json',before)
        best=float('inf');curve=[];selected=0
        for epoch in range(settings['epochs']):
            model.train();order=torch.randperm(len(train_games),device='cuda');loss_sum=0.;samples=0
            for at in range(0,len(order),settings['batch']):
                if time.monotonic()-start>settings['gpu_seconds']:raise TimeoutError('20 minute training cap')
                j=order[at:at+settings['batch']];x=[t[j] for t in tensors[0]];p=model(*x[:5]);y,mask=x[5:]
                mse=((p-y).square()*mask).sum(1)/mask.sum(1)
                pt=F.softmax((y/settings['temperature']).masked_fill(~mask,-1e9),dim=1)
                lp=F.log_softmax((p/settings['temperature']).masked_fill(~mask,-1e9),dim=1)
                kl=F.kl_div(lp,pt,reduction='none').sum(1)
                loss=((mse+settings['kl_weight']*kl)*weights[j]).mean()
                assert torch.isfinite(loss)
                opt.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1);opt.step()
                loss_sum+=float(loss.detach())*len(j);samples+=len(j)
            scheduler.step();scores=metrics(predict(tensors[1]),ty,tm,valid_games)
            row=dict(epoch=epoch+1,loss=loss_sum/samples,validation=scores,seconds=time.monotonic()-start)
            curve.append(row);print(json.dumps(row),flush=True)
            if scores['mse']<best:
                best=scores['mse'];selected=epoch+1;torch.save(model.state_dict(),target/'selected.pt')
            record['epochs_completed']=epoch+1
            (OUT/'training-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
        model.load_state_dict(torch.load(target/'selected.pt',weights_only=True));pred=predict(tensors[1])
        result=metrics(pred,ty,tm,valid_games);gate=plan['gate']
        checks=dict(mae=result['mae']<=gate['mae_max'],teacher_regret=result['teacher_regret']<=gate['teacher_regret_max'],
                    large_regret=result['regret_over_half_rate']<=gate['regret_over_half_rate_max'])
        np.savez(target/'validation.npz',pred=pred,target=ty,mask=tm,games=valid_games)
        write(OUT/'curve.json',curve)
        write(OUT/'result.json',dict(selected_epoch=selected,validation=result,checks=checks,pass_development_gate=all(checks.values()),
              parameters=sum(p.numel() for p in model.parameters()),checkpoint_sha256=sha(target/'selected.pt'),
              predictions_sha256=sha(target/'validation.npz'),scope='Teacher approximation on reused development games; not a FOW value or playing strength test.'))
        record.update(state='completed',peak_allocated_bytes=torch.cuda.max_memory_allocated(),selected_epoch=selected)
    except BaseException as e:
        record.update(state='failed',error=repr(e));raise
    finally:
        record.update(endedAt=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-start)
        (OUT/'training-receipt.json').write_text(json.dumps(record,indent=2)+'\n')


if __name__=='__main__':main()
