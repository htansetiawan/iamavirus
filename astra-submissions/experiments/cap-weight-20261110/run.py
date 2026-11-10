"""One fixed run of coupled mass estimators; no model or game is changed."""
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import time

import numpy as np
from common import OUT, library, sha, write


def data(spec):
    if 'population' in spec:
        p = json.loads(Path(spec['population']).read_text())
        lw = np.array([w['logw'] for w in p['worlds']], np.float32)
        # All immediate root-loss subsets, not just the historical move.
        labels = np.array([1 | (int(w['fatal'], 16) << 1) for w in p['worlds']], np.uint64)
        names = ['total']+[m['uci'] for m in p['moves']]
    else:
        lw = np.log(np.array(spec['weights'], np.float64)).astype(np.float32)
        labels = np.array([1 | (1 << (i+1)) for i in range(len(lw))], np.uint64)
        names = ['total']+[str(i) for i in range(len(lw))]
    return lw, labels, names


def main():
    plan = json.loads((OUT/'plan.json').read_text())
    for path, digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    os.sched_setaffinity(0, {plan['core']})
    os.nice(10)
    lib = library(); started = time.monotonic(); rows = []; error = None
    write(OUT/'started.json', dict(at=datetime.now(timezone.utc).isoformat(), pid=os.getpid(), plan_sha256=sha(OUT/'plan.json')))
    try:
        for spec in plan['datasets']:
            assert time.monotonic()-started < plan['wall_seconds']
            lw, labels, names = data(spec); f = len(names)
            sums, squares = np.zeros(4*f), np.zeros(4*f)
            delta, delta2 = np.zeros(f), np.zeros(f)
            t = time.monotonic()
            assert lib.astra_cap_batch(lw, labels, len(lw), spec['keep'], f, spec['seed'], spec['repeats'],
                                      sums, squares, delta, delta2)
            n = spec['repeats']; means = sums.reshape(4, f)/n
            seconds = time.monotonic()-t
            exact_mass = np.array([np.exp(lw.astype(np.float64))[(labels & (np.uint64(1) << np.uint64(i))) != 0].sum()
                                   for i in range(f)])
            variance = np.maximum(0, (squares.reshape(4, f)-n*means**2)/(n-1))
            se = np.sqrt(variance/n)
            sanity = bool(np.all(np.abs(means[1]-exact_mass) <= 6*se[1]+1e-11*np.maximum(1, exact_mass)))
            row = dict(spec=spec, names=names, count=len(lw), seconds=seconds, exact_mass=exact_mass.tolist(),
                       exact_probability=(exact_mass/exact_mass[0]).tolist(), sums=sums.tolist(), squares=squares.tolist(),
                       delta_sum=delta.tolist(), delta_square_sum=delta2.tolist(),
                       corrected_mass_six_se_sanity=sanity)
            write(OUT/f"{spec['id']}.json", row); rows.append(dict(id=spec['id'], sha256=sha(OUT/f"{spec['id']}.json")))
            print(json.dumps(dict(id=spec['id'], seconds=seconds, corrected_mass_sanity=sanity)), flush=True)
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        write(OUT/'completion.json', dict(at=datetime.now(timezone.utc).isoformat(), error=error,
              elapsed_seconds=time.monotonic()-started, rows=rows, scope='Estimator-only, all fixed arms retained; no native filter, search or arena changes.'))


if __name__ == '__main__':
    main()
