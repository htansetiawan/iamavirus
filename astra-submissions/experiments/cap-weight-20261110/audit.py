"""Independent NumPy aggregation of every draw and exact small-WOR enumeration."""
from datetime import datetime, timezone
import ctypes as C
import itertools
import json
import math
from pathlib import Path
import time

import numpy as np
from common import OUT, library, sha, write


def arrays(spec):
    # Deliberately independent of run.data and C subset accumulation.
    if 'population' in spec:
        p = json.loads(Path(spec['population']).read_text())
        x = np.array([r['logw'] for r in p['worlds']], np.float32).astype(np.float64)
        membership = np.array([[True]+[bool(int(r['fatal'], 16) & (1 << a)) for a in range(len(p['moves']))]
                               for r in p['worlds']], bool)
    else:
        x = np.log(np.array(spec['weights'], np.float64)).astype(np.float32).astype(np.float64)
        membership = np.column_stack((np.ones(len(x), bool), np.eye(len(x), dtype=bool)))
    return x, membership


def exact_old(weights, membership, keep):
    expectation = np.zeros(membership.shape[1])
    for order in itertools.permutations(range(len(weights)), keep):
        probability, total = 1., float(weights.sum())
        for i in order:
            probability *= weights[i]/total; total -= weights[i]
        selected = np.array(order)
        expectation += probability*(weights[selected] @ membership[selected])/weights[selected].sum()
    return expectation


def main():
    started = time.monotonic(); plan = json.loads((OUT/'plan.json').read_text())
    done = json.loads((OUT/'completion.json').read_text()); assert done['error'] is None
    assert len(done['rows']) == len(plan['datasets']) == 7
    for path, digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    lib = library(); reports = []
    for spec, receipt in zip(plan['datasets'], done['rows']):
        path = OUT/f"{spec['id']}.json"
        assert receipt['sha256'] == sha(path)
        row = json.loads(path.read_text()); assert row['spec'] == spec
        lw, membership = arrays(spec); r, n, k = spec['repeats'], len(lw), spec['keep']
        # Replay the exact scalar native RNG stream, independently compute
        # every rank, cutoff, correction and subset sum with array operations.
        rng = C.c_uint64(spec['seed']); u = np.empty(r*n, np.float64)
        lib.astra_cap_uniforms(C.byref(rng), len(u), u)
        uniform_hash = __import__('hashlib').sha256(u.tobytes()).hexdigest()
        keys = np.log(-np.log(u.reshape(r, n)))-lw
        order = np.argsort(keys, axis=1)
        indices = order[:, :k]
        cutoff = np.take_along_axis(keys, order[:, k:k+1], axis=1)
        selected_lw = lw[indices]
        d = selected_lw+cutoff
        assert d.min() > -700
        # exp(d) can overflow harmlessly: q then equals one in double precision.
        with np.errstate(over='ignore'):
            q = -np.expm1(-np.exp(d))
        w, corrected = np.exp(selected_lw), np.exp(selected_lw-np.log(q))
        labels = membership[indices]
        old = np.einsum('rk,rkf->rf', w, labels)
        new = np.einsum('rk,rkf->rf', corrected, labels)
        values = np.stack((old, new, old/w.sum(axis=1)[:, None], new/corrected.sum(axis=1)[:, None]))
        sums = values.sum(axis=1); squares = (values**2).sum(axis=1)
        native_sum = np.array(row['sums']).reshape(sums.shape)
        native_sq = np.array(row['squares']).reshape(sums.shape)
        assert np.allclose(sums, native_sum, atol=2e-8, rtol=2e-11), spec['id']
        assert np.allclose(squares, native_sq, atol=2e-8, rtol=2e-11), spec['id']
        diff = values[3]-values[2]
        assert np.allclose(diff.sum(axis=0), row['delta_sum'], atol=2e-9, rtol=1e-10)
        assert np.allclose((diff**2).sum(axis=0), row['delta_square_sum'], atol=2e-9, rtol=1e-10)
        mean = native_sum/r
        variance = np.maximum(0, (native_sq-r*mean**2)/(r-1)); se = np.sqrt(variance/r)
        target_mass = np.exp(lw) @ membership
        target_probability = target_mass/target_mass[0]
        assert np.allclose(target_mass, row['exact_mass'], atol=1e-10, rtol=1e-12)
        mass_sanity = bool(np.all(abs(mean[1]-target_mass) <= 6*se[1]+1e-11*np.maximum(1, target_mass)))
        assert mass_sanity == row['corrected_mass_six_se_sanity']
        exact_normalized = None
        if 'weights' in spec:
            exact_normalized = exact_old(np.exp(lw), membership, k)
            assert np.all(abs(mean[2]-exact_normalized) <= 6*se[2]+1e-10)
        mse = np.maximum(0, native_sq[2:]/r-2*mean[2:]*target_probability+target_probability**2)
        reports.append(dict(id=spec['id'], subsets=row['names'], trials=r,
              exact_probability=target_probability.tolist(), old_probability_mean=mean[2].tolist(),
              corrected_probability_mean=mean[3].tolist(), old_probability_bias=(mean[2]-target_probability).tolist(),
              corrected_probability_bias=(mean[3]-target_probability).tolist(),
              probability_mse_old=mse[0].tolist(), probability_mse_corrected=mse[1].tolist(),
              corrected_mass_mean=mean[1].tolist(), exact_mass=target_mass.tolist(), corrected_mass_se=se[1].tolist(),
              corrected_mass_six_se_sanity=mass_sanity,
              exact_old_normalized=None if exact_normalized is None else exact_normalized.tolist(),
              uniform_stream_sha256=uniform_hash))
    write(OUT/'audit.json', dict(at=datetime.now(timezone.utc).isoformat(), verified_datasets=len(reports),
          independently_replayed_draws=sum(s['repeats'] for s in plan['datasets']), reports=reports,
          corrected_mass_all_sanity=all(r['corrected_mass_six_se_sanity'] for r in reports),
          elapsed_seconds=time.monotonic()-started, auditor_sha256=sha(Path(__file__)),
          scope='Every draw independently ranked/aggregated from the native uniform stream; RNG is shared, not a second PRNG. '
                'Six empirical SE checks are diagnostics, not a proof or rigorous confidence guarantee. '
                'No claim that normalized correction is unbiased, lower MSE universally or stronger in play.'))
    print(json.dumps(dict(verified_datasets=len(reports), corrected_mass_all_sanity=all(r['corrected_mass_six_se_sanity'] for r in reports))), flush=True)


if __name__ == '__main__':
    main()
