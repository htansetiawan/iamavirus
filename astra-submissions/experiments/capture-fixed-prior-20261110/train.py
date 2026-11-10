"""One fixed four-fit CPU study; lock selection before later test features."""
from datetime import datetime,timezone
import ctypes
import gzip
import hashlib
import json
import os
from pathlib import Path
import signal
import time
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
import torch
from prepare import ROOT,HERE,OUT,BASE,library,sha,write
from model import logp,mask,synthetic_checks

def now():return datetime.now(timezone.utc).isoformat()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def encoded(s):
    sq=lambda p:ord(p[0])-97+8*(int(p[1])-1)
    return sq(s[:2])|(sq(s[2:4])<<6)|(('pnbrqk'.index(s[4]) if len(s)==5 else 6)<<12)

def collect(plan,lib,split,persist=True):
    started=time.monotonic();groups=[];meta=[];frames=0;digest=hashlib.sha256()
    moves=np.zeros(256,np.uint16);x=np.zeros((256,26),np.float32);full=np.zeros(256,np.float32);cheap=np.zeros(256,np.float32)
    counts=np.zeros(256,np.uint32);N=ctypes.c_uint();surprise=np.zeros(256,np.uint8);buffers=[ctypes.create_string_buffer(65) for _ in range(3)]
    selected=[g for g in plan['games'] if g['split']==split]
    for index,g in enumerate(selected):
        lib.prior_start();wanted=set(g['selected_plies'])
        sequence=g['moves'];assert hashlib.sha256(' '.join(sequence).encode()).hexdigest()==g['sequence_sha256']
        for ply in range(len(sequence)+1):
            side=lib.prior_state(*buffers);assert side==ply%2
            frames+=1
            if ply==len(sequence):continue
            action=encoded(sequence[ply])
            if ply in wanted:
                n=lib.quiet_features(moves,x,full,cheap,counts,ctypes.byref(N),surprise)
                where=np.flatnonzero(moves[:n]==action);assert len(where)==1 and n>0
                target=int(where[0]);features=x[:n].copy();base=np.stack((cheap[:n],full[:n]),axis=-1);h=counts[:n].copy()
                assert int(h.sum())<=N.value
                groups.append((features,base,h,target,N.value))
                meta.append(dict(game=g['game'],ply=ply,team=g[('white','black')[side]],n=n,target=target,
                     primary=ply//2>=8 and not bool(features[target,22]),capture=bool(features[target,0]),surprise=bool(surprise[target]),
                     self_capturable=bool(features[target,22]),history_n=N.value))
                for v in (features,base,h,np.array([target,N.value],np.int64)):digest.update(v.tobytes())
            assert lib.prior_step(action)>=0
        if (index+1)%500==0:print(json.dumps(dict(collect=split,games=index+1,decisions=len(groups))),flush=True)
    rows=len(groups);width=max(len(g[0]) for g in groups)
    X=np.zeros((rows,width,26),np.float32);B=np.zeros((rows,width,2),np.float32);H=np.zeros((rows,width),np.float32)
    valid=np.zeros((rows,width),bool);Y=np.empty(rows,np.int64);HN=np.empty(rows,np.float32)
    for i,(x,b,h,y,hn) in enumerate(groups):
        n=len(x);X[i,:n]=x;B[i,:n]=b;H[i,:n]=h;valid[i,:n]=True;Y[i]=y;HN[i]=hn
    del groups
    data={k:torch.from_numpy(v) for k,v in [('x',X),('base',B),('counts',H),('valid',valid),('y',Y),('history_n',HN)]}
    data['capture']=data['x'][:,:,0]>0
    receipt=dict(at=now(),split=split,games=len(selected),decisions=rows,width=width,native_frames=frames,unpacked_sha256=digest.hexdigest(),
                 array_bytes=X.nbytes+B.nbytes+H.nbytes+valid.nbytes+Y.nbytes+HN.nbytes,seconds=time.monotonic()-started)
    if persist:write(OUT/(split+'-data.json'),receipt)
    print(json.dumps(receipt),flush=True);return data,meta,receipt

