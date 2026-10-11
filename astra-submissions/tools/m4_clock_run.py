#!/usr/bin/env python3
"""Frozen on-policy matches, using the course referee's buffered-turn hook.

Local process-group pausing is for trusted executables; it is not an arena
security/memory sandbox. Each attempt is retained. No historical moves or true
boards are passed to a bot. Tiny match sets are screens, never Elo estimates.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

from local_turn_control import cleanup_registry, group_members, process_stat, run_controlled


def now():return datetime.now(timezone.utc).isoformat()
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(path,data):
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w') as f:
        json.dump(data,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
    tmp.replace(path)
def emit(**data):print(json.dumps(dict(at=now(),**data)),flush=True)


def prepare(args):
    run=args.run.resolve()
    run.mkdir(parents=True,exist_ok=True)
    if any(run.iterdir()):raise ValueError('Prepare requires a new empty run directory')
    if args.base<=0 or args.increment<0 or args.max_plies<1 or args.seconds<=0:
        raise ValueError('Invalid time control')
    if not 1<=args.samples<=4096 or len(set(args.seeds))!=len(args.seeds):raise ValueError('Invalid samples/seeds')
    if not args.scales or len(set(args.scales))!=len(args.scales) or not all(0<x<=1 for x in args.scales):
        raise ValueError('Invalid scales')
    sources={'candidate':args.binary,'opponent':args.opponent,'stockfish':args.stockfish,
             'runner.py':Path(__file__),'local_turn_control.py':Path(__file__).with_name('local_turn_control.py'),
             'referee.py':args.kit/'referee.py'}
    artifacts={}
    for name,source in sources.items():
        shutil.copy2(source,run/name)
        artifacts[name]={'source':str(source.resolve()),'sha256':sha(run/name)}
    jobs=[]
    for i,seed in enumerate(args.seeds):
        for j,side in enumerate(['white','black']):
            for scale in args.scales[::1 if (i+j)%2==0 else -1]:
                jobs.append({'id':f'seed{seed}-{side}-scale{scale:g}','seed':seed,'side':side,'scale':scale})
    excluded=set(args.exclude_job)
    if excluded-{j['id'] for j in jobs}:raise ValueError('Unknown excluded job')
    jobs=[j for j in jobs if j['id'] not in excluded]
    if not jobs:raise ValueError('No jobs remain')
    runtime=json.loads(subprocess.check_output([str(args.python),'-c',
        'import chess,sys,json,hashlib;print(json.dumps(dict(python=sys.version,chess_version=chess.__version__,chess_sha256=hashlib.sha256(open(chess.__file__,"rb").read()).hexdigest())))'],text=True))
    config={'schema':1,'created_at':now(),'run':str(run),'artifacts':artifacts,'python':str(args.python.absolute()),'runtime':runtime,
            'base':args.base,'increment':args.increment,'max_plies':args.max_plies,'max_seconds':args.seconds,
            'samples':args.samples,'iterations':1000000,'cpus':args.cpus,'jobs':jobs,'excluded_jobs':sorted(excluded),'opponent_name':args.opponent_name,
            'fast_roots':args.fast_roots,
            'classification':'small paired on-policy screening set; not an Elo estimate',
            'turn_control':'buffered observations and owned process-group SIGSTOP/SIGCONT',
            'security_sandbox':False,'failure_policy':'retain all attempts; halt on infrastructure, protocol or M4 instrumentation faults'}
    (run/'jobs').mkdir();write(run/'manifest.json',config)
    emit(prepared=str(run),manifest_sha256=sha(run/'manifest.json'),games=len(jobs))


def load(run):
    config=json.loads((run/'manifest.json').read_text())
    if config['run']!=str(run.resolve()):raise ValueError('Frozen directory moved')
    for name,data in config['artifacts'].items():
        if sha(run/name)!=data['sha256']:raise ValueError(f'Changed frozen artifact: {name}')
    return config


def clean_env(config):
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','M4SF_','OMP_','OPENBLAS_','MKL_'))}
    env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    env['PATH']=str(Path(config['python']).parent)+os.pathsep+env.get('PATH','/usr/bin:/bin')
    return env


def worker(run,job_id):
    config=load(run);job=next(j for j in config['jobs'] if j['id']==job_id)
    directory=run/'jobs'/job_id
    spec=importlib.util.spec_from_file_location('referee',run/'referee.py')
    referee=importlib.util.module_from_spec(spec);spec.loader.exec_module(referee)
    import chess
    if chess.__version__!=config['runtime']['chess_version'] or sha(chess.__file__)!=config['runtime']['chess_sha256']:
        raise ValueError('Python chess dependency changed')
    seed=f"FOW_SEED={job['seed']}"
    common=['/usr/bin/env',seed,f'MIST_STOCKFISH={run / "stockfish"}']
    candidate=[*common,'MIST_SEARCH=m4',f'MIST_SAMPLES={config["samples"]}',
               f'MIST_MAX_SECONDS={config["max_seconds"]}',f'MIST_M4_ITERATIONS={config["iterations"]}',
               f'MIST_M4_LEAF_SCALE={job["scale"]}','MIST_M4_CLOSURE=0','MIST_M4_WITNESSES=0',str(run/'candidate')]
    candidate.insert(-1,f'MIST_M4_FAST_ROOTS={int(config.get("fast_roots",False))}')
    opponent=[*common,str(run/'opponent')]
    white,black=(candidate,opponent) if job['side']=='white' else (opponent,candidate)
    def terminate(_signum,_frame):raise KeyboardInterrupt('Owned worker terminated')
    signal.signal(signal.SIGTERM,terminate)
    write(directory/'commands.json',{'white':white,'black':black,'chess_version':chess.__version__})
    replay=run_controlled(referee,white,black,base=config['base'],increment=config['increment'],
                          max_plies=config['max_plies'],match_id=job_id,
                          white_name=f'M4 scale{job["scale"]:g}' if job['side']=='white' else config['opponent_name'],
                          black_name=config['opponent_name'] if job['side']=='white' else f'M4 scale{job["scale"]:g}',
                          registry_path=directory/'processes.json',retain_stderr=True)
    write(directory/'game.json',replay)


def inspect_game(path,job,config=None):
    game=json.loads(path.read_text());side=job['side'];result=game['result']
    faults=[]
    if result not in ['1-0','0-1','1/2-1/2']:faults.append('infrastructure_result')
    if 'failedSide' in game:faults.append('bot_failure:'+game['failedSide'])
    if game.get('warnings'):faults.append('capture_warning')
    stderr=game.get('privateDiagnostics',{}).get(side,'')
    metrics=[dict(re.findall(r'(\w+)=([^ ]+)',line)) for line in stderr.splitlines() if line.startswith('mist-m4: ok=')]
    evals=[dict(re.findall(r'(\w+)=([^ ]+)',line)) for line in stderr.splitlines() if line.startswith('m4-eval:')]
    own_plies=[f['ply']-1 for f in game['frames'][1:] if (f['ply']%2==1)==(side=='white')]
    measured_plies=[int(m.get('ply',-1)) for m in metrics]
    if measured_plies!=own_plies or len(evals)!=len(own_plies):faults.append('missing_m4_diagnostics')
    setups=[dict(re.findall(r'(\w+)=([^ ]+)',line)) for line in stderr.splitlines() if line.startswith('m4-setup:')]
    if config and config.get('fast_roots') and [int(m.get('ply',-1)) for m in setups]!=own_plies:
        faults.append('missing_fast_root_diagnostics')
    for row in metrics:
        if row.get('ok')!='1' or row.get('snapshot')!='1':faults.append('m4_snapshot_or_search_failure')
        if row.get('over')!='0':faults.append('m4_reported_overrun')
    for row in evals:
        if row.get('ready')!='1' or float(row.get('failed',1))!=0:faults.append('stockfish_request_failure')
        if not abs(float(row.get('scale',-1))-job['scale'])<1e-6:faults.append('wrong_leaf_scale')
    score=None if result=='*' else .5 if result=='1/2-1/2' else float((result=='1-0')==(side=='white'))
    return {'result':result,'reason':game['reason'],'score':score,'plies':len(game['frames'])-1,
            'faults':sorted(set(faults)),'m4_decisions':len(metrics),'m4_carried_decisions':sum(int(m.get('carry',0))>0 for m in metrics),
            'cheap_carried_roots':sum(int(m.get('cheap_carried_roots',0)) for m in setups),
            'minimum_clocks':[min(f['clocks'][i] for f in game['frames']) for i in [0,1]],'failed_side':game.get('failedSide')}


def ensure_cleanup(directory):
    path=directory/'processes.json'
    unverified=cleanup_registry(path)
    records=json.loads(path.read_text()) if path.exists() else []
    for _ in range(100):
        live=[r for c in records for r in group_members(c['leader']['pgid']) if r['state'] not in ('Z','X')]
        if not live:break
        time.sleep(.01)
    return {'unverified_groups':unverified,'live_after_cleanup':live}


def summarize(run,config):
    rows=[json.loads(p.read_text()) for p in sorted((run/'jobs').glob('*/receipt.json'))]
    groups=defaultdict(list)
    for row in rows:groups[str(row['scale'])].append(row)
    totals={}
    for scale,group in groups.items():
        scores=[r['game']['score'] for r in group if r.get('game',{}).get('score') is not None]
        totals[scale]={'attempts':len(group),'scored':len(scores),'wins':scores.count(1),'draws':scores.count(.5),
                       'losses':scores.count(0),'mean_score':sum(scores)/len(scores) if scores else None,
                       'faults':sum(bool(r.get('faults')) for r in group)}
    summary={'at':now(),'complete':len(rows)==len(config['jobs']),'expected':len(config['jobs']),
             'classification':config['classification'],'totals':totals,'rows':rows}
    write(run/'summary.json',summary);return summary


def run_matches(args):
    run=args.run.resolve();config=load(run)
    lock=(run/'runner.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if sorted(os.sched_getaffinity(0))!=config['cpus']:raise ValueError('CPU affinity differs from plan')
    if Path(sys.executable).absolute()!=Path(config['python']):raise ValueError('Use the frozen Python environment')
    completed=summarize(run,config)
    if any(r.get('faults') for r in completed['rows']):raise ValueError('Previous faults need review; no automatic retry')
    done=0
    for job in config['jobs']:
        directory=run/'jobs'/job['id']
        if (directory/'receipt.json').exists():
            receipt=json.loads((directory/'receipt.json').read_text())
            if receipt.get('manifest_sha256')!=sha(run/'manifest.json') or any(receipt[k]!=v for k,v in job.items()):
                raise ValueError('Completed receipt belongs to another configuration')
            for name,digest in receipt['file_hashes'].items():
                if sha(directory/name)!=digest:raise ValueError('Changed completed match artifact')
            continue
        if directory.exists():
            started=json.loads((directory/'worker.json').read_text()) if (directory/'worker.json').exists() else None
            if started:
                current=process_stat(started['pid'])
                if current and current['state'] not in ('Z','X') and current['starttime']==started['starttime']:
                    raise RuntimeError('Existing worker still alive; observe it, do not restart')
            cleanup=ensure_cleanup(directory)
            receipt={**job,'faults':['interrupted_attempt'],'cleanup':cleanup,'file_hashes':{}}
            write(directory/'receipt.json',receipt);summarize(run,config)
            raise RuntimeError('Interrupted attempt retained; review before more games')
        directory.mkdir()
        emit(starting=job)
        command=[config['python'],str(run/'runner.py'),'worker','--run',str(run),'--job',job['id']]
        started_at=time.monotonic();timeout=2*config['base']+config['increment']*config['max_plies']+120
        timed_out=False
        with (directory/'worker.stdout').open('w') as out,(directory/'worker.stderr').open('w') as err:
            proc=subprocess.Popen(command,env=clean_env(config),stdout=out,stderr=err,start_new_session=True)
            write(directory/'worker.json',process_stat(proc.pid))
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out=True;proc.terminate()
                try:proc.wait(timeout=20)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
            finally:
                if proc.poll() is None:
                    proc.terminate()
                    try:proc.wait(timeout=20)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait()
                cleanup=ensure_cleanup(directory)
        faults=[]
        if proc.returncode or timed_out:faults.append('worker_failure')
        if cleanup['unverified_groups'] or cleanup['live_after_cleanup']:faults.append('cleanup_failure')
        game=inspect_game(directory/'game.json',job,config) if (directory/'game.json').exists() else None
        if game:faults+=game['faults']
        else:faults.append('missing_game')
        receipt={**job,'completed_at':now(),'elapsed':time.monotonic()-started_at,'returncode':proc.returncode,
                 'timed_out':timed_out,'cleanup':cleanup,'game':game,'faults':faults,
                 'manifest_sha256':sha(run/'manifest.json'),'file_hashes':{p.name:sha(p) for p in directory.iterdir() if p.is_file()}}
        write(directory/'receipt.json',receipt);summary=summarize(run,config)
        emit(completed=job['id'],game=game,faults=faults,totals=summary['totals'])
        if faults:raise RuntimeError('Match fault retained; stopped for review')
        done+=1
        if args.max_new_jobs and done>=args.max_new_jobs:break


def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='action',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--run',type=Path,required=True)
    for arg in ['binary','opponent','stockfish']:prep.add_argument('--'+arg,type=Path,required=True)
    prep.add_argument('--opponent-name',required=True);prep.add_argument('--kit',type=Path,default=Path.home()/'git/fow-starter')
    prep.add_argument('--python',type=Path,default=Path(sys.executable));prep.add_argument('--samples',type=int,default=32)
    prep.add_argument('--seconds',type=float,default=10);prep.add_argument('--base',type=float,default=180)
    prep.add_argument('--increment',type=float,default=2);prep.add_argument('--max-plies',type=int,default=512)
    prep.add_argument('--scales',type=float,nargs='+',default=[1,.9]);prep.add_argument('--seeds',type=int,nargs='+',default=[11,12])
    prep.add_argument('--exclude-job',action='append',default=[],help='Explicitly omit a job already retained in another immutable run')
    prep.add_argument('--fast-roots',action='store_true',help='Use cheap carried-root initialization (experimental)')
    prep.add_argument('--cpus',type=int,nargs='+',default=[6,7])
    run=sub.add_parser('run');run.add_argument('--run',type=Path,required=True);run.add_argument('--max-new-jobs',type=int)
    work=sub.add_parser('worker');work.add_argument('--run',type=Path,required=True);work.add_argument('--job',required=True)
    args=ap.parse_args()
    if args.action=='prepare':prepare(args)
    elif args.action=='worker':worker(args.run.resolve(),args.job)
    else:run_matches(args)


if __name__=='__main__':main()
