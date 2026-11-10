import ctypes as C
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BUILD = HERE/'build'
OUT = ROOT/'astra-submissions/analysis/cap-weight-20261110'
SOURCE = HERE.parent/'guard-controls-20261109/build/src'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def library():
    lib = C.CDLL(str(BUILD/'cap.so'))
    f32 = np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags='C_CONTIGUOUS')
    f64 = np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='C_CONTIGUOUS')
    u32 = np.ctypeslib.ndpointer(dtype=np.uint32, ndim=1, flags='C_CONTIGUOUS')
    u64 = np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, flags='C_CONTIGUOUS')
    lib.astra_cap_corrected.argtypes = [C.c_double, C.c_double]
    lib.astra_cap_corrected.restype = C.c_double
    lib.astra_cap_uniforms.argtypes = [C.POINTER(C.c_uint64), C.c_size_t, f64]
    lib.astra_cap_draw.argtypes = [f32, C.c_size_t, C.c_size_t, C.POINTER(C.c_uint64), C.c_int,
                                   u32, f64, C.POINTER(C.c_double)]
    lib.astra_cap_draw.restype = C.c_int
    lib.astra_native_shrink_verify.argtypes = [f32, C.c_size_t, C.c_size_t, C.c_uint64]
    lib.astra_native_shrink_verify.restype = C.c_int
    lib.astra_cap_batch.argtypes = [f32, u64, C.c_size_t, C.c_size_t, C.c_int, C.c_uint64, C.c_size_t,
                                   f64, f64, f64, f64]
    lib.astra_cap_batch.restype = C.c_int
    return lib


def draw(lib, lw, keep, seed, partition=0):
    idx = np.zeros(min(keep, len(lw)), np.uint32)
    adjusted = np.zeros(len(idx), np.float64)
    rng, cutoff = C.c_uint64(seed), C.c_double()
    k = lib.astra_cap_draw(lw, len(lw), keep, C.byref(rng), partition, idx, adjusted, C.byref(cutoff))
    assert k == len(idx)
    return idx, adjusted, cutoff.value, rng.value
