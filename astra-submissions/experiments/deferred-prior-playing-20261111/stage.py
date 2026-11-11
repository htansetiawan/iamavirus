"""Stage the exact deferred prior engine and gate its full-clock comparison."""
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parent
PREVIOUS = EXPERIMENTS/'exact-speed-playing-20261110'
sys.path.insert(0,str(PREVIOUS))
from build import ANALYSIS, FLAGS, ROOT, SHIP, SOURCES, now, preflight, read, save, sha
from prepare import freeze_playing

OUT = ANALYSIS/HERE.name
BUILD = HERE/'build'
TEST = ANALYSIS/'deferred-prior-speed-20261111'
PRIVATE = ROOT/'data/astra-spool'/TEST.name
CHANGES = ['belief.c','board.c','movemodel.c']


def stage():
    earlier = read(ANALYSIS/PREVIOUS.name/'build.json')
    assert earlier['passed'] and all(sha(path)==digest for path,digest in earlier['dependencies'].items())
    stress = read(TEST/'plan-summary.json')
    experiment = read(PRIVATE/'plan.json')
    assert stress['plan_sha256']==sha(PRIVATE/'plan.json') and stress['preflight_rows']==216
    belief = PRIVATE/'belief.c'
    assert sha(belief)==experiment['dependencies'][str(belief)]
    OUT.mkdir(exist_ok=False); BUILD.mkdir(exist_ok=False)
    old_build = PREVIOUS/'build'
    for name in ('base','referee.py','native-validator.so'):
        (BUILD/name).symlink_to((old_build/name).resolve(strict=True))
    candidate = BUILD/'candidate'
    shutil.copytree(old_build/'candidate/src',candidate/'src')
    shutil.copyfile(belief,candidate/'src/belief.c')
    for name in ('build.sh','run.sh'):
        shutil.copyfile(SHIP/name,candidate/name)
    for name in ('bin','data'):
        (candidate/name).symlink_to(SHIP/name,target_is_directory=True)

    calls = []
    def run(command):
        command = list(map(str,command))
        completed = subprocess.run(command,cwd=candidate,capture_output=True,text=True,check=True,timeout=60)
        calls.append(dict(command=command,stdout=completed.stdout,stderr=completed.stderr))

    run(['bash','build.sh'])
    checks = BUILD/'compiler-checks'; checks.mkdir()
    paths = [candidate/'src'/(name+'.c') for name in SOURCES]
    objects = [checks/(name+'.o') for name in SOURCES]
    for source,obj in zip(paths,objects):
        run(['g++','-x','c','-std=c11',*FLAGS,'-c',source,'-o',obj])
    run(['g++',*FLAGS,*objects,'-lm','-o',checks/'gpp-c'])
    run(['g++','-x','c++','-std=c++20','-fpermissive','-w',*FLAGS,*paths,'-lm','-o',checks/'gpp-cpp'])
    assert sorted(path.name for path in (candidate/'src').iterdir() if sha(path)!=sha(SHIP/'src'/path.name))==CHANGES
    binaries = {'v38':SHIP/'mist','gcc':candidate/'mist','gpp-c':checks/'gpp-c','gpp-cpp':checks/'gpp-cpp'}
    verified = preflight(binaries)
    paths = [Path(__file__), PREVIOUS/'build.py', PREVIOUS/'prepare.py', TEST/'plan-summary.json', *binaries.values(),
             *(candidate/'src').iterdir(), candidate/'build.sh',candidate/'run.sh',SHIP/'bin/stockfish',SHIP/'data/history.bin',
             BUILD/'referee.py',BUILD/'native-validator.so',belief]
    receipt = dict(at=now(),passed=True,changes=CHANGES,preflight=verified,
                   binaries={key:sha(path) for key,path in binaries.items()},dependencies={str(path):sha(path) for path in paths},
                   compiler_commands=calls,scope='Unnumbered local build. Matched full-clock games require the independent 348 gate and audit.')
    save(OUT/'build.json',receipt)
    print(dict(candidate=receipt['binaries']['gcc'],preflights=len(verified),changes=CHANGES),flush=True)


def freeze():
    freeze_playing(HERE,TEST,'exact_deferred_full_clock_design_allowed',CHANGES,3501111,
                   'Standalone reverse-ray, exact visibility and deferred prior scoring. V38 flags, solver and assets.',
                   'deferred-speed',Path(__file__))


if __name__=='__main__':
    {'stage':stage,'freeze':freeze}[sys.argv[1]]()
