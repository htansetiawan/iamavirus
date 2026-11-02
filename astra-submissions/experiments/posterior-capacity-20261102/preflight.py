"""Synthetic algebra and native portability checks. No fit and no test games."""
import ctypes
import json
import time
import numpy as np
import torch
from settings import HERE
from quadratic import Residual,mask_array


def main():
    torch.set_num_threads(2)
    rng=np.random.default_rng(2321102)
    x=rng.uniform(-1,1,(71,26)); x[rng.random(x.shape)<.7]=0
    linear=rng.normal(0,.1,26);q=rng.normal(0,.1,(26,26))*mask_array()
    model=Residual('quadratic','cpu')
    with torch.no_grad():model.linear.copy_(torch.from_numpy(linear));model.q.copy_(torch.from_numpy(q))
    tx=torch.from_numpy(x);actual=model(tx)
    i,j=np.nonzero(mask_array())
    reference=(tx*torch.from_numpy(linear)).sum(1)+(tx[:,i]*tx[:,j]*model.q[i,j]).sum(1)
    error=float((actual-reference).abs().max().detach())
    a=torch.autograd.grad(actual.sum(),model.q,retain_graph=True)[0]
    b=torch.autograd.grad(reference.sum(),model.q)[0]
    gradient=float((a-b).abs().max());assert max(error,gradient)<1e-12
    lib=ctypes.CDLL(str(HERE/'build/residual.so'))
    ptr=np.ctypeslib.ndpointer(dtype=np.float32,flags='C_CONTIGUOUS')
    lib.residual_logits.argtypes=[ptr,ptr,ctypes.c_int,ptr,ptr,ptr]
    xf=x.astype(np.float32);base=rng.normal(size=len(x)).astype(np.float32);out=np.empty_like(base)
    lin=linear.astype(np.float32);quad=q.astype(np.float32)
    lib.residual_logits(xf,base,len(x),np.zeros(26,np.float32),np.zeros((26,26),np.float32),out)
    assert np.array_equal(out,base)
    lib.residual_logits(xf,base,len(x),lin,quad,out)
    native_error=float(np.max(np.abs(out-(base+xf.astype(float)@lin.astype(float)+np.einsum('ni,ij,nj->n',xf.astype(float),quad.astype(float),xf.astype(float))))))
    assert native_error<2e-5
    # Bound feasibility using synthetic rows, without reading held-out labels or optimizing coefficients.
    bench=torch.randn((200000,26),dtype=torch.float64);started=time.monotonic()
    for _ in range(5):
        model.zero_grad();model(bench).square().mean().backward()
    elapsed=time.monotonic()-started
    print(json.dumps(dict(value_error=error,gradient_error=gradient,native_float_error=native_error,
                         zero_residual_bitwise=True,active_coefficients=26+int(mask_array().sum()),
                         synthetic_rows=200000,five_forward_backward_seconds=elapsed,no_fit=True)))


if __name__=='__main__':main()
