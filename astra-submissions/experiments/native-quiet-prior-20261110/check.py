"""Fixed native correctness checks only; no learned-posterior quality study."""
from datetime import datetime, timezone
import ctypes
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

import numpy as np
from prepare import ROOT, HERE, OUT, BUILD, BASE, OLD, MODEL, sha, save

sys.path.insert(0, str(ROOT / 'astra-submissions/tools'))
from reconstructed_cache import Cache, fields, actor_view, decode_move
from experience_index import unpack_view
from prior_training_cache import native_move


def bind(path):
    lib = ctypes.CDLL(str(path)); nd = lambda t: np.ctypeslib.ndpointer(dtype=t, flags='C_CONTIGUOUS')
    lib.prior_load.argtypes = [ctypes.c_char_p]
    lib.prior_state.argtypes = [ctypes.c_char_p] * 3
    lib.prior_step.argtypes = [ctypes.c_uint16]
    if hasattr(lib, 'adapter_scores'):
        lib.adapter_scores.argtypes = [nd(np.uint16)] + [nd(np.float32)] * 7 + [nd(np.uint32), ctypes.POINTER(ctypes.c_uint)]
    else:
        lib.quiet_features.argtypes = [nd(np.uint16)] + [nd(np.float32)] * 3 + [nd(np.uint32), ctypes.POINTER(ctypes.c_uint), nd(np.uint8)]
        lib.quiet_logp.argtypes = [nd(np.float32), nd(np.float32), ctypes.c_int, ctypes.c_int,
                                  nd(np.float32), nd(np.float32), nd(np.float32)]
    assert lib.prior_load(str(BASE / 'data/history.bin').encode())
    return lib


