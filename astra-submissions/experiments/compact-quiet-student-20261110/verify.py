"""Recompute development scores from the two selected CPU checkpoints."""
import numpy as np
import torch

from student import CompactQuietPrior
from train import OUT, STORE, ORIGINAL_FIT, Dataset, bootstrap, evaluate, load_plan, now, read, save, sha


def main():
    torch.set_num_threads(2)
    torch.set_float32_matmul_precision('highest')
    plan = load_plan()
    state = read(OUT/'execution.json')
    result = read(OUT/'result.json')
    assert state['status']=='complete' and state['decision']==result['decision']
    assert result['plan_sha256']==sha(OUT/'plan.json')
    dataset = Dataset(read(ORIGINAL_FIT),'cpu')
    indices = dataset.indices['development']
    metadata = [dataset.meta[i] for i in indices]
    primary = np.asarray([row['primary'] for row in metadata])
    assert int(primary.sum())==result['primary']
    records = {}
    raw = STORE/'development-logp.npz'
    with np.load(raw) as saved:
        for name,receipt in result['arms'].items():
            weights = STORE/(name+'.pt')
            assert sha(weights)==receipt['checkpoint_sha256']
            model = CompactQuietPrior(plan['rank']).eval()
            model.load_state_dict(torch.load(weights,map_location='cpu',weights_only=True))
            actual, captures = evaluate(dataset,indices,'student',model,plan['batch'])
            assert captures==receipt['exact_capture_checks']
            error = float(np.max(np.abs(saved[name]-actual)))
            assert error<plan['gates']['numeric_tolerance']
            observed_nll = float(-saved[name][primary].mean())
            assert observed_nll==result['nll'][name]==receipt['nll']
            best = min(receipt['curve'],key=lambda row:row['primary_nll'])
            assert best['epoch']==receipt['best_epoch'] and best['primary_nll']==observed_nll
            records[name] = dict(capture_checks=captures,max_recorded_logp_error=error,nll=observed_nll)
        gain = saved['hard']-saved['production']
        hard_interval = bootstrap([row for row in metadata if row['primary']],gain[primary],plan['seed'],2000)
        difference = saved['distilled']-saved['hard']
        assert abs(float(difference[primary].mean())-result['gains']['hard'])<1e-12
        assert result['conditions']['hard_label_control']==(float(difference[primary].mean())>=0)
        report = dict(at=now(),passed=True,arms=records,primary=int(primary.sum()),
            hard_gain_vs_production=float(gain[primary].mean()),hard_vs_production_interval95=hard_interval,
            saved_rows_sha256=sha(raw),plan_sha256=sha(OUT/'plan.json'),result_sha256=sha(OUT/'result.json'),
            scope='CPU checkpoint reproduction. Hard-label interval is descriptive development evidence for a separate held-out study.')
    save(OUT/'independent-review.json',report)
    print(report,flush=True)


if __name__=='__main__':
    main()
