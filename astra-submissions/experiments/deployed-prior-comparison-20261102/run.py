#!/usr/bin/env python3
"""One frozen predictive comparison; no fitting or playing-policy edits."""
import argparse
import ctypes
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

os.environ['OPENBLAS_NUM_THREADS'] = '1'
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/deployed-prior-comparison-20261102'
BUILD = HERE / 'build'
BASE = HERE.parent / 'queen-terminal-backport-20261102/build-r2/base'
STUDENT = HERE.parent / 'visible-response-20261101'
PROOF = HERE.parent / 'observable-response-audit-20261101'
MODEL = ROOT / 'astra-submissions/analysis/visible-response-20261101/models/response.bin'
COHORT = ROOT / 'astra-submissions/analysis/arena-intel-20261101-evening'
REF = ROOT.parent / 'fow-starter/referee.py'
sys.path.insert(0, str(STUDENT))
import data

NAMES = ('full', 'cheap', 'student', 'projected')
MASK64 = (1 << 64) - 1


def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, obj): p.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')
def unique(p, obj):
    with p.open('x') as f: json.dump(obj, f, indent=2, allow_nan=False); f.write('\n')


def mix(h, v):
    z = (h + 0x9E3779B97F4A7C15 * (v | 1)) & MASK64
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
    return z ^ (z >> 31)


def vh(view):
    h = 1469598103934665603
    for x in view.encode(): h = ((h ^ x) * 1099511628211) & MASK64
    return h


def native_move(uci):
    return data.encode_move(uci, 0) | (6 << 12 if len(uci) == 4 else 0)


