#!/usr/bin/env python3
"""Independent normal-form oracle for locally constrained Kuhn poker."""
import ctypes
import itertools
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy.optimize import linprog

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / 'astra-submissions/analysis/data-biased-search-20261101'


def library(name, src, flags):
    path = HERE / 'build' / name
    subprocess.run(['gcc', '-O2', '-shared', '-fPIC', '-std=c11', *flags,
                    '-I'+str(src), str(HERE/'test_kuhn.c'), str(src/'cfr.c'), '-lm', '-o', str(path)], check=True)
    lib = ctypes.CDLL(str(path))
    dp = np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')
    lib.kuhn_solve.argtypes = [dp, dp, ctypes.c_int, dp]
    return lib


def payoff(p0, p1):
    # Arrays are batch x card x (first/after or check/bet) x action.
    value = np.zeros((len(p0), len(p1)))
    for a, b in itertools.permutations(range(3), 2):
        win = 1 if a > b else -1
        after = p0[:, a, 1, 0, None] * -1 + p0[:, a, 1, 1, None] * 2*win
        check = p1[None, :, b, 0, 0]*win + p1[None, :, b, 0, 1]*after
        bet = p1[None, :, b, 1, 0] + p1[None, :, b, 1, 1]*2*win
        value += (p0[:, a, 0, 0, None]*check + p0[:, a, 0, 1, None]*bet)/6
    return value


def main():
    original = library('base-kuhn.so', HERE.parent/'stable-mix-20261101/build/base/src', [])
    patched = library('dbr-kuhn.so', HERE/'build/src', ['-DRESTRICTED'])
    rng = np.random.default_rng(2071102)
    q = rng.dirichlet(np.ones(2), 12).reshape(3, 4, 2)
    pure = np.eye(2)[np.array(list(itertools.product(range(2), repeat=6)))].reshape(64, 3, 2, 2)
    records = []
    for kind in ['off', 'opponent_half', 'both_half', 'both_threequarters', 'fixed']:
        c = np.zeros((3, 4, 1))
        if kind == 'opponent_half': c[:, 2:] = .5
        elif kind == 'both_half': c[:] = .5
        elif kind == 'both_threequarters': c[:] = .75
        elif kind == 'fixed': c[:] = 1
        out = np.zeros(120)
        patched.kuhn_solve(c.ravel(), q.ravel(), 12000, out)
        if kind == 'off':
            base = np.zeros(120); original.kuhn_solve(c.ravel(), q.ravel(), 12000, base)
            assert np.array_equal(base, out), np.max(abs(base-out))
        x = out[:24].reshape(3, 4, 2)
        p0 = (1-c[:, :2])*pure + c[:, :2]*q[:, :2]
        p1 = (1-c[:, 2:])*pure + c[:, 2:]*q[:, 2:]
        A = payoff(p0, p1)
        lp = linprog(np.r_[np.zeros(64), -1], A_ub=np.c_[-A.T, np.ones(64)], b_ub=np.zeros(64),
                     A_eq=np.array([[*np.ones(64), 0]]), b_eq=[1],
                     bounds=[(0, None)]*64+[(None, None)], method='highs')
        assert lp.success
        lower = float(payoff(x[None, :, :2], p1).min())
        upper = float(payoff(p0, x[None, :, 2:]).max())
        value = float(payoff(x[None, :, :2], x[None, :, 2:])[0, 0])
        assert lower-1e-9 <= lp.x[-1] <= upper+1e-9
        assert upper-lower < .02, (kind, lower, upper, lp.x[-1])
        assert np.all(x >= c*q-1e-12)
        records.append(dict(kind=kind, lp_value=float(lp.x[-1]), value=value,
                            row_guarantee=lower, column_bound=upper, gap=upper-lower))
    (OUT/'extensive-tests.json').write_text(json.dumps(records, indent=2)+'\n')
    print(json.dumps(records))


if __name__ == '__main__': main()
