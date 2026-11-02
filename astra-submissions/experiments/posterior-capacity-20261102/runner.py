from collections import defaultdict
import gc
import gzip
import json
import os
from pathlib import Path
import signal
import time
import traceback
import numpy as np
import torch
from settings import ROOT,OUT,Dataset,exporter,baseline_parity,game_mean,now,sha,unique
from quadratic import Residual,probabilities,values


def report(meta,pred,plan):
    masks={'primary':lambda r:r['primary'],'all':lambda r:True,
           'late':lambda r:r['primary'] and r['late'],'surprise':lambda r:r['primary'] and r['surprise']}
    result={}
    for name,mask in masks.items():
        ix=[i for i,r in enumerate(meta) if mask(r)]
        row=dict(cases=len(ix),games=len({meta[i]['game'] for i in ix}),unsupported=sum(not meta[i]['natural_support'] for i in ix))
        row['nll']={k:game_mean(-v[0],meta,mask) for k,v in pred.items()}
        row['actor_nll']={k:game_mean(-v[1],meta,mask) for k,v in pred.items()}
        row['gain']=game_mean(pred['quadratic-posterior'][0]-pred['baseline'][0],meta,mask)
        for k in ('linear-posterior','quadratic-actor'):
            row['gain_over_'+k]=game_mean(pred['quadratic-posterior'][0]-pred[k][0],meta,mask)
        result[name]=row
    p=result['primary'];s=result['surprise'];l=result['late'];a=result['all'];g=plan['gate']
    checks=dict(baseline_gain=p['gain']>=g['baseline_gain'],
                linear_posterior=p['gain_over_linear-posterior']>=g['linear_posterior_gain'],
                quadratic_actor=p['gain_over_quadratic-actor']>=g['quadratic_actor_gain'],
                late=l['gain'] is not None and l['gain']>=g['late_min_gain'],
                surprise_count=s['cases']>=g['min_surprise'],
                surprise=s['gain'] is not None and s['gain']>=g['surprise_min_gain'],
                all=a['gain']>=g['all_min_gain'],support=a['unsupported']<=g['max_support_failures'])
    return dict(metrics=result,checks=checks,passed=all(checks.values()))


def main():
    plan=json.loads((OUT/'plan.json').read_text());start=time.monotonic()
    os.sched_setaffinity(0,set(plan['cores']));torch.set_num_threads(2);torch.set_num_interop_threads(1)
    torch.manual_seed(plan['seed']);np.random.seed(plan['seed'])
    assert plan['device']=='cpu' and all(g['split']!='test' for g in plan['games'])
    for p,h in plan['dependencies'].items():assert sha(Path(p))==h,p
    def expired(*args):raise TimeoutError('Frozen45minute development bound')
    signal.signal(signal.SIGALRM,expired);signal.alarm(plan['wall_seconds'])
    unique(OUT/'execution.json',dict(at=now(),pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],
        plan_sha256=sha(OUT/'plan.json'),device='cpu',status='started'))
    try:
        raw=exporter.collect(plan,'train');vr=exporter.collect(plan,'validation')
        for split in ('train','validation'):
            old=json.loads((OUT.parent/'posterior-fit-20261102'/(split+'-data.json')).read_text())
            new=json.loads((OUT/(split+'-data.json')).read_text())
            assert old['features_sha256']==new['features_sha256'] and old['games']==new['games']
        unsupported=sum(not r['meta']['natural_support'] for r in raw)
        train=Dataset([r for r in raw if r['meta']['natural_support']],'cpu');val=Dataset(vr,'cpu');del raw,vr;gc.collect()
        parity=dict(train=baseline_parity(train),validation=baseline_parity(val))
        base=Residual('linear','cpu');base_scores=values(val,base,plan['probability_floor'])
        unique(OUT/'input-check.json',dict(parity=parity,excluded_train_unsupported=unsupported,same231_features=True))
        models=[]
        for form in plan['forms']:
            for target in plan['objectives']:
                for ridge in plan['ridges']:
                    model=Residual(form,'cpu');optimizer=torch.optim.Adam(model.parameters(),lr=plan['learning_rate'])
                    curve=[];best=None;name=f'{form}-{target}-{ridge:g}'
                    for step in range(1,plan['steps']+1):
                        optimizer.zero_grad();post,act=probabilities(train,model)
                        loss=-((post if target=='posterior' else act)*train.weight).sum()+ridge*model.penalty()
                        assert torch.isfinite(loss);loss.backward()
                        assert all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
                        optimizer.step()
                        if step%plan['validation_every']==0:
                            prediction=values(val,model,plan['probability_floor'])
                            nll=game_mean(-prediction[0],val.meta,lambda r:r['primary']);assert nll is not None
                            row=dict(step=step,train_loss=float(loss.detach()),validation_nll=nll,**model.coefficients())
                            curve.append(row)
                            if best is None or nll<best['validation_nll']:best=row
                    record=dict(form=form,objective=target,ridge=ridge,**best)
                    unique(OUT/(name+'-curve.json'),curve);unique(OUT/(name+'-model.json'),record);models.append(record)
                    print(json.dumps({k:v for k,v in record.items() if k not in ('linear','quadratic')}),flush=True)
        selection={f'{form}-{target}':min((m for m in models if m['form']==form and m['objective']==target),key=lambda r:(r['validation_nll'],r['ridge']))
                   for form in plan['forms'] for target in plan['objectives']}
        unique(OUT/'selection.json',selection)
        pred={'baseline':base_scores}
        for key,record in selection.items():
            model=Residual(record['form'],'cpu')
            with torch.no_grad():
                model.linear.copy_(torch.tensor(record['linear'],dtype=torch.float64))
                model.q.copy_(torch.tensor(record['quadratic'],dtype=torch.float64))
            pred[key]=values(val,model,plan['probability_floor'])
        with gzip.open(OUT/'validation-scores.jsonl.gz','xt') as f:
            for i,meta in enumerate(val.meta):
                record=dict(metadata=meta,predictions={k:dict(posterior_logp=float(v[0][i]),actor_logp=float(v[1][i])) for k,v in pred.items()})
                f.write(json.dumps(record,allow_nan=False)+'\n')
        result=report(val.meta,pred,plan)
        result.update(at=now(),elapsed=time.monotonic()-start,scope=plan['scope'],plan_sha256=sha(OUT/'plan.json'),
                      selection_sha256=sha(OUT/'selection.json'),scores_sha256=sha(OUT/'validation-scores.jsonl.gz'))
        unique(OUT/'result.json',result);print(json.dumps(result),flush=True)
        unique(OUT/'terminal.json',dict(at=now(),status='complete',elapsed=time.monotonic()-start))
    except BaseException as exc:
        unique(OUT/'terminal.json',dict(at=now(),status='failed',error=repr(exc),traceback=traceback.format_exc(),elapsed=time.monotonic()-start));raise
    finally:signal.alarm(0)


if __name__=='__main__':main()
