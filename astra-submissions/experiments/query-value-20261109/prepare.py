"""One fixed compression fit, on the old training/validation folds only."""
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import torch

from model import QueryValue
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/query-value-20261109'
OLD=ROOT/'astra-submissions/experiments/native-fow-value-20261102'
EVIDENCE=ROOT/'astra-submissions/analysis/native-fow-value-20261102'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
    with p.open('x') as f:json.dump(d,f,indent=2);f.write('\n')


def main():
    OUT.mkdir(exist_ok=False)
    selection=json.loads((EVIDENCE/'selection.json').read_text())
    dataset=OLD/'work/dataset/data.npz';teacher=OLD/'work/training/teacher.pt';flat=OLD/'work/training/distilled_student.pt'
    assert sha(dataset)==selection['data_sha256']
    assert sha(teacher)==selection['teacher']['sha256'] and sha(flat)==selection['distilled_student']['sha256']
    torch.set_num_threads(2);torch.manual_seed(2701110)
    m=QueryValue();x=torch.zeros((4,64,5),dtype=torch.long);h=torch.zeros(4)
    x[:,:,0]=torch.randint(13,(4,64));x[:,:,1:]=torch.randint(2,(4,64,4))
    m.eval();a=m(x,h);assert a.shape==(4,) and torch.isfinite(a).all()
    m.train();m(x,h).square().mean().backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in m.parameters())
    n=sum(p.numel() for p in m.parameters());assert n<160065
    deps=[HERE/'model.py',HERE/'prepare.py',HERE/'train.py',OLD/'models.py',teacher,flat,dataset,EVIDENCE/'selection.json']
    write(OUT/'preflight.json',dict(passed=True,parameters=n,fp32_payload_bytes=n*4,shape=list(a.shape),scope='CPU architecture/finite-gradient smoke, not prediction or runtime evidence.'))
    write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),architecture=dict(width=64,queries=8,cross_layers=1,latent_layers=1,heads=4,ffn=128),
        optimization=dict(seed=2701110,epochs=8,batch_size=512,lr=.001,weight_decay=.0001,clip_grad=1,loss='0.5outcome+0.5retained-teacher BCE, equal game weights'),
        dataset=dict(train_positions=193517,validation_positions=8746,old_test_access=False),
        baseline_calibration=selection['calibration'],baseline_flat_validation_logloss=selection['distilled_student']['validation_logloss'],
        gate=dict(validation_relative_logloss_gain_over_best_sf=.02,nonworse_validation_brier=True,nonworse_flat_student_logloss=True,max_parameters=160065),
        resource=dict(gpu=0,cores=[4,5],wall_seconds=1800,max_initial_used_MiB=2048,max_initial_utilization=10),
        dependencies={str(p):sha(p) for p in deps},
        scope='One fixed architecture/fit; old training/validation only. A development pass requires fresh temporal confirmation and native<=25us checks before search integration; no arena or CFR-value claim.'))
    print(json.dumps(dict(parameters=n,fp32_bytes=n*4,plan_sha256=sha(OUT/'plan.json'))))


if __name__=='__main__':main()
