"""Constrained conditional logit: only odds BETWEEN non-captures can change."""
import torch

COLUMNS=tuple(range(3,16))+tuple(range(17,26))
CONTINUOUS={12,14,21,23,24}

def mask(F):
    m=torch.triu(torch.ones(F,F),diagonal=1)
    for i,col in enumerate(COLUMNS[:F]):
        if col in CONTINUOUS:m[i,i]=1
    return m

def logp(data,idx,F,linear,quadratic):
    x=data['x'][idx][:,:,COLUMNS[:F]]
    base=data['base'][idx,:,0 if F==14 else 1]
    valid=data['valid'][idx];quiet=valid & ~data['capture'][idx]
    lp0=base.masked_fill(~valid,-torch.inf).log_softmax(-1)
    safe=quiet.clone();safe[~quiet.any(-1),0]=True
    delta=x@linear+torch.sum((x@quadratic)*x,dim=-1)
    old_mass=base.masked_fill(~safe,-torch.inf).logsumexp(-1,keepdim=True)
    new_mass=(base+delta).masked_fill(~safe,-torch.inf).logsumexp(-1,keepdim=True)
    correction=old_mass-new_mass
    use=quiet & (quiet.sum(-1,keepdim=True)>1)
    result=torch.where(use,lp0+delta+correction,lp0)
    # Original deployed empirical-history mixture; N may exceed counts.sum().
    counts=data['counts'][idx];N=data['history_n'][idx,None]
    # Avoid logaddexp(-inf,-inf) at padding: even a zero upstream gradient
    # can otherwise multiply its undefined derivative and contaminate a fit.
    safe_result=result.masked_fill(~valid,0)
    log_count=torch.where(valid,counts.log(),torch.zeros_like(counts))
    blended=torch.logaddexp(log_count,safe_result+torch.log(torch.tensor(4.0)))-(N+4).log()
    return torch.where(valid,torch.where(N>=3,blended,result),-torch.inf)

def synthetic_checks():
    torch.manual_seed(2931100)
    n,width=19,31
    data=dict(x=torch.rand(n,width,26),base=torch.randn(n,width,2),valid=torch.ones(n,width,dtype=torch.bool),
              capture=torch.rand(n,width)>.6,counts=torch.zeros(n,width),history_n=torch.zeros(n))
    data['capture'][0]=True;data['capture'][1]=False;data['capture'][2]=True;data['capture'][2,0]=False
    data['counts'][3:6]=torch.randint(0,3,(3,width)).float();data['history_n'][3:6]=data['counts'][3:6].sum(-1)+10
    data['valid'][3:6,-5:]=False
    idx=torch.arange(n);reports=[]
    for F in (14,22):
        zero=torch.zeros(F);zq=torch.zeros(F,F);baseline=logp(data,idx,F,zero,zq)
        lin=torch.randn(F,requires_grad=True);q=torch.randn(F,F,requires_grad=True)
        changed=logp(data,idx,F,lin,q*mask(F))
        assert torch.equal(changed[data['capture']],baseline[data['capture']])
        assert torch.isfinite(changed[data['valid']]).all()
        assert torch.equal(changed[:1],baseline[:1]) and torch.equal(changed[2:3],baseline[2:3])
        loss=changed[data['capture'] & data['valid']].sum();loss.backward()
        assert torch.count_nonzero(lin.grad)==0 and torch.count_nonzero(q.grad)==0
        reports.append(dict(features=F,capture_logp_bitwise=True,capture_gradient_zero=True,
                            no_quiet_and_singleton_identity=True,history_blend_preserved=True))
    return reports
