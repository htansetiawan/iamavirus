"""Conditional 16-game gate using the existing turn-isolated referee runner."""
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
EVIDENCE=ROOT/'astra-submissions/analysis/value-expansion-20261102';OUT=EVIDENCE/'full-games'
RUNNER=HERE.parent/'persistent-response-20261101/bench.py'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest


def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');tmp.replace(p)


def command(arm,seed):
    assert arm in ('base','candidate')
    return ['/usr/bin/env',f'FOW_SEED={seed}',f'MIST_EXPANSION_Q={int(arm=="candidate")}',
            '/bin/bash',str(HERE/'build'/arm/'run.sh')]


def inspect(job,directory):
    game=json.loads((directory/'replay.json').read_text());states,errors=ingest.validate_replay(game);faults=list(errors)
    if 'failedSide' in game:faults.append('bot failure: '+game['failedSide']+' '+game['reason'])
    if game['result'] not in ('1-0','0-1','1/2-1/2'):faults.append('non-game result')
    if game.get('warnings'):faults.append('capture warning')
    reports=[]
    for side in ('white','black'):
        text=game.get('privateDiagnostics',{}).get(side,'')
        stats=[dict(re.findall(r'(\w+)=([\d.]+)',s)) for s in text.splitlines() if s.startswith('astra-expansion-q ')]
        if side==job['side']:
            reports=stats
            if not stats or not any(int(s['scored'])>0 for s in stats):faults.append('new expansion rule not exercised')
            if any(int(s['recall_failures']) for s in stats):faults.append('information-set reach inconsistency')
        elif stats:faults.append('baseline unexpectedly enabled')
    controls=game.get('localTurnControl',{}).get('controls',[])
    if len(controls)!=2 or any(not any(e['op']=='freeze' for e in c['events']) for c in controls):faults.append('missing turn isolation')
    score=.5 if game['result']=='1/2-1/2' else float((game['result']=='1-0')==(job['side']=='white')) if game['result'] in ('1-0','0-1') else None
    return dict(job=job,result=game['result'],reason=game['reason'],score=score,faults=faults,plies=len(game['frames'])-1,
        final_clocks=game['frames'][-1]['clocks'],q_decisions=len(reports),q_seconds=sum(float(s['seconds']) for s in reports),
        replay_sha256=sha(directory/'replay.json'),validated_frames=len(states))


def module():
    spec=importlib.util.spec_from_file_location('qexp_full_game_runner',RUNNER)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.HERE=HERE;m.OUT=OUT;m.__file__=str(Path(__file__));m.command=command;m.inspect=inspect
    return m


def prepare():
    prior=json.loads((EVIDENCE/'plan.json').read_text());s=json.loads((EVIDENCE/'paired-summary.json').read_text())
    review=json.loads((EVIDENCE/'independent-review.json').read_text())
    assert s['gate_pass'] and review['labels_match'] and review['summary_sha256']==sha(EVIDENCE/'paired-summary.json')
    assert json.loads((EVIDENCE/'terminal.json').read_text())['status']=='complete'
    OUT.mkdir(exist_ok=False)
    shutil.copyfile(ROOT.parent/'fow-starter/referee.py',HERE/'build/referee.py')
    dependencies=dict(prior['dependencies'])
    for p in [RUNNER,Path(__file__),HERE/'build/referee.py',EVIDENCE/'paired-summary.json',EVIDENCE/'independent-review.json',
              EVIDENCE/'plan.json',ROOT/'astra-submissions/tools/local_turn_control.py']:
        dependencies[str(p)]=sha(p)
    # The reused loader accepts absolute paths. The earlier evidence uses
    # repository-relative keys; resolve them once before freezing this queue.
    dependencies={str(ROOT/k):v for k,v in dependencies.items()}
    for k,h in dependencies.items():assert sha(k)==h,k
    jobs=[]
    for pair in range(8):
        for side in ('white','black'):
            jobs.append(dict(id=f'qexp-p{pair}-{side}',phase='h2h',lane=pair%2,pair=pair,arm='candidate',side=side,
                engine_seed=2341200+2*pair,opponent_seed=2341201+2*pair,opponent='base'))
    plan=dict(created_at=now(),dependencies=dependencies,jobs=jobs,lanes={'0':'2,3','1':'4,5'},
        time_control={'base':180,'increment':2,'max_plies':1000},game_wall_cap=2450,batch_wall_cap=14400,
        gate='16 first-attempt games, eight colour-swapped pairs vs exact v37. >=10 points and zero technical faults/forfeits earns a separate opponent gate, not promotion. Otherwise close this frozen configuration. No extra games, tuning or restart of an already-started game.',
        resume='Skip only verified completed receipts. A started game with no result requires authoritative handle/process reconciliation; never automatically repeat it.',
        initial_position='Standard start; independently seeded engines; both colours share each pair of engine seeds.',
        candidate_binary_sha256=sha(HERE/'build/candidate/mist'),baseline_binary_sha256=sha(HERE/'build/base/mist'),
        gpu=False,truth_to_actor=False,source_mode='Production candidate, no paired/teacher export instrumentation',
        limitations='Small local full-game pilot against one reference. Not arena Elo, not a test against the actual instructors or duck, and not a release gate.')
    with (OUT/'plan.json').open('x') as f:json.dump(plan,f,indent=2);f.write('\n')
    module().load();print(json.dumps({'planned_games':16,'pairs':8,'plan_sha256':sha(OUT/'plan.json')}))


