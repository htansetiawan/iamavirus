"""Frozen unchanged-checkpoint, label-free reference conformance; no fitting."""
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import uuid

import numpy as np
import torch
from torch.nn.attention import SDPBackend,sdpa_kernel

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/quiet-teacher-reference-20261110'
sys.path.insert(0,str(HERE.parent/'world-quiet-attention-20261110'))
from model import WorldQuietTeacher,quiet_logp
from inputs import Inputs,move_to
from reference import forward
sys.path.insert(0,str(HERE.parent/'quiet-teacher-numerics-20261110'))
from diagnose import probe,lease


def now():return datetime.now(timezone.utc).isoformat()
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
def difference(a,b):return float(abs(a.astype(np.float64)-b.astype(np.float64)).max(initial=0))


@torch.no_grad()
def predict(model,batch,profile=False):
    operations=[]
    if profile:
        with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as prof:
            residual=forward(model,*batch['board'],batch['moves'],batch['x'])
        operations=sorted({event.key for event in prof.key_averages()})
    else:residual=forward(model,*batch['board'],batch['moves'],batch['x'])
    lp=quiet_logp(batch['base'],residual,batch['valid'],batch['capture'],batch['counts'],batch['history_n'])
    baseline=quiet_logp(batch['base'],torch.zeros_like(residual),batch['valid'],batch['capture'],batch['counts'],batch['history_n'])
    valid=batch['valid'];capture=batch['capture'][valid]
    assert torch.isfinite(residual[valid]).all() and torch.isfinite(lp[valid]).all()
    assert torch.equal(lp[valid][capture],baseline[valid][capture])
    return dict(residual=residual[valid].cpu().numpy(),logp=lp[valid].cpu().numpy(),baseline=baseline[valid].cpu().numpy(),capture=capture.cpu().numpy()),operations


