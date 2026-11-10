"""Stage and smoke-test the exact v38 speed changes as a standalone engine."""
from datetime import datetime, timezone
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPERIMENTS = HERE.parent
ANALYSIS = ROOT/'astra-submissions/analysis'
OUT = ANALYSIS/HERE.name
BUILD = HERE/'build'
SHIP = EXPERIMENTS/'guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
SPEED = ROOT/'data/astra-spool/exact-updater-speed-20261110'
REFERENCE = EXPERIMENTS/'last-only-fresh-pilot-20261110/build'
PATCHED = ('board.c','movemodel.c')
SOURCES = ('board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval','main')
FLAGS = ['-O2','-pthread','-D_POSIX_C_SOURCE=199309L']


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False)
        stream.write('\n')


def now():
    return datetime.now(timezone.utc).isoformat()


def preflight(binaries):
    spec = spec_from_file_location('exact_speed_course_ref',BUILD/'referee.py')
    ref = module_from_spec(spec)
    spec.loader.exec_module(ref)
    env = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_'))}
    env.update(MIST_STOCKFISH=str(SHIP/'bin/stockfish'), MIST_HISTORY_TABLE=str(SHIP/'data/history.bin'),
               ASTRA_SF_ALLCHILDREN='1', MIST_MAX_SECONDS='.12', FOW_SEED='3471110')
    receipts = []
    for name, binary in binaries.items():
        for white in (True,False):
            board = ref.FowBoard()
            feed = ['fow',('w' if white else 'b')+' 180 2',ref.observation(board,white)]
            if not white:
                board.push_uci('d2d4')
                feed.append(ref.observation(board,white))
            result = subprocess.run([str(binary)],input='\n'.join([*feed,'180','']),capture_output=True,
                                    text=True,env=env,timeout=20,check=True)
            rows = result.stdout.splitlines()
            assert rows and rows[0]=='ready'
            moves = [line[5:] for line in rows if line.startswith('move ')]
            assert len(moves)==1 and ref.chess.Move.from_uci(moves[0]) in ref.fow_moves(board)
            assert 'mist: stockfish ready' in result.stderr and 'fallback' not in result.stderr.lower()
            receipts.append(dict(binary=name, side='white' if white else 'black', backend='ready', legal=True,
                                 stdout_sha256=hashlib.sha256(result.stdout.encode()).hexdigest(),
                                 stderr_sha256=hashlib.sha256(result.stderr.encode()).hexdigest()))
    return receipts


def main():
    control = read(ANALYSIS/'last-only-fresh-pilot-20261110/plan.json')
    receipt = read(ANALYSIS/'exact-updater-speed-20261110/terminal-verification.json')
    result = read(ANALYSIS/'exact-updater-speed-20261110/result.json')
    speed = read(SPEED/'plan.json')
    assert receipt['plan_sha256']==sha(SPEED/'plan.json') and receipt['result_sha256']==sha(ANALYSIS/'exact-updater-speed-20261110/result.json')
    assert result['conditions']['parity'] and result['conditions']['aggregate_cost']
    assert sha(SHIP/'mist')==control['baseline_sha256']
    for name in PATCHED:
        assert sha(SPEED/name)==speed['dependencies'][str(SPEED/name)]
    OUT.mkdir(exist_ok=False); BUILD.mkdir(exist_ok=False)
    for name in ('base','referee.py','native-validator.so'):
        (BUILD/name).symlink_to((REFERENCE/name).resolve(strict=True))
    candidate = BUILD/'candidate'
    shutil.copytree(SHIP/'src',candidate/'src')
    for name in PATCHED:
        shutil.copyfile(SPEED/name,candidate/'src'/name)
    for name in ('build.sh','run.sh'):
        shutil.copyfile(SHIP/name,candidate/name)
    for name in ('data','bin'):
        (candidate/name).symlink_to(SHIP/name,target_is_directory=True)
    checks = BUILD/'compiler-checks'; checks.mkdir()
    commands = []
    def run(command):
        result = subprocess.run(list(map(str,command)),cwd=candidate,capture_output=True,text=True,timeout=60,check=True)
        commands.append(dict(args=list(map(str,command)), stdout=result.stdout, stderr_sha256=hashlib.sha256(result.stderr.encode()).hexdigest()))
    run(['bash','build.sh'])
    paths = [candidate/'src'/(name+'.c') for name in SOURCES]
    objects = [checks/(name+'.o') for name in SOURCES]
    for path,obj in zip(paths,objects):
        run(['g++','-x','c','-std=c11',*FLAGS,'-c',path,'-o',obj])
    run(['g++',*FLAGS,*objects,'-lm','-o',checks/'gpp-c'])
    run(['g++','-x','c++','-std=c++20','-fpermissive','-w',*FLAGS,*paths,'-lm','-o',checks/'gpp-cpp'])
    changed = sorted(path.name for path in (candidate/'src').iterdir() if sha(path)!=sha(SHIP/'src'/path.name))
    assert changed==sorted(PATCHED)
    assert all(sha(candidate/name)==sha(SHIP/name) for name in ('build.sh','run.sh'))
    binaries = {'v38':SHIP/'mist','gcc':candidate/'mist','gpp-c':checks/'gpp-c','gpp-cpp':checks/'gpp-cpp'}
    receipts = preflight(binaries)
    dependencies = {str(p):sha(p) for p in [Path(__file__),*binaries.values(),*(candidate/'src').iterdir(),
        candidate/'build.sh',candidate/'run.sh',SHIP/'bin/stockfish',SHIP/'data/history.bin',BUILD/'referee.py',BUILD/'native-validator.so',
        ANALYSIS/'exact-updater-speed-20261110/terminal-verification.json']}
    save(OUT/'build.json',dict(at=now(), passed=True, changes=changed, preflight=receipts, commands=commands,
                               binaries={key:sha(path) for key,path in binaries.items()},dependencies=dependencies,
                               scope='Unnumbered local build and legal opening smoke. Playing comparison gated separately.'))
    print(json.dumps(dict(passed=True, changes=changed, preflights=len(receipts), candidate_sha256=sha(candidate/'mist'))),flush=True)


if __name__=='__main__':
    main()
