#!/usr/bin/env python3
"""Hierarchical move prior: learn group mass, preserve within-group ranking.

Groups are check, capture/promotion, and quiet (in that priority order).
The unchanged 26-feature control is an offset. Seven learned group features
adjust tactical intent; zero coefficients exactly reproduce the control.
Uses true-state-conditioned replay features, not an observation-only policy.
"""
import argparse
import json
from pathlib import Path
import shutil
import time
import numpy as np
from m4_prior_fit import load, stats, bootstrap, calibration, sha

GATE_NAMES=['check_group','capture_promotion_group','log_count','check_log_count',
            'capture_log_count','mean_forward','mean_centre']


def groups(d, theta):
    logp, p, top = stats(theta, d)
    X=d['X'];N=len(d['starts'])
    kind=np.where(X[:,18]>0,0,np.where((X[:,0]>0)|(X[:,10]>0)|(X[:,11]>0),1,2))
    keys=3*d['segment']+kind
    count=np.bincount(keys,minlength=3*N)
    present=np.flatnonzero(count)
    mass=np.bincount(keys,weights=p,minlength=3*N)
    count_present=count[present]
    log_count=np.log(count_present)
    k=present%3
    gate_X=np.stack([k==0,k==1,log_count,(k==0)*log_count,(k==1)*log_count,
        np.bincount(keys,weights=X[:,12],minlength=3*N)[present]/count_present,
        np.bincount(keys,weights=X[:,14],minlength=3*N)[present]/count_present],axis=1).astype(float)
    inverse=np.full(3*N,-1,dtype=np.int64);inverse[present]=np.arange(len(present))
    n=np.count_nonzero(count.reshape(N,3),axis=1)
    starts=np.r_[0,np.cumsum(n)[:-1]]
    actual=d['starts']+d['played']
    gate={'X':gate_X,'counts':n,'starts':starts,'segment':present//3,
          'played':inverse[keys[actual]]-starts,'offset':np.log(mass[present]),
          'action_gate':inverse[keys],'base_p':p,'base_logp':logp,'base_top':top,
          'base_mass':mass[present],'kind':kind}
    if np.any(gate['played']<0) or not np.isfinite(gate['offset']).all():
        raise ValueError('bad class mapping or probability underflow')
    return gate


def gate_stats(theta,d):
    z=d['offset']+d['X']@theta
    maxima=np.maximum.reduceat(z,d['starts'])
    e=np.exp(z-maxima[d['segment']]);total=np.add.reduceat(e,d['starts'])
    p=e/total[d['segment']]
    logp=z[d['starts']+d['played']]-maxima-np.log(total)
    return logp,p


def fit_gate(d,l2=.001):
    theta=np.zeros(len(GATE_NAMES));X=d['X'];N=len(d['starts']);trace=[]
    def objective(t):return gate_stats(t,d)[0].mean()-.5*l2*float(t@t)
    current=objective(theta)
    for i in range(40):
        _,p=gate_stats(theta,d);mu=np.add.reduceat(p[:,None]*X,d['starts'])
        grad=(X[d['starts']+d['played']]-mu).mean(0)-l2*theta
        h=((X*p[:,None]).T@X-mu.T@mu)/N+l2*np.eye(len(theta))
        step=np.linalg.solve(h,grad);alpha=1.
        while alpha>=1e-6:
            trial=theta+alpha*step;value=objective(trial)
            if value>=current:break
            alpha*=.5
        if alpha<1e-6:raise RuntimeError('gate line search failed')
        gain=value-current;theta=trial;current=value
        trace.append({'iteration':i,'objective':float(current),'gain':float(gain),'alpha':alpha})
        if gain<1e-7:break
    return theta,trace


def probabilities(gate, theta):
    _,q=gate_stats(theta,gate)
    idx=gate['action_gate']
    return gate['base_p']*(q/gate['base_mass'])[idx]


