#!/usr/bin/env python3
"""Two convex fits; conditional observation scoring is evaluation-only."""
import argparse
import gzip
import hashlib
import json
import struct
import time
from pathlib import Path

import numpy as np
import torch

STATIC=39
TEMPORAL=52
FEATURES=STATIC+TEMPORAL
PARAMS=FEATURES+768

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class Data:
    def __init__(self,path,device):
        with gzip.open(path,'rb') as f:payload=f.read()
        magic,S,T,F=struct.unpack_from('<4i',payload)
        assert (magic,S,T,F)==(0x54503131,STATIC,TEMPORAL,FEATURES+4)
        off=16;heads=[];blocks=[]
        while off<len(payload):
            head=struct.unpack_from('<9i',payload,off);off+=36
            n=head[4];assert 0<n<=256 and 0<=head[5]<n
            blocks.append(np.frombuffer(payload,dtype='<f4',count=n*F,offset=off).reshape(n,F))
            heads.append(head);off+=4*n*F
        assert off==len(payload)
        A=np.concatenate(blocks);self.head=np.asarray(heads,dtype=np.int64)
        counts=self.head[:,4];self.N=len(counts)
        starts=np.r_[0,np.cumsum(counts)]
        self.X=torch.tensor(A[:,:FEATURES],dtype=torch.float64,device=device)
        idx=A[:,FEATURES:FEATURES+3].astype(np.int64)
        assert np.all((idx[:,0]>=0)&(idx[:,0]<6)) and np.all((idx[:,1:]>=0)&(idx[:,1:]<64))
        self.pf=torch.tensor(idx[:,0]*64+idx[:,1],device=device)
        self.pt=torch.tensor(idx[:,0]*64+idx[:,2],device=device)
        self.seg=torch.tensor(np.repeat(np.arange(self.N),counts),device=device)
        self.played=torch.tensor(starts[:-1]+self.head[:,5],device=device)
        self.counts=counts
        self.compatible=torch.tensor(A[:,-1]>0.5,device=device)
        self.device=device
        self.ambiguous=(np.add.reduceat(A[:,-1],starts[:-1])>1)&(A[starts[:-1]+self.head[:,5],-1]>0.5)

def logits(d,theta,temporal):
    z=d.X[:,:STATIC]@theta[:STATIC]
    if temporal:z=z+d.X[:,STATIC:]@theta[STATIC:FEATURES]
    return z+theta[FEATURES+d.pf]+theta[FEATURES+384+d.pt]

def log_sums(d,z,mask=None):
    if mask is not None:z=torch.where(mask,z,torch.full_like(z,-1e30))
    maxes=torch.full((d.N,),-1e30,dtype=z.dtype,device=z.device).scatter_reduce(0,d.seg,z,'amax').detach()
    e=torch.exp(z-maxes[d.seg])
    if mask is not None:e=e*mask
    sums=torch.zeros_like(maxes).index_add(0,d.seg,e)
    return maxes+torch.log(sums.clamp_min(1e-300))

def objective(d,theta,temporal,l2=1e-4):
    z=logits(d,theta,temporal)
    return (log_sums(d,z)-z[d.played]).mean()+0.5*l2*theta.square().sum()

def fit(d,temporal):
    theta=torch.zeros(PARAMS,device=d.device,dtype=torch.float64,requires_grad=True)
    optimizer=torch.optim.LBFGS([theta],lr=1,max_iter=150,max_eval=200,tolerance_grad=1e-7,
                               tolerance_change=1e-10,history_size=20,line_search_fn='strong_wolfe')
    calls=[];t0=time.monotonic()
    def closure():
        optimizer.zero_grad();loss=objective(d,theta,temporal);loss.backward()
        calls.append(float(loss.detach()))
        if len(calls)%20==0:print(json.dumps({'temporal':temporal,'calls':len(calls),'objective':calls[-1],'seconds':time.monotonic()-t0}),flush=True)
        return loss
    optimizer.step(closure)
    loss=closure()
    return theta.detach(),{'objective':float(loss.detach()),'max_gradient':float(theta.grad.abs().max()),
                           'calls':len(calls),'seconds':time.monotonic()-t0,'trace':calls}

@torch.no_grad()
def scores(d,theta,temporal):
    z=logits(d,theta,temporal);denom=log_sums(d,z);conditional=log_sums(d,z,d.compatible)
    played=z[d.played]
    return {'logp':(played-denom).cpu().numpy(),
            'conditional_logp':(played-conditional).cpu().numpy(),
            'observation_logp':(conditional-denom).cpu().numpy()}

def mean(xs,mask):return float(xs[mask].mean()) if np.any(mask) else None

def describe(d,values,mask):
    amb=mask&d.ambiguous
    return {'positions':int(mask.sum()),'ambiguous':int(amb.sum()),
            'nll':-mean(values['logp'],mask) if mask.any() else None,
            'ambiguous_unconditional_nll':-mean(values['logp'],amb) if amb.any() else None,
            'ambiguous_conditional_nll':-mean(values['conditional_logp'],amb) if amb.any() else None,
            'ambiguous_observation_nll':-mean(values['observation_logp'],amb) if amb.any() else None}

def bootstrap(games,difference,mask):
    ids=np.unique(games[mask]);sums=np.array([difference[(games==i)&mask].sum() for i in ids])
    counts=np.array([np.sum((games==i)&mask) for i in ids]);rng=np.random.default_rng(11012026)
    draws=[]
    for _ in range(40):
        ix=rng.integers(0,len(ids),size=(100,len(ids)))
        draws.extend((sums[ix].sum(1)/counts[ix].sum(1)).tolist())
    return {'games':len(ids),'mean_nats':float(sums.sum()/counts.sum()),
            'whole_game_bootstrap_95':np.quantile(draws,[.025,.975]).tolist(),'resamples':len(draws)}

