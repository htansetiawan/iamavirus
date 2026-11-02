"""Untrained export correctness and one-core runtime, before GPU fitting."""
import ctypes
import json
import os
import subprocess
import time
import numpy as np
import torch

from common import HERE, OUT, OLD, now, sha, write_new
from models import QueryStudent, pack_native


def main():
    os.sched_setaffinity(0, {0})
    torch.set_num_threads(1)
    build = HERE / 'build'; build.mkdir(exist_ok=True)
    libpath = build / 'query.so'
    cmd = ['gcc', '-std=c11', '-O3', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
           str(HERE / 'query_infer.c'), '-lm', '-o', str(libpath)]
    r = subprocess.run(cmd, capture_output=True, text=True); assert r.returncode == 0, r.stderr
    lib = ctypes.CDLL(str(libpath)); fp = ctypes.POINTER(ctypes.c_float); bp = ctypes.POINTER(ctypes.c_uint8)
    lib.fow_query_floats.restype = ctypes.c_size_t
    lib.fow_query_logit.argtypes = [fp, bp, ctypes.c_uint8]; lib.fow_query_logit.restype = ctypes.c_float
    lib.fow_query_batch.argtypes = [fp, bp, bp, ctypes.c_int, ctypes.c_int]; lib.fow_query_batch.restype = ctypes.c_double
    rng = np.random.default_rng(2381102)
    x = np.zeros((320, 64, 5), dtype=np.uint8)
    x[:, :, 0] = rng.choice(np.array([0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11]), size=(320, 64))
    x[:, :, 1:] = rng.integers(0, 2, size=(320, 64, 4))
    for row in x:
        a, b = rng.choice(64, 2, replace=False); row[a, 0] = 6; row[b, 0] = 12
    h = rng.integers(0, 101, size=320, dtype=np.uint8)
    d = np.load(OLD / 'work/dataset/data.npz'); ii = np.flatnonzero(d['fold'] == 0)[:64]
    x[:64] = d['x'][ii]; h[:64] = d['half'][ii]
    xp=x.ctypes.data_as(bp); hp=h.ctypes.data_as(bp)
    errors=[]
    for seed in (2381102, 2381103):
        torch.manual_seed(seed); net=QueryStudent().eval()
        # Exercise the halfmove path too; its training initialization is zero.
        with torch.no_grad(): net.half_weight.normal_(std=.05)
        packed=pack_native(net); assert len(packed)==lib.fow_query_floats(),(len(packed),lib.fow_query_floats())
        wp=packed.ctypes.data_as(fp)
        with torch.no_grad(): expected=net(torch.tensor(x,dtype=torch.long),torch.tensor(h,dtype=torch.float32)).numpy()
        actual=np.array([lib.fow_query_logit(wp,row.ctypes.data_as(bp),int(v)) for row,v in zip(x,h)])
        error=float(np.max(np.abs(actual-expected))); errors.append(error)
        assert np.isfinite(actual).all() and error<=2e-5,error
    packed.tofile(build/'preflight.fp32.bin')
    np.concatenate([x.reshape(len(x),-1),h[:,None]],axis=1).tofile(build/'preflight.inputs.bin')
    driver='''#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "../query_infer.c"
int main(int argc,char **argv) {
 if(argc!=3)return 2;
 FILE *a=fopen(argv[1],"rb"),*b=fopen(argv[2],"rb");if(!a||!b)return 3;
 size_t n=fow_query_floats();float *w=malloc(n*sizeof(float));
 if(!w||fread(w,sizeof(float),n,a)!=n)return 4;
 unsigned char row[321];int count=0;double sum=0;
 while(fread(row,1,sizeof(row),b)==sizeof(row)){
  float v=fow_query_logit(w,row,row[320]);if(!isfinite(v))return 5;sum+=v;count++;
 }
 printf("%d %.12f\\n",count,sum);free(w);fclose(a);fclose(b);return count==320?0:6;
}
'''
    (build/'sanity.c').write_text(driver)
    san=['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
         str(build/'sanity.c'),'-lm','-o',str(build/'sanity')]
    sr=subprocess.run(san,capture_output=True,text=True);assert sr.returncode==0,sr.stderr
    sr=subprocess.run([str(build/'sanity'),str(build/'preflight.fp32.bin'),str(build/'preflight.inputs.bin')],capture_output=True,text=True)
    assert sr.returncode==0,(sr.returncode,sr.stdout,sr.stderr)
    assert abs(float(sr.stdout.split()[1])-actual.sum())<1e-4,sr.stdout
    # Native loop prevents Python call overhead from dominating timing.
    lib.fow_query_batch(wp,xp,hp,len(x),3)
    timings=[];checks=[]
    for _ in range(7):
        start=time.perf_counter();checks.append(lib.fow_query_batch(wp,xp,hp,len(x),30))
        timings.append(1e6*(time.perf_counter()-start)/(len(x)*30))
    assert max(checks)-min(checks)<1e-8
    result=dict(at=now(),trained=False,parameters=sum(p.numel() for p in net.parameters()),
        export_floats=len(packed),export_bytes=packed.nbytes,positions=len(x),real_training_positions=64,
        cpu_affinity=sorted(os.sched_getaffinity(0)),max_logit_errors=errors,
        timings_microseconds=timings,median_microseconds=float(np.median(timings)),
        gates=dict(parity=max(errors)<=2e-5,size=packed.nbytes<=1048576,time=np.median(timings)<=50),
        sanitizer=dict(command=san,exit=sr.returncode,stdout=sr.stdout,stderr=sr.stderr),compiler=cmd,
        sources={p.name:sha(p) for p in [HERE/'models.py',HERE/'query_infer.c',HERE/'native_check.py',libpath]},
        scope='Two untrained weight seeds; folded native forward parity, sanitizers and one-core cached inference. Excludes feature encoding and search; not playing strength.')
    result['gates']={k:bool(v) for k,v in result['gates'].items()}
    write_new(OUT/'native-preflight.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':main()
