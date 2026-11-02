"""Single bounded fit, validation-only selection, then one held-out evaluation."""
from collections import defaultdict
import gc
import gzip
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import traceback
import numpy as np
import torch
from config import HERE, ROOT, OUT, now, sha, unique
from extract import collect
from model import Dataset, objective, scores


def checked_scores(data, theta, floor):
    with torch.no_grad():
        posterior, actor = [a.detach().cpu().numpy() for a in scores(data, theta)]
    for i, meta in enumerate(data.meta):
        if not meta['natural_support']:
            # Neither objective gets to omit unsupported cases or report log(1) for an absent parent.
            posterior[i] = actor[i] = np.log(floor)
    return np.clip(posterior, np.log(floor), 0), np.clip(actor, np.log(floor), 0)


def game_mean(values, meta, selected=None):
    grouped = defaultdict(list)
    for i, row in enumerate(meta):
        if selected is None or selected(row):
            grouped[row['game']].append(float(values[i]))
    return float(np.mean([np.mean(v) for v in grouped.values()])) if grouped else None


def baseline_parity(data):
    with torch.no_grad():
        z, _ = scores(data, torch.zeros(26, dtype=torch.float64, device=data.x.device))
    z = z.cpu().numpy(); prob_error = []; log_error = []
    for i, row in enumerate(data.meta):
        p = row['baseline_truth_mass']
        if p > 0:
            prob_error.append(abs(float(np.exp(z[i])) - p)); log_error.append(abs(float(z[i]) - np.log(p)))
        else:
            assert z[i] < -1e100
    result = dict(cases=len(data.meta), probability_error=max(prob_error, default=0), log_error=max(log_error, default=0))
    assert result['probability_error'] <= 5e-6 and result['log_error'] <= 5e-5, result
    return result


def evaluate(meta, pred, plan):
    masks = {'primary': lambda r:r['primary'], 'all': lambda r:True,
             'late': lambda r:r['primary'] and r['late'],
             'surprise': lambda r:r['primary'] and r['surprise']}
    summary = {}
    for name, mask in masks.items():
        ix = [i for i,r in enumerate(meta) if mask(r)]; games = sorted({meta[i]['game'] for i in ix})
        row = dict(cases=len(ix), games=len(games), unsupported=sum(not meta[i]['natural_support'] for i in ix))
        for kind in ('baseline', 'actor', 'posterior'):
            row[kind + '_nll'] = game_mean(-pred[kind][0], meta, mask)
            row[kind + '_actor_nll'] = game_mean(-pred[kind][1], meta, mask)
        row['gain'] = game_mean(pred['posterior'][0] - pred['baseline'][0], meta, mask)
        row['gain_over_actor'] = game_mean(pred['posterior'][0] - pred['actor'][0], meta, mask)
        summary[name] = row
    mask = masks['primary']; grouped = defaultdict(list)
    for i,r in enumerate(meta):
        if mask(r): grouped[r['game']].append(float(pred['posterior'][0][i] - pred['baseline'][0][i]))
    gains = np.array([np.mean(grouped[g]) for g in sorted(grouped)])
    assert len(gains), 'No primary held-out games'
    rng = np.random.default_rng(plan['seed'])
    boot = np.array([rng.choice(gains, len(gains), replace=True).mean() for _ in range(plan['bootstrap_samples'])])
    summary['primary']['gain_ci95'] = np.quantile(boot, [.025, .975]).tolist()
    g=plan['gate']; p=summary['primary']; s=summary['surprise']; l=summary['late']; a=summary['all']
    checks = dict(baseline_gain=p['gain'] >= g['baseline_gain'],
                  baseline_ci=p['gain_ci95'][0] > g['baseline_ci_lower'],
                  matched_actor=p['gain_over_actor'] >= g['actor_comparator_gain'],
                  late=l['gain'] is not None and l['gain'] >= g['late_min_gain'],
                  surprise_count=s['cases'] >= g['min_surprise'],
                  surprise=s['gain'] is not None and s['gain'] >= g['surprise_min_gain'],
                  all=a['gain'] >= g['all_min_gain'],
                  support=a['unsupported'] <= g['max_support_failures'])
    return dict(metrics=summary, checks=checks, passed=all(checks.values()))