def uci(move):
    def sq(s): return chr(97 + s % 8) + str(1 + s // 8)
    pr = (move >> 12) & 7
    return sq(move & 63) + sq((move >> 6) & 63) + ('pnbrqk'[pr] if pr != 6 else '')


def library():
    lib = ctypes.CDLL(str(BUILD / 'prior.so'))
    u8 = np.ctypeslib.ndpointer(dtype=np.uint8, flags='C_CONTIGUOUS')
    u16 = np.ctypeslib.ndpointer(dtype=np.uint16, flags='C_CONTIGUOUS')
    u32 = np.ctypeslib.ndpointer(dtype=np.uint32, flags='C_CONTIGUOUS')
    f64 = np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')
    lib.prior_load.argtypes = [ctypes.c_char_p]
    lib.prior_state.argtypes = [ctypes.c_char_p] * 3
    lib.prior_scores.argtypes = [ctypes.c_int, u16, f64, u32, ctypes.POINTER(ctypes.c_uint)]
    lib.prior_step.argtypes = [ctypes.c_uint16]
    lib.prior_history.argtypes = [ctypes.c_int]; lib.prior_history.restype = ctypes.c_uint64
    lib.astra_response_load.argtypes = [ctypes.c_char_p]; lib.astra_response_load.restype = ctypes.c_void_p
    lib.astra_response_probs.argtypes = [ctypes.c_void_p, u8, u16, ctypes.c_int, f64]
    lib.observable_fatal.argtypes = [u8, u16, ctypes.c_int, u8, u8]
    assert lib.prior_load(str(BASE / 'data/history.bin').encode())
    w = lib.astra_response_load(str(MODEL).encode()); assert w
    return lib, w


def prepare():
    os.sched_setaffinity(0, {2, 3})
    BUILD.mkdir(exist_ok=True)
    assert not (OUT / 'plan.json').exists()
    assert sha(BASE / 'mist') == '14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd'
    assert sha(MODEL) == '45a41cf4ecaae9324472ae93a81b349d597cec20364a7c73ef66e513df077c97'
    assert sha(REF) == '2f82ac292bfad29bcb2d701b73c060d1ca8281378b4598f08a620fe5c97255be'
    archive = json.loads((COHORT / 'archive.json').read_text())
    assert sha(COHORT / 'new-game-taxonomy.jsonl.gz') == archive['compressed_sha256']
    rows = [json.loads(x) for x in gzip.decompress((COHORT / 'new-game-taxonomy.jsonl.gz').read_bytes()).splitlines()]
    old = json.loads((data.OUT / 'manifest.json').read_text())
    seen = {g['sequence_sha256'] for g in old['games']}
    games, exclusions = [], []
    for row in sorted(rows, key=lambda x: x['game']):
        path = ROOT / 'data/raw/games' / row['game'] / 'replay.json'
        assert sha(path) == row['replay_sha256']
        rp = json.loads(path.read_text())
        assert '2026-11-01T20:00' <= rp['createdAt'] < '2026-11-02'
        seq = hashlib.sha256(' '.join(f['move'] for f in rp['frames'][1:]).encode()).hexdigest()
        reason = ('no target actor' if not any(rp[k] in data.TEAMS for k in ('white', 'black')) else
                  'sequence already seen' if seq in seen else
                  'unsupported rules' if rp.get('rulesVersion') != 'fow-v1' else None)
        if reason: exclusions.append(dict(game=row['game'], reason=reason)); continue
        seen.add(seq)
        games.append({k: row[k] for k in ('game', 'created_at', 'white', 'black', 'white_version', 'black_version', 'replay_sha256')})
        games[-1]['sequence_sha256'] = seq
    command = ['gcc', '-O3', '-std=c11', '-shared', '-fPIC', '-Wall', '-Wextra',
               '-I' + str(BASE / 'src'), '-I' + str(STUDENT), '-I' + str(PROOF),
               str(HERE / 'prior.c'), str(BASE / 'src/board.c'), str(BASE / 'src/movemodel.c'),
               str(STUDENT / 'response.c'), str(PROOF / 'proof.c'), '-lm', '-pthread', '-o', str(BUILD / 'prior.so')]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (OUT / 'build.log').write_text(result.stdout); assert result.returncode == 0, result.stdout
    lib, _ = library(); lib.prior_start()
    full = np.zeros(256); cheap = np.zeros(256); moves = np.zeros(256, dtype=np.uint16)
    counts = np.zeros(256, dtype=np.uint32); total = ctypes.c_uint()
    assert lib.prior_scores(1, moves, full, counts, ctypes.byref(total)) == 20
    assert lib.prior_scores(0, moves, cheap, counts, ctypes.byref(total)) == 20
    assert abs(full[:20].sum() - 1) < 2e-6 and abs(cheap[:20].sum() - 1) < 2e-6
    buffers = [ctypes.create_string_buffer(65) for _ in range(3)]
    lib.prior_state(*buffers)
    for s in (0, 1): assert lib.prior_history(s) == mix(0, vh(buffers[s + 1].value.decode()))
    fixture = dict(opening_legal_moves=20, full_sum=float(full[:20].sum()), cheap_sum=float(cheap[:20].sum()),
                   history_count=total.value, history_hashes_agree=True)
    unique(OUT / 'preflight.json', fixture)
    deps = [Path(__file__), HERE / 'prior.c', HERE / 'README.md', BASE / 'mist', BASE / 'data/history.bin',
            *(BASE / 'src').glob('*.c'), *(BASE / 'src').glob('*.h'), MODEL, STUDENT / 'data.py',
            STUDENT / 'response.c', STUDENT / 'response.h', PROOF / 'proof.c', PROOF / 'proof.h',
            ROOT / 'learning/features.py', ROOT / 'learning/histories.py', REF,
            COHORT / 'new-game-taxonomy.jsonl.gz', data.OUT / 'manifest.json', BUILD / 'prior.so']
    plan = dict(created=now(), games=games, exclusions=exclusions, source_games=len(rows), teams=data.TEAMS,
                dependencies={str(p): sha(p) for p in deps}, compiler=command, bootstrap_seed=2241102,
                bootstrap_draws=2000, gate=dict(gain_at_least=.05, lower_ci_above=0,
                    surprise_moves_at_least=100, surprise_gain_at_least=-.02),
                primary='projected+history minus full+history log likelihood, ply//2>=8, non-suicidal target, >=2 actions',
                history='minimum3, n0=4, untempered likelihood; true actor history, not merged belief histories',
                timeout_seconds=900, cores=[2, 3], scope='Predictor screen on known true parents; no posterior or Elo claim.')
    unique(OUT / 'plan.json', plan)
    print(json.dumps(dict(games=len(games), excluded=len(exclusions), preflight=fixture, plan_sha256=sha(OUT / 'plan.json'))), flush=True)


def scores(lib, weights, tokens, legal):
    native = np.zeros(256, np.uint16); counts = np.zeros(256, np.uint32); total = ctypes.c_uint()
    raw = []
    for full in (1, 0):
        p = np.zeros(256)
        n = lib.prior_scores(full, native, p, counts, ctypes.byref(total))
        order = {uci(int(native[i])): i for i in range(n)}
        assert sorted(order) == legal
        raw.append(p[[order[m] for m in legal]])
    hc = counts[[order[m] for m in legal]].copy()
    assert int(hc.sum()) == total.value
    actions = np.array([data.encode_move(m, int(tokens[1])) for m in legal], np.uint16)
    # tokens argument keeps colour beside the already actor-canonical view.
    view = tokens[0]
    student = np.zeros(len(legal)); fatal = np.zeros(len(legal), np.uint8); witness = fatal.copy()
    assert lib.astra_response_probs(weights, view, actions, len(legal), student) == 1
    assert lib.observable_fatal(view, actions, len(legal), fatal, witness) == 1
    projected = student.copy()
    if fatal.any() and not fatal.all(): projected[fatal.astype(bool)] = 0; projected /= projected.sum()
    raw.extend([student, projected]); raw = np.array(raw)
    assert np.all(abs(raw.sum(axis=1) - 1) < 3e-6)
    # Match engine float arithmetic for the empirical blend.
    blended = ((hc.astype(np.float32)[None] + np.float32(4) * raw.astype(np.float32)) /
               np.float32(total.value + 4)).astype(float) if total.value >= 3 else raw.copy()
    assert np.all(abs(blended.sum(axis=1) - 1) < 3e-6)
    return raw, blended, fatal, total.value


def group(rows, plan):
    if not rows: return dict(decisions=0)
    gains = np.array([r['nll']['full'] - r['nll']['projected'] for r in rows])
    ids = sorted({r['game'] for r in rows}); ix = {g: i for i, g in enumerate(ids)}
    sums = np.zeros(len(ids)); counts = np.zeros(len(ids))
    for r, gain in zip(rows, gains): sums[ix[r['game']]] += gain; counts[ix[r['game']]] += 1
    rng = np.random.default_rng(plan['bootstrap_seed']); draws = []
    for _ in range(plan['bootstrap_draws']):
        sample = rng.integers(len(ids), size=len(ids)); draws.append(float(sums[sample].sum() / counts[sample].sum()))
    return dict(decisions=len(rows), games=len(ids), gain=float(gains.mean()),
                interval95=np.quantile(draws, [.025, .975]).tolist(),
                mean_nll={k: float(np.mean([r['nll'][k] for r in rows])) for k in NAMES},
                mean_raw_nll={k: float(np.mean([r['raw_nll'][k] for r in rows])) for k in NAMES},
                top1={k: float(np.mean([r['top1'][k] for r in rows])) for k in NAMES},
                history_hits=sum(r['history_count'] >= 3 for r in rows),
                zero_target_probabilities={k: sum(r['zero'][k] for r in rows) for k in NAMES})


def run():
    plan = json.loads((OUT / 'plan.json').read_text()); os.sched_setaffinity(0, set(plan['cores']))
    for p, expected in plan['dependencies'].items(): assert sha(Path(p)) == expected, p
    assert not (OUT / 'execution.json').exists()
    state = dict(started=now(), pid=os.getpid(), status='running', completed_games=0, plan_sha256=sha(OUT / 'plan.json'))
    unique(OUT / 'execution.json', state)
    def timeout(*_): raise TimeoutError('frozen 15-minute wall cap')
    signal.signal(signal.SIGALRM, timeout); signal.alarm(plan['timeout_seconds'])
    records = []; frames = proofs = 0
    try:
        spec = importlib.util.spec_from_file_location('prior_screen_referee', REF)
        ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
        lib, weights = library()
        taxonomy = {r['game']: r for r in map(json.loads, gzip.decompress((COHORT / 'new-game-taxonomy.jsonl.gz').read_bytes()).splitlines())}
        with (OUT / 'decisions.jsonl').open('x') as stream:
            for g in plan['games']:
                path = ROOT / 'data/raw/games' / g['game'] / 'replay.json'; assert sha(path) == g['replay_sha256']
                rp = json.loads(path.read_text()); game_frames = rp['frames']
                actor = {ply: (view, legal, actual) for s, key in enumerate(('white', 'black')) if rp[key] in data.TEAMS
                         for ply, view, legal, actual in data.actor_decisions(rp, s)}
                lib.prior_start(); board = ref.FowBoard()
                histories = [mix(0, vh(game_frames[0][k])) for k in ('white', 'black')]
                game_rows = []
                for ply, frame in enumerate(game_frames):
                    buffers = [ctypes.create_string_buffer(65) for _ in range(3)]
                    native_side = lib.prior_state(*buffers)
                    actual_frame = ref.make_frame(board, frame['clocks'])
                    for i, key in enumerate(('board', 'white', 'black')):
                        assert buffers[i].value.decode() == frame[key] == actual_frame[key], (g['game'], ply, key)
                    for side in (0, 1): assert lib.prior_history(side) == histories[side]
                    assert native_side == ply % 2; frames += 1
                    if ply == len(game_frames) - 1: break
                    played = game_frames[ply + 1]['move']; mover = ply % 2
                    native_played = native_move(played)
                    row = None
                    if ply in actor:
                        tokens, legal, target = actor[ply]
                        assert sorted(m.uci() for m in ref.fow_moves(board)) == legal and target == played
                        raw, blended, flags, history_n = scores(lib, weights, (tokens, mover), legal)
                        for a in np.flatnonzero(flags):
                            b = board.copy(); b.push_uci(legal[a]); king = b.king(not b.turn)
                            assert king is not None and b.is_attacked_by(b.turn, king), (g['game'], ply, legal[a])
                            proofs += 1
                        ix = legal.index(played)
                        row = dict(game=g['game'], ply=ply, side=mover, team=rp[('white', 'black')[mover]],
                            actions=len(legal), move=played, history_count=history_n,
                            nll={k: -math.log(max(float(blended[i, ix]), 1e-300)) for i, k in enumerate(NAMES)},
                            raw_nll={k: -math.log(max(float(raw[i, ix]), 1e-300)) for i, k in enumerate(NAMES)},
                            top1={k: int(blended[i].argmax() == ix) for i, k in enumerate(NAMES)},
                            zero={k: bool(blended[i, ix] == 0) for i, k in enumerate(NAMES)})
                    board.push_uci(played)
                    fatal = lib.prior_step(native_played); assert fatal >= 0
                    king = board.king(not board.turn)
                    assert bool(fatal) == bool(king is not None and board.is_attacked_by(board.turn, king))
                    if row is not None:
                        row['suicidal'] = bool(fatal); game_rows.append(row)
                    after = game_frames[ply + 1]
                    for s, key in enumerate(('white', 'black')):
                        histories[s] = mix(mix(histories[s], native_played) if s == mover else histories[s], vh(after[key]))
                # Join descriptive labels only after every prediction in this game.
                tags = {r['ply'] - 1: r['tags'] for r in taxonomy[g['game']]['moves']}
                for row in game_rows:
                    row['tags'] = tags[row['ply']]; stream.write(json.dumps(row, allow_nan=False) + '\n')
                stream.flush(); records.extend(game_rows)
                state['completed_games'] += 1; dump(OUT / 'execution.json', state)
                if state['completed_games'] % 50 == 0: print(json.dumps(dict(games=state['completed_games'], decisions=len(records))), flush=True)
        primary = [r for r in records if r['ply'] // 2 >= 8 and not r['suicidal'] and r['actions'] >= 2]
        surprise = [r for r in primary if 'capture_unseen' in r['tags']]
        main, surprise_stats = group(primary, plan), group(surprise, plan)
        gate = plan['gate']
        advance = (main['gain'] >= gate['gain_at_least'] and main['interval95'][0] > gate['lower_ci_above']
                   and surprise_stats['decisions'] >= gate['surprise_moves_at_least']
                   and surprise_stats['gain'] >= gate['surprise_gain_at_least'])
        report = dict(finished=now(), plan_sha256=sha(OUT / 'plan.json'), games=len(plan['games']), frames_validated=frames,
            observable_proofs_verified=proofs, primary=main, surprise_captures=surprise_stats,
            all_moves=group(records, plan), by_team={t: group([r for r in primary if r['team'] == t], plan) for t in data.TEAMS},
            by_tag={t: group([r for r in primary if t in r['tags']], plan) for t in ('king_threat_unseen', 'queen_raid', 'queen_exposed_unseen', 'king_move', 'capture_unseen')},
            decision='posterior_experiment_design_allowed' if advance else 'stop_blanket_prior_replacement',
            decisions_sha256=sha(OUT / 'decisions.jsonl'), zero_probability_reporting='NLL uses floor1e-300; explicit zero counts retained, including visibly suicidal terminal moves.',
            scope=plan['scope'])
        unique(OUT / 'result.json', report); state['status'] = 'complete'
        print(json.dumps({k: report[k] for k in ('games', 'primary', 'surprise_captures', 'decision')}, indent=2), flush=True)
    except BaseException as e:
        state.update(status='failed', error=f'{type(e).__name__}: {e}'); raise
    finally:
        signal.alarm(0); state.update(ended=now(), frames_validated=frames, proofs_verified=proofs)
        dump(OUT / 'execution.json', state)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('command', choices=['prepare', 'run'])
    globals()[parser.parse_args().command]()
