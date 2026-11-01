#!/usr/bin/env python3
"""Fit on TRAIN, select on VALIDATION, report frozen TEST once.

Two-parameter monotone logistic calibration, no neural/GPU training.
Likelihood is weighted so each decision contributes one unit across its moves.
Held-out uncertainty resamples whole games, not correlated candidate moves.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import numpy as np


def logit(p):
    p=np.clip(np.asarray(p,dtype=float),1e-6,1-1e-6)
    return np.log(p)-np.log1p(-p)


def sigmoid(z):return 1/(1+np.exp(-np.clip(z,-50,50)))


def fit_logistic(p,y,w):
    x=np.column_stack((np.ones(len(p)),logit(p)))
    y=np.asarray(y,dtype=float);w=np.asarray(w,dtype=float);w=w/w.sum()
    prior=np.array([0.,1.]);beta=prior.copy();ridge=1e-5
    def loss(b):
        z=x@b
        return np.dot(w,np.logaddexp(0,z)-y*z)+.5*ridge*np.dot(b-prior,b-prior)
    for iteration in range(100):
        q=sigmoid(x@beta)
        gradient=x.T@(w*(q-y))+ridge*(beta-prior)
        hessian=x.T@((w*q*(1-q))[:,None]*x)+ridge*np.eye(2)
        step=np.linalg.solve(hessian,gradient);old=loss(beta);rate=1.
        while rate>1e-10:
            candidate=beta-rate*step;candidate[1]=max(0.,candidate[1])
            if loss(candidate)<=old+1e-14:break
            rate*=.5
        if rate<=1e-10:raise ValueError('calibration optimizer failed to descend')
        change=np.max(np.abs(candidate-beta));beta=candidate
        if change<1e-8:break
    return {'intercept':float(beta[0]),'slope':float(beta[1]),'iterations':iteration+1,
            'ridge_to_identity':ridge,'train_regularized_loss':float(loss(beta)),
            'probability_clip_for_logit':1e-6}


def predict(p,model):return sigmoid(model['intercept']+model['slope']*logit(p))


def point_losses(y,p):
    q=np.clip(p,1e-9,1-1e-9)
    return {'log_loss':-(y*np.log(q)+(1-y)*np.log1p(-q)), 'brier':(p-y)**2}


def scores(rows,p,played=False):
    mask=np.array([r['played'] or not played for r in rows],dtype=bool)
    y=np.array([r['fatal'] for r in rows],dtype=float)[mask];p=np.asarray(p)[mask]
    w=np.array([1. if played else r['decision_weight'] for r in rows])[mask]
    result={'rows':int(mask.sum()),'events':int(y.sum()),'weight_sum':float(w.sum()),
            'event_rate':float(np.average(y,weights=w)), 'mean_prediction':float(np.average(p,weights=w))}
    for key,loss in point_losses(y,p).items():result[key]=float(np.average(loss,weights=w))
    bins=[0,.01,.03,.1,.3,.7,1.0000001];result['bins']=[]
    for a,b in zip(bins,bins[1:]):
        selected=(p>=a)&(p<b)
        if not selected.any():continue
        result['bins'].append({'range':[a,min(b,1)],'rows':int(selected.sum()),'events':int(y[selected].sum()),
                               'predicted':float(np.average(p[selected],weights=w[selected])),
                               'observed':float(np.average(y[selected],weights=w[selected]))})
    return result


def paired_game_intervals(rows,p,q,played=False,repetitions=4000):
    groups=defaultdict(list)
    for i,r in enumerate(rows):
        if not played or r['played']:groups[r['game']].append(i)
    y=np.array([r['fatal'] for r in rows],dtype=float)
    w=np.array([1. if played else r['decision_weight'] for r in rows])
    lp,lq=point_losses(y,np.asarray(p)),point_losses(y,np.asarray(q));result={}
    ids=sorted(groups);rng=np.random.default_rng(11012026)
    resamples=rng.integers(0,len(ids),size=(repetitions,len(ids)))
    for metric in lp:
        numerator=np.array([np.dot(w[groups[g]],lq[metric][groups[g]]-lp[metric][groups[g]]) for g in ids])
        denominator=np.array([w[groups[g]].sum() for g in ids])
        samples=numerator[resamples].sum(axis=1)/denominator[resamples].sum(axis=1)
        result[metric]={'delta':float(numerator.sum()/denominator.sum()),
                        'game_bootstrap_95':np.quantile(samples,[.025,.975]).tolist(),'games':len(ids)}
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('directory',type=Path)
    args=ap.parse_args();out=args.directory
    plan=json.loads((out/'plan.json').read_text());receipt=json.loads((out/'receipt.json').read_text())
    assert receipt['state']=='complete' and len(receipt['completed'])==len(plan['games'])
    final=out/'calibration.json'
    if final.exists():raise ValueError('test report already exists; refuse silent retuning')
    split=defaultdict(list);hashes={}
    for game in plan['games']:
        path=out/'games'/f"{game['game']}.jsonl";payload=path.read_bytes()
        meta=json.loads(path.with_suffix('.meta.json').read_text())
        assert meta['game']==game and meta['provenance']==receipt['provenance']
        rows=[json.loads(s) for s in payload.splitlines()]
        assert rows and len(rows)==meta['candidates']
        assert all(r['game']==game['game'] and r['split']==game['split'] for r in rows)
        hashes[game['game']]=hashlib.sha256(payload).hexdigest();split[game['split']].extend(rows)
    train=split['train'];model=fit_logistic([r['sharp'] for r in train],[r['fatal'] for r in train],[r['decision_weight'] for r in train])
    predictions={}
    for name,rows in split.items():
        predictions[name]={'raw_sharp':np.array([r['sharp'] for r in rows]),'raw_flat':np.array([r['flat'] for r in rows]),
                           'calibrated_sharp':predict([r['sharp'] for r in rows],model)}
    # Selection uses validation only; insertion order keeps raw sharp on exact ties.
    val={k:scores(split['validation'],p) for k,p in predictions['validation'].items()}
    chosen=min(val,key=lambda k:val[k]['log_loss'])
    report={'model':model,'selected_on_validation':chosen,'data_sha256':hashes,
            'fit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'summary':{},'test_comparison_to_raw_sharp':{},'scope':'Probability calibration only; no Elo claim, no deployment, conditional on replay-reconstructed belief and opponent population.'}
    for name,rows in split.items():
        report['summary'][name]={k:{'all_candidates_decision_weighted':scores(rows,p),
                                  'played_moves':scores(rows,p,True)} for k,p in predictions[name].items()}
        report['summary'][name]['coverage']={'games':len({r['game'] for r in rows}),
            'decisions':len({(r['game'],r['ply']) for r in rows}),'rows':len(rows),
            'zero_sharp_true_events':sum(r['sharp']==0 and r['fatal'] for r in rows),
            'invalid_mass_rows':sum(r['invalid_mass']>0 for r in rows)}
    test=split['test'];pred=predictions['test']
    report['test_comparison_to_raw_sharp']={
        'all_candidates_decision_weighted':paired_game_intervals(test,pred['raw_sharp'],pred[chosen]),
        'played_moves':paired_game_intervals(test,pred['raw_sharp'],pred[chosen],True)}
    comparisons=report['test_comparison_to_raw_sharp']
    report['earns_engine_experiment']=(chosen!='raw_sharp'
        and comparisons['all_candidates_decision_weighted']['log_loss']['game_bootstrap_95'][1]<0
        and comparisons['all_candidates_decision_weighted']['brier']['delta']<0
        and comparisons['played_moves']['log_loss']['delta']<=0)
    report['gate']='Requires a non-identity validation winner, held-out log-loss improvement with game-bootstrap interval below zero, lower held-out Brier, and no played-move log-loss worsening. This only earns an engine experiment.'
    with final.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({'model':model,'selected':chosen,'test':comparisons,'earns_engine_experiment':report['earns_engine_experiment']},indent=2))


if __name__=='__main__':main()
