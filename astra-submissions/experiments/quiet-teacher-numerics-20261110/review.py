"""Independent stored-array arithmetic audit; no Torch, inference or labels."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'astra-submissions/analysis/quiet-teacher-numerics-20261110'


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    plan = json.loads((OUT / 'plan.json').read_text())
    result = json.loads((OUT / 'result.json').read_text())
    execution = json.loads((OUT / 'runner-execution.json').read_text())
    assert execution['status'] == 'complete' and execution['own_lease_released']
    assert sha(OUT / 'arithmetic-arrays.npz') == result['arrays_sha256']
    for path, expected in plan['dependencies'].items(): assert sha(path) == expected, path
    arrays = np.load(OUT / 'arithmetic-arrays.npz', allow_pickle=False)
    checks = 0

    def compare(key, left, right):
        nonlocal checks
        for kind in ('residual', 'logp'):
            a = arrays[left + '_' + kind]; b = arrays[right + '_' + kind]
            assert a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all()
            delta = [float(x) - float(y) for x, y in zip(a, b)]
            expected = result['comparisons'][key][kind]
            assert abs(max(map(abs, delta), default=0.) - expected['maximum']) < 1e-14
            rms = math.sqrt(math.fsum(x * x for x in delta) / len(delta))
            assert abs(rms - expected['rms']) < 1e-14
            checks += 1

    for label, _, _ in plan['batches']:
        for mode in plan['modes']:
            compare(mode + '_' + label, mode + '_cpu_' + label, mode + '_cuda_' + label)
        for device in ('cpu', 'cuda'):
            for mode in plan['modes'][:-1]:
                compare(mode+'_'+device+'_'+label+'_vs_f64_erf', mode+'_'+device+'_'+label, 'math-erf-f64_'+device+'_'+label)
            for reference in ('math-erf-f32', 'math-tanh-f32'):
                compare('default_'+device+'_'+label+'_vs_'+reference, 'default-f32_'+device+'_'+label, reference+'_'+device+'_'+label)
    assert checks == 84
    operations = result['operations']
    assert all('aten::_transformer_encoder_layer_fwd' in operations['default-f32_' + d] for d in ('cpu', 'cuda'))
    assert all('aten::_transformer_encoder_layer_fwd' not in operations[m + '_' + d]
               for m in plan['modes'][1:] for d in ('cpu', 'cuda'))
    assert all('aten::_scaled_dot_product_attention_math' in operations[m + '_' + d]
               for m in plan['modes'][1:] for d in ('cpu', 'cuda'))
    summary = dict(at=datetime.now(timezone.utc).isoformat(), passed=True, array_metrics_verified=checks,
        fixed_contexts=len(plan['context_indices']), checkpoint_sha256=sha(plan['checkpoint']),
        dependency_pins=len(plan['dependencies']), result_sha256=sha(OUT / 'result.json'),
        limitation='Independent NumPy/Python scalar audit of stored arrays and source pins; no independent Transformer implementation, no rerun, no development/test/NLL or model qualification.')
    with (OUT / 'independent-review.json').open('x') as stream: json.dump(summary, stream, indent=2); stream.write('\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__': main()
