"""Check export arithmetic and single-core cost before spending GPU time.

This smoke uses seeded random weights, not a trained outcome predictor.
"""
import ctypes
import json
import subprocess
import time

import numpy as np
import torch

from data import HERE,OUT,now,sha,write_new
from models import Student

ORDER=('piece.weight','vision.weight','castle.weight','ep.weight','bias','half_weight',
       'hidden.weight','hidden.bias','output.weight','output.bias')


def main():
    torch.set_num_threads(1);torch.manual_seed(2371102)
    libpath=HERE/'build/student.so'
    cmd=['gcc','-std=c11','-O3','-shared','-fPIC',str(HERE/'student_infer.c'),'-o',str(libpath)]
    r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
    net=Student().eval();state=net.state_dict()
    packed=np.concatenate([state[k].detach().numpy().reshape(-1) for k in ORDER]).astype(np.float32)
    assert len(packed)==160065
    rng=np.random.default_rng(2371102)
    x=np.zeros((256,64,5),dtype=np.uint8);x[:,:,0]=rng.integers(0,13,size=(256,64))
    x[:,:,1:]=rng.integers(0,2,size=(256,64,4));h=rng.integers(0,101,size=256,dtype=np.uint8)
    pilot=np.load(HERE/'work/pilot/data.npz');x[:len(pilot['x'])]=pilot['x'];h[:len(pilot['half'])]=pilot['half']
    lib=ctypes.CDLL(str(libpath));fp=ctypes.POINTER(ctypes.c_float);bp=ctypes.POINTER(ctypes.c_uint8)
    lib.fow_student_logit.argtypes=[fp,bp,ctypes.c_uint8];lib.fow_student_logit.restype=ctypes.c_float
    lib.fow_student_batch.argtypes=[fp,bp,bp,ctypes.c_int,ctypes.c_int];lib.fow_student_batch.restype=ctypes.c_double
    wp=packed.ctypes.data_as(fp)
    with torch.no_grad():expected=net(torch.tensor(x,dtype=torch.long),torch.tensor(h,dtype=torch.float32)).numpy()
    actual=np.array([lib.fow_student_logit(wp,row.ctypes.data_as(bp),int(v)) for row,v in zip(x,h)])
    error=float(np.max(np.abs(actual-expected)));assert error<2e-5,error
    samples=[];checks=[]
    for _ in range(7):
        begin=time.perf_counter();checksum=lib.fow_student_batch(wp,x.ctypes.data_as(bp),h.ctypes.data_as(bp),len(x),100)
        samples.append(1e6*(time.perf_counter()-begin)/(len(x)*100));checks.append(checksum)
    assert max(checks)-min(checks)<1e-8
    result=dict(at=now(),trained=False,parameters=len(packed),fp32_bytes=packed.nbytes,positions=len(x),
        max_logit_error=error,microseconds_per_position=samples,median_microseconds=float(np.median(samples)),
        timing_gate_met=float(np.median(samples))<=25,compiler=cmd,
        sources={p.name:sha(p) for p in [HERE/'student_infer.c',HERE/'native_check.py',HERE/'models.py',libpath]},
        scope='Seeded random weights, cached native single-core scalar calls (no Python per evaluation in timing); includes 24 real pilot inputs. Not model quality, end-to-end search speed or arena timing.')
    write_new(OUT/'native-preflight.json',result);print(json.dumps(result))


if __name__=='__main__':main()
