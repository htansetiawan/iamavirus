"""Build the independently confirmed observation-mass model as a complete bot."""

from importlib.util import module_from_spec, spec_from_file_location
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPERIMENTS = HERE.parent
ANALYSIS = ROOT/'astra-submissions/analysis'
OUT = ANALYSIS/HERE.name
BUILD = HERE/'build'
CONFIRM = ANALYSIS/'compact-mass-confirmation-20261111'
MODEL = ROOT/'data/astra-spool/compact-observation-mass-20261111'
SHIP = EXPERIMENTS/'guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
REFERENCE = EXPERIMENTS/'deferred-prior-playing-20261111/build'
SOURCES = ('board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval','main')
FLAGS = ['-O2','-pthread','-D_POSIX_C_SOURCE=199309L']


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value,indent=2,allow_nan=False)+'\n')


def now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def openings(binaries):
    spec = spec_from_file_location('compact_playing_ref',BUILD/'referee.py')
    referee = module_from_spec(spec)
    spec.loader.exec_module(referee)
    receipts = []
    for name, binary in binaries.items():
        for side in (0,1):
            board = referee.FowBoard()
            feed = ['fow', ('w' if side==0 else 'b')+' 180 2', referee.observation(board,side==0)]
            if side:
                board.push_uci('d2d4')
                feed.append(referee.observation(board,False))
            env = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_','OMP_','MKL_','OPENBLAS_'))}
            env.update(MIST_STOCKFISH=str(SHIP/'bin/stockfish'),MIST_HISTORY_TABLE=str(SHIP/'data/history.bin'),
                       ASTRA_SF_ALLCHILDREN='1',ASTRA_CAPTURE_FIXED='3',MIST_MAX_SECONDS='.12',FOW_SEED='3571111',
                       OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
            result = subprocess.run([str(binary)],input='\n'.join([*feed,'180','']),
                                    env=env,capture_output=True,text=True,check=True,timeout=25)
            moves = [line[5:] for line in result.stdout.splitlines() if line.startswith('move ')]
            assert result.stdout.splitlines()[0]=='ready' and len(moves)==1
            assert referee.chess.Move.from_uci(moves[0]) in referee.fow_moves(board)
            assert 'mist: stockfish ready' in result.stderr and 'fallback' not in result.stderr.lower()
            receipts.append(dict(binary=name,color=('white','black')[side],legal=True,scorer='ready',
                stdout_sha256=hashlib.sha256(result.stdout.encode()).hexdigest(),
                stderr_sha256=hashlib.sha256(result.stderr.encode()).hexdigest()))
    return receipts


def stage():
    result, audit = (read(CONFIRM/name) for name in ('result.json','terminal-verification.json'))
    plan_path = ROOT/'data/astra-spool/compact-mass-confirmation-20261111/plan.json'
    plan = read(plan_path)
    assert audit['result_sha256']==sha(CONFIRM/'result.json') and audit['plan_sha256']==sha(plan_path)
    assert result['decision']=='full_clock_integration_design_allowed' and not audit['failed']
    assert all(sha(path)==digest for path,digest in plan['dependencies'].items())
    assert sha(SHIP/'mist')==read(ANALYSIS/'deferred-prior-playing-20261111/plan.json')['baseline_sha256']
    OUT.mkdir(exist_ok=False)
    BUILD.mkdir(exist_ok=False)
    for name in ('base','referee.py','native-validator.so'):
        (BUILD/name).symlink_to((REFERENCE/name).resolve(strict=True))
    candidate = BUILD/'candidate'
    shutil.copytree(SHIP/'src',candidate/'src')
    for name in ('belief.c','movemodel.c','weights.h'):
        shutil.copyfile(MODEL/name,candidate/'src'/name)
    header = EXPERIMENTS/'compact-observation-mass-20261111/redistribute.h'
    shutil.copyfile(header,candidate/'src/redistribute.h')
    shutil.copyfile(SHIP/'build.sh',candidate/'build.sh')
    launcher = (SHIP/'run.sh').read_text()
    assert launcher.startswith('#!/bin/bash\n')
    launcher = launcher.replace('#!/bin/bash\n',
                                '#!/bin/bash\nexport ASTRA_CAPTURE_FIXED=3\n',1)
    (candidate/'run.sh').write_text(launcher)
    for name in ('bin','data'):
        (candidate/name).symlink_to(SHIP/name,target_is_directory=True)
    checks = BUILD/'compiler-checks'
    checks.mkdir()
    calls = []
    def run(command):
        command = list(map(str,command))
        completed = subprocess.run(command,cwd=candidate,capture_output=True,text=True,timeout=90,check=True)
        calls.append(dict(command=command,stdout=completed.stdout,stderr=completed.stderr))
    run(['bash','build.sh'])
    paths = [candidate/'src'/(name+'.c') for name in SOURCES]
    objects = [checks/(name+'.o') for name in SOURCES]
    for source,obj in zip(paths,objects):
        run(['g++','-x','c','-std=c11',*FLAGS,'-c',source,'-o',obj])
    run(['g++',*FLAGS,*objects,'-lm','-o',checks/'gpp-c'])
    run(['g++','-x','c++','-std=c++20','-fpermissive','-w',*FLAGS,*paths,'-lm','-o',checks/'gpp-cpp'])
    changed = sorted(path.name for path in (candidate/'src').iterdir()
                     if not (SHIP/'src'/path.name).exists() or sha(path)!=sha(SHIP/'src'/path.name))
    assert changed==['belief.c','movemodel.c','redistribute.h','weights.h']
    assert sha(candidate/'build.sh')==sha(SHIP/'build.sh')
    binaries = {'v38':SHIP/'mist','gcc':candidate/'mist','gpp-c':checks/'gpp-c','gpp-cpp':checks/'gpp-cpp'}
    preflight = openings(binaries)
    deps = [Path(__file__),plan_path,CONFIRM/'result.json',CONFIRM/'terminal-verification.json',
            *binaries.values(),*(candidate/'src').iterdir(),candidate/'build.sh',candidate/'run.sh',
            SHIP/'bin/stockfish',SHIP/'data/history.bin',BUILD/'referee.py',BUILD/'native-validator.so']
    save(OUT/'build.json',dict(at=now(),passed=True,changes=changed,launcher_mode='ASTRA_CAPTURE_FIXED=3',
         preflight=preflight,compiler_commands=calls,binaries={k:sha(v) for k,v in binaries.items()},
         dependencies={str(path):sha(path) for path in deps},
         scope='Unnumbered full bot from fixed 353 model and confirmed 355 posterior. Original board/CFR/Stockfish/guards/time flags. Optimized full-feature kernel and quiet mass update only. Real-clock comparison is separately frozen.'))
    print(json.dumps(dict(changes=changed,preflights=len(preflight),candidate_sha256=sha(candidate/'mist'))),flush=True)


if __name__ == '__main__':
    stage()
