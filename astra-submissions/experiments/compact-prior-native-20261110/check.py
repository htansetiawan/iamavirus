"""Compile an isolated native implementation and compare exact features and cost."""
import ctypes as C
import importlib.util
import itertools
import json
from pathlib import Path
import os
import signal
import subprocess
import time

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('holdout', EXPERIMENTS/'compact-prior-holdout-20261110/run.py')
holdout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(holdout)
from features import structural

BASE = EXPERIMENTS/'guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren/src'
OUT = holdout.ANALYSIS/HERE.name
BUILD = holdout.SPOOL/HERE.name
STATE = holdout.CACHE
PASSED = holdout.OUT


def freeze():
    result, receipt = (holdout.read(PASSED/name) for name in ('result.json', 'terminal-verification.json'))
    assert receipt['result_sha256'] == holdout.sha(PASSED/'result.json')
    assert result['decision'] == 'native_cost_design_allowed'
    old = holdout.read(PASSED/'plan.json')
    deps = dict(old['dependencies'])
    extra = [*HERE.glob('*'), *BASE.glob('*.[ch]'), *(PASSED/name for name in ('plan.json', 'result.json', 'terminal-verification.json'))]
    deps.update({str(p): holdout.sha(p) for p in extra if p.is_file()})
    plan = dict(at=holdout.now(), dependencies=deps, cores=[2, 3], max_seconds=600, samples=64,
                sample_salt='compact-native342:', batch=256, timing_repeats=2,
                exact_speed_ratio_max=.90, compact_ratio_max=1.05, parity_tolerance=.0001,
                minimum_parents=4_000, minimum_moves=100_000,
                scope='Isolated full-mode feature, compact score and CPU cost comparison on prior training trajectories. Cheap regime and deployed engine untouched.')
    OUT.mkdir(exist_ok=False)
    holdout.write(OUT/'plan.json', plan, exclusive=True)
    print(json.dumps(dict(pins=len(deps), plan_sha256=holdout.sha(OUT/'plan.json'))), flush=True)


def export_weights(model):
    names = dict(piece='piece.weight', visibility='visibility.weight', castling='castling.weight',
                 en_passant='en_passant.weight', halfmove='halfmove.weight', halfmove_bias='halfmove.bias',
                 source='source.weight', target='target.weight', promotion='promotion.weight',
                 feature='move_features.weight', scalar='scalar.weight')
    state = model.state_dict()
    def literal(values):
        return '{' + ','.join(literal(x) if np.ndim(x) else float(x).hex()+'f' for x in values) + '}'
    output = []
    for name, key in names.items():
        value = state[key].numpy()
        if name == 'feature':
            value = value.T
        elif name in ('halfmove', 'scalar'):
            value = value.reshape(-1)
        shape = ''.join(f'[{size}]' for size in value.shape)
        output.append(f'static const float compact_{name}{shape} = {literal(value)};\n')
    (BUILD/'weights.h').write_text(''.join(output))


def build(model):
    BUILD.mkdir(exist_ok=False)
    export_weights(model)
    original = (BASE/'movemodel.c').read_text()
    fast = original
    substitutions = (
        ('    if (is_attacked(&q, to, other)) {',
         '    const int destination_attacked = is_attacked(&q, to, other);\n    if (destination_attacked) {'),
        ("        char seen[65];\n        observation(&q, other, seen);\n        if (seen[to] == '?') {",
         '''        /* The moved piece occupies to. It is visible iff the opponent
         * can capture on to, or sees the victim of an en-passant capture. */
        bb_t adjacent = 0;
        if (q.ep >= 0) {
            if (to % 8 > 0) adjacent |= UINT64_C(1) << (to - 1);
            if (to % 8 < 7) adjacent |= UINT64_C(1) << (to + 1);
        }
        const int ep_visible = (adjacent & q.by_color[other] & q.by_type[PAWN]) != 0;
        if (!destination_attacked && !ep_visible) {'''),
    )
    for before, after in substitutions:
        assert fast.count(before) == 1
        fast = fast.replace(before, after)
    edited = BUILD/'movemodel.c'
    edited.write_text(fast + '\n' + (HERE/'folded.c').read_text())
    common = ['gcc', '-O3', '-std=c11', '-fPIC', '-ffp-contract=off', '-Wall', '-Wextra', '-I'+str(BASE)]
    commands = [common + ['-Dmove_features=original_move_features', '-Dmove_logits=original_move_logits',
                          '-c', str(BASE/'movemodel.c'), '-o', str(BUILD/'original.o')],
                common + ['-shared', str(edited), str(BASE/'board.c'), str(HERE/'check.c'), str(BUILD/'original.o'),
                          '-lm', '-o', str(BUILD/'check.so')]]
    for command in commands:
        subprocess.run(command, check=True, timeout=30)
    return {path.name: holdout.sha(path) for path in (edited, BUILD/'weights.h', BUILD/'check.so', BUILD/'original.o')}


