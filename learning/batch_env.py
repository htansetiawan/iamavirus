"""Python face of the batched C++ simulator (batch_env.cc).

    env = BatchEnv(n_games=256, max_plies=400)
    events = env.take_events(i, side)        # (k, 32, 8, 8) planes and (k, 8) scalars since the last call
    cands  = env.candidates(i)               # canonical from/to and promotion codes for the side to move
    status = env.step_all(actions)           # one candidate index per game (-1 = skip)

`benchmark()` measures raw decisions per second with uniform random play.
"""
from __future__ import annotations

import ctypes
import time

import numpy as np

from . import _native

_lib = _native.library()
_lib.fow_batch_new.restype = ctypes.c_void_p
_lib.fow_batch_new.argtypes = [ctypes.c_int, ctypes.c_int]
_lib.fow_batch_free.argtypes = [ctypes.c_void_p]
_lib.fow_batch_reset.argtypes = [ctypes.c_void_p, ctypes.c_int]
for name in ("fow_batch_side_to_move", "fow_batch_status", "fow_batch_reason", "fow_batch_plies"):
    getattr(_lib, name).argtypes = [ctypes.c_void_p, ctypes.c_int]
    getattr(_lib, name).restype = ctypes.c_int
_lib.fow_batch_board.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p]
_FP = np.ctypeslib.ndpointer(dtype=np.float32, flags="C_CONTIGUOUS")
_IP = np.ctypeslib.ndpointer(dtype=np.int32, flags="C_CONTIGUOUS")
_lib.fow_batch_take_events.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, _FP, _FP, ctypes.c_int]
_lib.fow_batch_take_events.restype = ctypes.c_int
_lib.fow_batch_candidates.argtypes = [ctypes.c_void_p, ctypes.c_int, _IP, _IP, _IP, ctypes.c_int]
_lib.fow_batch_candidates.restype = ctypes.c_int
_lib.fow_batch_danger.argtypes = [ctypes.c_void_p, ctypes.c_int, _IP, ctypes.c_int]
_lib.fow_batch_danger.restype = ctypes.c_int
_lib.fow_batch_view.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
_lib.fow_batch_step_all.argtypes = [ctypes.c_void_p, _IP, _IP, ctypes.c_int]
_lib.fow_batch_step_all.restype = ctypes.c_int
_lib.fow_batch_random_rollout.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_ulonglong, ctypes.c_int]
_lib.fow_batch_random_rollout.restype = ctypes.c_longlong

MAX_EVENTS = 4
MAX_CANDIDATES = 256


class BatchEnv:
    def __init__(self, n_games: int, max_plies: int = 400, threads: int = 1):
        self.n = n_games
        self.threads = threads
        self.h = _lib.fow_batch_new(n_games, max_plies)
        self._planes = np.zeros((MAX_EVENTS, 32 * 64), np.float32)
        self._scalars = np.zeros((MAX_EVENTS, 8), np.float32)
        self._from = np.zeros(MAX_CANDIDATES, np.int32)
        self._to = np.zeros(MAX_CANDIDATES, np.int32)
        self._promo = np.zeros(MAX_CANDIDATES, np.int32)

    def __del__(self):
        if getattr(self, "h", None):
            _lib.fow_batch_free(self.h)
            self.h = None

    def reset(self, i: int) -> None:
        _lib.fow_batch_reset(self.h, i)

    def side_to_move(self, i: int) -> int:
        return _lib.fow_batch_side_to_move(self.h, i)

    def status(self, i: int) -> int:
        return _lib.fow_batch_status(self.h, i)

    def board(self, i: int) -> str:
        buf = ctypes.create_string_buffer(65)
        _lib.fow_batch_board(self.h, i, buf)
        return buf.value.decode()

    def take_events(self, i: int, side: int):
        k = _lib.fow_batch_take_events(self.h, i, side, self._planes, self._scalars, MAX_EVENTS)
        return self._planes[:k].reshape(k, 32, 8, 8).copy(), self._scalars[:k].copy()

    def candidates(self, i: int):
        k = _lib.fow_batch_candidates(self.h, i, self._from, self._to, self._promo, MAX_CANDIDATES)
        return self._from[:k].copy(), self._to[:k].copy(), self._promo[:k].copy()

    def danger(self, i: int) -> np.ndarray:
        """1 per candidate (candidate order) that leaves the mover's king capturable on the true board."""
        out = np.zeros(MAX_CANDIDATES, np.int32)
        k = _lib.fow_batch_danger(self.h, i, out, MAX_CANDIDATES)
        return out[:k].copy()

    def view(self, i: int, side: int) -> str:
        buf = ctypes.create_string_buffer(66)
        _lib.fow_batch_view(self.h, i, side, buf)
        return buf.value.decode()

    def step_all(self, actions: np.ndarray) -> np.ndarray:
        status = np.zeros(self.n, np.int32)
        _lib.fow_batch_step_all(self.h, np.ascontiguousarray(actions, dtype=np.int32), status, self.threads)
        return status


def benchmark(n_games: int = 256, steps: int = 200, threads: int = 1) -> float:
    env = BatchEnv(n_games, threads=threads)
    started = time.time()
    decisions = _lib.fow_batch_random_rollout(env.h, steps, 1, threads)
    rate = decisions / (time.time() - started)
    return rate


if __name__ == "__main__":
    for threads in (1, 2, 4):
        print(f"{threads} thread(s): {benchmark(threads=threads):,.0f} decisions/s (uniform random play, rules + features)")
