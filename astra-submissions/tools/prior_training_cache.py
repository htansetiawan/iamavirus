"""Ragged, lossless native prior features. Privileged world data, not actor input.

This is the original 293 feature representation and original TRAIN selection,
not a learned compression scheme, independent dataset, new prior or policy.
"""
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

CANDIDATE = np.dtype([
    ('x', '<f4', (26,)), ('base', '<f4', (2,)), ('history', '<u4'),
    ('move', '<u2'), ('surprise', 'u1'), ('reserved', 'u1')])
CONTEXT = struct.Struct('<QIIHHHBB')
SCHEMA = 'astra-original293-ragged-v1'
assert CANDIDATE.itemsize == 120 and CONTEXT.size == 24


def native_move(value):
    """Cache none/q/r/b/n -> native none/q/r/b/n = 6/4/3/2/1."""
    promo = value >> 12
    if not 0 <= value < 65535 or promo > 4:
        raise ValueError('cache move')
    return (value & 4095) | ((6, 4, 3, 2, 1)[promo] << 12)


def cache_move(value):
    promotion = {6: 0, 4: 1, 3: 2, 2: 3, 1: 4}.get(value >> 12)
    if not 0 <= value <= 65535 or promotion is None:
        raise ValueError('native move')
    return (value & 4095) | (promotion << 12)


def update_digest(digest, rows, target, history_total):
    """Exact byte order of original train.collect(), including uint32 counts."""
    for value in (rows['x'], rows['base'], rows['history'],
                  np.array([target, history_total], dtype='<i8')):
        digest.update(np.ascontiguousarray(value).tobytes())


class PriorCache:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.manifest = json.loads((self.folder / 'manifest.json').read_text())
        if self.manifest['schema'] != SCHEMA:
            raise ValueError('prior cache schema')
        for name in ('candidates.bin', 'contexts.bin'):
            with (self.folder / name).open('rb') as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != self.manifest['sha256'][name]:
                    raise ValueError('prior cache checksum: ' + name)
        self.rows = np.memmap(self.folder / 'candidates.bin', dtype=CANDIDATE, mode='r')
        self.contexts = (self.folder / 'contexts.bin').read_bytes()
        if len(self.contexts) != self.manifest['contexts'] * CONTEXT.size:
            raise ValueError('prior context size')
        if len(self.rows) != self.manifest['candidates']:
            raise ValueError('prior candidate count')

    def record(self, number):
        if not 0 <= number < self.manifest['contexts']:
            raise IndexError(number)
        context = CONTEXT.unpack_from(self.contexts, number * CONTEXT.size)
        start, _, _, target, count, _, _, _ = context
        if not 0 <= target < count or start + count > len(self.rows):
            raise ValueError('prior context range')
        return context, self.rows[start:start + count]