class Native:
    def __init__(self):
        self.lib = C.CDLL(str(BUILD/'check.so'))
        self.lib.fow_init()
        nd = lambda dtype: np.ctypeslib.ndpointer(dtype=dtype, flags='C_CONTIGUOUS')
        self.lib.check_parent.argtypes = [C.c_char_p, C.c_int, C.c_uint64, C.c_int, C.c_int,
                                          C.c_uint16, C.c_int, nd(np.uint16), *[nd(np.float32)]*3, nd(np.uint32)]
        self.lib.time_parents.argtypes = [C.c_int]
        self.lib.time_parents.restype = C.c_double
        self.moves = np.zeros(256, np.uint16)
        self.base, self.logp, self.residual = [np.zeros(256, np.float32) for _ in range(3)]
        self.special = np.zeros(3, np.uint32)

    def parent(self, full, side, castle, ep, half, previous, keep):
        count = self.lib.check_parent(full.encode(), side, castle, ep, half, previous, keep,
                                      self.moves, self.base, self.logp, self.residual, self.special)
        assert count > 0, (count, full, side, castle, ep, half, previous)
        return count


def fixture(native):
    # Move-list coverage includes en-passant visibility after a double push,
    # capture of its victim, edge-file guards, promotions, and castling.
    def make(pieces, side, castle=0, ep=-1):
        board = ['-']*64
        for square, piece in pieces.items():
            board[ord(square[0])-97+8*(int(square[1])-1)] = piece
        return native.parent(''.join(board), side, castle, ep, 0, 0, False)
    counts = []
    for file, adjacent in (('a', 'b'), ('e', 'd'), ('h', 'g')):
        for side in (0, 1):
            kings = {'e1': 'K', 'e8': 'k'}
            home, advanced, victim, own, their = (('2', '4', '4', 'P', 'p') if side == 0 else ('7', '5', '5', 'p', 'P'))
            counts.append(make({**kings, file+home: own, adjacent+victim: their}, side))
            ep = ord(file)-97 + (16 if side == 0 else 40)
            counts.append(make({**kings, file+advanced: own, adjacent+victim: their}, side^1, ep=ep))
    counts.append(make({'a1':'R','e1':'K','h1':'R','e8':'k','a7':'P'}, 0, castle=129))
    return len(counts), sum(counts)


