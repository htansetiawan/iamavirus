"""Reproduce gate-1 builds/tests on an extraction of the exact r4 archive."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import time

HERE = Path(__file__).resolve().parent
scratch = Path((HERE/'scratch-path.txt').read_text().strip())
env = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_', 'FOW_'))}
results = []


def run(label, argv, cwd, timeout=120):
    started = time.monotonic()
    p = subprocess.run(argv, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout)
    row = {'label':label, 'argv':argv, 'seconds':time.monotonic()-started,
           'returncode':p.returncode, 'stdout':p.stdout, 'stderr':p.stderr}
    results.append(row)
    (HERE/'build-test-receipt.json').write_text(json.dumps(results,indent=2)+'\n')
    print(label, p.returncode, round(row['seconds'],3), flush=True)
    if p.returncode:
        raise SystemExit(p.stderr[-2000:])


def handshake(label, cwd):
    sha = hashlib.sha256((cwd/'mist').read_bytes()).hexdigest()
    for side in ('w','b'):
        started = time.monotonic()
        p = subprocess.run(['bash','run.sh'], cwd=cwd, env=env,
                           input=f'fow\n{side} 180 2\n', text=True,
                           capture_output=True, timeout=15)
        assert p.returncode == 0 and p.stdout.strip() == 'ready', p
        row = {'label':label+' handshake '+side, 'executable_sha256':sha,
               'seconds':time.monotonic()-started, 'returncode':p.returncode,
               'stdout':p.stdout,'stderr':p.stderr}
        results.append(row)
        (HERE/'build-test-receipt.json').write_text(json.dumps(results,indent=2)+'\n')
        print(row['label'],sha,round(row['seconds'],3),flush=True)


gcc = scratch/'gcc'; gpp = scratch/'gpp'
run('exact build.sh (gcc)', ['bash','build.sh'], gcc)
handshake('gcc',gcc)
run('compile focused tests', ['make','build/test_rule','build/test_front'],gcc)
run('test_rule', ['./build/test_rule'],gcc)
run('test_front', ['./build/test_front'],gcc)
sources = ['src/'+s+'.c' for s in ('board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval','main')]
flags = ['-O2','-pthread','-D_POSIX_C_SOURCE=199309L']
objects=[]
for source in sources:
    obj=Path(source).stem+'.o'; objects.append(obj)
    run('g++ C compile '+source,['g++','-x','c','-std=c11',*flags,'-c',source,'-o',obj],gpp)
run('g++ C link',['g++',*flags,*sorted(objects),'-lm','-o','mist'],gpp)
handshake('g++ -x c',gpp)
run('g++ C++ fallback',['g++','-x','c++','-std=c++20','-fpermissive','-w',*flags,*sources,'-lm','-o','mist'],gpp)
handshake('g++ -x c++',gpp)
