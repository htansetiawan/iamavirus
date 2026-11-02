"""Neutrality, boundedness, gradients, native parity and CPU budget."""
import ctypes
import json
import os
import subprocess
import time
import numpy as np
import torch
from common import HERE, OUT, OLD, now, sha, write_new
from models import FlatResidual, QueryResidual, combine, pack
from native import build


def main():
    os.sched_setaffinity(0,{0});torch.set_num_threads(1);torch.manual_seed(2391102)
    library,cmd=build();lib=ctypes.CDLL(str(library))
    fp=ctypes.POINTER(ctypes.c_float);bp=ctypes.POINTER(ctypes.c_uint8)
    rng=np.random.default_rng(2391102);x=np.zeros((256,64,5),dtype=np.uint8)
    x[:,:,0]=rng.choice([0,1,2,3,4,5,7,8,9,10,11],size=(256,64));x[:,:,1:]=rng.integers(0,2,size=(256,64,4))
    for row in x:
        a,b=rng.choice(64,2,replace=False);row[a,0]=6;row[b,0]=12
    h=rng.integers(0,101,size=256,dtype=np.uint8);z=np.linspace(-14,14,256,dtype=np.float32)
    with np.load(OLD/'work/dataset/data.npz') as d:
        ii=np.flatnonzero(d['fold']==0)[:32];x[:32]=d['x'][ii];h[:32]=d['half'][ii]
    tx=torch.tensor(x,dtype=torch.long);th=torch.tensor(h,dtype=torch.float32);tz=torch.tensor(z)
    native={};payloads={};expected_sum=0
    for kind,klass in [('flat',FlatResidual),('query',QueryResidual)]:
        torch.manual_seed(2391102);model=klass().eval()
        single=getattr(lib,'fow_residual_'+kind+'_logit');single.argtypes=[fp,bp,ctypes.c_uint8,ctypes.c_float];single.restype=ctypes.c_float
        batch=getattr(lib,'fow_residual_'+kind+'_batch');batch.argtypes=[fp,bp,bp,fp,ctypes.c_int,ctypes.c_int];batch.restype=ctypes.c_double
        def evaluate():
            packed=pack(model,kind);wp=packed.ctypes.data_as(fp)
            with torch.no_grad():p=model(tx,th,tz).numpy()
            actual=np.array([single(wp,row.ctypes.data_as(bp),int(v),float(a)) for row,v,a in zip(x,h,z)])
            assert np.isfinite(actual).all() and np.max(abs(actual-z))<=2+2e-6
            assert np.max(abs(actual-p))<2e-5
            return packed,p,actual
        packed,neutral,actual=evaluate();assert np.array_equal(neutral,z) and np.array_equal(actual,z)
        # Neutral initialization must still allow the output layer to learn.
        model.train();loss=torch.nn.functional.binary_cross_entropy_with_logits(model(tx[:32],th[:32],tz[:32]),torch.zeros(32))
        loss.backward();assert model.output.weight.grad.abs().sum()>0
        assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
        with torch.no_grad():model.output.weight.normal_(std=.1);model.output.bias.normal_(std=.1)
        model.eval();packed,p,actual=evaluate();nonzero_error=float(np.max(abs(actual-p)))
        assert np.max(abs(actual-z))>.01
        wp=packed.ctypes.data_as(fp);samples=[];xp=x.ctypes.data_as(bp);hp=h.ctypes.data_as(bp);zp=z.ctypes.data_as(fp)
        batch(wp,xp,hp,zp,len(x),3)
        for _ in range(7):
            start=time.perf_counter();batch(wp,xp,hp,zp,len(x),20)
            samples.append(1e6*(time.perf_counter()-start)/(len(x)*20))
        packed.tofile(HERE/'build'/(kind+'.weights.bin'));expected_sum+=actual.sum()
        native[kind]=dict(parameters=sum(p.numel() for p in model.parameters()),export_bytes=packed.nbytes,
            neutral_exact=True,nonzero_max_logit_error=nonzero_error,microseconds=samples,median_microseconds=float(np.median(samples)),
            time_pass=bool(np.median(samples)<=50),size_pass=packed.nbytes<=1048576)
        with torch.no_grad():model.output.bias.copy_(torch.tensor([-1000.,1000.]))
        _,p,actual=evaluate();native[kind]['extreme_max_logit_error']=float(np.max(abs(actual-p)))
    # Independent analytic gradient of the bounded two-head combination.
    a=torch.tensor(rng.normal(size=(37,2)),dtype=torch.float64,requires_grad=True)
    v=torch.tensor(rng.normal(size=37)*5,dtype=torch.float64);combine(a,v).sum().backward()
    s=np.clip(v.numpy()/4,-1,1);u=(a.detach().numpy()[:,0]+a.detach().numpy()[:,1]*s)/2
    deriv=1-np.tanh(u)**2;expected=np.stack([deriv,deriv*s],axis=1)
    gradient_error=float(np.max(abs(a.grad.numpy()-expected)));assert gradient_error<1e-12
    x.tofile(HERE/'build/x.bin');h.tofile(HERE/'build/h.bin');z.tofile(HERE/'build/z.bin')
    driver='''#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <math.h>
size_t fow_residual_query_floats(void);
float fow_residual_query_logit(const float*,const uint8_t*,uint8_t,float);
float fow_residual_flat_logit(const float*,const uint8_t*,uint8_t,float);
int main(int argc,char **argv){
 if(argc!=6)return 2;FILE *f[5];for(int i=0;i<5;i++){f[i]=fopen(argv[i+1],"rb");if(!f[i])return 3;}
 size_t sizes[2]={160098,fow_residual_query_floats()};float *w[2];
 for(int i=0;i<2;i++){w[i]=malloc(sizes[i]*4);if(!w[i]||fread(w[i],4,sizes[i],f[i])!=sizes[i])return 4;}
 uint8_t x[320],h;float z;int count=0;double sum=0;
 while(fread(x,1,320,f[2])==320){if(fread(&h,1,1,f[3])!=1||fread(&z,4,1,f[4])!=1)return 5;
 float a=fow_residual_flat_logit(w[0],x,h,z),b=fow_residual_query_logit(w[1],x,h,z);
 if(!isfinite(a)||!isfinite(b))return 6;sum+=a+b;count++;}
 free(w[0]);free(w[1]);for(int i=0;i<5;i++)fclose(f[i]);printf("%d %.12f\\n",count,sum);return count==256?0:7;
}
'''
    (HERE/'build/sanity.c').write_text(driver)
    command=['gcc','-std=c11','-O1','-g','-fsanitize=address,undefined',str(HERE/'build/sanity.c'),
        str(HERE/'build/flat.c'),str(HERE/'build/query.c'),'-lm','-o',str(HERE/'build/sanity')]
    r=subprocess.run(command,capture_output=True,text=True);assert r.returncode==0,r.stderr
    r=subprocess.run([str(HERE/'build/sanity'),*[str(HERE/'build'/p) for p in ('flat.weights.bin','query.weights.bin','x.bin','h.bin','z.bin')]],capture_output=True,text=True)
    assert r.returncode==0,(r.returncode,r.stdout,r.stderr)
    # The sanitizer sums a+b in float; its checksum differs only by summation rounding.
    assert abs(float(r.stdout.split()[1])-expected_sum)<1e-4
    result=dict(at=now(),native=native,gradient_max_error=gradient_error,sanitizer=dict(command=command,exit=r.returncode,stdout=r.stdout,stderr=r.stderr),
        compiler=cmd,sources={str(p):sha(p) for p in [HERE/'models.py',HERE/'native.py',HERE/'preflight.py',HERE/'build/flat.c',HERE/'build/query.c',library]},
        passed=all(v['time_pass'] and v['size_pass'] for v in native.values()),
        scope='Untrained neutral/random/extreme heads; arithmetic, gradients, sanitizers and native one-core inference. No fit or model-quality score.')
    write_new(OUT/'preflight.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':main()