def measure(plan):
    fit=json.loads(Path(plan['fit_plan']).read_text());source=Inputs(fit)
    assert len(source.indices)==plan['train_contexts']
    assert hashlib.sha256(source.indices.astype('<i8').tobytes()).hexdigest()==plan['train_context_indices_sha256']
    state=torch.load(plan['checkpoint'],map_location='cpu',weights_only=True)
    models={device:WorldQuietTeacher(**fit['architecture']).to(device).eval() for device in ('cpu','cuda')}
    for model in models.values():model.load_state_dict(state)
    assert torch.backends.mha.get_fastpath_enabled(),'test must keep global module fastpath enabled'
    private=OUT/'private';private.mkdir(exist_ok=False)
    canonical=np.lib.format.open_memmap(private/'canonical.npy',mode='w+',dtype=np.float32,shape=(len(source.prior.rows),2));canonical[:]=np.nan
    records=[];maximum=dict(cpu_gpu_residual=0.,cpu_gpu_logp=0.,batch_residual=0.,batch_logp=0.,diagnostic_residual=0.,diagnostic_logp=0.)
    operations={};actions={};capture_actions={};started=time.monotonic()
    old=np.load(plan['diagnostic_arrays'],allow_pickle=False)
    # Original324 controls were the same390fit-TRAIN inputs, with MHA flag off.
    # This implementation must match them with MHA still globally enabled.
    for label,lo,hi in [('b256',0,256),('b134',256,390),('b1',0,1)]:
        for device in ('cpu','cuda'):
            batch,_=source.batch(source.indices[lo:hi],device)
            pred,ops=predict(models[device],batch,profile=label=='b256')
            if ops:
                operations[device]=ops
                assert all(key not in ops for key in ('aten::_transformer_encoder_layer_fwd','aten::_native_multi_head_attention','aten::_addmm_activation'))
                assert 'aten::_scaled_dot_product_attention_math' in ops and 'aten::gelu' in ops
            for kind in ('residual','logp'):
                delta=difference(pred[kind],old['math-erf-f32_'+device+'_'+label+'_'+kind])
                maximum['diagnostic_'+kind]=max(maximum['diagnostic_'+kind],delta)
                assert delta<plan['tolerance'],('324 reference mismatch',device,label,kind,delta)
    # Original grad-enabled FP64 implementation is an independent graph control.
    model64=WorldQuietTeacher(**fit['architecture']).double().eval();model64.load_state_dict(state)
    small,_=source.batch(source.indices[:64]);small=move_to(small,dtype=torch.float64)
    explicit=forward(model64,*small['board'],small['moves'],small['x'])
    with torch.enable_grad(),sdpa_kernel(SDPBackend.MATH):
        original=model64(*small['board'],small['moves'],small['x']).detach()
    grad_reference_error=float((explicit-original).abs().max())
    assert grad_reference_error<plan['float64_tolerance']
    del model64
    for width in plan['full_pass_batch_sizes']+[1]:
        selected=source.indices if width!=1 else source.indices[np.asarray(plan['singleton_offsets'])]
        name='b'+str(width);actions[name]=0;capture_actions[name]=0
        for index,start in enumerate(range(0,len(selected),width)):
            indices=selected[start:start+width]
            trim=int(source.context[indices]['count'].max()) if width==1 else None
            cpu,positions=source.batch(indices,width=trim);gpu=move_to(cpu,device='cuda')
            cp,_=predict(models['cpu'],cpu);gp,_=predict(models['cuda'],gpu)
            for kind in ('residual','logp'):
                delta=difference(cp[kind],gp[kind]);maximum['cpu_gpu_'+kind]=max(maximum['cpu_gpu_'+kind],delta)
                assert delta<plan['tolerance'],('CPU/GPU',name,index,kind,delta)
            if width==plan['full_pass_batch_sizes'][0]:
                canonical[positions,0]=cp['residual'];canonical[positions,1]=cp['logp']
            else:
                for column,kind in enumerate(('residual','logp')):
                    assert np.isfinite(canonical[positions,column]).all()
                    delta=difference(cp[kind],canonical[positions,column]);maximum['batch_'+kind]=max(maximum['batch_'+kind],delta)
                    assert delta<plan['tolerance'],('batch shape',name,index,kind,delta)
            file=private/(name+'-'+str(index).zfill(4)+'.npz')
            np.savez_compressed(file,indices=indices,positions=positions,**{'cpu_'+k:v for k,v in cp.items()},**{'cuda_'+k:v for k,v in gp.items()})
            records.append(dict(name=name,index=index,contexts=len(indices),actions=len(positions),file=file.name,sha256=sha(file)))
            actions[name]+=len(positions);capture_actions[name]+=int(cp['capture'].sum())
            if index%32==0:print(json.dumps(dict(pass_name=name,completed_contexts=min(start+width,len(selected)),total_contexts=len(selected))),flush=True)
    canonical.flush()
    assert torch.backends.mha.get_fastpath_enabled(),'process-wide MHA flag was modified'
    for model in models.values():
        assert all(torch.equal(value.cpu(),state[key]) for key,value in model.state_dict().items()),'weights changed'
    assert sha(plan['checkpoint'])==plan['dependencies'][plan['checkpoint']]
    assert sum(p.stat().st_size for p in private.iterdir())<plan['max_private_bytes']
    save(private/'batch-receipts.json',records)
    report=dict(at=now(),train_contexts=len(source.indices),passes=plan['full_pass_batch_sizes'],singletons=len(plan['singleton_offsets']),
        actions=actions,capture_actions=capture_actions,maximum_errors=maximum,float64_grad_reference_error=grad_reference_error,
        unchanged_checkpoint=True,global_mha_flag_unchanged=True,operations=operations,peak_torch_gpu_bytes=torch.cuda.max_memory_allocated(),
        seconds=time.monotonic()-started,private_files=len(records),private_bytes=sum(p.stat().st_size for p in private.iterdir()),
        batch_receipts_sha256=sha(private/'batch-receipts.json'),canonical_sha256=sha(private/'canonical.npy'),
        torch_version=torch.__version__,torch_git=torch.version.git_version,
        precision=dict(matmul=torch.get_float32_matmul_precision(),cuda_tf32=torch.backends.cuda.matmul.allow_tf32,cudnn_tf32=torch.backends.cudnn.allow_tf32),
        decision='numerical_conformance_passed_independent_audit_required',scope=plan['scope'])
    assert report['peak_torch_gpu_bytes']<plan['max_gpu_bytes']
    save(OUT/'result.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='operations'},indent=2),flush=True)


def main():
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('fixed15minute conformance bound')));signal.alarm(900)
    plan=json.loads((OUT/'plan.json').read_text());assert not (OUT/'started.json').exists()
    for path,expected in plan['dependencies'].items():assert sha(path)==expected,path
    checks=[probe()]
    if checks[0]['free']:time.sleep(5);checks.append(probe())
    save(OUT/'gpu-admission.json',dict(checks=checks,services_stopped=False))
    if len(checks)!=2 or not all(c['free'] for c in checks):print('GPU busy; no trained inference attempted');return
    ident=uuid.uuid4().hex;lease(ident);started=time.monotonic()
    execution=dict(status='running',started_at=now(),lease=ident,source_publication=os.environ['ASTRA_SOURCE_PUBLICATION'])
    save(OUT/'started.json',execution)
    try:
        os.sched_setaffinity(0,{2,3});torch.set_num_threads(2)
        torch.set_float32_matmul_precision('highest');torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        measure(plan)
        spec=importlib.util.spec_from_file_location('reference_independent_review',HERE/'review.py')
        review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
        review.main()
        save(OUT/'final-decision.json',dict(at=now(),decision='held_out_prediction_design_allowed',teacher_qualified=False,
             old320failure_reclassified=False,checkpoint_changed=False,scope='Numerical implementation conformance only. Separately freeze fresh prediction inputs and gates before scoring; no student, native, posterior, ZIP or arena promotion.'))
        execution.update(status='complete')
    except BaseException as exc:execution.update(status='failed',error=repr(exc));raise
    finally:
        lease(ident,remove=True);execution.update(ended_at=now(),seconds=time.monotonic()-started,own_lease_released=True)
        save(OUT/'runner-execution.json',execution)


if __name__=='__main__':main()
