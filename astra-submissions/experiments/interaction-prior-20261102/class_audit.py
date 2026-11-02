"""Decompose fixed predictors' gain; this cannot reopen the failed gate."""
from collections import defaultdict
import ctypes
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from review import ROOT, OUT, ci, sha


def main():
    os.sched_setaffinity(0, {2, 3})
    plan = json.loads((OUT / 'plan-cpu.json').read_text())
    selected = json.loads((OUT / 'selection.json').read_text())['selected']
    source = HERE.parent / 'full-prior-cost-20261102/build-r2/sparse/src'
    binary = HERE / 'build/class-probe.so'
    assert not binary.exists()
    cmd = ['gcc', '-O3', '-std=c11', '-shared', '-fPIC', '-pthread', '-I' + str(source),
           str(HERE / 'class_probe.c'), str(source / 'board.c'), str(source / 'movemodel.c'), '-lm', '-o', str(binary)]
    subprocess.run(cmd, check=True, capture_output=True, timeout=60)
    lib = ctypes.CDLL(str(binary))
    nd = lambda t: np.ctypeslib.ndpointer(dtype=t, flags='C_CONTIGUOUS')
    lib.prior_load.argtypes = [ctypes.c_char_p]
    lib.prior_step.argtypes = [ctypes.c_uint16]
    lib.observation_class.argtypes = [ctypes.c_uint16, nd(np.uint8), ctypes.c_char_p]
    lib.interaction_features.argtypes = [nd(np.uint16), nd(np.float32), nd(np.float32), nd(np.float32), nd(np.uint32), ctypes.POINTER(ctypes.c_uint), nd(np.uint8)]
    lib.interaction_logits.argtypes = [nd(np.float32), nd(np.float32), ctypes.c_int, ctypes.c_int, nd(np.float32), nd(np.float32), nd(np.float32)]
    assert lib.prior_load(str(HERE.parent / 'queen-terminal-backport-20261102/build-r2/base/data/history.bin').encode())
    with gzip.open(OUT / 'decisions.jsonl.gz', 'rt') as f:
        scored = [json.loads(line) for line in f]
    rows = {(r['game'], r['ply']): r for r in scored if r['primary']}
    models = {F: (np.array(selected[f'{F}-quadratic']['linear'], np.float32),
                  np.array(selected[f'{F}-quadratic']['quadratic'], np.float32)) for F in (18, 26)}
    moves = np.zeros(256, np.uint16); x = np.zeros((256, 26), np.float32)
    full = np.zeros(256, np.float32); cheap = np.zeros(256, np.float32)
    counts = np.zeros(256, np.uint32); surprise = np.zeros(256, np.uint8)
    mask = np.zeros(256, np.uint8); total = ctypes.c_uint(); observed = ctypes.create_string_buffer(65)
    output_rows = []
    for game in (g for g in plan['games'] if g['split'] == 'test'):
        path = ROOT / 'data/raw/games' / game['game'] / 'replay.json'
        assert sha(path) == game['replay_sha256']
        replay = json.loads(path.read_text()); lib.prior_start()
        for ply, frame in enumerate(replay['frames'][1:]):
            uci = frame['move']; square = lambda s: ord(s[0]) - 97 + 8 * (int(s[1]) - 1)
            action = square(uci[:2]) | square(uci[2:4]) << 6 | (('pnbrqk'.index(uci[4]) if len(uci) == 5 else 6) << 12)
            row = rows.get((game['game'], ply))
            if row:
                n = lib.interaction_features(moves, x, full, cheap, counts, ctypes.byref(total), surprise)
                assert n == lib.observation_class(action, mask, observed)
                assert observed.value.decode() == frame[('black', 'white')[ply % 2]]
                y = row['target']; valid = mask[:n].astype(bool)
                assert moves[y] == action and valid[y]
                result = {'game': game['game'], 'ply': ply, 'class_size': int(valid.sum()),
                          'surprise': row['surprise'], 'gain': {}}
                for F, base in ((18, cheap), (26, full)):
                    fitted = np.empty(n, np.float32)
                    lib.interaction_logits(x, base, n, F, *models[F], fitted)
                    scores = []
                    for z in (base[:n], fitted):
                        e = np.exp(z.astype(float) - float(z.max())); p = e / e.sum()
                        if total.value >= 3:
                            p = (counts[:n] + 4 * p) / (total.value + 4)
                        lp = float(np.log(p[y])); lo = float(np.log(p[valid].sum()))
                        scores.append((lp, lo, lp - lo))
                    delta = np.array(scores[1]) - np.array(scores[0])
                    assert abs(delta[0] - delta[1] - delta[2]) < 1e-10
                    original = row['probabilities'][str(F)]
                    assert abs(delta[0] - np.log(original['quadratic'] / original['base'])) < 2e-5
                    result['gain'][str(F)] = dict(zip(('action', 'observation', 'conditional'), delta.tolist()))
                output_rows.append(result)
            assert lib.prior_step(action) >= 0
    assert len(output_rows) == len(rows)
    report = {}
    for cohort, predicate in [('all', lambda r: True), ('ambiguous', lambda r: r['class_size'] > 1),
                              ('singleton', lambda r: r['class_size'] == 1), ('surprise', lambda r: r['surprise'])]:
        subset = [r for r in output_rows if predicate(r)]
        report[cohort] = {'decisions': len(subset), 'modes': {}}
        for F in ('18', '26'):
            report[cohort]['modes'][F] = {part: {'gain': float(np.mean([r['gain'][F][part] for r in subset])),
                'interval95': ci(subset, [r['gain'][F][part] for r in subset])} for part in ('action', 'observation', 'conditional')}
    with (OUT / 'observation-class-rows.jsonl.gz').open('xb') as f:
        with gzip.GzipFile(filename='', fileobj=f, mode='wb', mtime=0) as gz:
            for row in output_rows:
                gz.write((json.dumps(row) + '\n').encode())
    summary = dict(at=datetime.now(timezone.utc).isoformat(), cohorts=report,
        sources={str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), HERE / 'class_probe.c', binary]},
        rows_sha256=sha(OUT / 'observation-class-rows.jsonl.gz'),
        scope='Post-fit diagnosis with fixed coefficients. Both class likelihood and within-class likelihood can affect a multi-parent belief; this true-parent decomposition is not a posterior or strength test. The failed 228 gate remains closed.')
    with (OUT / 'observation-class-audit.json').open('x') as f:
        json.dump(summary, f, indent=2); f.write('\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
