"""Independent exported-C scores, replay legality, and post-fit taxonomy audit."""
from collections import defaultdict
import ctypes
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ['OPENBLAS_NUM_THREADS'] = '1'
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/interaction-prior-20261102'
sys.path.insert(0, str(ROOT))
from learning import ingest, move_taxonomy


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ci(rows, gains):
    groups = defaultdict(lambda: [0., 0])
    for row, gain in zip(rows, gains):
        groups[row['game']][0] += float(gain)
        groups[row['game']][1] += 1
    v = np.array(list(groups.values()))
    rng = np.random.default_rng(2281102)
    means = []
    for _ in range(2000):
        sample = v[rng.integers(len(v), size=len(v))]
        means.append(sample[:, 0].sum() / sample[:, 1].sum())
    return np.quantile(means, [.025, .975]).tolist()


def main():
    os.sched_setaffinity(0, {2, 3})
    plan = json.loads((OUT / 'plan-cpu.json').read_text())
    assert json.loads((OUT / 'execution.json').read_text())['status'] == 'complete'
    for path, digest in plan['dependencies'].items():
        assert sha(Path(path)) == digest, path
    chosen = json.loads((OUT / 'selection.json').read_text())
    lock = json.loads((OUT / 'selection-lock.json').read_text())
    result = json.loads((OUT / 'result.json').read_text())
    assert sha(OUT / 'selection.json') == lock['sha256'] == result['selection_sha256']
    assert sha(OUT / 'decisions.jsonl.gz') == result['scores_sha256']
    assert (OUT / 'selection-lock.json').stat().st_mtime_ns < (OUT / 'test-data.json').stat().st_mtime_ns
    for mode in (18, 26):
        for kind in ('linear', 'quadratic'):
            candidates = []
            for ridge in plan['ridges'][kind]:
                model = json.loads((OUT / f'{mode}-{kind}-{ridge}-model.json').read_text())
                curve = json.loads((OUT / f'{mode}-{kind}-{ridge}-curve.json').read_text())
                best = min(curve, key=lambda row: row['validation_nll'])
                assert model['epoch'] == best['epoch'] and model['validation_nll'] == best['validation_nll']
                candidates.append(model)
            assert chosen['selected'][f'{mode}-{kind}'] == min(candidates, key=lambda m: m['validation_nll'])
    with gzip.open(OUT / 'decisions.jsonl.gz', 'rt') as f:
        scored = [json.loads(line) for line in f]
    by_key = {(r['game'], r['ply']): r for r in scored}
    assert len(by_key) == len(scored)
    expected = {(g['game'], p) for g in plan['games'] if g['split'] == 'test' for p in g['selected_plies']}
    assert set(by_key) == expected
    assert len({g['game'] for g in plan['games']}) == len(plan['games'])
    assert len({g['sequence_sha256'] for g in plan['games']}) == len(plan['games'])
    lib = ctypes.CDLL(str(HERE / 'build/bridge.so'))
    nd = lambda dtype: np.ctypeslib.ndpointer(dtype=dtype, flags='C_CONTIGUOUS')
    lib.prior_load.argtypes = [ctypes.c_char_p]
    lib.prior_step.argtypes = [ctypes.c_uint16]
    lib.interaction_features.argtypes = [nd(np.uint16), nd(np.float32), nd(np.float32), nd(np.float32), nd(np.uint32), ctypes.POINTER(ctypes.c_uint), nd(np.uint8)]
    lib.interaction_logits.argtypes = [nd(np.float32), nd(np.float32), ctypes.c_int, ctypes.c_int, nd(np.float32), nd(np.float32), nd(np.float32)]
    assert lib.prior_load(str(HERE.parent / 'queen-terminal-backport-20261102/build-r2/base/data/history.bin').encode())
    models = {}
    for mode in (18, 26):
        for kind in ('base', 'linear', 'quadratic'):
            model = chosen['selected'].get(f'{mode}-{kind}')
            models[mode, kind] = (np.array(model['linear'], np.float32), np.array(model['quadratic'], np.float32)) if model else (np.zeros(mode, np.float32), np.zeros((mode, mode), np.float32))
    moves = np.zeros(256, np.uint16)
    features = np.zeros((256, 26), np.float32)
    full, cheap = np.zeros(256, np.float32), np.zeros(256, np.float32)
    counts, surprise = np.zeros(256, np.uint32), np.zeros(256, np.uint8)
    total = ctypes.c_uint()
    probability_error = log_probability_error = 0.
    frames = probabilities = 0
    tags = {}
    for game in (g for g in plan['games'] if g['split'] == 'test'):
        path = ROOT / 'data/raw/games' / game['game'] / 'replay.json'
        assert sha(path) == game['replay_sha256']
        replay = json.loads(path.read_text())
        states, errors = ingest.validate_replay(replay)
        assert not errors, (game['game'], errors)
        frames += len(states)
        labels = move_taxonomy.label_game(replay)
        for m in labels['moves']:
            tags[game['game'], m['ply'] - 1] = m['tags']
        lib.prior_start()
        for ply, frame in enumerate(replay['frames'][1:]):
            uci = frame['move']
            square = lambda s: ord(s[0]) - 97 + 8 * (int(s[1]) - 1)
            action = square(uci[:2]) | square(uci[2:4]) << 6 | (('pnbrqk'.index(uci[4]) if len(uci) == 5 else 6) << 12)
            row = by_key.get((game['game'], ply))
            if row:
                n = lib.interaction_features(moves, features, full, cheap, counts, ctypes.byref(total), surprise)
                target = int(np.flatnonzero(moves[:n] == action)[0])
                assert target == row['target'] and n == row['n'] and total.value == row['history_count']
                assert bool(surprise[target]) == row['surprise']
                assert (ply // 2 >= 8 and not bool(features[target, 22])) == row['primary']
                for mode in (18, 26):
                    for kind in ('base', 'linear', 'quadratic'):
                        output = np.empty(n, np.float32)
                        linear, quadratic = models[mode, kind]
                        lib.interaction_logits(features, cheap if mode == 18 else full, n, mode, linear, quadratic, output)
                        exps = np.exp(output.astype(float) - float(output.max()))
                        p = float(exps[target] / exps.sum())
                        if total.value >= 3:
                            p = (int(counts[target]) + 4 * p) / (total.value + 4)
                        original = row['probabilities'][str(mode)][kind]
                        probability_error = max(probability_error, abs(p - original))
                        log_probability_error = max(log_probability_error, abs(np.log(p) - np.log(original)))
                        probabilities += 1
            assert lib.prior_step(action) >= 0
    assert probability_error < 5e-6 and log_probability_error < 2e-5, (probability_error, log_probability_error)
    primary = [r for r in scored if r['primary']]
    diagnostics = {}
    for mode in ('18', '26'):
        loss = {kind: -np.log(np.array([r['probabilities'][mode][kind] for r in primary])) for kind in ('base', 'linear', 'quadratic')}
        gain = loss['base'] - loss['quadratic']
        expected = result['modes'][mode]
        assert abs(float(gain.mean()) - expected['gain']) < 1e-12
        assert np.allclose(ci(primary, gain), expected['interval95'], atol=1e-12, rtol=0)
        for kind in loss:
            assert abs(float(loss[kind].mean()) - expected['nll'][kind]) < 1e-12
        audit = {}
        for tag in move_taxonomy.KEYS + ['native_surprise_capture']:
            indices = [i for i, row in enumerate(primary) if (row['surprise'] if tag == 'native_surprise_capture' else tag in tags[row['game'], row['ply']])]
            if not indices:
                continue
            audit[tag] = {'decisions': len(indices), 'gain': float(gain[indices].mean()),
                'interval95': ci([primary[i] for i in indices], gain[indices])}
        diagnostics[mode] = audit
    receipt = {'at': datetime.now(timezone.utc).isoformat(), 'test_games': 300, 'test_decisions': len(scored),
        'primary_decisions': len(primary), 'independently_validated_frames': frames,
        'exported_C_probabilities_checked': probabilities, 'maximum_probability_error': probability_error,
        'maximum_log_probability_error': log_probability_error,
        'all_source_hashes_verified': True, 'validation_selection_recomputed': True,
        'selection_locked_before_test_receipt': True, 'no_duplicate_games_or_sequences': True,
        'primary_scores_and_bootstrap_recomputed': True, 'taxonomy': diagnostics,
        'sources': {str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), ROOT / 'learning/ingest.py', ROOT / 'learning/move_taxonomy.py']},
        'scope': 'Post-fit descriptive taxonomy slices, not new acceptance tests or tuning evidence on an untouched holdout.'}
    with (OUT / 'independent-review.json').open('x') as f:
        json.dump(receipt, f, indent=2); f.write('\n')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'taxonomy'}, indent=2))


if __name__ == '__main__':
    main()
