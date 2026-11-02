"""Independent grouped score/selection audit and CPU replay of saved weights."""
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import tarfile

import numpy as np
import torch

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
HERE=ROOT/'astra-submissions/experiments/multipv-distillation-20261102'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    receipt=json.loads((OUT/'training-receipt.json').read_text())
    result=json.loads((OUT/'result.json').read_text());plan=json.loads((OUT/'plan.json').read_text())
    contract=json.loads((OUT/'training-contract.json').read_text())
    assert receipt['state']=='completed' and receipt['epochs_completed']==32
    for p,h in contract['source_sha256'].items():assert sha(ROOT/p)==h,p
    work=HERE/'work';target=work/'training'
    assert sha(target/'selected.pt')==result['checkpoint_sha256']
    assert sha(target/'validation.npz')==result['predictions_sha256']
    data=np.load(work/'data.npz');values=np.load(target/'validation.npz')
    val=data['fold']==1
    for name,key in [('target','y'),('mask','mask'),('games','game')]:
        np.testing.assert_array_equal(values[name],data[key][val])
    per_game=defaultdict(list)
    for p,y,mask,g in zip(values['pred'],values['target'],values['mask'],values['games']):
        p=p[mask].astype(float);y=y[mask].astype(float)
        selected=max(range(len(p)),key=lambda j:p[j]);gap=max(y)-y[selected]
        per_game[int(g)].append((statistics.mean((p-y)**2),statistics.mean(abs(p-y)),gap,float(gap>.5)))
    computed={key:statistics.mean(statistics.mean(r[k] for r in group) for group in per_game.values())
              for k,key in enumerate(('mse','mae','teacher_regret','regret_over_half_rate'))}
    for key,value in computed.items():assert abs(value-result['validation'][key])<1e-6
    curve=json.loads((OUT/'curve.json').read_text());chosen=min(curve,key=lambda r:r['validation']['mse'])
    assert chosen['epoch']==result['selected_epoch']==receipt['selected_epoch']
    g=plan['gate'];passes=bool(computed['mae']<=g['mae_max'] and computed['teacher_regret']<=g['teacher_regret_max'] and computed['regret_over_half_rate']<=g['regret_over_half_rate_max'])
    assert passes==result['pass_development_gate']
    spec=importlib.util.spec_from_file_location('model249',HERE/'model.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    torch.set_num_threads(2);model=module.MultiPVStudent().eval()
    model.load_state_dict(torch.load(target/'selected.pt',weights_only=True,map_location='cpu'))
    ix=np.flatnonzero(val)[np.random.default_rng(249).choice(int(val.sum()),128,replace=False)]
    x=[torch.as_tensor(data[n][ix],dtype=torch.float32 if n=='half' else torch.long) for n in ('piece','castle','ep','half','actions')]
    with torch.no_grad():p=model(*x).numpy();reverse=model(*x[:4],x[4].flip(1)).numpy()[:,::-1]
    # Map original row indices back to prediction-array positions.
    saved=values['pred'][np.searchsorted(np.flatnonzero(val),ix)]
    parity=float(np.max(np.abs(p-saved)));permutation=float(np.max(np.abs(p-reverse)))
    assert parity<2e-5 and permutation<2e-5
    # Retain exact arrays/weights so the failed run is independently replayable.
    if not (OUT/'model-evidence.tar.gz').exists():
        with tarfile.open(OUT/'model-evidence.tar.gz','w:gz') as tar:
            for path in (work/'data.npz',target/'selected.pt',target/'validation.npz'):
                tar.add(path,arcname=path.name)
    with tarfile.open(OUT/'model-evidence.tar.gz','r:gz') as tar:
        for path in (work/'data.npz',target/'selected.pt',target/'validation.npz'):
            assert hashlib.sha256(tar.extractfile(path.name).read()).hexdigest()==sha(path)
    output=dict(passed=True,metrics=computed,independent_gate=passes,validation_games=len(per_game),
                cpu_cuda_max_abs=parity,candidate_permutation_max_abs=permutation,cpu_parity_parents=128,
                selected_epoch=chosen['epoch'],evidence_sha256=sha(OUT/'model-evidence.tar.gz'),
                evidence_bytes=(OUT/'model-evidence.tar.gz').stat().st_size,source_sha256=sha(__file__),
                scope='Recomputed game weighting, epoch selection, metrics and gate; exact checkpoint CPU parity and candidate permutation; archived array/weight hashes. No native runtime or strength claim.')
    with (OUT/'audit.json').open('x') as f:json.dump(output,f,indent=2);f.write('\n')
    print(json.dumps(output))


if __name__=='__main__':main()