def compare(d,all_scores,teams,cluster=False):
    both={name:describe(d,s,np.ones(d.N,dtype=bool)) for name,s in all_scores.items()}
    result={'overall':both,'by_team':{},'by_colour':{},'by_previous_capture':{}}
    for i,name in enumerate(teams):
        mask=d.head[:,3]==i
        result['by_team'][name]={a:describe(d,s,mask) for a,s in all_scores.items()}
    for side in [0,1]:
        result['by_colour'][str(side)]={a:describe(d,s,d.head[:,2]==side) for a,s in all_scores.items()}
    for capture in [False,True]:
        result['by_previous_capture'][str(capture)]={a:describe(d,s,(d.head[:,7]>0)==capture) for a,s in all_scores.items()}
    delta=all_scores['temporal']['conditional_logp']-all_scores['static']['conditional_logp']
    result['ambiguous_gain']=mean(delta,d.ambiguous)
    result['all_move_nll_change']=both['temporal']['nll']-both['static']['nll']
    ref=np.isin(d.head[:,3],[teams.index(n) for n in ['Instructors','duck','HYPOTHERMIA']])&d.ambiguous
    result['reference_ambiguous_gain']=mean(delta,ref)
    if cluster:
        result['ambiguous_gain_uncertainty']=bootstrap(d.head[:,0],delta,d.ambiguous)
        result['all_move_gain_uncertainty']=bootstrap(d.head[:,0],all_scores['temporal']['logp']-all_scores['static']['logp'],np.ones(d.N,dtype=bool))
    return result

def write_scores(path,d,values):
    with gzip.open(path,'wt') as f:
        for i,h in enumerate(d.head):
            r={'game_index':int(h[0]),'ply':int(h[1]),'side':int(h[2]),'team_id':int(h[3]),'legal_moves':int(h[4]),
               'history_known':bool(h[6]>=0),'previous_capture_value':int(h[7]),'ambiguous':bool(d.ambiguous[i])}
            for arm,s in values.items():
                r[arm]={k:(float(v[i]) if k=='logp' or d.ambiguous[i] else None) for k,v in s.items()}
            f.write(json.dumps(r)+'\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--device',default='cuda');args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=False);torch.set_num_threads(2);torch.manual_seed(11012026)
    torch.backends.cuda.matmul.allow_tf32=False
    manifest=json.loads((args.data/'manifest.json').read_text())
    receipt={'manifest_sha256':sha(args.data/'manifest.json'),'script_sha256':sha(Path(__file__)),
             'torch':torch.__version__,'device':args.device,'l2':1e-4,'models':{},'scope':'True-parent predictive experiment; no posterior or strength claim.'}
    d=Data(args.data/'train.features.bin.gz',args.device);models={}
    for arm,temporal in [('static',False),('temporal',True)]:
        model,stats=fit(d,temporal);models[arm]=model
        path=args.out/(arm+'.json');path.write_text(json.dumps({'coefficients':model.cpu().tolist(),'fit':stats},indent=2)+'\n')
        receipt['models'][arm]={'sha256':sha(path),'fit':{k:v for k,v in stats.items() if k!='trace'}}
    # Commit parameter hashes before validation/test scoring; no adaptation afterward.
    (args.out/'frozen-models.json').write_text(json.dumps(receipt,indent=2)+'\n')
    del d;torch.cuda.empty_cache() if args.device=='cuda' else None
    validation=Data(args.data/'validation.features.bin.gz',args.device)
    vals={arm:scores(validation,t,arm=='temporal') for arm,t in models.items()}
    report=compare(validation,vals,manifest['teams'])
    report['passes_validation']=report['ambiguous_gain']>=.02 and report['all_move_nll_change']<=.005
    (args.out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    write_scores(args.out/'validation-scores.jsonl.gz',validation,vals)
    print(json.dumps({'validation':{k:report[k] for k in ['ambiguous_gain','all_move_nll_change','reference_ambiguous_gain','passes_validation']}}),flush=True)
    del validation,vals;torch.cuda.empty_cache() if args.device=='cuda' else None
    if not report['passes_validation']:
        (args.out/'status.json').write_text(json.dumps({'state':'complete','test_scored':False,'earns_belief_integration':False,'reason':'validation gate failed'},indent=2)+'\n');return
    for arm in models:assert sha(args.out/(arm+'.json'))==receipt['models'][arm]['sha256']
    test=Data(args.data/'test.features.bin.gz',args.device)
    vals={arm:scores(test,t,arm=='temporal') for arm,t in models.items()}
    report=compare(test,vals,manifest['teams'],cluster=True)
    report['passes_test']=(report['ambiguous_gain_uncertainty']['whole_game_bootstrap_95'][0]>0 and
                           report['all_move_nll_change']<=.005 and report['reference_ambiguous_gain']>=-.01)
    (args.out/'test.json').write_text(json.dumps(report,indent=2)+'\n')
    write_scores(args.out/'test-scores.jsonl.gz',test,vals)
    (args.out/'status.json').write_text(json.dumps({'state':'complete','test_scored':True,'earns_belief_integration':report['passes_test']},indent=2)+'\n')
    print(json.dumps({'test':{k:report[k] for k in ['ambiguous_gain','all_move_nll_change','reference_ambiguous_gain','ambiguous_gain_uncertainty','passes_test']}}),flush=True)
if __name__=='__main__':main()
