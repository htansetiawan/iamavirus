"""One fixed CPU prediction pass after source sealing; no refit/GPU/arena write."""
import ctypes
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import numpy as np
import torch

from protocol import ROOT,OUT,OLD,now,sha,write,check_pins,summarize,gate_result
from features import Producer,batch
# prepare.py already imports293's module named model. Load the teacher under
# an explicit independent name so Python's module cache cannot alias them.
spec=importlib.util.spec_from_file_location('confirmed_world_architecture',OLD.parent/'world-quiet-attention-20261110/model.py')
world_model=importlib.util.module_from_spec(spec);spec.loader.exec_module(world_model)
WorldQuietTeacher,quiet_logp=world_model.WorldQuietTeacher,world_model.quiet_logp
from model import COLUMNS,mask

class ScalarResidual(torch.nn.Module):
    def __init__(self,kind):
        super().__init__();self.linear=torch.nn.Parameter(torch.zeros(22))
        self.quadratic=torch.nn.Parameter(torch.zeros(22,22),requires_grad=kind=='quadratic')
        self.register_buffer('mask',mask(22))
    def forward(self,b):
        x=b['x'][:,:,COLUMNS]
        return x@self.linear+((x@(self.quadratic*self.mask))*x).sum(-1)
sys.path.insert(0,str(OLD.parent/'quiet-teacher-reference-20261110'))
from reference import forward


def load_models(plan):
    teacher=WorldQuietTeacher(**plan['architecture']).eval()
    teacher.load_state_dict(torch.load(plan['weights']['teacher'],map_location='cpu',weights_only=True))
    models={'teacher':teacher}
    for kind in ('linear','quadratic'):
        model=ScalarResidual(kind).eval();model.load_state_dict(torch.load(plan['weights'][kind],map_location='cpu',weights_only=True));models[kind]=model
    models['production']=ScalarResidual('quadratic').eval()
    original=json.loads(Path(plan['weights']['production']).read_text())
    with torch.no_grad():
        models['production'].linear.copy_(torch.tensor(original['linear']))
        models['production'].quadratic.copy_(torch.tensor(original['quadratic']))
    return models


@torch.no_grad()
def predictions(models,b):
    lp={};residual={}
    for kind in ('base','linear','quadratic','production','teacher'):
        delta=torch.zeros_like(b['base']) if kind=='base' else forward(models[kind],*b['board'],b['moves'],b['x']) if kind=='teacher' else models[kind](b)
        residual[kind]=delta
        lp[kind]=quiet_logp(b['base'],delta,b['valid'],b['capture'],b['counts'],b['history_n'])
        assert torch.isfinite(lp[kind][b['valid']]).all()
    capture=b['valid']&b['capture']
    assert all(torch.equal(value[capture],lp['base'][capture]) for value in lp.values())
    return lp,residual


