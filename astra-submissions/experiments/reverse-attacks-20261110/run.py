"""Validate target-centric attack queries on the rules-checked replay cache."""
from collections import Counter
import ctypes as C
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import signal
from statistics import median
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPERIMENTS = HERE.parent
ANALYSIS = ROOT/'astra-submissions/analysis'
OUT = ANALYSIS/HERE.name
STORE = ROOT/'data/astra-spool'
CACHE = STORE/'recovered-replay-cache-20261110'
BUILD = STORE/HERE.name
BASE = EXPERIMENTS/'guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren/src'
TOOLS = ROOT/'astra-submissions/tools'
sys.path.insert(0, str(TOOLS))
from reconstructed_cache import Cache, fields
from experience_index import unpack_view


def sha(path):
    with Path(path).open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, obj):
    with Path(path).open('x') as file:
        json.dump(obj, file, indent=2, allow_nan=False)
        file.write('\n')


def now():
    return datetime.now(timezone.utc).isoformat()


def select(games, count):
    candidates = [row for row in games if row['split']=='train']
    assert len(candidates)>=count
    return sorted(candidates, key=lambda row: hashlib.sha256(
        ('reverse-attacks344:'+row['sequence_sha256']).encode()).digest())[:count]


def freeze():
    audited = ANALYSIS/'recovered-replay-cache-20261110/terminal-verification.json'
    assert sha(CACHE/'manifest.json')==read(audited)['manifest_sha256']
    games = select(read(CACHE/'games.json'), 192)
    frames = sum(row['records'] for row in games)
    assert 10_000<=frames<=32_000
    pins = [*HERE.glob('*.py'), *HERE.glob('*.c'), BASE/'board.c', BASE/'fow.h', audited,
            TOOLS/'reconstructed_cache.py', TOOLS/'experience_index.py',
            *(CACHE/name for name in ('manifest.json','games.json','records.bin'))]
    plan = dict(at=now(), games=len(games), frames=frames, synthetic=384, seed=3441110,
                child_stride=19, core=6, timeout_seconds=240, timing_pairs=12,
                ratio_limit=.75, child_min=20_000, pins={str(p):sha(p) for p in sorted(pins)},
                trajectory_hash=hashlib.sha256('\n'.join(row['sequence_sha256'] for row in games).encode()).hexdigest(),
                scope='Native rule-equivalence and bounded feature/guard-shaped attack workload. No search, belief, model or arena change.')
    OUT.mkdir(exist_ok=False)
    save(OUT/'plan.json', plan)
    print(json.dumps(dict(pins=len(pins), frames=frames, plan_sha256=sha(OUT/'plan.json'))), flush=True)


def build():
    BUILD.mkdir(exist_ok=False)
    before = (BASE/'board.c').read_text()
    start = before.index('int is_attacked(')
    end = before.index('\n}\n',start)+3
    original = before[start:end]
    assert original.count('is_attacked(')==1
    code = before[:start]+(HERE/'attack.c').read_text()+before[end:]
    point = 'void fow_init(void) {\n'
    assert code.count(point)==1
    code = code.replace(point, 'static void init_attack_queries(void);\n\n'+point+'    init_attack_queries();\n')
    candidate = BUILD/'board.c'
    candidate.write_text(code+'\n'+original.replace('is_attacked(', 'reference_attack(')+'\n')
    binary = BUILD/'probe.so'
    command = ['gcc','-O3','-std=c11','-Wall','-Wextra','-Werror','-shared','-fPIC','-I'+str(BASE),
               str(candidate),str(HERE/'probe.c'),'-o',str(binary)]
    subprocess.run(command, check=True, timeout=30)
    lib = C.CDLL(str(binary)); lib.fow_init()
    lib.probe.argtypes = [C.c_char_p,C.c_int,C.c_uint64,C.c_int,C.c_int,C.c_int,C.c_int]
    lib.measure.argtypes = [C.c_int,C.POINTER(C.c_uint64)]
    lib.measure.restype = C.c_double
    return lib, dict(source_sha256=sha(candidate), binary_sha256=sha(binary), command=command)


