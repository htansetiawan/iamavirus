#!/usr/bin/env python3
"""Build a relocated, unversioned runtime directory without changing trial bytes."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PARENT=HERE.parent/'persistent-response-20261101'
OUT=ROOT/'astra-submissions/analysis/persistent-readiness-20261102'
MODEL=ROOT/'astra-submissions/analysis/visible-response-20261101/models/response.bin'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import rules
from learning.compare_archives import kill_tree
from package_release import next_version


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def clean_env():
    e={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_','OMP_','MKL_','OPENBLAS_'))}
    e.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1');return e


def smoke(stage,mode,side):
    env=clean_env();env.update(MIST_MAX_SECONDS='.25',FOW_SEED='2181102')
    # Deliberately launch outside the runtime directory; only its relative
    # assets and run.sh may configure the evaluator, table and student.
    stem=OUT/f'{mode}-{side}';feed=[];output=[];moves=[];start=time.monotonic()
    with stem.with_suffix('.stderr').open('w') as err:
        proc=subprocess.Popen(['bash',str(stage/'run.sh')],cwd='/tmp',stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,env=env,start_new_session=True)
        sel=selectors.DefaultSelector();sel.register(proc.stdout,selectors.EVENT_READ)
        def send(line):feed.append(line);proc.stdin.write(line+'\n');proc.stdin.flush()
        def receive(timeout):
            assert sel.select(timeout),'protocol read deadline'
            line=proc.stdout.readline().rstrip('\n');output.append(line);return line
        try:
            send('fow');send(('w' if side==0 else 'b')+' 180 2');assert receive(10)=='ready'
            ready_seconds=time.monotonic()-start
            state=rules.GameState()
            while len(moves)<2:
                send(state.board.observation(side))
                if state.board.side==side:
                    send('180');line=receive(10);assert re.fullmatch(r'move [a-h][1-8][a-h][1-8][qrbn]?',line),line
                    move=line[5:];assert move in state.board.legal_moves(),move;moves.append(move)
                else:
                    legal=[m for m in state.board.legal_moves() if not state.board.move_loses_king(m)]
                    assert legal;move=next((m for m in ('d2d4','d7d5','g1f3','g8f6') if m in legal),sorted(legal)[0])
                state.push(move);assert state.outcome() is None
            proc.stdin.close();assert proc.wait(timeout=10)==0
        except BaseException:
            if proc.poll() is None:kill_tree(proc.pid);proc.wait()
            raise
        finally:
            sel.close();stem.with_suffix('.input').write_text('\n'.join(feed)+'\n');stem.with_suffix('.stdout').write_text('\n'.join(output)+'\n')
    text=stem.with_suffix('.stderr').read_text()
    assert 'mist: stockfish ready' in text and 'history table ' in text
    modes=[l for l in text.splitlines() if l.startswith('astra_persistent: ')]
    responses=[l for l in text.splitlines() if l.startswith('astra_visible: opponent_sets ')]
    assert len(modes)==len(responses)==2,(modes,responses)
    for line in modes:
        fields=line.split()[1:];r={fields[i]:float(fields[i+1]) for i in range(0,len(fields),2)}
        assert r['prior']==.25 and r['branches']==2*r['physical_worlds']
    for line in responses:
        assert 'failures 0 mismatches 0' in line and 'load_failed 0' in line,line
    return dict(mode=mode,side=side,moves=moves,ready_seconds=ready_seconds,total_seconds=time.monotonic()-start,exit_code=proc.returncode,
                stockfish=True,history=True,model_mode_decisions=len(modes),stdout_sha256=sha(stem.with_suffix('.stdout')),stderr_sha256=sha(stem.with_suffix('.stderr')))


def main():
    OUT.mkdir(parents=True,exist_ok=False);work=HERE/'build';work.mkdir(exist_ok=False)
    provenance=json.loads((PARENT/'provenance.json').read_text())
    for path,h in provenance['source_sha256'].items():assert sha(ROOT/path)==h,path
    assert sha(PARENT/'build/mist')==provenance['binary_sha256'] and sha(MODEL)==provenance['model_sha256']
    stage=work/'relocated-runtime';stage.mkdir();shutil.copytree(PARENT/'build/src',stage/'src')
    for folder in ('bin','data'):(stage/folder).mkdir()
    for name in ('bin/stockfish','bin/STOCKFISH-COPYING.txt','data/history.bin'):
        shutil.copy2(PARENT/'build/base'/name,stage/name)
    shutil.copy2(MODEL,stage/'data/response.bin')
    for name in ('build.sh','run.sh'):shutil.copy2(HERE/name,stage/name)
    files={str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()}
    origin=dict(parent_archive='fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip',parent_archive_sha256=sha(ROOT/'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'),
                candidate_provenance_sha256=sha(PARENT/'provenance.json'),trial_binary_sha256=provenance['binary_sha256'],initial_files_sha256=files,
                prospective_next_version=next_version(),version_reserved=False,zip_created=False,
                note='Unversioned readiness directory only. Recheck the +1 rule and match evidence before any future release. Stockfish licence retained.')
    save(OUT/'implementation-origin.json',origin)
    execution=dict(status='running',pid=os.getpid(),started_at=datetime.now(timezone.utc).isoformat(),completed_modes=0)
    save(OUT/'execution.json',execution);rows=[]
    try:
        for mode in ('gcc','gxx-c','gxx-cpp'):
            env=clean_env();shim=work/f'shim-{mode}';shim.mkdir()
            if mode!='gcc':
                for compiler in ('gcc','cc'):
                    p=shim/compiler;p.write_text('#!/bin/sh\nexit 127\n');p.chmod(0o755)
                if mode=='gxx-cpp':
                    p=shim/'g++';p.write_text('#!/bin/sh\nif [ "$1" = "-x" ] && [ "$2" = "c" ]; then exit 127; fi\nexec /usr/bin/g++ "$@"\n');p.chmod(0o755)
                env['PATH']=str(shim)+os.pathsep+env['PATH']
            (stage/'mist').unlink(missing_ok=True)
            start=time.monotonic();p=subprocess.run(['bash',str(stage/'build.sh')],cwd='/tmp',capture_output=True,text=True,env=env,timeout=60)
            seconds=time.monotonic()-start;(OUT/f'{mode}.build.log').write_text(p.stdout+p.stderr)
            row=dict(mode=mode,build_seconds=seconds,returncode=p.returncode,stdout=p.stdout,binary_sha256=sha(stage/'mist') if (stage/'mist').exists() else None)
            rows.append(row);save(OUT/'results.json',rows);assert p.returncode==0,row
            expected={'gcc':'build: done (gcc)','gxx-c':'build: done (g++ -x c)','gxx-cpp':'build: done (g++ as C++)'}[mode]
            assert expected in p.stdout,row
            row['under_15_seconds']=seconds<15
            if mode=='gcc':assert row['binary_sha256']==provenance['binary_sha256'],'Default rebuilt bytes differ from the playing candidate'
            shutil.copy2(stage/'mist',work/f'mist-{mode}')
            row['smokes']=[smoke(stage,mode,side) for side in (0,1)]
            execution['completed_modes']+=1;save(OUT/'results.json',rows);save(OUT/'execution.json',execution)
        # A missing student must not silently become a weaker runtime mode.
        asset=stage/'data/response.bin';asset.rename(stage/'data/response.bin.saved')
        try:
            p=subprocess.run(['bash',str(stage/'run.sh')],cwd='/tmp',input='',capture_output=True,text=True,env=clean_env(),timeout=10)
            assert p.returncode!=0 and not p.stdout and 'required asset missing: data/response.bin' in p.stderr
            save(OUT/'missing-model.json',dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
        finally:(stage/'data/response.bin.saved').rename(asset)
        for name,h in files.items():assert sha(stage/name)==h,name
        for path,h in provenance['source_sha256'].items():assert sha(ROOT/path)==h,path
        assert sha(PARENT/'build/mist')==provenance['binary_sha256']
        execution['status']='complete'
    except BaseException as e:execution.update(status='failed',error=f'{type(e).__name__}: {e}');raise
    finally:
        execution['finished_at']=datetime.now(timezone.utc).isoformat();save(OUT/'execution.json',execution)
        save(OUT/'toolchain.json',{c:subprocess.check_output([c,'--version'],text=True).splitlines()[0] for c in ('gcc','g++')})
    print(json.dumps({'modes':len(rows),'smokes':sum(len(r['smokes']) for r in rows),'all_builds_under_15s':all(r['under_15_seconds'] for r in rows),'default_binary_matches_trial':True,'zip_created':False}))


if __name__=='__main__':main()