@torch.no_grad()
def evaluate(data,F,lin,q):
    out=[]
    for start in range(0,len(data['y']),512):
        idx=torch.arange(start,min(start+512,len(data['y'])))
        value=logp(data,idx,F,lin,q).gather(1,data['y'][idx,None]).squeeze(1)
        assert torch.isfinite(value).all();out.append(value.numpy())
    return np.concatenate(out).astype(float)

def fit(plan,data,val,vm,F,kind):
    torch.manual_seed(plan['seed']);generator=torch.Generator().manual_seed(plan['seed'])
    lin=torch.nn.Parameter(torch.zeros(F));qraw=torch.nn.Parameter(torch.zeros(F,F),requires_grad=kind=='quadratic')
    qmask=mask(F);parameters=[lin]+([qraw] if kind=='quadratic' else [])
    optimizer=torch.optim.Adam(parameters,lr=plan['learning_rate']);primary=np.array([m['primary'] for m in vm]);assert primary.any()
    def snapshot(epoch,nll):return dict(features=F,kind=kind,epoch=epoch,validation_nll=nll,linear=lin.detach().tolist(),quadratic=(qraw*qmask).detach().tolist())
    initial=float(-evaluate(val,F,lin,qraw*qmask)[primary].mean());best=snapshot(0,initial);curves=[dict(epoch=0,validation_nll=initial)]
    name=f'{F}-{kind}';started=time.monotonic()
    for epoch in range(1,plan['epochs']+1):
        permutation=torch.randperm(len(data['y']),generator=generator);total=0.;batches=0
        for start in range(0,len(permutation),plan['batch']):
            idx=permutation[start:start+plan['batch']];q=qraw*qmask
            lp=logp(data,idx,F,lin,q).gather(1,data['y'][idx,None]).squeeze(1)
            loss=-lp.mean()+plan['ridge']*(lin.square().sum()+q.square().sum())
            assert torch.isfinite(loss);optimizer.zero_grad();loss.backward()
            assert all(torch.isfinite(p.grad).all() for p in parameters)
            optimizer.step();total+=float(loss.detach());batches+=1
        nll=float(-evaluate(val,F,lin,qraw*qmask)[primary].mean())
        if nll<best['validation_nll']:best=snapshot(epoch,nll)
        row=dict(epoch=epoch,validation_nll=nll,training_objective=total/batches,seconds=time.monotonic()-started)
        curves.append(row);save(OUT/(name+'-curve.json'),curves);print(json.dumps(dict(fit=name,**row)),flush=True)
    write(OUT/(name+'-model.json'),best);return best

def native_score(lib,data,F,model):
    lin=np.array(model['linear'],np.float32);q=np.array(model['quadratic'],np.float32)
    probabilities=[];capture_checks=0;capture_error=0.;all_lp=[]
    zero=np.zeros(F,np.float32);zeroq=np.zeros((F,F),np.float32)
    for i in range(len(data['y'])):
        n=int(data['valid'][i].sum());x=data['x'][i,:n].numpy().copy();base=data['base'][i,:n,0 if F==14 else 1].numpy().copy()
        lp=np.empty(n,np.float32);baseline=np.empty(n,np.float32)
        lib.quiet_logp(x,base,n,F,lin,q,lp);lib.quiet_logp(x,base,n,F,zero,zeroq,baseline)
        capture=x[:,0]>0;assert np.array_equal(lp[capture],baseline[capture])
        capture_checks+=int(capture.sum());capture_error=max(capture_error,float(abs(lp[capture]-baseline[capture]).max(initial=0)))
        target=int(data['y'][i]);value=float(lp[target]);hn=float(data['history_n'][i]);h=float(data['counts'][i,target])
        if hn>=3:value=float(np.logaddexp(np.log(h) if h else -np.inf,np.log(4.)+value)-np.log(hn+4))
        probabilities.append(value);all_lp.append(lp)
    return np.array(probabilities),dict(capture_actions=capture_checks,capture_logp_error=capture_error),all_lp

def bootstrap(meta,delta,seed,draws):
    grouped={}
    for m,d in zip(meta,delta):
        r=grouped.setdefault(m['game'],[0.,0]);r[0]+=float(d);r[1]+=1
    v=np.array(list(grouped.values()));rng=np.random.default_rng(seed);values=[]
    for _ in range(draws):
        sample=v[rng.integers(len(v),size=len(v))];values.append(sample[:,0].sum()/sample[:,1].sum())
    return np.quantile(values,[.025,.975]).tolist()

