#!/usr/bin/env python3
"""Compare prior 2 against prior 1 using one immutable archive and real clocks.

One shared binary/model/book; only the per-process prior setting differs.
No ZIP is produced and no arena version is activated.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import shlex
import signal
import statistics
import subprocess
import time
import zipfile

ASTRA = Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cores', required=True)
    parser.add_argument('--pairs', type=int, default=4)
    parser.add_argument('--seed', type=int, default=12000)
    parser.add_argument('--kit', type=Path, default=Path.home()/'git/fow-starter')
    parser.add_argument('--ort', type=Path, default=Path.home()/'git/onnxruntime-sdk/onnxruntime-linux-x64-1.24.2')
    args = parser.parse_args()
    runtime, out, archive = args.runtime.resolve(), args.output.resolve(), args.archive.resolve()
    if args.pairs < 1 or not runtime.is_relative_to(ASTRA):
        parser.error('positive pair count and Astra-owned runtime required')
    if sha(archive) != args.expected_sha256:
        raise ValueError('archive hash differs from design')
    runtime.mkdir(parents=True, exist_ok=False); out.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if Path(name).is_absolute() or '..' in Path(name).parts:
                raise ValueError('unsafe archive member')
        z.extractall(runtime)
    env = {k:v for k,v in os.environ.items() if not k.startswith(('FOW_', 'ASTRA_'))}
    env['ORT_HOME'] = str(args.ort.resolve())
    state = {'state':'building','started_at':datetime.now(timezone.utc).isoformat(),
             'pid':os.getpid(),'archive':str(archive),'archive_sha256':args.expected_sha256,
             'runtime':str(runtime),'cores':args.cores,'pairs_planned':args.pairs,'seed':args.seed,
             'time_control':{'base':180,'increment':2},'candidate_prior':2,'control_prior':1,
             'runner_sha256':sha(Path(__file__)),'referee_sha256':sha(args.kit/'referee.py'),
             'games':[],'interpretation':'Paired clocked screening on one opponent; not an Elo estimate or standalone promotion gate.'}
    def save():
        tmp=out/'state.tmp'; tmp.write_text(json.dumps(state,indent=2)+'\n'); tmp.replace(out/'state.json')
    save()
    try:
        with (out/'build.log').open('w') as log:
            subprocess.run(['bash','build.sh'],cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        if 'ONNX Runtime found' not in (out/'build.log').read_text():
            raise RuntimeError('neural inference did not build')
        pinned={str(p.relative_to(runtime)):sha(p) for p in runtime.rglob('*') if p.is_file()}
        state.update(state='running',runtime_files_sha256=pinned);save()
        pair_scores=[]
        for pair in range(args.pairs):
            scores=[]
            for candidate_side in (0,1):
                seed=args.seed+2*pair
                priors=(2,1) if candidate_side==0 else (1,2)
                commands=[shlex.join(['env',f'FOW_SEED={seed+side}',f'FOW_OPPONENT_PRIOR={priors[side]}',
                                     'bash',str(runtime/'run.sh')]) for side in (0,1)]
                replay=out/f'pair{pair}-candidate-{candidate_side}.json'
                command=['taskset','-c',args.cores,str(args.kit/'.venv/bin/python'),str(args.kit/'referee.py'),
                         '--trusted-local','--white',commands[0],'--black',commands[1],
                         '--white-name',f'prior{priors[0]}','--black-name',f'prior{priors[1]}',
                         '--base-time','180','--increment','2','--max-plies','1000','--output',str(replay)]
                started=time.monotonic()
                with replay.with_suffix('.log').open('w') as log:
                    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
                    state['live_referee_pid']=process.pid;save()
                    try:
                        returncode=process.wait(timeout=1300)
                    except BaseException:
                        os.killpg(process.pid,signal.SIGTERM)
                        try:process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid,signal.SIGKILL);process.wait()
                        raise
                if returncode:raise RuntimeError('referee failed: '+str(replay.with_suffix('.log')))
                game=json.loads(replay.read_text())
                result=game['result']
                if result not in ('1-0','0-1','1/2-1/2'):raise ValueError('unknown result')
                score=.5 if result=='1/2-1/2' else float(result==('1-0' if candidate_side==0 else '0-1'))
                record={'pair':pair,'candidate_side':candidate_side,'seed_by_color':[seed,seed+1],
                        'score':score,'result':result,'reason':game['reason'],'plies':len(game['frames'])-1,
                        'final_clocks':game['frames'][-1]['clocks'],'elapsed_seconds':time.monotonic()-started,
                        'replay':str(replay),'replay_sha256':sha(replay)}
                state['games'].append(record);state.pop('live_referee_pid',None);scores.append(score);save()
                print(json.dumps(record),flush=True)
            pair_scores.append(statistics.mean(scores))
        unchanged=all(sha(runtime/name)==digest for name,digest in pinned.items()) and sha(archive)==args.expected_sha256
        if not unchanged:raise RuntimeError('runtime changed during comparison')
        rng=random.Random(20261008)
        samples=sorted(statistics.mean(rng.choices(pair_scores,k=len(pair_scores))) for _ in range(10000))
        state.update(state='complete',completed_at=datetime.now(timezone.utc).isoformat(),
                     runtime_unchanged=True,score=statistics.mean(pair_scores),pair_scores=pair_scores,
                     paired_bootstrap_95=[samples[249],samples[9749]])
        save();print(json.dumps({'state':state['state'],'score':state['score'],'paired_bootstrap_95':state['paired_bootstrap_95']}),flush=True)
    except BaseException as error:
        state.update(state='failed',error=repr(error));save();raise


if __name__=='__main__':main()
