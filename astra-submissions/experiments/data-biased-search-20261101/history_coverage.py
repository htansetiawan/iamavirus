#!/usr/bin/env python3
"""Post-screen coverage on actual opponent histories; no policy inputs change."""
import ctypes
import json
from pathlib import Path
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/data-biased-search-20261101'
BASE = HERE.parent/'stable-mix-20261101/build/base'
sys.path.insert(0, str(ROOT))
from learning import ingest

MASK = (1 << 64)-1


def view_hash(view):
    h = 1469598103934665603
    for b in view.encode(): h = ((h ^ b)*1099511628211) & MASK
    return h


def mix(h, value):
    z = (h + 0x9E3779B97F4A7C15*(value | 1)) & MASK
    z = ((z ^ (z >> 30))*0xBF58476D1CE4E5B9) & MASK
    z = ((z ^ (z >> 27))*0x94D049BB133111EB) & MASK
    return z ^ (z >> 31)


def encode(move):
    def square(text): return ord(text[0])-97 + 8*(int(text[1])-1)
    promo = {'n':1, 'b':2, 'r':3, 'q':4}[move[4]] if len(move) == 5 else 6
    return square(move[:2]) | square(move[2:4]) << 6 | promo << 12


def main():
    libpath = HERE/'build/hash-reference.so'
    subprocess.run(['gcc', '-O2', '-shared', '-fPIC', '-std=c11',
                    *[str(BASE/'src'/f) for f in ['board.c', 'belief.c', 'movemodel.c']],
                    '-lm', '-pthread', '-o', str(libpath)], check=True)
    lib = ctypes.CDLL(str(libpath))
    lib.view_hash.argtypes = [ctypes.c_char_p]; lib.view_hash.restype = ctypes.c_uint64
    lib.history_mix.argtypes = [ctypes.c_uint64, ctypes.c_uint64]; lib.history_mix.restype = ctypes.c_uint64
    lib.move_to_uci.argtypes = [ctypes.c_uint16, ctypes.c_char_p]
    for move in ['e2e4', 'e1g1', 'e8c8', 'e5d6', 'h7h8n', 'a2a1q', 'a7b8r', 'g2g1b']:
        text = ctypes.create_string_buffer(6); lib.move_to_uci(encode(move), text)
        assert text.value.decode() == move
    table = (BASE/'data/history.bin').read_bytes()
    assert table[:8] == b'MISTHIST' and struct.unpack_from('<II', table, 8) == (1, (len(table)-16)//16)
    counts = {}
    for h, move, count in struct.iter_unpack('<QII', table[16:]): counts.setdefault(h, {})[move] = count
    plan = json.loads((OUT/'plan.json').read_text()); rows = []; parity = 0
    for game in plan['games']:
        replay = json.loads((ROOT/'data/raw/games'/game['game']/'replay.json').read_text())
        states, errors = ingest.validate_replay(replay); assert not errors
        side = 1-game['side']; key = ['white', 'black'][side]; h = 0
        for ply, frame in enumerate(replay['frames']):
            if ply and (ply-1) % 2 == side:
                code = encode(frame['move']); expected = lib.history_mix(h, code)
                h = mix(h, code); assert h == expected; parity += 1
            v = view_hash(frame[key]); assert v == lib.view_hash(frame[key].encode()); parity += 1
            expected = lib.history_mix(h, v); h = mix(h, v); assert h == expected; parity += 1
            if ply % 2 != side or ply == len(states)-1: continue
            available = counts.get(h, {}); N = sum(available.values())
            legal = {encode(m) for m in states[ply].board.legal_moves()}
            supported = N >= 3 and all(m in legal for m in available)
            actual = encode(replay['frames'][ply+1]['move'])
            rows.append(dict(game=game['game'], opponent=game['opponent'], ply=ply, own_turn=ply//2+1,
                             history=f'{h:016x}', count=N, supported=supported,
                             actual_count=available.get(actual, 0), confidence=.5*N/(20+N) if supported else 0))
    groups = []
    for lo, hi in [(1, 4), (5, 8), (9, 12), (13, 20), (21, 1000)]:
        group = [r for r in rows if lo <= r['own_turn'] <= hi]
        groups.append(dict(own_turns=[lo, hi], decisions=len(group), supported=sum(r['supported'] for r in group),
                           actual_move_in_table=sum(r['supported'] and r['actual_count'] > 0 for r in group)))
    result = dict(scope='Descriptive actual opponent-history coverage on the same eight games; not sampled search-world coverage or a strength estimate.',
                  native_hash_parity_checks=parity, native_move_codec_cases=8, decisions=len(rows),
                  groups=groups, rows=rows)
    (OUT/'actual-history-coverage.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'rows'}, indent=2))


if __name__ == '__main__': main()