@torch.no_grad()
def execute(plan, old):
    model = holdout.load_models(old)['hard']
    artifacts = build(model)
    native = Native()
    fixtures, fixture_actions = fixture(native)
    assert (native.special > 0).all()
    producer = holdout.Producer(old['native_state_library'])
    previous = {row['sequence_sha256'] for row in holdout.read(holdout.SEQUENCE_EXCLUSIONS[-1])}
    from hashlib import sha256
    cache = holdout.Cache(STATE)
    try:
        games = sorted((row for row in cache.games if row['split']=='train' and row['sequence_sha256'] in previous),
                       key=lambda g: sha256((plan['sample_salt']+g['sequence_sha256']).encode()).digest())[:plan['samples']]
        assert len(games) == plan['samples']
        parent_count = actions = capture_count = 0
        error = residual_error = 0.
        rows, saved, capture = [], [], []

        def compare():
            b = holdout.batch(rows)
            delta = model(b)
            no_history = torch.zeros_like(b['history_n'])
            prediction = holdout.quiet_logp(b['base'], delta, b['valid'], b['capture'], b['counts'], no_history)
            nonlocal error, residual_error
            for i, ((actual_logp, actual_residual), skip) in enumerate(zip(saved, capture)):
                n = len(actual_logp)
                error = max(error, float(abs(prediction[i, :n].numpy()-actual_logp).max()))
                residual_error = max(residual_error, float(abs(delta[i, :n].numpy()[~skip]-actual_residual[~skip]).max(initial=0)))
            rows.clear(); saved.clear(); capture.clear()

        for game in games:
            prior = 0
            for inputs, meta in holdout.contexts(producer, cache, game, True):
                full = producer.buffers[0].value.decode()
                _, _, _, _, half, side = inputs['board']
                n = native.parent(full, int(side), producer.native.castle.value, producer.native.ep.value, int(half), prior, True)
                assert n == len(inputs['native_moves']) and np.array_equal(native.moves[:n], inputs['native_moves'])
                prior = int(inputs['native_moves'][meta['target']])
                skip = inputs['x'][:, 0]>0
                parent_count += 1
                actions += n
                capture_count += int(skip.sum())
                rows.append(inputs); saved.append((native.logp[:n].copy(), native.residual[:n].copy())); capture.append(skip)
                if len(rows)==plan['batch']:
                    compare()
        if rows:
            compare()
    finally:
        cache.close()
    for arm in range(3):
        assert native.lib.time_parents(arm) > 0
    timings = []
    for order in itertools.permutations(range(3)):
        for _ in range(plan['timing_repeats']):
            seconds = [0.]*3
            for arm in order:
                seconds[arm] = native.lib.time_parents(arm)
            assert min(seconds) > 0
            timings.append(dict(order=order, cpu_seconds=seconds))
    ratio = {key: float(np.median([row['cpu_seconds'][i]/row['cpu_seconds'][j] for row in timings]))
             for key, i, j in (('exact_over_original',1,0), ('compact_over_original',2,0), ('compact_over_exact',2,1))}
    conditions = dict(parity=max(error, residual_error)<plan['parity_tolerance'],
                      coverage=parent_count>=plan['minimum_parents'] and actions>=plan['minimum_moves'],
                      exact_cost=ratio['exact_over_original']<=plan['exact_speed_ratio_max'],
                      compact_cost=ratio['compact_over_original']<=plan['compact_ratio_max'])
    return dict(at=holdout.now(), conditions=conditions, decision='sequential_design_allowed' if all(conditions.values()) else 'close_native_configuration',
                parents=parent_count, actions=actions, games=len(games), fixture_positions=fixtures, fixture_actions=fixture_actions,
                capture_entries=capture_count, specials=dict(zip(('promotions','castles','en_passant'), map(int, native.special))),
                logp_max_error=error, quiet_residual_max_error=residual_error, ratio=ratio, timings=timings,
                compiled_hashes=artifacts, plan_sha256=holdout.sha(OUT/'plan.json'))


def main():
    import sys
    if sys.argv[1:] == ['freeze']:
        freeze()
        return
    assert sys.argv[1:] == ['run']
    plan = holdout.read(OUT/'plan.json')
    old = holdout.read(PASSED/'plan.json')
    for path, expected in plan['dependencies'].items():
        assert holdout.sha(path) == expected, path
    os.sched_setaffinity(0, set(plan['cores']))
    torch.set_num_threads(2)
    torch.set_float32_matmul_precision('highest')
    start = time.monotonic()
    def timeout(*_):
        raise TimeoutError('native prior CPU bound exceeded')
    signal.signal(signal.SIGALRM, timeout)
    # Keep the shared reservation owner distinct from the earlier holdout.
    holdout.OWNER = 'astra-'+HERE.name
    with holdout.lease(plan['cores']):
        receipt = dict(status='running', started_at=holdout.now(), plan_sha256=holdout.sha(OUT/'plan.json'))
        holdout.write(OUT/'execution.json', receipt, exclusive=True)
        signal.alarm(plan['max_seconds'])
        try:
            result = execute(plan, old)
            holdout.write(OUT/'result.json', result, exclusive=True)
            receipt.update(status='complete', result_sha256=holdout.sha(OUT/'result.json'))
            print(json.dumps({key: result[key] for key in ('parents','actions','ratio','conditions','decision')}), flush=True)
        except BaseException as exc:
            receipt.update(status='failed', error=repr(exc))
            raise
        finally:
            signal.alarm(0)
            receipt.update(ended_at=holdout.now(), seconds=time.monotonic()-start)
            holdout.write(OUT/'execution.json', receipt)


if __name__ == '__main__':
    main()