def main():
    started=time.monotonic();plan=json.loads((OUT/'plan.json').read_text());check_pins(plan)
    assert torch.__version__==plan['torch_version']
    assert torch.version.git_version==plan['torch_git']
    source=json.loads((OUT/'source-audit.json').read_text());cohort=json.loads((OUT/'cohort.json').read_text())
    assert source['passed'] and source['cohort_sha256']==sha(OUT/'cohort.json')
    assert not (OUT/'scoring.json').exists()
    os.sched_setaffinity(0,set(plan['cores']));torch.set_num_threads(2);torch.set_float32_matmul_precision('highest')
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('fixed30minute CPU scoring bound')));signal.alarm(1800)
    receipt=dict(status='running',started_at=now(),cohort_sha256=sha(OUT/'cohort.json'));write(OUT/'scoring.json',receipt,exclusive=True)
    private=Path(plan['archive'])/'private';private.mkdir(exist_ok=False)
    try:
        producer=Producer(plan['native_state_library']);rows=[];metadata=[];digest=hashlib.sha256();frames=0
        for g in cohort['games']:
            path=Path(plan['archive'])/'games'/g['game']/'replay.json';assert sha(path)==g['replay_sha256']
            replay=json.loads(path.read_bytes())
            for inputs,meta in producer.game(g,replay):
                for v in inputs['board']+[inputs[k] for k in ('x','base','counts','moves','history_n')]:digest.update(np.asarray(v).tobytes())
                rows.append(inputs);metadata.append(meta)
            frames+=g['frames']
        models=load_models(plan);saved=[];files=[];capture_actions=0;max_native=0.
        weight={k:(np.ascontiguousarray(v.linear.detach().numpy()),np.ascontiguousarray((v.quadratic*v.mask).detach().numpy())) for k,v in models.items() if k!='teacher'}
        weight['base']=(np.zeros(22,np.float32),np.zeros((22,22),np.float32))
        for number,start in enumerate(range(0,len(rows),plan['batch'])):
            stop=min(start+plan['batch'],len(rows));b=batch(rows[start:stop]);lp,residual=predictions(models,b)
            for local,row in enumerate(rows[start:stop]):
                i=start+local;m=metadata[i];n=len(row['moves']);record=dict(**m,logp={k:float(v[local,m['target']]) for k,v in lp.items()});saved.append(record)
                for kind in weight:
                    lin,q=weight[kind];native=np.empty(n,np.float32)
                    producer.lib.quiet_logp(row['x'],row['base'],n,22,lin,q,native)
                    values=native.astype(np.float64);N=float(row['history_n'])
                    if N>=3:
                        with np.errstate(divide='ignore'):values=np.logaddexp(np.log(row['counts'].astype(float)),np.log(4.)+values)-np.log(N+4)
                    err=float(abs(values-lp[kind][local,:n].numpy()).max(initial=0));max_native=max(max_native,err)
                    assert err<plan['gate']['numeric_tolerance'],('native comparator',kind,m['game'],m['ply'],err)
                capture_actions+=int(row['x'][:,0].sum())
            file=private/f'batch-{number:04d}.npz'
            arrays={k:v.numpy() for k,v in b.items() if k!='board'}
            arrays.update({'board'+str(i):v.numpy() for i,v in enumerate(b['board'])})
            arrays.update({'logp_'+k:v.numpy() for k,v in lp.items()});arrays['teacher_residual']=residual['teacher'].numpy()
            np.savez_compressed(file,**arrays);files.append(dict(file=file.name,sha256=sha(file),start=start,stop=stop))
            if number%16==0:print(json.dumps(dict(stage='fixed_CPU_prediction',completed=stop,total=len(rows))),flush=True)
        score_path=private/'decisions.jsonl.gz'
        with gzip.open(score_path,'xt') as stream:
            for r in saved:stream.write(json.dumps(r)+'\n')
        write(private/'batch-receipts.json',files,exclusive=True)
        assert sum(p.stat().st_size for p in private.iterdir())<plan['private_bytes_cap']
        checks=dict(capture_actions=capture_actions,capture_action_error=0.,native_control_max_error=max_native)
        metrics=summarize(plan,saved);conditions=gate_result(plan,metrics,checks)
        result=dict(at=now(),metrics=metrics,conditions=conditions,checks=checks,decision='distillation_design_allowed' if all(conditions.values()) else 'close_corrected_teacher_confirmation',
            source_frames=frames,source_audit_sha256=sha(OUT/'source-audit.json'),input_sha256=digest.hexdigest(),plan_sha256=sha(OUT/'plan.json'),cohort_sha256=sha(OUT/'cohort.json'),scores_sha256=sha(score_path),
            batch_receipts_sha256=sha(private/'batch-receipts.json'),weights_unchanged=all(sha(p)==plan['dependencies'][p] for p in plan['weights'].values()),
            scope='Corrected explicit-erf teacher future action prediction only, all controls fixed. No fit, posterior, runtime, playing or old320reclassification. Raw tensors/row predictions local only; aggregate publication.')
        assert result['weights_unchanged'];write(OUT/'result.json',result,exclusive=True)
        receipt.update(status='complete',decision=result['decision']);print(json.dumps(result,indent=2),flush=True)
    except BaseException as exc:receipt.update(status='failed',error=repr(exc));raise
    finally:
        receipt.update(ended_at=now(),seconds=time.monotonic()-started);write(OUT/'scoring.json',receipt);signal.alarm(0)


if __name__=='__main__':main()
