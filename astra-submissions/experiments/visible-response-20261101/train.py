#!/usr/bin/env python3
"""Bounded GPU fit, validation-only selection, then one frozen test evaluation."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np
import torch
from torch import nn

import data
from model import LinearPolicy, StudentPolicy, TeacherPolicy, masked_log_probs

HERE, OUT, BUILD = data.HERE, data.OUT, data.BUILD
SEED, BATCH, EPOCHS = 2081101, 256, 12
CLASSES = {'linear':LinearPolicy, 'direct':StudentPolicy, 'teacher':TeacherPolicy, 'distilled':StudentPolicy}


def stamp(): return datetime.now(timezone.utc).isoformat()
def dump(path, value): path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


class Packed:
    def __init__(self, split, device):
        self.split = split; raw = np.load(BUILD/(split+'.npz'))
        self.tokens = torch.tensor(raw['tokens'], dtype=torch.uint8, device=device)
        self.actions = torch.tensor(raw['actions'].astype(np.int64), device=device)
        self.offsets = torch.tensor(raw['offsets'].astype(np.int64), device=device)
        self.target = torch.tensor(raw['target'].astype(np.int64), device=device)
        self.meta = {k:raw[k].copy() for k in ['game','ply','side','team']}
        self.n = len(self.target); self.device = device

    def batch(self, indices):
        start = self.offsets[indices]; lengths = self.offsets[indices+1]-start
        column = torch.arange(int(lengths.max()), device=self.device)[None]
        mask = column < lengths[:, None]
        positions = (start[:, None]+column).clamp_max(len(self.actions)-1)
        moves = self.actions[positions].masked_fill(~mask, 0)
        return self.tokens[indices].long(), moves, mask, self.target[indices], positions


@torch.no_grad()
def score(net, dataset):
    net.eval(); losses=[]; correct=[]
    for start in range(0, dataset.n, BATCH):
        idx = torch.arange(start, min(start+BATCH,dataset.n), device=dataset.device)
        tokens, moves, mask, target, _ = dataset.batch(idx)
        with torch.autocast('cuda', dtype=torch.bfloat16): logits = net(tokens, moves)
        lp = masked_log_probs(logits.float(), mask)
        losses.append(-lp.gather(1,target[:,None]).squeeze(1).cpu().numpy())
        correct.append((lp.argmax(1)==target).cpu().numpy())
    return np.concatenate(losses), np.concatenate(correct)


def metrics(loss, correct, meta):
    result = {}
    selections = {'all':np.ones(len(loss),dtype=bool), 'post8':meta['ply']//2+1 > 8,
                  'references':np.isin(meta['team'],[data.TEAMS.index(x) for x in ['Instructors','duck','HYPOTHERMIA']])}
    selections['references_post8'] = selections['references'] & selections['post8']
    for key, mask in selections.items():
        result[key] = dict(n=int(mask.sum()), nll=float(loss[mask].mean()), top1=float(correct[mask].mean()))
    return result


def groups(loss, correct, meta):
    result = {}
    for team, name in enumerate(data.TEAMS):
        for side in [0, 1]:
            mask = (meta['team']==team) & (meta['side']==side) & (meta['ply']//2+1 > 8)
            if mask.any(): result[f'{name}:{side}'] = dict(n=int(mask.sum()), nll=float(loss[mask].mean()), top1=float(correct[mask].mean()))
    return result


def save_predictions(name, split, loss, correct, meta):
    path = BUILD/(name+'-'+split+'-scores.npz')
    np.savez(path, nll=loss, correct=correct, **meta)
    return dict(path=str(path.relative_to(data.ROOT)), sha256=sha(path))


@torch.no_grad()
def teacher_targets(teacher, dataset, deadline):
    teacher.eval(); output = torch.empty(len(dataset.actions), dtype=torch.float16, device=dataset.device)
    for start in range(0,dataset.n,BATCH):
        if time.monotonic()>deadline: raise TimeoutError('90-minute training cap')
        idx=torch.arange(start,min(start+BATCH,dataset.n),device=dataset.device)
        tokens,moves,mask,_,positions=dataset.batch(idx)
        with torch.autocast('cuda',dtype=torch.bfloat16): logits=teacher(tokens,moves)
        probs=masked_log_probs(logits.float(),mask,2).exp()
        output[positions[mask]]=probs[mask].half()
    return output


def fit(name, training, validation, deadline, soft=None):
    torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    net=CLASSES[name]().to(training.device)
    opt=torch.optim.AdamW(net.parameters(),lr=3e-4 if name=='teacher' else 1e-3,weight_decay=1e-4)
    best=float('inf'); best_epoch=None; stale=0; records=[]; path=BUILD/(name+'.pt')
    assert not path.exists()
    for epoch in range(1,EPOCHS+1):
        net.train(); order=torch.randperm(training.n,device=training.device)
        total=0.; count=0; began=time.monotonic()
        for start in range(0,training.n,BATCH):
            if time.monotonic()>deadline: raise TimeoutError('90-minute training cap')
            idx=order[start:start+BATCH];tokens,moves,mask,target,positions=training.batch(idx)
            opt.zero_grad(set_to_none=True)
            with torch.autocast('cuda',dtype=torch.bfloat16): logits=net(tokens,moves)
            lp=masked_log_probs(logits.float(),mask)
            ce=-lp.gather(1,target[:,None]).squeeze(1).mean()
            if soft is None: loss=ce
            else:
                q=soft[positions].float().masked_fill(~mask,0)
                q=q/q.sum(1,keepdim=True)
                student=masked_log_probs(logits.float(),mask,2)
                kl=(q*(q.clamp_min(1e-30).log()-student)).sum(1).mean()
                loss=.5*ce+2*kl
            if not torch.isfinite(loss): raise ValueError('nonfinite training loss')
            loss.backward(); nn.utils.clip_grad_norm_(net.parameters(),1.0);opt.step()
            total+=float(loss.detach())*len(idx);count+=len(idx)
        nll,correct=score(net,validation); report=metrics(nll,correct,validation.meta)
        value=report['post8']['nll']
        if value<best-1e-6:
            best=value;best_epoch=epoch;stale=0
            torch.save(net.state_dict(),path)
        else: stale+=1
        record=dict(model=name,epoch=epoch,train_objective=total/count,validation=report,
                    seconds=time.monotonic()-began,best_epoch=best_epoch,
                    cuda_peak_bytes=torch.cuda.max_memory_allocated())
        records.append(record)
        with (OUT/'epochs.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
        print(json.dumps(record),flush=True)
        if stale>=3:break
    net.load_state_dict(torch.load(path,weights_only=True));net.eval()
    nll,correct=score(net,validation)
    result=dict(model=name,parameters=sum(p.numel() for p in net.parameters()),best_epoch=best_epoch,
                epochs=len(records),sha256=sha(path),validation=metrics(nll,correct,validation.meta),
                predictions=save_predictions(name,'validation',nll,correct,validation.meta))
    dump(OUT/(name+'-validation.json'),result)
    return net,result


def paired_bootstrap(base, candidate, meta):
    use=meta['ply']//2+1>8; groups=np.unique(meta['game'][use])
    totals=np.array([(base[use & (meta['game']==g)]-candidate[use & (meta['game']==g)]).sum() for g in groups])
    counts=np.array([(use & (meta['game']==g)).sum() for g in groups])
    rng=np.random.default_rng(SEED+1); values=[]
    for _ in range(2000):
        draw=rng.integers(0,len(groups),len(groups));values.append(totals[draw].sum()/counts[draw].sum())
    return dict(game_clusters=len(groups),gain=float(totals.sum()/counts.sum()),
                lower95=float(np.quantile(values,.025)),upper95=float(np.quantile(values,.975)))


def main():
    assert torch.cuda.is_available()
    torch.set_num_threads(2); torch.set_num_interop_threads(2)
    torch.cuda.set_per_process_memory_fraction(12*1024**3/torch.cuda.get_device_properties(0).total_memory)
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
    torch.backends.cuda.matmul.allow_tf32=False
    # No resume is implicit: preserve an interrupted run for an explicit audit.
    assert not (OUT/'training-execution.json').exists()
    frozen=json.loads((OUT/'training-plan.json').read_text())
    for rel,h in frozen['source_sha256'].items(): assert sha(data.ROOT/rel)==h,rel
    assert sha(OUT/'manifest.json')==frozen['manifest_sha256']
    for rec in json.loads((OUT/'data-receipts.json').read_text()):assert sha(BUILD/(rec['split']+'.npz'))==rec['sha256']
    status=dict(status='running',started_at=stamp(),pid=os.getpid(),torch=torch.__version__,device=torch.cuda.get_device_name(0))
    dump(OUT/'training-execution.json',status); deadline=time.monotonic()+5400
    try:
        training=Packed('train','cuda');validation=Packed('validation','cuda'); results={};models={}
        for name in ['linear','direct','teacher']:
            models[name],results[name]=fit(name,training,validation,deadline)
        soft=teacher_targets(models['teacher'],training,deadline)
        models['distilled'],results['distilled']=fit('distilled',training,validation,deadline,soft)
        chosen=min(['direct','distilled'],key=lambda k:results[k]['validation']['post8']['nll'])
        val_gain=results['linear']['validation']['post8']['nll']-results[chosen]['validation']['post8']['nll']
        frozen_models=dict(chosen=chosen,validation_post8_gain=val_gain,models=results,at_utc=stamp(),
                           rule='Lowest validation post-eight NLL of two students; require gain >= .1 versus linear before test.')
        dump(OUT/'frozen-models.json',frozen_models)
        if val_gain<.1:
            dump(OUT/'decision.json',dict(decision='stop_validation',reason='Chosen student gain below .1 nats',**frozen_models))
        else:
            del training,validation,soft;torch.cuda.empty_cache();test=Packed('test','cuda');scores={};test_results={}
            for name,net in models.items():
                assert sha(BUILD/(name+'.pt'))==results[name]['sha256']
                nll,correct=score(net,test);scores[name]=nll
                test_results[name]=dict(metrics=metrics(nll,correct,test.meta),by_team_colour_post8=groups(nll,correct,test.meta),predictions=save_predictions(name,'test',nll,correct,test.meta))
            interval=paired_bootstrap(scores['linear'],scores[chosen],test.meta)
            refs=test_results['linear']['metrics']['references_post8']['nll']-test_results[chosen]['metrics']['references_post8']['nll']
            advance=interval['gain']>=.1 and interval['lower95']>0 and refs>=-.01
            dump(OUT/'test-results.json',test_results)
            dump(OUT/'decision.json',dict(decision='native_prototype_allowed' if advance else 'stop_test',chosen=chosen,
                                         test_post8_gain=interval,reference_post8_gain=refs,
                                         scope='Predictive gate only; no policy or Elo measurement'))
        status['status']='complete'
    except BaseException as error:
        status.update(status='failed',error=repr(error));raise
    finally:
        status['ended_at']=stamp();status['cuda_peak_bytes']=torch.cuda.max_memory_allocated()
        dump(OUT/'training-execution.json',status)


if __name__=='__main__':main()
