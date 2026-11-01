#!/usr/bin/env python3
"""Bounded 180+2 pilot with exclusive first-attempt receipts and turn isolation."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/stable-mix-20261101'
sys.path[:0]=[str(HERE/'build'),str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest,rules
from local_turn_control import run_controlled,cleanup_registry

def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,data):
    q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');q.replace(p)
def clean_env():
    e={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_','OMP_','OPENBLAS_','MKL_'))}
    e.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1');return e

def smoke():
    OUT.mkdir(parents=True,exist_ok=True)
    misty=HERE/'build/misty';misty.mkdir(exist_ok=True)
    with zipfile.ZipFile(ROOT/'data/zoo/misty-v16.zip') as z:z.extractall(misty)
    for f in ['referee.py']:
        shutil.copyfile(ROOT.parent/'fow-starter'/f,HERE/'build'/f)
    shutil.copyfile(ROOT/'astra-submissions/tools/local_turn_control.py',HERE/'build/local_turn_control.py')
    feed='fow\nw 180 2\n'+rules.Board().observation(0)+'\n180\n'
    results=[]
    for arm,d in [('base',HERE/'build/base'),('candidate',HERE/'build/candidate'),('misty',misty)]:
        e=clean_env();e.update(FOW_SEED='11012026',MIST_ACTION_SEED='20301',MIST_ROOT_MIX='2' if arm=='candidate' else '0',MIST_MAX_SECONDS='.5')
        p=subprocess.run(['taskset','-c','0,1','bash',str(d/'run.sh')],input=feed,capture_output=True,text=True,env=e,timeout=40)
        moves=[l[5:].strip() for l in p.stdout.splitlines() if l.startswith('move ')]
        result={'arm':arm,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'moves':moves}
        results.append(result)
        assert p.returncode==0 and len(moves)==1 and moves[0] in rules.Board().legal_moves(),result
        if arm=='candidate':assert 'astra-mix: mode=2 ' in p.stderr and re.search(r'observations=[1-9]',p.stderr)
    write(OUT/'smoke.json',results);print(json.dumps({'smoke_pass':len(results)}))

def prepare():
    assert (OUT/'smoke.json').exists() and (HERE/'correctness.json').exists()
    dependencies={str(p):sha(p) for p in [HERE/'build/base/mist',HERE/'build/candidate/mist',
                  HERE/'build/base/bin/stockfish',HERE/'build/base/data/history.bin',HERE/'build/referee.py',
                  HERE/'build/local_turn_control.py',HERE/'build/misty/run.sh',HERE/'build/misty/misty_bot.py',
                  HERE/'build/base/run.sh',HERE/'build/candidate/run.sh',Path(__file__)]}
    misty_python=Path('/home/henrytan/fable-persist/scratchpad/misty/venv/bin/python')
    code='''import hashlib,importlib.metadata,json,sys
d=importlib.metadata.distribution('misty-chess')
files={str(d.locate_file(f).resolve()):hashlib.sha256(d.locate_file(f).read_bytes()).hexdigest() for f in d.files if d.locate_file(f).is_file()}
print(json.dumps({'version':d.version,'python':sys.version,'files':files}))'''
    package=json.loads(subprocess.check_output([str(misty_python),'-c',code],text=True))
    dependencies.update(package['files'])
    sf=Path('/home/henrytan/fable-persist/scratchpad/misty/bin/stockfish').resolve();dependencies[str(sf)]=sha(sf)
    jobs=[]
    for pair in range(2):
        seed=203100+pair*2
        for side in ('white','black'):
            jobs.append({'id':f'h2h-p{pair}-{side}','phase':'h2h','lane':pair,'pair':pair,'arm':'candidate','side':side,
                         'engine_seed':seed,'opponent_seed':seed+1,'action_seed':seed+10000,'opponent':'base'})
            for arm in ('candidate','base'):
                jobs.append({'id':f'misty-p{pair}-{side}-{arm}','phase':'misty','lane':pair,'pair':pair,'arm':arm,'side':side,
                             'engine_seed':seed+100,'opponent_seed':seed+101,'action_seed':seed+10100,'opponent':'misty'})
    import chess
    dependencies[str(Path(chess.__file__).resolve())]=sha(chess.__file__)
    plan={'created':now(),'provenance':json.loads((HERE/'provenance.json').read_text()),'dependencies':dependencies,
          'misty_version':package['version'],'misty_python':package['python'],'jobs':jobs,'lanes':{'0':'0,1','1':'6,7'},
          'time_control':{'base':180,'increment':2,'max_plies':1000},'game_wall_cap':2450,
          'turn_control':'owned process-group pause and buffered observations; not a security sandbox',
          'policy':'MIST_ROOT_MIX=2; top-three, stable positive support every iteration after half budget, excluded mass to argmax; no safety-margin guarantee',
          'screen':'4 head-to-head games. Any protocol/infrastructure fault stops its lane and requires review. Score <=1/4 closes pilot. Otherwise 8 candidate/control games vs Misty. Larger gate only if clean, H2H >=1/2 and candidate Misty score >= control; these small samples never justify release or Elo claims.',
          'resume_policy':'No repeated first attempts. Existing incomplete starts require process/receipt reconciliation, not automatic replay.'}
    with (OUT/'plan.json').open('x') as f:json.dump(plan,f,indent=2)
    print(json.dumps({'jobs':len(jobs),'h2h':4,'misty':8,'misty_version':package['version'],'dependency_files':len(dependencies)}))

def load():
    p=json.loads((OUT/'plan.json').read_text())
    for path,h in p['dependencies'].items():assert sha(path)==h,('changed dependency',path)
    return p

def argv(job,opponent=False):
    arm=job['opponent'] if opponent else job['arm'];seed=job['opponent_seed'] if opponent else job['engine_seed']
    d=HERE/'build'/arm
    return ['/usr/bin/env',f'FOW_SEED={seed}',f'MIST_ACTION_SEED={job["action_seed"]}',
            'MIST_ROOT_MIX='+('2' if arm=='candidate' else '0'),'/bin/bash',str(d/'run.sh')]

def worker(job_id):
    plan=load();job=next(j for j in plan['jobs'] if j['id']==job_id);directory=OUT/'jobs'/job_id
    spec=importlib.util.spec_from_file_location('referee',HERE/'build/referee.py')
    referee=importlib.util.module_from_spec(spec);spec.loader.exec_module(referee)
    ours,theirs=argv(job),argv(job,True)
    white,black=(ours,theirs) if job['side']=='white' else (theirs,ours)
    game=run_controlled(referee,white,black,base=180,increment=2,max_plies=1000,match_id=job_id,
                       white_name=job['arm'] if job['side']=='white' else job['opponent'],
                       black_name=job['opponent'] if job['side']=='white' else job['arm'],
                       registry_path=directory/'processes.json',retain_stderr=True)
    write(directory/'replay.json',game)

def inspect(job,directory):
    game=json.loads((directory/'replay.json').read_text())
    states,errors=ingest.validate_replay(game)
    faults=list(errors)
    if 'failedSide' in game:faults.append('bot failure: '+game['failedSide']+' '+game['reason'])
    if game['result'] not in ('1-0','0-1','1/2-1/2'):faults.append('non-game result')
    if game.get('warnings'):faults.append('capture warning')
    text=game.get('privateDiagnostics',{}).get(job['side'],'')
    mix=[]
    for line in text.splitlines():
        if line.startswith('astra-mix: mode='):
            mix.append(dict(re.findall(r'(\w+)=([^ ]+)',line)))
    if job['arm']=='candidate' and not mix:faults.append('missing mixture diagnostics')
    if job['arm']=='base' and mix:faults.append('unexpected mixture diagnostics')
    for m in mix:
        if m['mode']!='2' or not 0<float(m['p'])<=1:faults.append('invalid mixture diagnostic')
        if int(m['observations'])==0 and m['selected']!=m['argmax']:faults.append('mixed without observed support')
    controls=game.get('localTurnControl',{}).get('controls',[])
    if len(controls)!=2 or any(not any(e['op']=='freeze' for e in c['events']) for c in controls):faults.append('missing turn isolation')
    score=.5 if game['result']=='1/2-1/2' else float((game['result']=='1-0')==(job['side']=='white')) if game['result'] in ('1-0','0-1') else None
    return {'job':job,'result':game['result'],'reason':game['reason'],'score':score,'faults':faults,
            'plies':len(game['frames'])-1,'final_clocks':game['frames'][-1]['clocks'],
            'mix_decisions':len(mix),'mixed_support_decisions':sum(float(m['alternatives_mass'])>0 for m in mix),
            'non_argmax_choices':sum(m['selected']!=m['argmax'] for m in mix),
            'replay_sha256':sha(directory/'replay.json'),'validated_frames':len(states)}

def lane(phase,lane_id):
    plan=load();chosen=[j for j in plan['jobs'] if j['phase']==phase and j['lane']==lane_id]
    if phase=='misty':
        first=[OUT/'jobs'/j['id']/'result.json' for j in plan['jobs'] if j['phase']=='h2h']
        assert all(p.exists() for p in first),'head-to-head incomplete'
        rows=[json.loads(p.read_text()) for p in first]
        assert not any(r['faults'] for r in rows) and sum(r['score'] for r in rows)>1,'head-to-head did not advance'
    lock=(OUT/f'{phase}-lane{lane_id}.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for job in chosen:
        d=OUT/'jobs'/job['id'];d.mkdir(parents=True,exist_ok=True)
        if (d/'result.json').exists():
            result=json.loads((d/'result.json').read_text());assert not result['faults'];continue
        with (d/'started.json').open('x') as f:json.dump({'at':now(),'job':job,'parent_pid':os.getpid(),'plan_sha256':sha(OUT/'plan.json')},f,indent=2)
        start=time.monotonic()
        p=subprocess.Popen(['taskset','-c',plan['lanes'][str(lane_id)],sys.executable,str(Path(__file__)),'worker','--job',job['id']],
                           stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=clean_env(),start_new_session=True)
        write(d/'handle.json',{'pid':p.pid,'started':now(),'job':job['id']})
        try:
            stdout,stderr=p.communicate(timeout=plan['game_wall_cap'])
            timeout=False
        except subprocess.TimeoutExpired:
            timeout=True;p.kill();stdout,stderr=p.communicate()
        unverified=cleanup_registry(d/'processes.json')
        (d/'stdout.txt').write_text(stdout);(d/'stderr.txt').write_text(stderr)
        if p.returncode or timeout or unverified or not (d/'replay.json').exists():
            result={'job':job,'score':None,'faults':[f'worker exit={p.returncode} timeout={timeout} unverified={unverified}']}
        else:result=inspect(job,d)
        result.update(exit=p.returncode,elapsed_seconds=time.monotonic()-start,finished=now())
        write(d/'result.json',result);print(json.dumps(result),flush=True)
        if result['faults']:raise RuntimeError(result['faults'])

def summarize():
    plan=load();rows=[]
    for j in plan['jobs']:
        path=OUT/'jobs'/j['id']/'result.json'
        if path.exists():rows.append(json.loads(path.read_text()))
    summary={'complete_jobs':len(rows),'planned_jobs':len(plan['jobs']),'faults':[r for r in rows if r['faults']],
             'panels':{},'classification':'small full-clock pilot, not an Elo estimate or release gate'}
    for phase,arm in [('h2h','candidate'),('misty','candidate'),('misty','base')]:
        r=[r for r in rows if r['job']['phase']==phase and r['job']['arm']==arm]
        scores=[v['score'] for v in r if v.get('score') is not None]
        summary['panels'][phase+'/'+arm]={'games':len(scores),'wins':scores.count(1),'draws':scores.count(.5),'losses':scores.count(0),
                                        'score':sum(scores)/len(scores) if scores else None,
                                        'mixed_decisions':sum(v.get('mixed_support_decisions',0) for v in r),
                                        'non_argmax_choices':sum(v.get('non_argmax_choices',0) for v in r)}
    write(OUT/'summary.json',summary);print(json.dumps(summary,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['smoke','prepare','worker','lane','summarize'])
    ap.add_argument('--job');ap.add_argument('--phase',choices=['h2h','misty']);ap.add_argument('--lane',type=int,choices=[0,1])
    a=ap.parse_args()
    if a.command=='worker':worker(a.job)
    elif a.command=='lane':lane(a.phase,a.lane)
    else:globals()[a.command]()