def start():
    module().load()
    with (OUT/'batch-start.json').open('x') as f:json.dump({'at':now(),'monotonic':time.monotonic()},f)


def lane(lane_id):
    m=module();plan=m.load();started=json.loads((OUT/'batch-start.json').read_text())
    lock=(OUT/f'lane{lane_id}.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for job in [j for j in plan['jobs'] if j['lane']==lane_id]:
        d=OUT/'jobs'/job['id'];d.mkdir(parents=True,exist_ok=True)
        if (d/'result.json').exists():
            r=json.loads((d/'result.json').read_text());assert r['job']==job and not r['faults'] and r['exit']==0;continue
        remaining=plan['batch_wall_cap']-(time.monotonic()-started['monotonic'])
        if remaining<=1:raise RuntimeError('batch wall cap; pending games not started')
        with (d/'started.json').open('x') as f:json.dump({'at':now(),'job':job,'parent_pid':os.getpid(),'plan_sha256':sha(OUT/'plan.json')},f,indent=2)
        begin=time.monotonic()
        p=subprocess.Popen(['taskset','-c',plan['lanes'][str(lane_id)],sys.executable,str(Path(__file__)),'worker','--job',job['id']],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=m.clean_env(),start_new_session=True)
        write(d/'handle.json',{'pid':p.pid,'started':now(),'job':job['id'],'pid_scope':'worker in original exec namespace'})
        try:stdout,stderr=p.communicate(timeout=min(plan['game_wall_cap'],remaining));timeout=False
        except subprocess.TimeoutExpired:timeout=True;p.kill();stdout,stderr=p.communicate()
        unverified=m.cleanup_registry(d/'processes.json');(d/'stdout.txt').write_text(stdout);(d/'stderr.txt').write_text(stderr)
        if p.returncode or timeout or unverified or not (d/'replay.json').exists():
            result=dict(job=job,score=None,faults=[f'worker exit={p.returncode} timeout={timeout} unverified={unverified}'])
        else:result=inspect(job,d)
        result.update(exit=p.returncode,elapsed_seconds=time.monotonic()-begin,finished=now());write(d/'result.json',result)
        print(json.dumps(result),flush=True)
        if result['faults']:raise RuntimeError(result['faults'])


def summarize():
    plan=module().load();rows=[]
    for j in plan['jobs']:
        p=OUT/'jobs'/j['id']/'result.json'
        if p.exists():r=json.loads(p.read_text());assert r['job']==j;rows.append(r)
    scores=[r['score'] for r in rows if r['score'] is not None]
    faults=[r for r in rows if r['faults'] or r['exit']!=0]
    decision='incomplete'
    if faults:decision='technical_failure_no_promotion'
    elif len(rows)==16:decision='separate_opponent_gate' if sum(scores)>=10 else 'close_configuration'
    result=dict(at=now(),completed=len(rows),planned=16,wins=scores.count(1),draws=scores.count(.5),losses=scores.count(0),points=sum(scores),
        faults=faults,decision=decision,scope='Local full-clock pilot; no arena Elo or release claim.')
    write(OUT/'summary.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('prepare','start','worker','lane','summarize'));p.add_argument('--job');p.add_argument('--lane',type=int,choices=(0,1));a=p.parse_args()
    if a.command=='worker':module().worker(a.job)
    elif a.command=='lane':lane(a.lane)
    else:globals()[a.command]()
