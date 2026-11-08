"""Exact-archive build/protocol/game checks, independent of the strength gate."""
from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import zipfile

from prepare import HERE, ROOT, OUT, sha
from package import STAGED
sys.path[:0] = [str(ROOT), str(ROOT / 'astra-submissions/tools')]
from learning import ingest, rules
from local_turn_control import cleanup_registry, group_members, run_controlled

DEST = HERE / 'build/zip-extracted'
REFEREE = ROOT.parent / 'fow-starter/referee.py'
BASELINE = ROOT.parent / 'fow-starter/baseline.py'
IMAGE = 'sha256:89f08877815e0fc7a51234dd71b6faffd02c4687f73dede860f37429137bbcd7'

def write(p, value):
    with p.open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')

def clean_env():
    e = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_', 'ASTRA_', 'FOW_', 'OMP_', 'MKL_', 'OPENBLAS_'))}
    e.update(FOW_SEED='380008', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    return e

def referee():
    spec = importlib.util.spec_from_file_location('v38_zip_referee', REFEREE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def command():
    return ['/bin/bash', str(DEST / 'run.sh')]

def build():
    os.sched_setaffinity(0, {4, 5})
    assert sha(STAGED) == json.loads((OUT / 'staged.json').read_text())['archive_sha256']
    DEST.mkdir(exist_ok=False)
    with zipfile.ZipFile(STAGED) as z:
        assert z.testzip() is None
        for n in z.namelist():
            rel = Path(n)
            assert not rel.is_absolute() and '..' not in rel.parts and not n.endswith('/')
            p = DEST / rel
            p.parent.mkdir(exist_ok=True, parents=True)
            p.write_bytes(z.read(n))
            p.chmod(z.getinfo(n).external_attr >> 16 & 0o777)
    for n,h in json.loads((DEST / 'astra-release.json').read_text())['source_sha256'].items():
        assert sha(DEST / n) == h, n
    (DEST / 'smoke.input').write_text('fow\nw 180 2\n' + rules.Board().observation(0) + '\n180\n')
    script = '''set -eu
ln -s /usr/bin/gcc-12 /usr/local/bin/gcc
ln -s /usr/bin/g++-12 /usr/local/bin/g++
runuser -u builder -- sh -eu -c 'cd /work; bash build.sh; ./run.sh < smoke.input > container-smoke.stdout 2> container-smoke.stderr'
'''
    args = ['docker', 'run', '--rm', '--name', 'astra-v38-zip-validation', '--runtime=runc',
            '--network=none', '--cpuset-cpus=4,5', '--memory=4g', '--pids-limit=64',
            '--mount', f'type=bind,src={DEST},dst=/work', IMAGE, '/bin/sh', '-c', script]
    start = time.monotonic()
    with (OUT / 'zip-build.log').open('x') as f:
        r = subprocess.run(args, stdout=f, stderr=subprocess.STDOUT, timeout=300)
    record = dict(command=args, exit_code=r.returncode, seconds=time.monotonic()-start,
                  archive_sha256=sha(STAGED), environment='Ubuntu 22.04, gcc/g++ 12.3, no network or GPU, 4 GiB cgroup, 64 PID limit')
    write(OUT / 'zip-build.json', record)
    assert r.returncode == 0, 'Retain failure and inspect zip-build.log'
    stdout = (DEST / 'container-smoke.stdout').read_text()
    stderr = (DEST / 'container-smoke.stderr').read_text()
    moves = [s[5:] for s in stdout.splitlines() if s.startswith('move ')]
    assert stdout.splitlines()[0] == 'ready' and len(moves) == 1 and moves[0] in rules.Board().legal_moves()
    assert 'mist: stockfish ready' in stderr
    write(OUT / 'container-smoke.json', dict(stdout=stdout, stderr=stderr, passed=True, native_sha256=sha(DEST/'mist'), scorer_sha256=sha(DEST/'bin/stockfish')))
    print(json.dumps(dict(container_build=True, container_first_move=moves[0], seconds=record['seconds'])), flush=True)

def smokes():
    os.sched_setaffinity(0, {4,5})
    os.environ.clear(); os.environ.update(clean_environment)
    ref = referee()
    rows = []
    for side in (True, False):
        for remaining in (180., .2):
            board = ref.FowBoard()
            start = time.monotonic()
            bot = ref.Bot(command(), side, 180, 2, initialization_timeout=15)
            row = dict(side='white' if side else 'black', remaining=remaining, startup_seconds=time.monotonic()-start, moves=[])
            try:
                assert row['startup_seconds'] < 15
                bot.observe(ref.observation(board, side), 0)
                if not side:
                    board.push_uci('d2d4'); bot.observe(ref.observation(board, side), 1)
                move, elapsed = bot.move(remaining)
                assert move in {m.uci() for m in ref.fow_moves(board)} and elapsed < remaining
                row['moves'].append(dict(move=move, elapsed=elapsed))
                board.push_uci(move); bot.observe(ref.observation(board, side), len(board.move_stack))
                move = sorted(m.uci() for m in ref.fow_moves(board))[0]
                board.push_uci(move); bot.observe(ref.observation(board, side), len(board.move_stack))
                move, elapsed = bot.move(remaining)
                assert move in {m.uci() for m in ref.fow_moves(board)} and elapsed < remaining
                row['moves'].append(dict(move=move, elapsed=elapsed))
            finally:
                bot.close()
                row.update(stderr=bot.stderr_excerpt.decode(), failure=bot.failure)
                rows.append(row)
                (OUT/'zip-smokes.json').write_text(json.dumps(dict(passed=False, rows=rows), indent=2)+'\n')
            assert bot.failure is None and 'mist: stockfish ready' in row['stderr']
    (OUT/'zip-smokes.json').write_text(json.dumps(dict(passed=True, rows=rows), indent=2)+'\n')
    print(json.dumps(dict(protocol_smokes=4, legal_decisions=8, maximum_startup_seconds=max(r['startup_seconds'] for r in rows))),flush=True)

def game(side):
    os.sched_setaffinity(0, {4,5})
    os.environ.clear(); os.environ.update(clean_environment)
    ref = referee(); directory = OUT / ('zip-game-' + side)
    directory.mkdir(exist_ok=False)
    write(directory/'started.json', dict(at=datetime.now(timezone.utc).isoformat(), side=side, archive_sha256=sha(STAGED), native_sha256=sha(DEST/'mist'), referee_sha256=sha(REFEREE), baseline_sha256=sha(BASELINE)))
    ours, theirs = command(), [sys.executable, str(BASELINE)]
    white, black = (ours,theirs) if side == 'white' else (theirs,ours)
    stop = threading.Event(); peak = [0]
    def monitor():
        while not stop.wait(.05):
            try:
                registry = json.loads((directory/'processes.json').read_text())
                group = registry[0 if side=='white' else 1]['leader']['pgid']
                rss = 0
                for member in group_members(group):
                    data = Path(f"/proc/{member['pid']}/statm").read_text().split()
                    rss += int(data[1]) * os.sysconf('SC_PAGE_SIZE')
                peak[0] = max(peak[0], rss)
            except (OSError, ValueError, IndexError):
                pass
    thread = threading.Thread(target=monitor, daemon=True); thread.start()
    try:
        replay = run_controlled(ref,white,black,base=180,increment=2,max_plies=1000,
                 white_name='v38' if side=='white' else 'baseline.py', black_name='v38' if side=='black' else 'baseline.py',
                 registry_path=directory/'processes.json',retain_stderr=True)
        write(directory/'replay.json',replay)
    finally:
        stop.set(); thread.join(); assert not cleanup_registry(directory/'processes.json')
    states, errors = ingest.validate_replay(replay)
    assert not errors and 'failedSide' not in replay and not replay.get('warnings')
    assert 0 < peak[0] < 4*1024**3
    assert 'mist: stockfish ready' in replay['privateDiagnostics'][side]
    board = ref.FowBoard(); history = Counter({ref.position_key(board):1})
    for ply,frame in enumerate(replay['frames']):
        if ply:
            assert ref.outcome(board,history) is None
            assert frame['move'] in {m.uci() for m in ref.fow_moves(board)}
            board.push_uci(frame['move']);history[ref.position_key(board)]+=1
        actual = ref.make_frame(board,frame['clocks'])
        assert all(actual[k] == frame[k] for k in ('board','white','black'))
    assert ref.outcome(board,history) == (replay['result'],replay['reason'])
    result = dict(passed=True,side=side,result=replay['result'],reason=replay['reason'],frames=len(states),
                  peak_group_rss_bytes=peak[0],memory_scope='sampled sum of native and scorer RSS, including shared pages twice; not a host runtime cgroup limit',
                  final_clocks=replay['frames'][-1]['clocks'],replay_sha256=sha(directory/'replay.json'))
    write(directory/'result.json',result); print(json.dumps(result),flush=True)

def finish():
    build_record = json.loads((OUT/'zip-build.json').read_text())
    smoke = json.loads((OUT/'zip-smokes.json').read_text())
    games = [json.loads((OUT/('zip-game-'+side)/'result.json').read_text()) for side in ('white','black')]
    assert build_record['exit_code'] == 0 and smoke['passed'] and all(r['passed'] for r in games)
    assert sha(STAGED) == build_record['archive_sha256'] == json.loads((OUT/'staged.json').read_text())['archive_sha256']
    manifest = json.loads((DEST/'astra-release.json').read_text())
    for n,h in manifest['source_sha256'].items(): assert sha(DEST/n)==h,n
    write(OUT/'zip-validation.json',dict(passed=True,at=datetime.now(timezone.utc).isoformat(),archive_sha256=sha(STAGED),native_sha256=sha(DEST/'mist'),
          build_sha256=sha(OUT/'zip-build.json'),smokes_sha256=sha(OUT/'zip-smokes.json'),games=games,
          scope='Package compatibility and correctness, not a strength estimate. Ubuntu runtime is a compatibility check, not the exact gVisor arena image.'))
    print(json.dumps(dict(passed=True,archive_sha256=sha(STAGED))),flush=True)

clean_environment = clean_env()
if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'game': game(sys.argv[2])
    else: {'build':build,'smokes':smokes,'finish':finish}[action]()
