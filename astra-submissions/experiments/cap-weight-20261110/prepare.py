"""Prepare parity/numerical checks, then freeze an estimator-only experiment."""
from datetime import datetime, timezone
import ctypes as C
from decimal import Decimal, localcontext
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from common import HERE, ROOT, BUILD, OUT, SOURCE, sha, write, library, draw


def decimal_reference(logw, cutoff):
    d = logw+cutoff
    if d > 8:
        return logw  # Remaining double error is below exp(-exp(8)).
    with localcontext() as ctx:
        ctx.prec = max(100, int(abs(d)/math.log(10))+100)
        w, t = Decimal.from_float(logw), Decimal.from_float(cutoff)
        z = (w+t).exp()
        return float(w-(Decimal(1)-(-z).exp()).ln())


def main():
    BUILD.mkdir(exist_ok=False); OUT.mkdir(exist_ok=False)
    flags = ['gcc', '-std=c11', '-pthread', '-I', str(SOURCE), '-I', str(HERE)]
    inputs = [str(HERE/'native.c'), str(SOURCE/'board.c'), str(SOURCE/'movemodel.c')]
    commands = []
    for target, options in [('cap.so', ['-O2', '-Wall', '-Wextra', '-fPIC', '-shared']),
                            ('sanitize', ['-O1', '-g', '-DASTRA_CAP_MAIN', '-fsanitize=address,undefined', '-fno-omit-frame-pointer'])]:
        cmd = [*flags, *options, *inputs, '-lm', '-o', str(BUILD/target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        assert result.returncode == 0, result.stderr
        commands.append(dict(command=cmd, stderr=result.stderr))
    result = subprocess.run([str(BUILD/'sanitize')], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    lib = library()
    cases = []
    for lw in [-1000., -100., -5., 0., 10.]:
        for d in [-1000., -700., -100., -40., -20., -19.999, -8., 0., 4., 8., 9., 1000.]:
            threshold = d-lw
            actual = lib.astra_cap_corrected(lw, threshold)
            expected = decimal_reference(lw, threshold)
            assert abs(actual-expected) < 2e-10, (lw, threshold, actual, expected)
            shifted = lib.astra_cap_corrected(lw+600, threshold-600)-600
            assert abs(actual-shifted) < 2e-10
            cases.append(dict(logw=lw, cutoff=threshold, absolute_error=abs(actual-expected)))
    pop_path = ROOT/'astra-submissions/analysis/root-population-20261110/case/population.json'
    population = json.loads(pop_path.read_text())
    weights = np.array([w['logw'] for w in population['worlds']], dtype=np.float32)
    parity = []
    for seed in range(2861000, 2861016):
        for keep in [32, 128, 512, 2048]:
            a = draw(lib, weights, keep, seed)
            b = draw(lib, weights, keep, seed, 1)
            assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1]) and a[2:] == b[2:]
            rng = C.c_uint64(seed); uniforms = np.empty(len(weights), np.float64)
            lib.astra_cap_uniforms(C.byref(rng), len(weights), uniforms)
            keys = np.log(-np.log(uniforms))-weights.astype(np.float64)
            expected = np.sort(np.argsort(keys)[:keep]).astype(np.uint32)
            assert np.array_equal(a[0], expected) and abs(a[2]-np.partition(keys, keep)[keep]) < 1e-13
            assert a[3] == rng.value and lib.astra_native_shrink_verify(weights, len(weights), keep, seed)
            parity.append(dict(seed=seed, keep=keep, cutoff=a[2]))
    # Complete retention is an identity and does not consume selection RNG.
    idx, corrected, cutoff, seed = draw(lib, weights[:5], 5, 7)
    assert np.array_equal(idx, np.arange(5)) and np.array_equal(corrected, weights[:5])
    assert math.isinf(cutoff) and seed == 7
    write(OUT/'preflight.json', dict(at=datetime.now(timezone.utc).isoformat(), passed=True,
          native_shrink_and_partition_cases=parity, numeric_cases=cases, full_retention_identity=True,
          address_undefined_sanitizers=True, sanitizer_stdout=result.stdout, commands=commands))
    datasets = [dict(id='toy-heavy', weights=[.8, .15, .05], keep=2, repeats=100000, seed=2862000),
                dict(id='toy-uniform', weights=[1]*6, keep=3, repeats=100000, seed=2862001),
                dict(id='toy-mixed', weights=[1, .3, .1, .03, .01, .003], keep=3, repeats=100000, seed=2862002)]
    datasets += [dict(id=f'population-{k}', population=str(pop_path), keep=k, repeats=1024,
                      seed=2863000+i) for i, k in enumerate([32, 128, 512, 2048])]
    deps = [HERE/'correction.h', HERE/'native.c', HERE/'common.py', HERE/'prepare.py', HERE/'run.py',
            HERE/'audit.py', BUILD/'cap.so', SOURCE/'belief.c', SOURCE/'belief.h', SOURCE/'board.c',
            SOURCE/'fow.h', SOURCE/'movemodel.c', SOURCE/'movemodel.h', pop_path]
    write(OUT/'plan.json', dict(at=datetime.now(timezone.utc).isoformat(), datasets=datasets,
          dependencies={str(p): sha(p) for p in deps}, core=6, wall_seconds=120,
          method='Exact native exponential rank keys and selected indices, with smallest-excluded cutoff. '
                 'Original masses versus q-corrected masses on the SAME selected worlds. Fixed arbitrary subset labels. '
                 'All rows/seeds/k values reported; no optimization, true-board target or model fit.',
          checks='Native RNG/index/metadata parity; numeric/scale invariance; unnormalized corrected sample means '
                 'within six empirical standard errors of exact subset masses; original normalized toy means agree '
                 'with independent exact ordered-WOR enumeration. Report normalized bias/MSE, including regressions. '
                 'These mathematical checks never authorize a playing promotion.',
          qualifications='Ideal continuous-key unbiasedness is for unnormalized masses. Native keys use finite pseudo-random '
                         'uniforms; self-normalized ratios retain bias, and corrected estimates may have higher variance. '
                         'The existing fitted guard raises all log-weights to power 1/temp, which would also transform '
                         'the correction. A sequential candidate needs separately defined measures/guard semantics. '
                         'This is not closed dual-measure252, a global temperature refit or a qsort-speed experiment.',
          sources=['https://jmlr.org/papers/volume21/19-985/19-985.pdf#page=25',
                   'https://nickduffield.net/download/papers/priority.pdf']))
    print(json.dumps(dict(prepared=True, native_parity_cases=len(parity), numeric_cases=len(cases), datasets=len(datasets))), flush=True)


if __name__ == '__main__':
    main()
