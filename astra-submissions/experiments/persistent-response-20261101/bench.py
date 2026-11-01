#!/usr/bin/env python3
"""Bounded full-clock pilot after the frozen replay and tactical gates."""
import argparse
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

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/persistent-response-20261101/full-games'
PRIOR=HERE.parent/'stable-mix-20261101'
MODEL=ROOT/'astra-submissions/analysis/visible-response-20261101/models/response.bin'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest,rules
from local_turn_control import run_controlled,cleanup_registry

def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def clean_env():
    e={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_','OMP_','OPENBLAS_','MKL_'))}
    e.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1');return e
def command(arm,seed):
    d=HERE/'build'/arm
    return ['/usr/bin/env',f'FOW_SEED={seed}',f'ASTRA_VISIBLE_CONFIDENCE={.25 if arm=="candidate" else 0}',
            f'ASTRA_VISIBLE_MODEL={MODEL}',f'ASTRA_VISIBLE_PROJECT={1 if arm=="candidate" else 0}',f'ASTRA_PERSISTENT={1 if arm=="candidate" else 0}','/bin/bash',str(d/'run.sh')]

def smoke():
    OUT.mkdir(parents=True,exist_ok=True)
    assert json.loads((OUT.parent/'summary.json').read_text())['decision']=='manual_review_before_full_games'
    assert json.loads((OUT.parent/'manual-review.json').read_text())['decision']=='bounded_full_clock_pilot'
    for name in ['base','misty']:
        dest=HERE/'build'/name
        if not dest.exists():dest.symlink_to(PRIOR/'build'/name,target_is_directory=True)
    candidate=HERE/'build/candidate';candidate.mkdir(exist_ok=True)
    for name in ['bin','data']:
        dest=candidate/name
        if not dest.exists():dest.symlink_to(PRIOR/'build/base'/name,target_is_directory=True)
    if not (candidate/'mist').exists():(candidate/'mist').symlink_to(HERE/'build/mist')
    shutil.copyfile(PRIOR/'build/base/run.sh',candidate/'run.sh')
    shutil.copyfile(PRIOR/'build/referee.py',HERE/'build/referee.py')
    feed='fow\nw 180 2\n'+rules.Board().observation(0)+'\n180\n';rows=[]
    for arm in ['base','candidate','misty']:
        env=clean_env();env['MIST_MAX_SECONDS']='.5'
        r=subprocess.run(['taskset','-c','0,1',*command(arm,214200)],input=feed,text=True,capture_output=True,env=env,timeout=60)
        moves=[s[5:] for s in r.stdout.splitlines() if s.startswith('move ')]
        row=dict(arm=arm,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr);rows.append(row)
        write(OUT/'smoke.json',rows)
        assert r.returncode==0 and len(moves)==1 and moves[0] in rules.Board().legal_moves(),row
        if arm=='candidate':assert 'astra_visible: opponent_sets ' in r.stderr and 'load_failed 0' in r.stderr and 'astra_persistent: prior 0.25 ' in r.stderr
    print(json.dumps({'smoke_pass':3}))

def prepare():
    assert len(json.loads((OUT/'smoke.json').read_text()))==3
    previous=json.loads((PRIOR.parent.parent/'analysis/stable-mix-20261101/plan.json').read_text())
    dependencies={str(p):sha(p) for p in [HERE/'build/base/mist',HERE/'build/mist',MODEL,
                  HERE/'build/base/bin/stockfish',HERE/'build/base/data/history.bin',HERE/'build/referee.py',
                  ROOT/'astra-submissions/tools/local_turn_control.py',HERE/'build/misty/run.sh',HERE/'build/misty/misty_bot.py',
                  HERE/'build/base/run.sh',HERE/'build/candidate/run.sh',Path(__file__),OUT.parent/'summary.json',OUT.parent/'manual-review.json',OUT.parent/'referee-review.json',HERE/'provenance.json']}
    for p,h in previous['dependencies'].items():
        if '/fable-persist/' in p:
            assert sha(p)==h,('Misty package changed',p);dependencies[p]=h
    jobs=[]
    for pair in range(4):
        for side in ['white','black']:
            jobs.append(dict(id=f'h2h-p{pair}-{side}',phase='h2h',lane=pair%2,pair=pair,arm='candidate',side=side,
                             engine_seed=214200+2*pair,opponent_seed=214201+2*pair,opponent='base'))
    for pair in range(2):
        for side in ['white','black']:
            for arm in ['candidate','base']:
                jobs.append(dict(id=f'misty-p{pair}-{side}-{arm}',phase='misty',lane=pair,pair=pair,arm=arm,side=side,
                                 engine_seed=214300+2*pair,opponent_seed=214301+2*pair,opponent='misty'))
    plan=dict(created_at=now(),dependencies=dependencies,jobs=jobs,lanes={'0':'0,1','1':'6,7'},
              time_control={'base':180,'increment':2,'max_plies':1000},game_wall_cap=2450,
              misty_version=previous['misty_version'],model_sha256=sha(MODEL),confidence=.25,projection=True,persistent=True,parent_pilot='Raw local response 0/8 and projected local response 2/8 versus v37; this tests a persistent latent opponent mode with fresh seeds.',
              gate='Eight head-to-head games, both colours. Any technical fault stops its lane. H2H score <=2/8 closes this configuration. Otherwise run eight Misty games (four candidate, four control). Larger trial only if H2H >=4/8 and candidate Misty score >= control, with no technical faults. No release or Elo claim from these small samples.',
              limitations='Misty is an authentic local engine, not verified arena bytes. Seeds need not control all Misty randomness. The material regression and response-model error remain known risks.',
              turn_control='Verified ownership of stopped/resumed bot process groups; observations charged on the next active turn. Not a security sandbox.',
              resume='Never repeat a started game automatically. Reconcile authoritative process handles and first-attempt receipts.')
    with (OUT/'plan.json').open('x') as f:json.dump(plan,f,indent=2)
    print(json.dumps({'jobs':len(jobs),'h2h':8,'conditional_misty':8,'dependency_files':len(dependencies)}))

def load():
    plan=json.loads((OUT/'plan.json').read_text())
    for p,h in plan['dependencies'].items():assert sha(p)==h,('changed dependency',p)
    return plan

def worker(job_id):
    plan=load();job=next(j for j in plan['jobs'] if j['id']==job_id);directory=OUT/'jobs'/job_id
    spec=importlib.util.spec_from_file_location('response_referee',HERE/'build/referee.py')
    referee=importlib.util.module_from_spec(spec);spec.loader.exec_module(referee)
    ours=command(job['arm'],job['engine_seed']);theirs=command(job['opponent'],job['opponent_seed'])
    white,black=(ours,theirs) if job['side']=='white' else (theirs,ours)
    game=run_controlled(referee,white,black,base=180,increment=2,max_plies=1000,match_id=job_id,
                       white_name=job['arm'] if job['side']=='white' else job['opponent'],
                       black_name=job['opponent'] if job['side']=='white' else job['arm'],
                       registry_path=directory/'processes.json',retain_stderr=True)
    write(directory/'replay.json',game)

def inspect(job,directory):
    game=json.loads((directory/'replay.json').read_text());states,errors=ingest.validate_replay(game);faults=list(errors)
    if 'failedSide' in game:faults.append('bot failure: '+game['failedSide']+' '+game['reason'])
    if game['result'] not in ('1-0','0-1','1/2-1/2'):faults.append('non-game result')
    if game.get('warnings'):faults.append('capture warning')
    text=game.get('privateDiagnostics',{}).get(job['side'],'');reports=[]
    for line in text.splitlines():
        if line.startswith('astra_visible: opponent_sets '):
            parts=line.split()[1:];reports.append({parts[i]:float(parts[i+1]) for i in range(0,len(parts),2)})
    if job['arm']=='candidate' and not reports:faults.append('missing learned response diagnostics')
    if job['arm']=='candidate' and not any(r.get('projected_sets',0)>0 for r in reports):faults.append('projection never active')
    if job['arm']=='base' and reports:faults.append('unexpected learned response diagnostics')
    if 'model_load_failed' in text:faults.append('model load failure')
    if any(r[k] for r in reports for k in ['failures','mismatches','load_failed']):faults.append('response query/input error')
    modes=[]
    for line in text.splitlines():
        if line.startswith('astra_persistent: '):
            parts=line.split()[1:];modes.append({parts[i]:float(parts[i+1]) for i in range(0,len(parts),2)})
    if job['arm']=='candidate' and (not modes or any(m['prior']!=.25 or m['branches']!=2*m['physical_worlds'] for m in modes)):faults.append('persistent mode missing or construction mismatch')
    if job['arm']=='base' and modes:faults.append('unexpected persistent mode')
    controls=game.get('localTurnControl',{}).get('controls',[])
    if len(controls)!=2 or any(not any(e['op']=='freeze' for e in c['events']) for c in controls):faults.append('missing turn isolation')
    score=.5 if game['result']=='1/2-1/2' else float((game['result']=='1-0')==(job['side']=='white')) if game['result'] in ('1-0','0-1') else None
    return dict(job=job,result=game['result'],reason=game['reason'],score=score,faults=faults,plies=len(game['frames'])-1,
                final_clocks=game['frames'][-1]['clocks'],persistent_decisions=len(modes),model_decisions=len(reports),model_seconds=sum(r['seconds'] for r in reports),
                replay_sha256=sha(directory/'replay.json'),validated_frames=len(states))

def lane(phase,lane_id):
    plan=load();chosen=[j for j in plan['jobs'] if j['phase']==phase and j['lane']==lane_id]
    if phase=='misty':
        files=[OUT/'jobs'/j['id']/'result.json' for j in plan['jobs'] if j['phase']=='h2h'];assert all(p.exists() for p in files)
        rows=[json.loads(p.read_text()) for p in files];assert not any(r['faults'] for r in rows) and sum(r['score'] for r in rows)>2
    lock=(OUT/f'{phase}-lane{lane_id}.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for job in chosen:
        d=OUT/'jobs'/job['id'];d.mkdir(parents=True,exist_ok=True)
        if (d/'result.json').exists():
            result=json.loads((d/'result.json').read_text());assert not result['faults'];continue
        with (d/'started.json').open('x') as f:json.dump({'at':now(),'job':job,'parent_pid':os.getpid(),'plan_sha256':sha(OUT/'plan.json')},f,indent=2)
        start=time.monotonic()
        proc=subprocess.Popen(['taskset','-c',plan['lanes'][str(lane_id)],sys.executable,str(Path(__file__)),'worker','--job',job['id']],
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=clean_env(),start_new_session=True)
        write(d/'handle.json',{'pid':proc.pid,'started':now(),'job':job['id']})
        try:stdout,stderr=proc.communicate(timeout=plan['game_wall_cap']);timeout=False
        except subprocess.TimeoutExpired:timeout=True;proc.kill();stdout,stderr=proc.communicate()
        unverified=cleanup_registry(d/'processes.json');(d/'stdout.txt').write_text(stdout);(d/'stderr.txt').write_text(stderr)
        if proc.returncode or timeout or unverified or not (d/'replay.json').exists():
            result=dict(job=job,score=None,faults=[f'worker exit={proc.returncode} timeout={timeout} unverified={unverified}'])
        else:result=inspect(job,d)
        result.update(exit=proc.returncode,elapsed_seconds=time.monotonic()-start,finished=now());write(d/'result.json',result)
        print(json.dumps(result),flush=True)
        if result['faults']:raise RuntimeError(result['faults'])

def summarize():
    plan=load();rows=[]
    for j in plan['jobs']:
        p=OUT/'jobs'/j['id']/'result.json'
        if p.exists():rows.append(json.loads(p.read_text()))
    result=dict(completed=len(rows),planned=len(plan['jobs']),faults=[r for r in rows if r['faults']],panels={},scope='Small full-clock pilot, not an Elo estimate or release gate')
    for phase,arm in [('h2h','candidate'),('misty','candidate'),('misty','base')]:
        scores=[r['score'] for r in rows if r['job']['phase']==phase and r['job']['arm']==arm and r['score'] is not None]
        result['panels'][phase+'/'+arm]=dict(games=len(scores),wins=scores.count(1),draws=scores.count(.5),losses=scores.count(0),score=sum(scores)/len(scores) if scores else None)
    write(OUT/'summary.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['smoke','prepare','worker','lane','summarize']);p.add_argument('--job');p.add_argument('--phase',choices=['h2h','misty']);p.add_argument('--lane',type=int,choices=[0,1]);args=p.parse_args()
    if args.command=='worker':worker(args.job)
    elif args.command=='lane':lane(args.phase,args.lane)
    else:globals()[args.command]()
