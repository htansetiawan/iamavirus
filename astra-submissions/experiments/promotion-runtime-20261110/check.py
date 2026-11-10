"""Production compilation and opening protocol checks for the bounded310 patch."""
from datetime import datetime,timezone
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/promotion-runtime-20261110'
TREE=HERE/'build'
ZIP=ROOT/'astra-submissions/iamavirus-v38-mist-c-allchildren.zip'
DEPLOYED=ROOT/'astra-submissions/experiments/guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
PATCH=ROOT/'astra-submissions/experiments/promotion-ledger-20261110/promotion-ledger.patch.gz'
SOURCES=['board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval','main']
sys.path.insert(0,str(ROOT.parent/'fow-starter'));import referee as ref

def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')


def main():
    OUT.mkdir(exist_ok=False);TREE.mkdir(exist_ok=False)
    assert sha(ZIP)=='ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f'
    lease=json.loads((ROOT/'chatroom/cores.json').read_text())['allocation']
    assert any(x.get('lease')=='312-promotion-runtime' and x.get('cores')==[2,3] for x in lease)
    assert not any({2,3}&set(x.get('cores',[])) for x in lease if x.get('lease')!='312-promotion-runtime')
    os.sched_setaffinity(0,{2,3})
    with zipfile.ZipFile(ZIP) as archive:
        launchers=[n for n in archive.namelist() if n=='run.sh' or n.endswith('/run.sh')]
        assert len(launchers)==1;prefix=launchers[0][:-len('run.sh')]
        copied=[]
        for member in archive.namelist():
            if not member.startswith(prefix) or member.endswith('/'):continue
            name=member[len(prefix):]
            if not(name.startswith('src/') or name in ('build.sh','run.sh')):continue
            assert '..' not in Path(name).parts
            data=archive.read(member);assert data==(DEPLOYED/name).read_bytes()
            target=TREE/name;target.parent.mkdir(exist_ok=True);target.write_bytes(data);copied.append(name)
            if name.endswith('.sh'):target.chmod(0o755)
    patched=subprocess.run(['patch','--batch','--forward','-p1','-d',str(TREE)],
        input=gzip.decompress(PATCH.read_bytes()),capture_output=True,timeout=10)
    assert patched.returncode==0,patched.stderr
    expected=json.loads((ROOT/'astra-submissions/analysis/promotion-ledger-20261110/patch-review.json').read_text())
    assert sha(TREE/'src/main.c')==expected['amended_main_sha256']
    changed=[n for n in copied if (TREE/n).read_bytes()!=(DEPLOYED/n).read_bytes()]
    assert changed==['src/main.c']
    for parent,name in [('bin','stockfish'),('data','history.bin')]:
        (TREE/parent).mkdir();(TREE/parent/name).symlink_to(DEPLOYED/parent/name)
    commands=[]
    def command(label,argv,timeout=15):
        start=time.monotonic();p=subprocess.run(argv,cwd=TREE,capture_output=True,text=True,timeout=timeout)
        row=dict(label=label,argv=argv,exit_code=p.returncode,seconds=time.monotonic()-start,stdout=p.stdout,stderr=p.stderr)
        commands.append(row);assert p.returncode==0,row
    # Execute the actual packaged primary build script, not a substitute recipe.
    command('packaged-build-script',['bash','build.sh'])
    shutil.copy2(TREE/'mist',TREE/'mist-gcc')
    objdir=TREE/'objects-xc';objdir.mkdir()
    for name in SOURCES:
        command('g++-c-'+name,['g++','-x','c','-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=199309L','-c','src/'+name+'.c','-o',str(objdir/(name+'.o'))])
    command('g++-c-link',['g++','-pthread',*[str(objdir/(n+'.o')) for n in SOURCES],'-lm','-o','mist-xc'])
    command('g++-cpp',['g++','-x','c++','-std=c++20','-fpermissive','-w','-O2','-pthread','-D_POSIX_C_SOURCE=199309L',
                                  *['src/'+n+'.c' for n in SOURCES],'-lm','-o','mist-cpp'])
    old=ROOT/'astra-submissions/experiments/farsight-root-20261110/study.py'
    spec=importlib.util.spec_from_file_location('existing_native_process_runner',old)
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    checks=[]
    for side in (0,1):
        b=ref.FowBoard();feed=['fow',f"{('w','b')[side]} 180 2",ref.observation(b,side==0)]
        if side:
            b.push_uci('e2e4');feed.append(ref.observation(b,False))
        feed.append('180');payload='\n'.join(feed)+'\n'
        legal={m.uci() for m in ref.fow_moves(b)};parent_move=None
        for label,binary in [('parent',DEPLOYED/'mist'),('gcc-script',TREE/'run.sh'),('g++-c',TREE/'mist-xc'),('g++-cpp',TREE/'mist-cpp')]:
            folder=OUT/f'{side}-{label}'
            env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
            env.update(MIST_FORCE_MOVES='',MIST_MAX_SECONDS='0',FOW_SEED='3121110',
                MIST_STOCKFISH=str(TREE/'bin/stockfish'),MIST_HISTORY_TABLE=str(TREE/'data/history.bin'),
                ASTRA_SF_ALLCHILDREN='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
            start=time.monotonic();stdout,stderr=runner.run_native(binary,folder,payload,env,15)
            elapsed=time.monotonic()-start
            lines=stdout.splitlines();assert len(lines)==2 and lines[0]=='ready' and lines[1].startswith('move ')
            move=lines[1][5:];assert move in legal and 'stockfish ready' in stderr
            if label=='parent':parent_move=move
            if label=='gcc-script':assert move==parent_move
            checks.append(dict(side=side,build=label,move=move,parent_move=parent_move,
                seconds=elapsed,legal=True,exited_zero=True,owned_processes_closed=True,
                binary_sha256=sha(binary)))
    result=dict(at=now(),passed=True,changed_archive_members=changed,main_sha256=sha(TREE/'src/main.c'),
        source_matches_tested_patch=True,build_commands=commands,protocol_checks=checks,
        modes=['packaged-gcc-script','g++-C-front-end','g++-C++20-fallback'],
        all_opening_gcc_choices_match_parent=True,stockfish_and_history_unchanged=True,
        scope='Local build/protocol acceptance only. Zero timed growth fixes20finalCFRiterations; this is not an arena-clock or strength test. Only the promotion arithmetic source differs.',
        limitations=['Host compiler versions and timings do not reproduce the course machine.','Opening smokes do not exercise promotions;310supplies21 arithmetic fixtures and311supplies a real fixed-belief mask comparison.','Original recapture/terminal approximations remain. No ZIP, release number, live arena or Fable-source change.'],
        dependencies={str(p):sha(p) for p in [Path(__file__),ZIP,PATCH,old,DEPLOYED/'bin/stockfish',DEPLOYED/'data/history.bin',ROOT.parent/'fow-starter/referee.py']},
        local_binaries={n:sha(TREE/n) for n in ('mist-gcc','mist-xc','mist-cpp')})
    write(OUT/'result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('build_commands','protocol_checks','dependencies')},indent=2),flush=True)


if __name__=='__main__':
    try:main()
    except BaseException as e:
        if OUT.is_dir() and not(OUT/'failure.json').exists():write(OUT/'failure.json',dict(at=now(),error=repr(e)))
        raise
