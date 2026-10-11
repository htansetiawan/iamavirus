#!/usr/bin/env python3
"""Paired conditional-logit experiment; CPU-only, game-disjoint evaluation.

Newton fitting follows the C project's tools/fit_move_model.py. Models share
training rows, regularization, optimizer and splits. Extra features alone differ.
True-state-conditioned action prediction is not an executable observation policy.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import time

import numpy as np

NAMES = ['capture','captured_value','king_capture','knight','bishop','rook','queen','king',
         'double_push','castle','promote_queen','underpromote','forward','retreat','centre',
         'develop','recapture','advanced_pawn','check','escape','into_attack','hang_value',
         'self_capturable','undefended','king_zone','xray_king','hidden_check','silent_check',
         'silent_move','concealed_mover','new_vision','concealed_king_zone']


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def load(path, games):
    raw=path.read_bytes()
    if len(raw)<4 or struct.unpack_from('<I',raw)[0]!=32:raise ValueError('feature header')
    off=4; rows=[]; meta=[]
    while off<len(raw):
        if off+20>len(raw):raise ValueError('truncated record')
        n,k,g,ply,side=struct.unpack_from('<5I',raw,off);off+=20
        if not (0< n<=256 and k<n and g<len(games) and side in (0,1)):
            raise ValueError('invalid record metadata')
        if ply>=games[g]['plies'] or side!=ply%2 or not games[g]['used_sides'][side]:
            raise ValueError('game metadata does not agree with feature record')
        size=n*32*4
        if off+size>len(raw):raise ValueError('truncated features')
        rows.append(np.frombuffer(raw,dtype='<f4',count=n*32,offset=off).reshape(n,32))
        meta.append((n,k,g,ply,side));off+=size
    if not rows:raise ValueError('empty split')
    meta=np.array(meta,dtype=np.int64)
    X=np.concatenate(rows).astype(np.float64)
    if not np.isfinite(X).all():raise ValueError('nonfinite feature')
    counts=meta[:,0];starts=np.r_[0,np.cumsum(counts)[:-1]]
    expected=sum(sum(g['used_sides'][ply%2] for ply in range(g['plies'])) for g in games)
    if len(meta)!=expected:raise ValueError('missing replay rows')
    return dict(X=X,counts=counts,starts=starts,played=meta[:,1],game=meta[:,2],
                ply=meta[:,3],side=meta[:,4],segment=np.repeat(np.arange(len(meta)),counts))


def stats(theta,d):
    z=d['X'][:,:len(theta)]@theta
    maxima=np.maximum.reduceat(z,d['starts'])
    e=np.exp(z-maxima[d['segment']]);totals=np.add.reduceat(e,d['starts'])
    p=e/totals[d['segment']]
    logp=z[d['starts']+d['played']]-maxima-np.log(totals)
    # Deterministic first argmax: equal-score ties must not all count correct.
    candidate=np.where(z==maxima[d['segment']],np.arange(len(z)),len(z))
    top=np.minimum.reduceat(candidate,d['starts'])==d['starts']+d['played']
    return logp,p,top


def fit(d,width,l2=1e-3,iters=40):
    X=d['X'][:,:width];N=len(d['starts']);theta=np.zeros(width);trace=[]
    def objective(t):return stats(t,d)[0].mean()-.5*l2*float(t@t)
    current=objective(theta)
    for i in range(iters):
        _,p,_=stats(theta,d)
        mu=np.add.reduceat(p[:,None]*X,d['starts'])
        grad=(X[d['starts']+d['played']]-mu).mean(0)-l2*theta
        H=((X*p[:,None]).T@X-mu.T@mu)/N+l2*np.eye(width)
        step=np.linalg.solve(H,grad);alpha=1.
        while alpha>=1e-6:
            trial=theta+alpha*step;value=objective(trial)
            if value>=current:break
            alpha*=.5
        if alpha<1e-6:raise RuntimeError('Newton line search failed')
        gain=value-current;theta=trial;current=value
        row=dict(iteration=i,objective=float(current),gain=float(gain),alpha=alpha,
                 gradient_norm=float(np.linalg.norm(grad)))
        trace.append(row);print(json.dumps(dict(width=width,**row)),flush=True)
        if gain<1e-7:break
    return theta,trace


def bootstrap(delta,group,repetitions=2000):
    """Move-weighted paired mean, resampling entire game clusters."""
    if not len(delta):return None
    _,index=np.unique(group,return_inverse=True)
    sums=np.bincount(index,weights=delta);counts=np.bincount(index);rng=np.random.default_rng(831)
    samples=[]
    for _ in range(repetitions):
        selected=rng.integers(len(sums),size=len(sums))
        samples.append(sums[selected].sum()/counts[selected].sum())
    return dict(mean=float(np.mean(delta)),ci95=np.quantile(samples,[.025,.975]).tolist(),
                games=len(sums),moves=len(delta))


def calibration(p,y):
    bins=[]
    for lo,hi in zip([0,.01,.05,.1,.2,.5],[.01,.05,.1,.2,.5,1.0000001]):
        sel=(p>=lo)&(p<hi)
        if np.any(sel):bins.append(dict(low=lo,high=min(hi,1.),n=int(sel.sum()),
             forecast=float(p[sel].mean()),observed=float(y[sel].mean())))
    return dict(events=int(y.sum()),moves=len(y),mean_probability=float(p.mean()),
                prevalence=float(y.mean()),brier=float(np.mean((p-y)**2)),bins=bins)


def evaluate(d,games,models):
    starts=d['starts'];played=starts+d['played'];X=d['X'];silent=X[:,28]>0
    actual_silent=silent[played];mid=d['ply']>=16
    output={'games':len(games),'moves':len(starts),'models':{},'paired':{}}
    predictions={};row_records={}
    for name,theta in models.items():
        logp,p,top=stats(theta,d)
        quiet_mass=np.add.reduceat(p*silent,starts)
        # Only evaluate conditional quantities on rows whose observed move is quiet.
        conditional_p=p*silent/np.maximum(quiet_mass[d['segment']],1e-300)
        conditional_logp=logp-np.log(np.maximum(quiet_mass,1e-300))
        predictions[name]=dict(logp=logp,p=p,conditional_logp=conditional_logp,
            hidden=np.add.reduceat(p*X[:,26],starts),silent_check=np.add.reduceat(p*X[:,27],starts),
            quiet_hidden=np.add.reduceat(conditional_p*X[:,26],starts))
        cohorts={}
        for cohort,sel,quiet in [('all',np.ones(len(starts),bool),False),('ply16plus',mid,False),
                                ('unchanged_observation',actual_silent,True),
                                ('unchanged_ply16plus',actual_silent&mid,True)]:
            chosen_log=conditional_logp if quiet else logp
            hp=predictions[name]['quiet_hidden' if quiet else 'hidden']
            if not np.any(sel):continue
            cohorts[cohort]=dict(moves=int(sel.sum()),nll=float(-chosen_log[sel].mean()),
                 hidden_check=calibration(hp[sel],X[played,26][sel]))
            if not quiet:cohorts[cohort].update(top1=float(top[sel].mean()),
                 gain_over_uniform=float((logp[sel]+np.log(d['counts'][sel])).mean()),
                 silent_check=calibration(predictions[name]['silent_check'][sel],X[played,27][sel]))
        team_names=np.array([games[g]['white' if side==0 else 'black'] for g,side in zip(d['game'],d['side'])])
        teams={team:dict(moves=int((team_names==team).sum()),nll=float(-logp[team_names==team].mean()))
               for team in sorted(set(team_names))}
        output['models'][name]=dict(cohorts=cohorts,teams=teams)
        row_records[name+'_logp']=logp
        row_records[name+'_hidden']=predictions[name]['hidden']
        row_records[name+'_quiet_hidden']=predictions[name]['quiet_hidden']
    a,b=predictions['control26'],predictions['visibility32']
    for cohort,sel,quiet in [('all',np.ones(len(starts),bool),False),('ply16plus',mid,False),
                            ('unchanged_observation',actual_silent,True),('unchanged_ply16plus',actual_silent&mid,True)]:
        lp='conditional_logp' if quiet else 'logp';hp='quiet_hidden' if quiet else 'hidden';y=X[played,26]
        output['paired'][cohort]=dict(
            log_likelihood_gain=bootstrap((b[lp]-a[lp])[sel],d['game'][sel]),
            hidden_brier_reduction=bootstrap(((a[hp]-y)**2-(b[hp]-y)**2)[sel],d['game'][sel]))
    row_records.update(game=d['game'],ply=d['ply'],side=d['side'],actual_hidden=X[played,26],actual_silent=actual_silent)
    return output,row_records


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    args.out.mkdir(exist_ok=False);shutil.copyfile(__file__,args.out/'fit.py')
    manifest=json.loads((args.data/'manifest.json').read_text());hashes=json.loads((args.data/'features.json').read_text())
    groups=[set(g['id'] for g in manifest['games'][s]) for s in ['train','validation','test']]
    if any(groups[i]&groups[j] for i in range(3) for j in range(i)):raise ValueError('split overlap')
    begin=time.time();train=load(args.data/'train.bin',manifest['games']['train']);models={};traces={}
    if sha(args.data/'train.bin')!=hashes['train']['sha256']:raise ValueError('train hash')
    for name,width in [('control26',26),('visibility32',32)]:
        models[name],traces[name]=fit(train,width)
    artifact=dict(features=NAMES,models={name:t.tolist() for name,t in models.items()},traces=traces,
        l2=.001,source_sha256=sha(Path(__file__)),manifest_sha256=sha(args.data/'manifest.json'),
        classification='CPU true-state-conditioned replay prediction. Not Elo or a realizable actor policy.')
    (args.out/'models.json').write_text(json.dumps(artifact,indent=2)+'\n');del train
    for split in ['validation','test']:
        if sha(args.data/(split+'.bin'))!=hashes[split]['sha256']:raise ValueError('split hash')
        d=load(args.data/(split+'.bin'),manifest['games'][split]);result,rows=evaluate(d,manifest['games'][split],models)
        (args.out/(split+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        np.savez_compressed(args.out/(split+'-rows.npz'),**rows)
        print(json.dumps({'split':split,'paired':result['paired']}),flush=True);del d
    (args.out/'complete.json').write_text(json.dumps({'elapsed_seconds':time.time()-begin,
        'outputs':{p.name:sha(p) for p in sorted(args.out.iterdir()) if p.is_file()}},indent=2)+'\n')


if __name__=='__main__':main()
