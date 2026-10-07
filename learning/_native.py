"""Builds and loads the shared library exposing the C++ rules and engine.

The learning code never carries a second copy of the rules. `librules.so` is
compiled from the engine sources in the repository root into `build/`, which is
ignored by git, and rebuilt whenever a source is newer than the library.
"""
from __future__ import annotations

import ctypes
import fcntl
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT / "build"
LIBRARY = BUILD_DIR / "librules.so"

SOURCES = [
    "rules_capi.cc", "engine.cc", "belief.cc", "search.cc", "evaluation.cc",
    "observation.cc", "transposition.cc", "regret.cc", "position.cc",
    "move.cc", "bitboard.cc", "opponent_model.cc",
]
HEADERS = [
    "bitboard.h", "move.h", "position.h", "observation.h", "evaluation.h",
    "transposition.h", "search.h", "belief.h", "regret.h", "engine.h",
    "piece_square.h", "opponent_model.h", "opponent_weights.h",
]


def _stale() -> bool:
    if not LIBRARY.exists():
        return True
    built = LIBRARY.stat().st_mtime
    for name in SOURCES + HEADERS:
        if (ROOT / name).stat().st_mtime > built:
            return True
    return False


def ensure_built(verbose: bool = True) -> Path:
    BUILD_DIR.mkdir(exist_ok=True)
    with open(BUILD_DIR / ".build.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if _stale():
            compiler = os.environ.get("CXX", "g++")
            command = [compiler, "-O2", "-std=c++20", "-shared", "-fPIC",
                       "-DNDEBUG", "-mpopcnt", "-o", str(LIBRARY)]
            command += [str(ROOT / name) for name in SOURCES]
            if verbose:
                print(f"[rules] building {LIBRARY.name}", file=sys.stderr)
            subprocess.run(command, check=True, cwd=ROOT)
    return LIBRARY


_library: ctypes.CDLL | None = None


def library() -> ctypes.CDLL:
    global _library
    if _library is None:
        path = ensure_built()
        lib = ctypes.CDLL(str(path))
        c_void = ctypes.c_void_p
        c_str = ctypes.c_char_p
        c_u64 = ctypes.c_ulonglong
        signatures = {
            "fow_initialize": ([], None),
            "fow_position_new": ([], c_void),
            "fow_position_clone": ([c_void], c_void),
            "fow_position_free": ([c_void], None),
            "fow_position_set_fen": ([c_void, c_str], ctypes.c_int),
            "fow_position_set_board": ([c_void, c_str, ctypes.c_int, c_u64, ctypes.c_int], ctypes.c_int),
            "fow_position_board": ([c_void, c_str], None),
            "fow_position_observation": ([c_void, ctypes.c_int, c_str], None),
            "fow_position_visible": ([c_void, ctypes.c_int], c_u64),
            "fow_position_side": ([c_void], ctypes.c_int),
            "fow_position_en_passant": ([c_void], ctypes.c_int),
            "fow_position_castling": ([c_void], c_u64),
            "fow_position_halfmove": ([c_void], ctypes.c_int),
            "fow_position_set_halfmove": ([c_void, ctypes.c_int], None),
            "fow_position_repetition_key": ([c_void], c_u64),
            "fow_position_legal_moves": ([c_void, c_str, ctypes.c_int], ctypes.c_int),
            "fow_position_push": ([c_void, c_str], ctypes.c_int),
            "fow_position_mover_lost": ([c_void], ctypes.c_int),
            "fow_position_king_square": ([c_void, ctypes.c_int], ctypes.c_int),
            "fow_position_piece_at": ([c_void, ctypes.c_int], ctypes.c_int),
            "fow_position_is_attacked": ([c_void, ctypes.c_int, ctypes.c_int], ctypes.c_int),
            "fow_move_loses_king": ([c_void, c_str], ctypes.c_int),
            "fow_legal_from_observation": ([c_str, ctypes.c_int, c_u64, ctypes.c_int, c_str, ctypes.c_int], ctypes.c_int),
            "fow_infer_en_passant": ([c_str, c_str, ctypes.c_int], ctypes.c_int),
            "fow_engine_new": ([ctypes.c_int, ctypes.c_double, ctypes.c_double, c_u64, c_u64, ctypes.c_int], c_void),
            "fow_engine_free": ([c_void], None),
            "fow_engine_observe": ([c_void, c_str, ctypes.c_int], ctypes.c_int),
            "fow_engine_choose": ([c_void, c_str, ctypes.c_double, c_str], ctypes.c_int),
            "fow_engine_notify": ([c_void, c_str], None),
        }
        for name, (argtypes, restype) in signatures.items():
            function = getattr(lib, name)
            function.argtypes = argtypes
            function.restype = restype
        lib.fow_initialize()
        _library = lib
    return _library