def evaluate(d, gate, theta):
    actual=d['starts']+d['played'];X=d['X'];allrows=np.ones(len(actual),bool)
    output={};pred={}
    for name,p in [('control26',gate['base_p']),('intent',probabilities(gate,theta))]:
        np.testing.assert_allclose(np.add.reduceat(p,d['starts']),1,atol=1e-12)
        logp=np.log(p[actual]);silent_mass=np.add.reduceat(p*(X[:,28]>0),d['starts'])
        silent_hidden=np.add.reduceat(p*X[:,26]*(X[:,28]>0),d['starts'])
        hidden=np.add.reduceat(p*X[:,26],d['starts'])
        pred[name]=(logp,logp-np.log(np.maximum(silent_mass,1e-300)),hidden,
                    silent_hidden/np.maximum(silent_mass,1e-300))
        cohorts={}
        for label,sel,quiet in [('all',allrows,False),('unchanged_view',X[actual,28]>0,True)]:
            chosen=pred[name][1 if quiet else 0];prob=pred[name][3 if quiet else 2]
            cohorts[label]={'moves':int(sel.sum()),'nll':float(-chosen[sel].mean()),
                            'hidden_check':calibration(prob[sel],X[actual,26][sel])}
        output[name]=cohorts
    a,b=pred['control26'],pred['intent'];paired={}
    for label,sel,quiet in [('all',allrows,False),('unchanged_view',X[actual,28]>0,True)]:
        j=1 if quiet else 0;k=3 if quiet else 2;y=X[actual,26]
        paired[label]={'log_likelihood_gain':bootstrap((b[j]-a[j])[sel],d['game'][sel]),
                       'hidden_brier_reduction':bootstrap(((a[k]-y)**2-(b[k]-y)**2)[sel],d['game'][sel])}
    return {'cohorts':output,'paired':paired}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data',type=Path,required=True);ap.add_argument('--base',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();args.out.mkdir(exist_ok=False)
    started=time.monotonic();shutil.copyfile(__file__,args.out/'fit.py')
    manifest=json.loads((args.data/'manifest.json').read_text());hashes=json.loads((args.data/'features.json').read_text())
    sets=[{g['id'] for g in manifest['games'][s]} for s in ['train','validation','test']]
    if any(sets[i]&sets[j] for i in range(3) for j in range(i)):raise ValueError('split overlap')
    base=json.loads(args.base.read_text());theta=np.array(base['models']['control26'])
    if len(theta)!=26 or base['manifest_sha256']!=sha(args.data/'manifest.json'):raise ValueError('base data identity')
    if sha(args.data/'train.bin')!=hashes['train']['sha256']:raise ValueError('train hash')
    d=load(args.data/'train.bin',manifest['games']['train']);gate=groups(d,theta)
    np.testing.assert_allclose(probabilities(gate,np.zeros(7)),gate['base_p'],atol=1e-14)
    gamma,trace=fit_gate(gate)
    artifact={'base_theta':theta.tolist(),'gate_theta':gamma.tolist(),'gate_features':GATE_NAMES,'trace':trace,
              'l2':.001,'source_sha256':sha(Path(__file__)),'base_sha256':sha(args.base),
              'manifest_sha256':sha(args.data/'manifest.json'),'training_moves':len(d['starts']),
              'training_games':len(manifest['games']['train']),'test_shard_used':False}
    (args.out/'model.json').write_text(json.dumps(artifact,indent=2)+'\n');del d,gate
    # Validation only: prior rounds already consumed the legacy test split.
    if sha(args.data/'validation.bin')!=hashes['validation']['sha256']:raise ValueError('validation hash')
    d=load(args.data/'validation.bin',manifest['games']['validation']);gate=groups(d,theta)
    result=evaluate(d,gate,gamma);result['seconds']=time.monotonic()-started
    (args.out/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'gate':dict(zip(GATE_NAMES,gamma)),'validation':result},indent=2),flush=True)


if __name__=='__main__':main()