def check(lib, plan):
    tested = Counter()
    cache = Cache(CACHE)
    try:
        games = select(cache.games, plan['games'])
        assert hashlib.sha256('\n'.join(g['sequence_sha256'] for g in games).encode()).hexdigest()==plan['trajectory_hash']
        for game in games:
            for ply in range(game['records']):
                row = fields(cache.record(game['start']+ply))
                full = unpack_view(row[0]).encode()
                castling, ep, halfmove, side = row[3:7]
                final = ply+1==game['records']
                expand = not final and tested['frames']%plan['child_stride']==0
                count = lib.probe(full,side,castling,ep,halfmove,expand,not final)
                assert count>=0,(game['game'],ply,count)
                tested.update(frames=1, timed_parents=not final, expanded_parents=expand, children=count,
                              ep_parents=ep>=0, castling_rights_parents=castling!=0,
                              missing_king_parents=(b'K' not in full or b'k' not in full))
    finally:
        cache.close()
    rng = random.Random(plan['seed'])
    for i in range(plan['synthetic']):
        # Arbitrary boards exercise ray blockers and multiple promoted sliders.
        # No move generation from structurally invalid synthetic positions.
        board = ['-']*64
        for sq in rng.sample(range(64), i%33):
            board[sq] = rng.choice('PNBRQKpnbrqk')
        assert lib.probe(''.join(board).encode(),i%2,0,-1,0,False,False)==0
    tested['synthetic']=plan['synthetic']
    tested['comparisons']=128*(tested['frames']+tested['children']+tested['synthetic'])
    return dict(tested)


def cost(lib, plan):
    def measure(arm):
        checksum = C.c_uint64()
        seconds = lib.measure(arm,C.byref(checksum))
        assert seconds>0 and checksum.value>0
        return seconds,checksum.value
    _, expected = measure(0)
    assert measure(1)[1]==expected
    rows = []
    for i in range(plan['timing_pairs']):
        order = (0,1) if i%2==0 else (1,0)
        times = [0.0,0.0]
        for arm in order:
            times[arm], actual = measure(arm)
            assert actual==expected
        rows.append(dict(order=order, original_seconds=times[0], reverse_seconds=times[1], ratio=times[1]/times[0]))
    return dict(checksum=expected, passes=rows, median_ratio=median(row['ratio'] for row in rows))


def run():
    plan = read(OUT/'plan.json')
    os.sched_setaffinity(0,{plan['core']})
    for path,expected in plan['pins'].items():
        assert sha(path)==expected,path
    assert not (OUT/'execution.json').exists()
    start = time.monotonic()
    status = dict(started_at=now(), plan_sha256=sha(OUT/'plan.json'))
    def timeout(*_):
        raise TimeoutError('reverse attack test exceeded its wall bound')
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(plan['timeout_seconds'])
    try:
        lib, compiled = build()
        checked = check(lib,plan)
        timing = cost(lib,plan)
        gates = dict(parity=checked['frames']==plan['frames'] and checked['children']>=plan['child_min'],
                     cost=timing['median_ratio']<=plan['ratio_limit'])
        save(OUT/'result.json',dict(at=now(), checked=checked, timing=timing, conditions=gates,
                                    compiled=compiled, plan_sha256=sha(OUT/'plan.json'),
                                    decision='native_trajectory_check_allowed' if all(gates.values()) else 'close_reverse_attack_configuration'))
        status.update(status='complete',result_sha256=sha(OUT/'result.json'))
        print(json.dumps(dict(checked=checked, ratio=timing['median_ratio'], gates=gates)),flush=True)
    except BaseException as error:
        status.update(status='failed',error=repr(error))
        raise
    finally:
        signal.alarm(0)
        save(OUT/'execution.json',dict(**status, ended_at=now(), seconds=time.monotonic()-start))


if __name__=='__main__':
    {'freeze':freeze,'run':run}[sys.argv[1]]()