def main():
    plan=json.loads((OUT/'plan.json').read_text());os.sched_setaffinity(0,set(plan['cores']));torch.set_num_threads(2)
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    state=dict(at=now(),status='running',phase='preflight');write(OUT/'execution.json',state)
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('frozen30-minute bound')));signal.alarm(plan['max_seconds'])
    started=time.monotonic()
    try:
        lib=library();write(OUT/'math-checks.json',synthetic_checks())
        train,tm,_=collect(plan,lib,'train');val,vm,_=collect(plan,lib,'validation');selected={}
        state['phase']='fit';save(OUT/'execution.json',state)
        for F in (14,22):
            for kind in ('linear','quadratic'):selected[f'{F}-{kind}']=fit(plan,train,val,vm,F,kind)
        write(OUT/'selection.json',dict(at=now(),selected=selected,test_features_opened=False))
        write(OUT/'selection-lock.json',dict(at=now(),sha256=sha(OUT/'selection.json'),test_features_opened=False))
        del train,tm,val,vm;__import__('gc').collect()
        state['phase']='late-evaluation';save(OUT/'execution.json',state)
        test,meta,_=collect(plan,lib,'test');primary=np.array([m['primary'] for m in meta]);surprise=primary & np.array([m['surprise'] for m in meta])
        capture=np.array([m['capture'] for m in meta]);assert surprise.sum()>=plan['gate']['surprise_min']
        results={};predictions={};checks={}
        for F in (14,22):
            predictions[F]={};checks[F]={}
            for kind in ('base','linear','quadratic'):
                model=selected[f'{F}-{kind}'] if kind!='base' else dict(linear=[0.]*F,quadratic=np.zeros((F,F)).tolist())
                lp,check,_=native_score(lib,test,F,model);predictions[F][kind]=lp;checks[F][kind]=check
            gain=predictions[F]['quadratic']-predictions[F]['base'];linear=predictions[F]['quadratic']-predictions[F]['linear']
            assert np.array_equal(predictions[F]['quadratic'][capture],predictions[F]['base'][capture])
            pm=[m for m,ok in zip(meta,primary) if ok];ci=bootstrap(pm,gain[primary],plan['seed'],plan['bootstrap_draws'])
            gate=plan['gate'];r=dict(primary=int(primary.sum()),surprise_captures=int(surprise.sum()),nll={k:float(-v[primary].mean()) for k,v in predictions[F].items()},
               gain=float(gain[primary].mean()),interval95=ci,matched_linear_gain=float(linear[primary].mean()),all_move_gain=float(gain.mean()),
               surprise_gain=float(gain[surprise].mean()),capture_target_max_error=float(abs(gain[capture]).max(initial=0)))
            r['conditions']=dict(gain=r['gain']>=gate['cheap_gain' if F==14 else 'full_gain'],confidence=ci[0]>0,
                matched_linear=r['matched_linear_gain']>=gate['matched_linear_gain'],all_moves=r['all_move_gain']>=0,
                capture_identity=r['capture_target_max_error']==0 and all(c['capture_logp_error']==0 for c in checks[F].values()))
            results[str(F)]=r
        with (OUT/'decisions.jsonl.gz').open('xb') as stream:
            with gzip.GzipFile(filename='',fileobj=stream,mode='wb',mtime=0) as z:
                for i,m in enumerate(meta):z.write((json.dumps({**m,'logp':{str(F):{k:float(v[i]) for k,v in predictions[F].items()} for F in (14,22)}})+'\n').encode())
        result=dict(at=now(),modes=results,native_checks=checks,decision='prospective_posterior_design_allowed' if all(c for r in results.values() for c in r['conditions'].values()) else 'close_capture_fixed_configuration',
                    selection_sha256=sha(OUT/'selection.json'),scores_sha256=sha(OUT/'decisions.jsonl.gz'),scope=plan['scope'])
        write(OUT/'result.json',result);print(json.dumps(result,indent=2),flush=True);state.update(status='complete',phase='done')
    except BaseException as exc:state.update(status='failed',error=repr(exc));raise
    finally:
        signal.alarm(0);state.update(ended=now(),seconds=time.monotonic()-started);save(OUT/'execution.json',state)
if __name__=='__main__':main()
