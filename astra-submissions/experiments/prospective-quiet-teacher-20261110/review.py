"""Independent stored statistics/input audit plus FP64 teacher function check."""
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np
import torch

from protocol import ROOT,OUT,sha,check_pins,now,write,PRIORITY,TEAMS,stamp_ns
from features import Producer
from score import load_models
sys.path.insert(0,str(ROOT/'astra-submissions/experiments/quiet-teacher-reference-20261110'))
from reference import forward


def main():
    plan=json.loads((OUT/'plan.json').read_text());check_pins(plan)
    assert torch.__version__==plan['torch_version']
    assert torch.version.git_version==plan['torch_git']
    result=json.loads((OUT/'result.json').read_text())
    cohort=json.loads((OUT/'cohort.json').read_text());private=Path(plan['archive'])/'private'
    assert sha(OUT/'cohort.json')==result['cohort_sha256'] and sha(OUT/'plan.json')==result['plan_sha256']
    collection=json.loads((OUT/'execution.json').read_text());scoring=json.loads((OUT/'scoring.json').read_text())
    assert stamp_ns(collection['started_at'])<stamp_ns(plan['cutoff'])<=stamp_ns(cohort['sealed_at'])<stamp_ns(scoring['started_at'])
    assert result['source_audit_sha256']==sha(OUT/'source-audit.json')
    records=json.loads((private/'batch-receipts.json').read_text())
    assert sha(private/'batch-receipts.json')==result['batch_receipts_sha256']
    path=private/'decisions.jsonl.gz';assert sha(path)==result['scores_sha256']
    with gzip.open(path,'rt') as stream:rows=[json.loads(line) for line in stream]
    torch.set_num_threads(2);torch.set_float32_matmul_precision('highest')
    model=load_models(plan)['teacher'].double().eval()
    checked=0;capture_actions=0;worst64=0.;digest=hashlib.sha256();total=0
    producer=Producer(plan['native_state_library'])
    generated=(item for g in cohort['games'] for item in producer.game(g,json.loads((Path(plan['archive'])/'games'/g['game']/'replay.json').read_text())))
    for receipt in records:
        path=private/receipt['file'];assert sha(path)==receipt['sha256'];assert receipt['start']==total
        with np.load(path,allow_pickle=False) as arrays:
            count=receipt['stop']-receipt['start'];assert arrays['valid'].shape[0]==count
            for i in range(count):
                inputs,meta=next(generated);saved=rows[total];assert {k:saved[k] for k in meta}==meta
                n=len(inputs['moves']);assert int(arrays['valid'][i].sum())==n and arrays['valid'][i,:n].all()
                for key in ('x','base','counts','moves'):
                    assert np.array_equal(arrays[key][i,:n],inputs[key]),key
                assert arrays['history_n'][i]==inputs['history_n']
                assert all(np.array_equal(arrays['board'+str(k)][i],v) for k,v in enumerate(inputs['board']))
                for value in inputs['board']+[inputs[k] for k in ('x','base','counts','moves','history_n')]:digest.update(np.asarray(value).tobytes())
                capture=inputs['x'][:,0]>0;capture_actions+=int(capture.sum())
                for kind in plan['models']:
                    lp=arrays['logp_'+kind][i,:n];assert np.isfinite(lp).all()
                    assert float(lp[meta['target']])==saved['logp'][kind]
                    assert np.array_equal(lp[capture],arrays['logp_base'][i,:n][capture])
                total+=1
            # First64new contexts, fixed before scores, independent FP64 check.
            if checked<64:
                take=min(count,64-checked)
                board=[torch.from_numpy(arrays['board'+str(k)][:take]).to(torch.float64) if k==4 else torch.from_numpy(arrays['board'+str(k)][:take]) for k in range(6)]
                value=forward(model,*board,torch.from_numpy(arrays['moves'][:take]),torch.from_numpy(arrays['x'][:take]).double()).numpy()
                valid=arrays['valid'][:take];error=float(abs(value[valid]-arrays['teacher_residual'][:take][valid]).max(initial=0))
                assert error<plan['gate']['numeric_tolerance'];worst64=max(worst64,error);checked+=take
    assert next(generated,None) is None and total==len(rows)==result['metrics']['decisions']
    assert digest.hexdigest()==result['input_sha256'] and capture_actions==result['checks']['capture_actions']
    selected=[r for r in rows if r['primary']];metrics=result['metrics'];count=len(selected)
    assert count==metrics['primary']
    nll={kind:-math.fsum(r['logp'][kind] for r in selected)/count for kind in plan['models']}
    assert all(abs(nll[k]-metrics['nll'][k])<1e-12 for k in nll)
    def interval(values,seed):
        by={}
        for row,value in zip(selected,values):
            entry=by.setdefault(row['game'],[0.,0]);entry[0]+=value;entry[1]+=1
        keys=sorted(by);rng=np.random.default_rng(seed);est=[]
        for _ in range(plan['bootstrap_draws']):
            ids=[keys[i] for i in rng.integers(len(keys),size=len(keys))]
            est.append(sum(by[k][0] for k in ids)/sum(by[k][1] for k in ids))
        return np.quantile(est,[.025,.975])
    for index,(key,control) in enumerate([('gain','base'),('matched_quadratic_gain','quadratic'),('production_quadratic_gain','production')]):
        values=[r['logp']['teacher']-r['logp'][control] for r in selected]
        assert abs(math.fsum(values)/count-metrics[key])<1e-12
        assert max(abs(interval(values,plan['seed']+index)-metrics[key+'_interval95']))<1e-12
    gain=[r['logp']['teacher']-r['logp']['base'] for r in rows]
    assert abs(math.fsum(gain)/len(gain)-metrics['all_move_gain'])<1e-12
    assert max((abs(v) for r,v in zip(rows,gain) if r['capture']),default=0)==metrics['capture_target_error']==0
    assert sum(r['primary'] and r['surprise'] for r in rows)==metrics['surprise_captures']
    assert sum(r['capture'] for r in rows)==metrics['capture_targets']
    for t in PRIORITY:
        subset=[r for r in selected if r['team_id']==t];m=metrics['priority'][t]
        assert m['games']==len({r['game'] for r in subset}) and m['decisions']==len(subset)
        expected_gain=math.fsum(r['logp']['teacher']-r['logp']['base'] for r in subset)/len(subset) if subset else 0.
        assert abs(m['gain']-expected_gain)<1e-12
    g=plan['gate'];m=metrics;c=result['checks']
    expected=dict(primary=count>=g['primary_min'],native_gain=m['gain']>=g['native_gain'],matched_quadratic=m['matched_quadratic_gain']>=g['quadratic_gain'],
        production_quadratic=m['production_quadratic_gain']>=g['quadratic_gain'],native_confidence=m['gain_interval95'][0]>0,
        production_confidence=m['production_quadratic_gain_interval95'][0]>0,all_moves=m['all_move_gain']>=0,capture_identity=m['capture_target_error']==0 and c['capture_action_error']==0,
        capture_coverage=m['surprise_captures']>=g['surprise_min'],native_control_parity=c['native_control_max_error']<g['numeric_tolerance'],
        priority_coverage=all(m['priority'][t]['games']>=g['priority_games_min'] for t in PRIORITY),priority_nonregression=all(m['priority'][t]['gain']>=0 for t in PRIORITY))
    assert expected==result['conditions']
    decision='distillation_design_allowed' if all(expected.values()) else 'close_corrected_teacher_confirmation'
    assert decision==result['decision']
    report=dict(passed=True,at=now(),rows=total,primary=count,input_digest_verified=True,capture_actions=capture_actions,
        fp64_contexts=checked,fp64_max_residual_error=worst64,independent_nll=nll,conditions=expected,decision=decision,
        result_sha256=sha(OUT/'result.json'),limitation='Raw inputs are regenerated through the same producer with C/course checks; independent scalar aggregation/bootstrap and exact stored-target/capture checks. FP64uses the corrected reference architecture, not a separately trained/implemented network. Native control parity comes from the original pinned C comparison. Raw tensors/row probabilities stay local.')
    write(OUT/'independent-review.json',report,exclusive=True);print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
