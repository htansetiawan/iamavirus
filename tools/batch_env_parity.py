"""Parity test: the batched C++ simulator's input planes equal learning/features.py on random games.

    python tools/batch_env_parity.py
"""
import sys, random, ctypes
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from learning import _native, features, rules
from learning import batch_env as be
lib = _native.library()
lib.fow_batch_view.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
lib.fow_batch_last_move.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p]
rng = random.Random(3)
env = be.BatchEnv(8, max_plies=160)
views = {i: {0: [], 1: []} for i in range(8)}; phases = {i: {0: [], 1: []} for i in range(8)}
plies = {i: {0: [], 1: []} for i in range(8)}; own = {i: {0: {}, 1: {}} for i in range(8)}
got = {i: {0: [], 1: []} for i in range(8)}
buf = ctypes.create_string_buffer(66)
def record(i, side, phase, ply):
    lib.fow_batch_view(env.h, i, side, buf); views[i][side].append(buf.value.decode()); phases[i][side].append(phase); plies[i][side].append(ply)
for i in range(8):
    for side in (0, 1):
        record(i, side, 0, 0)
        p, s = env.take_events(i, side); got[i][side].append(p)
done = [False] * 8
for step in range(160):
    actions = np.full(8, -1, np.int32)
    movers = {}
    for i in range(8):
        if done[i]: continue
        f, t, pr = env.candidates(i)
        if len(f) == 0: done[i] = True; continue
        actions[i] = rng.randrange(len(f)); movers[i] = env.side_to_move(i)
    if not movers: break
    status = env.step_all(actions)
    for i, mover in movers.items():
        lib.fow_batch_last_move(env.h, i, buf); mv = buf.value.decode()
        own[i][mover][len(views[i][mover]) - 1] = mv
        if status[i] != 0: done[i] = True; continue
        ply = env_ply = len(views[i][0]) + len(views[i][1])  # not used
        for side in (0, 1):
            record(i, side, 1 if side == mover else 2, step + 1)
            p, s = env.take_events(i, side); got[i][side].append(p)
worst = 0.0; events = 0
for i in range(8):
    for side in (0, 1):
        n = len(views[i][side])
        own_map = {k: v for k, v in own[i][side].items() if k < n}
        planes, scalars = features.replay_events(side, views[i][side], phases[i][side], plies[i][side], own_map)
        c = np.concatenate(got[i][side]).reshape(-1, 32, 8, 8)
        m = min(len(c), len(planes)); events += m
        worst = max(worst, float(np.abs(c[:m] - planes[:m]).max()))
print(f"parity: {events} observation events compared across 16 game sides; worst plane difference {worst:.2e}")

assert worst == 0.0, "batched simulator features differ from features.py"
