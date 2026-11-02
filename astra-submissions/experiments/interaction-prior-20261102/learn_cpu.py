#!/usr/bin/env python3
"""In-memory conditional-choice training; freeze choices before opening test."""
from datetime import datetime,timezone
import ctypes,gzip,hashlib,json,math,os,signal,sys,time
from pathlib import Path
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
import torch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];OUT=ROOT/'astra-submissions/analysis/interaction-prior-20261102'
HISTORY=HERE.parent/'queen-terminal-backport-20261102/build-r2/base/data/history.bin'
CONTINUOUS=(1,12,14,21,23,24)

def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def unique(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def encoded(uci):
 def sq(s):return ord(s[0])-97+8*(int(s[1])-1)
 return sq(uci[:2])|(sq(uci[2:4])<<6)|((('pnbrqk'.index(uci[4]) if len(uci)==5 else 6))<<12)

def library():
 lib=ctypes.CDLL(str(HERE/'build/bridge.so'))
 nd=lambda dtype:np.ctypeslib.ndpointer(dtype=dtype,flags='C_CONTIGUOUS')
 lib.prior_load.argtypes=[ctypes.c_char_p];lib.prior_state.argtypes=[ctypes.c_char_p]*3;lib.prior_step.argtypes=[ctypes.c_uint16]
 lib.interaction_features.argtypes=[nd(np.uint16),nd(np.float32),nd(np.float32),nd(np.float32),nd(np.uint32),ctypes.POINTER(ctypes.c_uint),nd(np.uint8)]
 lib.interaction_logits.argtypes=[nd(np.float32),nd(np.float32),ctypes.c_int,ctypes.c_int,nd(np.float32),nd(np.float32),nd(np.float32)]
 assert lib.prior_load(str(HISTORY).encode())
 return lib

def mask_array(F):
 m=np.triu(np.ones((F,F),np.float32),1)
 for i in CONTINUOUS:
  if i<F:m[i,i]=1
 return m

def selftest(lib):
 rng=np.random.default_rng(228);x=rng.uniform(-1,1,(31,26)).astype(np.float32);x[rng.random(x.shape)<.6]=0;base=rng.normal(size=31).astype(np.float32);reports=[]
 for F in (18,26):
  lin=np.zeros(F,np.float32);q=np.zeros((F,F),np.float32);out=np.empty(31,np.float32)
  lib.interaction_logits(x,base,31,F,lin,q,out);assert np.array_equal(out,base)
  lin=rng.normal(0,.15,F).astype(np.float32);q=rng.normal(0,.15,(F,F)).astype(np.float32)*mask_array(F)
  lib.interaction_logits(x,base,31,F,lin,q,out)
  ref=base.astype(float)+x[:,:F].astype(float)@lin.astype(float)+np.einsum('ni,ij,nj->n',x[:,:F].astype(float),q.astype(float),x[:,:F].astype(float))
  error=float(np.max(np.abs(ref-out)));assert error<1e-5,error
  reports.append(dict(features=F,zero_residual_bitwise=True,nonzero_max_error=error))
 return reports

def collect(plan,lib,split):
 start=time.monotonic();groups=[];meta=[];digest=hashlib.sha256();frames=0
 moves=np.zeros(256,np.uint16);features=np.zeros((256,26),np.float32);full=np.zeros(256,np.float32);cheap=np.zeros(256,np.float32);counts=np.zeros(256,np.uint32);total=ctypes.c_uint();surprise=np.zeros(256,np.uint8);buffers=[ctypes.create_string_buffer(65) for _ in range(3)]
 for idx,g in enumerate(x for x in plan['games'] if x['split']==split):
  path=ROOT/'data/raw/games'/g['game']/'replay.json';assert sha(path)==g['replay_sha256'];rp=json.loads(path.read_text());lib.prior_start();selected=set(g['selected_plies'])
  for ply,frame in enumerate(rp['frames']):
   side=lib.prior_state(*buffers);assert side==ply%2
   for key,buf in zip(('board','white','black'),buffers):assert buf.value.decode()==frame[key],(g['game'],ply,key)
   frames+=1
   if ply==len(rp['frames'])-1:continue
   action=encoded(rp['frames'][ply+1]['move'])
   if ply in selected:
    n=lib.interaction_features(moves,features,full,cheap,counts,ctypes.byref(total),surprise);target=np.flatnonzero(moves[:n]==action);assert len(target)==1 and n>0;target=int(target[0]);assert int(counts[:n].sum())<=total.value
    x=features[:n].copy();b=np.stack([cheap[:n],full[:n]],axis=1);h=counts[:n].copy();groups.append((x,b,h,target,total.value))
    meta.append(dict(game=g['game'],ply=ply,team=rp[('white','black')[side]],target=target,n=n,primary=ply//2>=8 and not bool(x[target,22]),surprise=bool(surprise[target]),self_capturable=bool(x[target,22]),history_count=total.value))
    for value in (x,b,h,np.array([target,total.value],np.int64)):digest.update(value.tobytes())
   assert lib.prior_step(action)>=0,(g['game'],ply)
  if (idx+1)%500==0:print(json.dumps({'collection':split,'games':idx+1,'groups':len(groups)}),flush=True)
 N=len(groups);width=max(len(g[0]) for g in groups);assert width<=256
 X=np.zeros((N,width,26),np.float32);B=np.zeros((N,width,2),np.float32);H=np.zeros((N,width),np.float32);valid=np.zeros((N,width),bool);Y=np.empty(N,np.int64);HN=np.empty(N,np.float32)
 for i,(x,b,h,y,hn) in enumerate(groups):
  n=len(x);X[i,:n]=x;B[i,:n]=b;H[i,:n]=h;valid[i,:n]=True;Y[i]=y;HN[i]=hn
 del groups
 data={k:torch.from_numpy(v).to('cpu') for k,v in [('x',X),('base',B),('counts',H),('valid',valid),('y',Y),('history_n',HN)]}
 receipt=dict(split=split,games=sum(g['split']==split for g in plan['games']),decisions=N,width=width,native_validated_frames=frames,unpacked_sha256=digest.hexdigest(),elapsed=time.monotonic()-start,bytes=X.nbytes+B.nbytes+H.nbytes+valid.nbytes+Y.nbytes)
 unique(OUT/(split+'-data.json'),receipt);print(json.dumps(receipt),flush=True)
 return data,meta

def logits(data,indices,F,linear,q):
 x=data['x'][indices,:,:F];base=data['base'][indices,:,0 if F==18 else 1]
 z=base+(x@linear)+torch.sum((x@q)*x,dim=-1)
 return z.masked_fill(~data['valid'][indices],-torch.inf)

@torch.no_grad()
def evaluate(data,F,linear,q,batch=1024):
 rows=[]
 for start in range(0,len(data['y']),batch):
  idx=torch.arange(start,min(start+batch,len(data['y'])),device='cpu');z=logits(data,idx,F,linear,q);p=z.softmax(-1);h=data['counts'][idx];N=data['history_n'][idx,None]
  p=torch.where(N>=3,(h+4*p)/(N+4),p)
  target=p.gather(1,data['y'][idx,None]).squeeze(1);assert torch.isfinite(target).all()
  rows.append(target.cpu().numpy())
 return np.concatenate(rows)

def train_one(plan,data,val,vm,F,kind,ridge):
 torch.manual_seed(plan['seed']);generator=torch.Generator(device='cpu').manual_seed(plan['seed']);linear=torch.nn.Parameter(torch.zeros(F,device='cpu'));qraw=torch.nn.Parameter(torch.zeros((F,F),device='cpu'),requires_grad=kind=='quadratic');mask=torch.tensor(mask_array(F),device='cpu')
 parameters=[linear]+([qraw] if kind=='quadratic' else []);optimizer=torch.optim.Adam(parameters,lr=plan['learning_rate']);best=None;curves=[];primary=np.array([r['primary'] for r in vm]);assert primary.any()
 name=f'{F}-{kind}-{ridge}';start=time.monotonic()
 for epoch in range(plan['epochs']):
  permutation=torch.randperm(len(data['y']),device='cpu',generator=generator);total=0.;batches=0
  for i in range(0,len(permutation),plan['batch']):
   idx=permutation[i:i+plan['batch']];q=qraw*mask;z=logits(data,idx,F,linear,q);loss=torch.nn.functional.cross_entropy(z,data['y'][idx])+ridge*(linear.square().sum()+q.square().sum())
   assert torch.isfinite(loss);optimizer.zero_grad();loss.backward();optimizer.step();total+=float(loss.detach());batches+=1
  p=evaluate(val,F,linear,qraw*mask);nll=float(-np.log(np.maximum(p[primary].astype(float),1e-30)).mean());row=dict(epoch=epoch+1,training_objective=total/batches,validation_nll=nll,elapsed=time.monotonic()-start);curves.append(row)
  if best is None or nll<best['validation_nll']:
   best=dict(features=F,kind=kind,ridge=ridge,epoch=epoch+1,validation_nll=nll,linear=linear.detach().cpu().tolist(),quadratic=(qraw*mask).detach().cpu().tolist())
  save(OUT/(name+'-curve.json'),curves);print(json.dumps({'fit':name,**row}),flush=True)
 unique(OUT/(name+'-model.json'),best);return best

def native_parity(lib,model,data):
 F=model['features'];lin=np.array(model['linear'],np.float32);q=np.array(model['quadratic'],np.float32);worst=0.;cases=min(100,len(data['y']))
 for i in np.linspace(0,len(data['y'])-1,cases,dtype=int):
  n=int(data['valid'][i].sum());x=data['x'][i,:n].cpu().numpy().copy();base=data['base'][i,:n,0 if F==18 else 1].cpu().numpy().copy();out=np.empty(n,np.float32)
  lib.interaction_logits(x,base,n,F,lin,q,out)
  idx=torch.tensor([int(i)],device='cpu');reference=logits(data,idx,F,torch.tensor(lin,device='cpu'),torch.tensor(q,device='cpu'))[0,:n].detach().cpu().numpy()
  worst=max(worst,float(np.abs(reference-out).max()))
 assert worst<2e-5,worst
 return dict(features=F,cases=cases,maximum_logit_error=worst)

def bootstrap(meta,delta,seed,draws):
 sums={}
 for m,d in zip(meta,delta):
  a=sums.setdefault(m['game'],[0.,0]);a[0]+=float(d);a[1]+=1
 values=np.array(list(sums.values()));rng=np.random.default_rng(seed);scores=[]
 for _ in range(draws):
  pick=values[rng.integers(len(values),size=len(values))];scores.append(pick[:,0].sum()/pick[:,1].sum())
 return [float(x) for x in np.quantile(scores,[.025,.975])]

def run():
 plan=json.loads((OUT/'plan-cpu.json').read_text());os.sched_setaffinity(0,set(plan['cores']));torch.set_num_threads(2);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
 for p,h in plan['dependencies'].items():assert sha(Path(p))==h,p
 state=dict(started=now(),status='running',phase='preflight',plan_sha256=sha(OUT/'plan-cpu.json'));unique(OUT/'execution.json',state)
 def expired(*_):raise TimeoutError('45-minute training and evaluation cap')
 signal.signal(signal.SIGALRM,expired);signal.alarm(plan['max_seconds'])
 try:
  lib=library();unique(OUT/'preflight.json',dict(native=selftest(lib),compute='CPU, two cores; GPU untouched',torch=torch.__version__))
  train,tm=collect(plan,lib,'train');val,vm=collect(plan,lib,'validation');selected={};models=[]
  state['phase']='fitting';save(OUT/'execution.json',state)
  for F in (18,26):
   for kind in ('linear','quadratic'):
    candidates=[train_one(plan,train,val,vm,F,kind,ridge) for ridge in plan['ridges'][kind]]
    chosen=min(candidates,key=lambda m:m['validation_nll']);selected[f'{F}-{kind}']=chosen;models+=candidates
  unique(OUT/'selection.json',{'at':now(),'selected':selected,'test_opened':False,'native_parity':[native_parity(lib,m,val) for m in selected.values()]})
  # No test features or scores exist before the selected model hashes are pinned.
  unique(OUT/'selection-lock.json',{'sha256':sha(OUT/'selection.json'),'at':now(),'test_opened':False})
  del train,tm,val,vm;__import__('gc').collect();test,meta=collect(plan,lib,'test');results={};predictions={};primary=np.array([m['primary'] for m in meta]);surprise=np.array([m['surprise'] for m in meta])&primary
  assert int(surprise.sum())>=plan['gate']['surprise_min'],int(surprise.sum())
  for F in (18,26):
   predictions[F]={}
   for kind in ('base','linear','quadratic'):
    model=selected[f'{F}-{kind}'] if kind!='base' else {'linear':[0.]*F,'quadratic':np.zeros((F,F)).tolist()}
    p=evaluate(test,F,torch.tensor(model['linear'],device='cpu'),torch.tensor(model['quadratic'],device='cpu'));predictions[F][kind]=p
   losses={k:-np.log(np.maximum(v.astype(float),1e-30)) for k,v in predictions[F].items()};gain=losses['base']-losses['quadratic'];lin_gain=losses['linear']-losses['quadratic'];pm=[m for m,ok in zip(meta,primary) if ok]
   report={'primary_decisions':int(primary.sum()),'surprise_captures':int(surprise.sum()),'nll':{k:float(v[primary].mean()) for k,v in losses.items()},'gain':float(gain[primary].mean()),'interval95':bootstrap(pm,gain[primary],plan['seed'],plan['bootstrap_draws']), 'matched_linear_gain':float(lin_gain[primary].mean()),'surprise_gain':float(gain[surprise].mean()),'all_move_gain':float(gain.mean()),'zeros_primary':int((predictions[F]['quadratic'][primary]<=0).sum())}
   gate=plan['gate'];conditions={'gain':report['gain']>=gate['cheap_gain' if F==18 else 'full_gain'],'interval':report['interval95'][0]>0,'matched_linear':report['matched_linear_gain']>=gate['matched_linear_gain'],'surprise':report['surprise_gain']>=gate['surprise_gain_min'],'all_move':report['all_move_gain']>=0,'no_zeros':report['zeros_primary']==0}
   report['conditions']=conditions;results[str(F)]=report
  with (OUT/'decisions.jsonl.gz').open('xb') as f:
   with gzip.GzipFile(filename='',fileobj=f,mode='wb',mtime=0) as z:
    for i,m in enumerate(meta):z.write((json.dumps({**m,'probabilities':{str(F):{k:float(v[i]) for k,v in predictions[F].items()} for F in (18,26)}})+'\n').encode())
  result={'modes':results,'decision':'capped_posterior_design_allowed' if all(v for r in results.values() for v in r['conditions'].values()) else 'close_interaction_configuration','selection_sha256':sha(OUT/'selection.json'),'scores_sha256':sha(OUT/'decisions.jsonl.gz'),'scope':plan['scope']}
  unique(OUT/'result.json',result);print(json.dumps(result,indent=2));state.update(status='complete',phase='done')
 except BaseException as e:state.update(status='failed',error=f'{type(e).__name__}: {e}');raise
 finally:signal.alarm(0);state['ended']=now();save(OUT/'execution.json',state)

if __name__=='__main__':run()
