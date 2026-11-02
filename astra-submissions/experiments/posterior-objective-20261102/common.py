from pathlib import Path
import ctypes
import hashlib
import os
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/posterior-objective-20261102'
BASE = HERE.parent / 'full-prior-cost-20261102/build-r2/sparse/src'
HISTORY = HERE.parent / 'queen-terminal-backport-20261102/build-r2/base/data/history.bin'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


class Row(ctypes.Structure):
    _fields_ = [('key', ctypes.c_uint64), ('castle', ctypes.c_uint64),
                ('x', ctypes.c_float * 26), ('base', ctypes.c_float),
                ('history_count', ctypes.c_uint32), ('move', ctypes.c_uint16),
                ('ep', ctypes.c_int8), ('side', ctypes.c_int8),
                ('halfmove', ctypes.c_int32), ('board', ctypes.c_char * 65)]


DTYPE = np.dtype({'names': [name for name, _ in Row._fields_],
    'formats': ['<u8', '<u8', ('<f4', 26), '<f4', '<u4', '<u2', 'i1', 'i1', '<i4', 'S65'],
    'offsets': [getattr(Row, name).offset for name, _ in Row._fields_],
    'itemsize': ctypes.sizeof(Row)})


def array(pointer, n):
    return np.frombuffer(ctypes.string_at(pointer, n * ctypes.sizeof(Row)), dtype=DTYPE).copy()


def library():
    for key in list(os.environ):
        if key.startswith('MIST_'):
            del os.environ[key]
    os.environ.update(MIST_THREADS='2', MIST_MODEL_TEMP='2', MIST_MODEL_FULL_BELOW='10000',
                      MIST_HISTORY_TABLE=str(HISTORY))
    lib = ctypes.CDLL(str(HERE / 'build/bridge.so'))
    lib.pl_start.argtypes = [ctypes.c_int]
    lib.pl_count.restype = ctypes.c_size_t
    lib.pl_own.argtypes = [ctypes.c_uint16, ctypes.c_char_p]
    lib.pl_own.restype = ctypes.c_size_t
    lib.pl_opponent.argtypes = [ctypes.c_char_p]
    lib.pl_opponent.restype = ctypes.c_size_t
    lib.pl_position.argtypes = [ctypes.c_size_t]
    lib.pl_position.restype = ctypes.POINTER(Row)
    lib.pl_parent.argtypes = [ctypes.c_size_t, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int),
                             ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint)]
    lib.pl_parent.restype = ctypes.POINTER(Row)
    lib.pl_load()
    return lib


def encode(uci):
    sq = lambda s: ord(s[0]) - 97 + 8 * (int(s[1]) - 1)
    return sq(uci[:2]) | sq(uci[2:4]) << 6 | (('pnbrqk'.index(uci[4]) if len(uci) == 5 else 6) << 12)


def position_tuple(row):
    return (bytes(row['board']).decode(), int(row['side']), int(row['castle']), int(row['ep']))


class StateKey:
    """Independent implementation of the published position_key equivalence.

    Halfmove and history are deliberately absent, as in the production merge.
    """
    def __init__(self):
        state = 20261009
        def next64():
            nonlocal state
            mask = 2**64 - 1
            state = (state + 0x9E3779B97F4A7C15) & mask
            z = state
            z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & mask
            z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & mask
            return z ^ (z >> 31)
        self.piece = [[[next64() for _ in range(64)] for _ in range(6)] for _ in range(2)]
        self.side = next64(); self.castle = []; self.ep = []
        for _ in range(64):
            self.castle.append(next64()); self.ep.append(next64())

    def __call__(self, board, side, castle, ep):
        key = self.side if side else 0
        for sq, piece in enumerate(board):
            if piece != '-':
                key ^= self.piece[int(piece.islower())]['pnbrqk'.index(piece.lower())][sq]
        for sq in range(64):
            if castle >> sq & 1:
                key ^= self.castle[sq]
        if ep >= 0:
            key ^= self.ep[ep]
        return key | 1
