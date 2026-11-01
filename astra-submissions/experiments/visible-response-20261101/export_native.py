#!/usr/bin/env python3
"""Freeze learned weights, compare native sparse inference with FP32 PyTorch."""
import ctypes
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import time

import numpy as np
import torch

import data
from model import StudentPolicy

ORDER=['board.0.weight','board.0.bias','board.2.weight','board.2.bias',
       'action.0.weight','action.0.bias','action.2.weight','action.2.bias']


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    torch.set_num_threads(1)
    assert json.loads((data.OUT/'training-execution.json').read_text())['status']=='complete'
    decision=json.loads((data.OUT/'decision.json').read_text()); assert decision['decision']=='native_prototype_allowed'
    frozen=json.loads((data.OUT/'frozen-models.json').read_text());name=frozen['chosen']
    assert sha(data.BUILD/(name+'.pt'))==frozen['models'][name]['sha256']
    directory=data.OUT/'models';directory.mkdir(exist_ok=True)
    # Preserve all four research checkpoints in non-executable NumPy format.
    archives={}
    for key,record in frozen['models'].items():
        source=data.BUILD/(key+'.pt');assert sha(source)==record['sha256']
        state=torch.load(source,map_location='cpu',weights_only=True)
        target=directory/(key+'.npz');assert not target.exists()
        np.savez_compressed(target,**{k:v.numpy() for k,v in state.items()})
        archives[key]=dict(sha256=sha(target),bytes=target.stat().st_size)
    state=torch.load(data.BUILD/(name+'.pt'),map_location='cpu',weights_only=True)
    w=np.concatenate([state[key].numpy().ravel() for key in ORDER]).astype('<f4')
    assert len(w)==68417
    target=directory/'response.bin';target.write_bytes(b'ASTRARP1'+struct.pack('<II',1,len(w))+w.tobytes())
    command=['gcc','-O3','-std=c11','-shared','-fPIC',str(data.HERE/'response.c'),'-lm','-o',str(data.BUILD/'response.so')]
    subprocess.run(command,check=True)
    lib=ctypes.CDLL(str(data.BUILD/'response.so'))
    f32=np.ctypeslib.ndpointer(dtype=np.float32,flags='C_CONTIGUOUS')
    u8=np.ctypeslib.ndpointer(dtype=np.uint8,flags='C_CONTIGUOUS');u16=np.ctypeslib.ndpointer(dtype=np.uint16,flags='C_CONTIGUOUS')
    f64=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    lib.astra_response_logits.argtypes=[f32,u8,u16,ctypes.c_int,f32]
    lib.astra_response_probs.argtypes=[f32,u8,u16,ctypes.c_int,f64]
    net=StudentPolicy().eval();net.load_state_dict(state)
    raw=np.load(data.BUILD/'validation.npz');idx=np.random.default_rng(2081102).choice(len(raw['target']),1024,replace=False)
    max_logits=max_probs=0.;times=[];queries=[]
    for index in idx:
        tokens=raw['tokens'][index];moves=raw['actions'][int(raw['offsets'][index]):int(raw['offsets'][index+1])]
        output=np.zeros(len(moves),np.float32);prob=np.zeros(len(moves),np.float64)
        assert lib.astra_response_logits(w,tokens,moves,len(moves),output)==1
        assert lib.astra_response_probs(w,tokens,moves,len(moves),prob)==1
        with torch.no_grad():
            expected=net(torch.from_numpy(tokens.astype(np.int64))[None],torch.from_numpy(moves.astype(np.int64))[None])[0].numpy()
        expected_prob=np.exp(expected.astype(np.float64)-expected.max());expected_prob/=expected_prob.sum()
        max_logits=max(max_logits,float(abs(output-expected).max()));max_probs=max(max_probs,float(abs(prob-expected_prob).max()))
        assert abs(prob.sum()-1)<1e-12
        queries.append((tokens,moves,prob))
    assert max_logits<2e-4 and max_probs<2e-5,(max_logits,max_probs)
    for tokens,moves,prob in queries:
        start=time.perf_counter_ns()
        for _ in range(20):assert lib.astra_response_probs(w,tokens,moves,len(moves),prob)==1
        times.append((time.perf_counter_ns()-start)/20/1000)
    record=dict(chosen=name,parameters=len(w),model_bytes=target.stat().st_size,model_sha256=sha(target),
                archives=archives,compiler=command,library_sha256=sha(data.BUILD/'response.so'),
                queries=1024,max_logit_error=max_logits,max_probability_error=max_probs,
                median_query_microseconds=float(np.median(times)),p95_query_microseconds=float(np.quantile(times,.95)),
                median_candidates=float(np.median([len(q[1]) for q in queries])),max_candidates=max(len(q[1]) for q in queries),
                timing_scope='CPU0, one thread, batch1; includes Python ctypes call overhead; not an arena throughput measurement.',
                arithmetic='Sparse one-hot gather and shared board contribution; no quantization or model-weight change.',
                source_sha256={str(p.relative_to(data.ROOT)):sha(p) for p in [data.HERE/'response.c',data.HERE/'response.h',Path(__file__)]})
    (data.OUT/'native-parity.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))


if __name__=='__main__':main()