def main():
    started=time.monotonic(); plan=json.loads((OUT/'plan.json').read_text())
    os.sched_setaffinity(0,set(plan['cores'])); torch.set_num_threads(2); torch.set_num_interop_threads(1)
    np.random.seed(plan['seed']); torch.manual_seed(plan['seed'])
    for p,h in plan['dependencies'].items(): assert sha(Path(p)) == h, p
    def expired(signum, frame): raise TimeoutError('Frozen wall-time bound reached')
    signal.signal(signal.SIGALRM, expired); signal.alarm(plan['wall_seconds'])
    gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],capture_output=True,text=True)
    device='cuda' if gpu.returncode==0 and not gpu.stdout.strip() and torch.cuda.is_available() else 'cpu'
    execution=dict(at=now(), pid=os.getpid(), proc_start_ticks=Path('/proc/self/stat').read_text().split()[21],
                   plan_sha256=sha(OUT/'plan.json'), device=device, gpu_probe=gpu.stdout.strip(),
                   torch_version=torch.__version__, status='running')
    unique(OUT/'execution.json',execution); print(json.dumps(execution),flush=True)
    try:
        train_cases=collect(plan,'train'); validation_cases=collect(plan,'validation')
        train_all=Dataset(train_cases,device); validation=Dataset(validation_cases,device)
        parity={'train':baseline_parity(train_all),'validation':baseline_parity(validation)}
        unsupported=sum(not r['meta']['natural_support'] for r in train_cases)
        if unsupported:
            del train_all
            train=Dataset([r for r in train_cases if r['meta']['natural_support']],device)
        else: train=train_all
        assert len(train.meta)>0
        del train_cases,validation_cases; gc.collect()
        unique(OUT/'training-input-check.json',dict(parity=parity,train_excluded_unsupported=unsupported,
                                                   supported_training_cases=len(train.meta)))
        candidates=[]
        for kind in ('actor','posterior'):
            for ridge in plan['ridges']:
                theta=torch.zeros(26,dtype=torch.float64,device=device,requires_grad=True)
                opt=torch.optim.Adam([theta],lr=plan['learning_rate']); curve=[]; best=None
                for step in range(1,plan['steps']+1):
                    opt.zero_grad(); loss=objective(train,theta,kind,ridge)
                    assert torch.isfinite(loss); loss.backward(); assert torch.isfinite(theta.grad).all(); opt.step()
                    if step%plan['validation_every']==0:
                        v,_=checked_scores(validation,theta,plan['probability_floor'])
                        val=game_mean(-v,validation.meta,lambda r:r['primary']); assert val is not None
                        item=dict(step=step,loss=float(loss.detach().cpu()),validation_nll=val,
                                  coefficients=theta.detach().cpu().tolist())
                        curve.append(item)
                        if best is None or val < best['validation_nll']: best=item
                record=dict(kind=kind,ridge=ridge,**best)
                name=f'{kind}-{ridge:g}'
                unique(OUT/(name+'-curve.json'),curve); unique(OUT/(name+'-model.json'),record)
                candidates.append(record)
                print(json.dumps({k:v for k,v in record.items() if k!='coefficients'}),flush=True)
        selection={kind:min((r for r in candidates if r['kind']==kind),key=lambda r:(r['validation_nll'],r['ridge']))
                   for kind in ('actor','posterior')}
        unique(OUT/'selection.json',selection)
        unique(OUT/'selection-lock.json',dict(at=now(),sha256=sha(OUT/'selection.json'),
                                             curves={p.name:sha(p) for p in OUT.glob('*-curve.json')}))
        del train,validation
        if not unsupported: del train_all
        gc.collect()
        if device=='cuda': torch.cuda.empty_cache()
        # No test exporter call or labels are read before selection is persisted.
        test_cases=collect(plan,'test'); test=Dataset(test_cases,device); del test_cases; gc.collect()
        parity['test']=baseline_parity(test)
        pred={'baseline':checked_scores(test,torch.zeros(26,dtype=torch.float64,device=device),plan['probability_floor'])}
        for kind in ('actor','posterior'):
            theta=torch.tensor(selection[kind]['coefficients'],dtype=torch.float64,device=device)
            pred[kind]=checked_scores(test,theta,plan['probability_floor'])
        scorepath=OUT/'test-scores.jsonl.gz'
        with gzip.open(scorepath,'xt') as f:
            for i,meta in enumerate(test.meta):
                row=dict(meta)
                for kind,(post,act) in pred.items():row[kind]=dict(posterior_logp=float(post[i]),actor_logp=float(act[i]))
                f.write(json.dumps(row,allow_nan=False)+'\n')
        result=evaluate(test.meta,pred,plan)
        result.update(at=now(),device=device,elapsed=time.monotonic()-started,parity=parity,
                      scores_sha256=sha(scorepath),selection_sha256=sha(OUT/'selection.json'),
                      plan_sha256=sha(OUT/'plan.json'),scope=plan['scope'])
        unique(OUT/'result.json',result); print(json.dumps(result),flush=True)
        unique(OUT/'terminal.json',dict(at=now(),status='complete',elapsed=time.monotonic()-started))
    except BaseException as exc:
        unique(OUT/'terminal.json',dict(at=now(),status='failed',elapsed=time.monotonic()-started,
                                     error=repr(exc),traceback=traceback.format_exc()))
        raise
    finally:
        signal.alarm(0)


if __name__=='__main__':main()
