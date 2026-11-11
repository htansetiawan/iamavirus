"""Check complete-engine compiler paths against the confirmed posterior traces."""

import os
from pathlib import Path
import subprocess
import sys

from stage import BUILD, EXPERIMENTS, FLAGS, HERE, MODEL, OUT, ROOT, now, read, save, sha

sys.path.insert(0,str(EXPERIMENTS/'quiet-prior-sequential-20261110'))
from run import environment, stable

FRESH = ROOT/'data/astra-spool/compact-mass-confirmation-20261111'
PRIVATE = ROOT/'data/astra-spool/compact-mass-playing-parity-20261111'
LEGACY = EXPERIMENTS/'quiet-prior-sequential-20261110'


def main():
    build = read(OUT/'build.json')
    assert build['passed'] and all(sha(p)==v for p,v in build['dependencies'].items())
    plan = read(FRESH/'plan.json')
    assert read(ROOT/'astra-submissions/analysis'/FRESH.name/'terminal-verification.json')['plan_sha256']==sha(FRESH/'plan.json')
    calls = {f"{row['game']}-s{row['seed_index']}-{row['arm']}":row for row in read(FRESH/'calls.json')}
    def rows(path):
        return [__import__('json').loads(line) for line in path.read_text().splitlines()]
    ranked = []
    for game in plan['games']:
        tag = game['game']+'-s0-learned'
        path = FRESH/(tag+'.stdout')
        assert sha(path)==calls[tag]['stdout_sha256']
        data = rows(path)
        ranked.append((sum(row['full_update'] for row in data),game))
    selected = [plan['games'][0],max(ranked,key=lambda row:row[0])[1]]
    assert selected[0]['game']!=selected[1]['game']
    PRIVATE.mkdir(exist_ok=False)
    src = BUILD/'candidate/src'
    checks = BUILD/'compiler-checks'
    common = ['-I'+str(src),'-I'+str(LEGACY/'build')]
    commands = []
    def compile(command):
        command=list(map(str,command))
        completed=subprocess.run(command,capture_output=True,text=True,timeout=90,check=True)
        commands.append(dict(command=command,stderr=completed.stderr))
    compile(['gcc','-std=c11',*FLAGS,*common,LEGACY/'trace.c',*[src/name for name in ('board.c','belief.c','movemodel.c')],'-lm','-o',PRIVATE/'gcc'])
    compile(['g++','-x','c','-std=c11',*FLAGS,*common,'-c',LEGACY/'trace.c','-o',PRIVATE/'trace.o'])
    compile(['g++',*FLAGS,PRIVATE/'trace.o',*[checks/(name+'.o') for name in ('board','belief','movemodel')],'-lm','-o',PRIVATE/'gpp-c'])
    compile(['g++','-x','c++','-std=c++20','-fpermissive','-w',*FLAGS,*common,
             LEGACY/'trace.c',*[src/name for name in ('board.c','belief.c','movemodel.c')],'-lm','-o',PRIVATE/'gpp-cpp'])
    records=[]
    verified_rows=0
    for game in selected:
        for seed_index,seed in enumerate(plan['seeds']):
            tag=f"{game['game']}-s{seed_index}-learned"
            original=FRESH/(tag+'.stdout')
            assert sha(original)==calls[tag]['stdout_sha256']
            expected=rows(original)
            for compiler in ('gcc','gpp-c','gpp-cpp'):
                env=environment('original')
                env['ASTRA_CAPTURE_FIXED']='3'
                label=f"{game['game']}-s{seed_index}-{compiler}"
                stdout,stderr=(PRIVATE/(label+'.'+suffix) for suffix in ('stdout','stderr'))
                with stdout.open('x') as output,stderr.open('x') as error:
                    result=subprocess.run([str(PRIVATE/compiler),game['trace'],str(seed)],env=env,
                                          stdout=output,stderr=error,check=True,timeout=180)
                actual=rows(stdout)
                assert stable(actual)==stable(expected),(label,'compiler changes posterior')
                verified_rows+=len(actual)
                records.append(dict(game=game['game'],seed_index=seed_index,compiler=compiler,code=result.returncode,
                                    rows=len(actual),stdout_sha256=sha(stdout),stderr_sha256=sha(stderr)))
    paths=[Path(__file__),OUT/'build.json',FRESH/'plan.json',FRESH/'calls.json',LEGACY/'trace.c',
           LEGACY/'build/guard_predicates.h',*PRIVATE.glob('gcc'),*PRIVATE.glob('gpp-*')]
    save(OUT/'trace-parity.json',dict(at=now(),passed=True,calls=records,verified_rows=verified_rows,
         dependencies={str(p):sha(p) for p in paths},commands=commands,
         selection='First frozen confirmation game and the game with the most full-model updates. Both fixed confirmation seeds. No selection by model gain or playing outcome.',
         scope='The complete bot sources compiled through each supported compiler produce exactly the confirmed O3 trace fingerprints, weights and risk diagnostics with timing fields excluded.'))
    print(dict(passed=True,calls=len(records),verified_rows=verified_rows),flush=True)


if __name__=='__main__':
    main()