def environment(mode):
    env = {k: v for k, v in os.environ.items() if not k.startswith(('MIST_', 'ASTRA_', 'FOW_', 'OMP_', 'MKL_', 'OPENBLAS_'))}
    env.update(MIST_THREADS='2', MIST_MODEL_FULL_BELOW='10000', MIST_MODEL_TEMP='2',
               MIST_HISTORY_TABLE=str(BASE / 'data/history.bin'), MIST_HISTORY_MIN='3', MIST_HISTORY_N0='4',
               ASTRA_CAPTURE_FIXED=str(mode), OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    return env


def main():
    started = time.monotonic(); plan = json.loads((OUT / 'check-plan.json').read_text())
    for path, expected in plan['dependencies'].items(): assert sha(path) == expected, path
    assert not (OUT / 'check-execution.json').exists()
    os.sched_setaffinity(0, set(plan['cores']))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('native correctness cap')))
    signal.alarm(plan['max_seconds'])
    state = dict(status='running', started_at=datetime.now(timezone.utc).isoformat(), phase='likelihood_parity')
    save(OUT / 'check-execution.json', state)
    try:
        adapter = bind(BUILD / 'adapter.so'); reference = bind(OLD / 'build/bridge.so')
        cache = Cache(plan['state_cache'])
        model = json.loads(MODEL.read_text()); linear = np.array(model['linear'], np.float32); quadratic = np.array(model['quadratic'], np.float32)
        buffers = [[ctypes.create_string_buffer(65) for _ in range(3)] for _ in range(2)]
        moves = np.zeros(256, np.uint16); oldmoves = np.zeros_like(moves)
        lp = [np.zeros(256, np.float32) for _ in range(6)]
        x = np.zeros((256, 26), np.float32); oldx = np.zeros_like(x)
        counts = np.zeros(256, np.uint32); oldcounts = np.zeros_like(counts)
        total = ctypes.c_uint(); oldtotal = ctypes.c_uint()
        full = np.zeros(256, np.float32); cheap = np.zeros_like(full); surprise = np.zeros(256, np.uint8)
        expected = np.zeros_like(full); contexts = actions = frames = captures = 0; error = 0.
        specials = dict(promotion_actions=0, castle_actions=0, ep_actions=0)
        games = {g['game']: g for g in cache.games}
        for identifier in plan['games']:
            game = games[identifier]; selected = set(game['selected_plies'])
            adapter.prior_start(); reference.prior_start()
            for ply in range(game['records']):
                raw = cache.record(game['start'] + ply); row = fields(raw)
                want = [unpack_view(row[0]), actor_view(raw, 0), actor_view(raw, 1)]
                for lib, bufs in zip((adapter, reference), buffers):
                    assert lib.prior_state(*bufs) == row[6]
                    assert [b.value.decode() for b in bufs] == want
                frames += 1
                if ply == game['moves']: continue
                if ply in selected:
                    n = adapter.adapter_scores(moves, *lp, x, counts, ctypes.byref(total))
                    other = reference.quiet_features(oldmoves, oldx, full, cheap, oldcounts, ctypes.byref(oldtotal), surprise)
                    assert n == other and 0 < n <= 256
                    assert np.array_equal(moves[:n], oldmoves[:n]) and np.array_equal(x[:n], oldx[:n])
                    assert np.array_equal(counts[:n], oldcounts[:n]) and total.value == oldtotal.value
                    reference.quiet_logp(oldx[:n].copy(), full[:n].copy(), n, 22, linear, quadratic, expected[:n])
                    difference = float(abs(lp[2][:n] - expected[:n]).max(initial=0)); error = max(error, difference)
                    assert difference <= plan['max_reference_error']
                    capture = x[:n, 0] > 0
                    assert np.array_equal(lp[0][:n], lp[1][:n]), 'zero head changes original normalization'
                    assert np.array_equal(lp[3][:n], lp[4][:n]), 'zero head changes native history/temperature'
                    assert np.array_equal(lp[2][:n][capture], lp[0][:n][capture])
                    assert np.array_equal(lp[5][:n][capture], lp[3][:n][capture]), 'capture weight changes'
                    assert np.isfinite(np.stack(lp)[:, :n]).all()
                    contexts += 1; actions += n; captures += int(capture.sum())
                    specials['promotion_actions'] += int(((moves[:n] >> 12) != 6).sum())
                    specials['castle_actions'] += int(x[:n, 9].sum())
                    # EP capture has a pawn diagonal target on an empty square.
                    board = want[0]
                    for move, cap in zip(moves[:n], capture):
                        if cap and board[int(move) & 63].lower() == 'p' and board[(int(move) >> 6) & 63] == '-': specials['ep_actions'] += 1
                action = native_move(row[7])
                assert adapter.prior_step(action) >= 0 and reference.prior_step(action) >= 0
        save(OUT / 'likelihood-parity.json', dict(passed=True, games=len(plan['games']), frames=frames, contexts=contexts,
             actions=actions, capture_actions=captures, reference_max_error=error, special_actions=specials,
             zero_head_native_bits_equal=True, capture_native_history_temperature_bits_equal=True,
             scope='Exact native computation checks on reused TRAIN states, not prediction gain or sequential quality.'))
        all_rows = {}; cheap_updates = 0; capped_runs = 0
        for case in plan['traces']:
            for name, binary, mode in [('original', 'trace-original', 0), ('off', 'trace-adapter', 0), ('zero', 'trace-adapter', 1)]:
                label = case['game'] + '-' + name
                def limit(): resource.setrlimit(resource.RLIMIT_AS, (3 * 1024 ** 3, 3 * 1024 ** 3))
                with (OUT / (label + '.stdout')).open('x') as output, (OUT / (label + '.stderr')).open('x') as stderr:
                    child = subprocess.Popen([str(BUILD / binary), case['trace']], env=environment(mode),
                                             stdout=output, stderr=stderr, start_new_session=True, preexec_fn=limit)
                    try: code = child.wait(timeout=plan['child_seconds'])
                    except BaseException:
                        if child.poll() is None:
                            os.killpg(child.pid, signal.SIGTERM)
                            try: child.wait(timeout=5)
                            except subprocess.TimeoutExpired: os.killpg(child.pid, signal.SIGKILL); child.wait()
                        raise
                assert code == 0, label
                rows = [json.loads(line) for line in (OUT / (label + '.stdout')).read_text().splitlines()]
                assert len(rows) == case['rows']
                stable = [{k: v for k, v in row.items() if k != 'update_seconds'} for row in rows]
                if name == 'original':
                    all_rows[case['game']] = stable
                    cheap_updates += sum(r['decision'] and r['parents'] > 10000 for r in rows)
                    capped_runs += any(r['ever_capped'] for r in rows)
                else: assert stable == all_rows[case['game']], label + ' differs'
        assert cheap_updates > 0 and capped_runs > 0, 'native cheap/cap control not exercised'
        result = dict(passed=True, traces=len(plan['traces']), executions=3 * len(plan['traces']),
                      per_arm_updates=sum(c['rows'] for c in plan['traces']),
                      cheap_opponent_updates=cheap_updates, capped_traces=capped_runs,
                      ordered_population_history_float_weight_rng_fingerprints_equal=True,
                      max_reference_error=error, seconds=time.monotonic()-started,
                      scope='Native full-head and off/zero correctness only. No learned sequential run, cost gate, posterior/strength estimate or promotion.')
        save(OUT / 'check-result.json', result); state.update(status='complete', phase='checked')
        print(json.dumps(result, indent=2), flush=True)
    except BaseException as exc:
        state.update(status='failed', error=repr(exc)); raise
    finally:
        signal.alarm(0); state.update(ended_at=datetime.now(timezone.utc).isoformat(), seconds=time.monotonic()-started)
        (OUT / 'check-execution.json').write_text(json.dumps(state, indent=2) + '\n')


if __name__ == '__main__': main()
