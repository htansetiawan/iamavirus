"""Recover exactly the 293 TRAIN feature bytes; no scoring, fitting or API."""
from datetime import datetime, timezone
import ctypes
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'astra-submissions/analysis/ragged-train-20261110'
sys.path.insert(0, str(ROOT / 'astra-submissions/tools'))
sys.path.insert(0, str(HERE.parent / 'capture-fixed-prior-20261110'))
import numpy as np
from reconstructed_cache import Cache, fields, actor_view, FATAL, CAPTURE, SELECTED
from experience_index import unpack_view
from prior_training_cache import CANDIDATE, CONTEXT, SCHEMA, native_move, cache_move, update_digest
from prepare import library


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, obj):
    with Path(path).open('x') as stream:
        json.dump(obj, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    started = time.monotonic()
    plan = json.loads((OUT / 'plan.json').read_text())
    for path, expected in plan['dependencies'].items():
        assert sha(path) == expected, path
    os.sched_setaffinity(0, set(plan['cores']))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('600s export bound')))
    signal.alarm(plan['max_seconds'])
    cache = Cache(plan['state_cache'])
    destination = Path(plan['destination'])
    destination.mkdir(exist_ok=False)
    lib = library()
    moves = np.zeros(256, np.uint16)
    x = np.zeros((256, 26), np.float32)
    full = np.zeros(256, np.float32)
    cheap = np.zeros(256, np.float32)
    counts = np.zeros(256, np.uint32)
    surprise = np.zeros(256, np.uint8)
    history_total = ctypes.c_uint()
    buffers = [ctypes.create_string_buffer(65) for _ in range(3)]
    digest = hashlib.sha256()
    candidates = contexts = frames = 0
    capture_targets = fatal_targets = max_width = 0
    original = json.loads(Path(plan['original_plan']).read_text())
    train = [g for g in original['games'] if g['split'] == 'train']
    assert [g['game'] for g in train] == [g['game'] for g in cache.games]
    try:
        with (destination / 'candidates.bin').open('xb') as data, (destination / 'contexts.bin').open('xb') as index:
            for game_index, game in enumerate(cache.games):
                lib.prior_start()
                wanted = set(train[game_index]['selected_plies'])
                assert wanted == set(game['selected_plies'])
                for ply in range(game['records']):
                    global_index = game['start'] + ply
                    raw = cache.record(global_index)
                    row = fields(raw)
                    assert lib.prior_state(*buffers) == row[6] == ply % 2
                    expected = [unpack_view(row[0]), actor_view(raw, 0), actor_view(raw, 1)]
                    assert [b.value.decode() for b in buffers] == expected
                    frames += 1
                    if ply == game['moves']:
                        assert ply not in wanted
                        continue
                    action = native_move(row[7])
                    if ply in wanted:
                        assert row[8] & SELECTED
                        n = lib.quiet_features(moves, x, full, cheap, counts, ctypes.byref(history_total), surprise)
                        assert 0 < n <= 256
                        targets = np.flatnonzero(moves[:n] == action)
                        assert len(targets) == 1
                        target = int(targets[0])
                        records = np.zeros(n, CANDIDATE)
                        records['x'] = x[:n]
                        records['base'][:, 0] = cheap[:n]
                        records['base'][:, 1] = full[:n]
                        records['history'] = counts[:n]
                        records['move'] = [cache_move(int(m)) for m in moves[:n]]
                        records['surprise'] = surprise[:n]
                        assert np.isfinite(records['x']).all() and np.isfinite(records['base']).all()
                        assert int(records['history'].sum()) <= history_total.value
                        assert int(records['move'][target]) == row[7]
                        assert bool(x[target, 0]) == bool(row[9] & CAPTURE)
                        assert bool(x[target, 22]) == bool(row[9] & FATAL)
                        update_digest(digest, records, target, history_total.value)
                        context = CONTEXT.pack(candidates, global_index, history_total.value, target, n, game_index, row[8], row[9])
                        data.write(records.tobytes()); index.write(context)
                        candidates += n; contexts += 1
                        capture_targets += bool(row[9] & CAPTURE)
                        fatal_targets += bool(row[9] & FATAL)
                        max_width = max(max_width, n)
                        assert data.tell() + index.tell() <= plan['max_bytes'], 'SSD bound'
                    assert lib.prior_step(action) >= 0
                if (game_index + 1) % 500 == 0:
                    print(json.dumps(dict(games=game_index + 1, contexts=contexts, candidates=candidates)), flush=True)
        receipt = json.loads(Path(plan['original_receipt']).read_text())
        assert len(cache.games) == receipt['games'] == 4000
        assert contexts == receipt['decisions'] == 92940
        assert frames == receipt['native_frames'] == 356161
        assert max_width == receipt['width'] == 92
        assert digest.hexdigest() == receipt['unpacked_sha256'], 'original TRAIN bytes differ'
        manifest = dict(schema=SCHEMA, contexts=contexts, candidates=candidates, candidate_bytes=120, context_bytes=24,
                        games=4000, frames=frames, max_width=max_width, capture_targets=capture_targets,
                        fatal_targets=fatal_targets, unpacked_sha256=digest.hexdigest(),
                        plan_sha256=sha(OUT / 'plan.json'), state_cache_manifest_sha256=sha(Path(plan['state_cache']) / 'manifest.json'),
                        sha256={name: sha(destination / name) for name in ('candidates.bin', 'contexts.bin')},
                        scope=plan['scope'])
        save(destination / 'manifest.json', manifest)
        result = dict(at=datetime.now(timezone.utc).isoformat(), passed=True, seconds=time.monotonic()-started,
                      manifest=manifest, manifest_sha256=sha(destination / 'manifest.json'),
                      bytes=sum(p.stat().st_size for p in destination.iterdir()), original_padded_bytes=receipt['array_bytes'])
        assert result['bytes'] <= plan['max_bytes']
        save(OUT / 'export.json', result)
        print(json.dumps(result, indent=2), flush=True)
    finally:
        cache.close()
        signal.alarm(0)


if __name__ == '__main__':
    main()
