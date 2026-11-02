#!/usr/bin/env python3
"""Fixed confirmation queue using the existing turn-isolated pilot runner."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/persistent-confirmation-20261102'
PARENT=HERE.parent/'persistent-response-20261101'
PILOT=ROOT/'astra-submissions/analysis/persistent-response-20261101/full-games'
RUNNER=PARENT/'bench.py'
sys.path.insert(0,str(ROOT))
from learning import rules


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def pair_interval(panels):
    """Exact percentile bootstrap, independently resampling pairs per panel."""
    import numpy as np
    distribution=np.array([1.]);games=0
    for points in panels:
        assert points and all(x in (0,.5,1,1.5,2) for x in points)
        mass=np.bincount([round(2*x) for x in points],minlength=5)/len(points)
        for _ in points:distribution=np.convolve(distribution,mass)
        games+=2*len(points)
    assert games and abs(float(distribution.sum())-1)<1e-10
    cdf=np.cumsum(distribution)
    return [int(np.searchsorted(cdf,q))/(2*games) for q in (.025,.975)]

def module():
    spec=importlib.util.spec_from_file_location('confirmation_pilot_runner',RUNNER)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    # worker subprocesses re-enter this adapter, which reinstalls the globals.
    # No frozen runner or playing source file is edited.
    m.HERE=HERE;m.OUT=OUT;m.__file__=str(Path(__file__))
    return m


def prepare():
    OUT.mkdir(parents=True,exist_ok=False);build=HERE/'build';build.mkdir(exist_ok=False)
    for arm in ('candidate','base','misty'):(build/arm).symlink_to(PARENT/'build'/arm,target_is_directory=True)
    shutil.copy2(PARENT/'build/referee.py',build/'referee.py')
    archive=ROOT/'fable-submissions/iamavirus-v35-mist-c-v14.zip';target=build/'v35';target.mkdir()
    with zipfile.ZipFile(archive) as z:
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
        z.extractall(target)
    r=subprocess.run(['bash','build.sh'],cwd=target,capture_output=True,text=True,timeout=60)
    (OUT/'v35-build.log').write_text(r.stdout+r.stderr);r.check_returncode()
    m=module();smokes=[]
    feed='fow\nw 180 2\n'+rules.Board().observation(0)+'\n180\n'
    for arm in ('v35','base','candidate','misty'):
        env=m.clean_env();env['MIST_MAX_SECONDS']='.5'
        r=subprocess.run(m.command(arm,219000),cwd='/tmp',input=feed,capture_output=True,text=True,env=env,timeout=60)
        moves=[l[5:] for l in r.stdout.splitlines() if l.startswith('move ')]
        record=dict(arm=arm,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr);smokes.append(record);save(OUT/'smoke.json',smokes)
        assert r.returncode==0 and r.stdout.splitlines()[0]=='ready' and len(moves)==1 and moves[0] in rules.Board().legal_moves(),record
        if arm=='candidate':assert 'astra_persistent: prior 0.25 ' in r.stderr and 'load_failed 0' in r.stderr
    save(OUT/'preparation.json',dict(source_sha256=sha(Path(__file__)),reused_runner_sha256=sha(RUNNER),v35_archive_sha256=sha(archive),v35_binary_sha256=sha(target/'mist'),smokes_passed=4))
    print(json.dumps({'prepared':True,'smokes':4,'frozen':False,'matches_started':0}))


def freeze():
    # This command cannot freeze a continuation before the entire original
    # pilot and its conditional controls finish without technical faults.
    pilot=json.loads((PILOT/'plan.json').read_text());records=[]
    for job in pilot['jobs']:
        path=PILOT/'jobs'/job['id']/'result.json';r=json.loads(path.read_text())
        assert r['job']==job and r['exit']==0 and not r['faults'];records.append(r)
    hh=sum(r['score'] for r in records if r['job']['phase']=='h2h')
    score={arm:sum(r['score'] for r in records if r['job']['phase']=='misty' and r['job']['arm']==arm) for arm in ('candidate','base')}
    assert hh>=4 and score['candidate']>=score['base']
    deps=dict(pilot['dependencies'])
    for p in (RUNNER,Path(__file__),OUT/'preparation.json',OUT/'smoke.json',OUT/'arithmetic-check.json',
              ROOT/'fable-submissions/iamavirus-v35-mist-c-v14.zip',ROOT/'learning/rules.py',ROOT/'learning/ingest.py'):
        deps[str(p)]=sha(p)
    for job in pilot['jobs']:
        p=PILOT/'jobs'/job['id']/'result.json';deps[str(p)]=sha(p)
    for arm in ('candidate','base','v35','misty'):
        directory=HERE/'build'/arm
        for rel in ('run.sh','mist','bin/stockfish','data/history.bin','misty_bot.py'):
            p=directory/rel
            if p.is_file():deps[str(p)]=sha(p)
    deps[str(HERE/'build/referee.py')]=sha(HERE/'build/referee.py')
    assert sha(HERE/'build/candidate/mist')=='00dc640d9773296b7af7f35b9faceb7f1b2ea6e49199742091415825e5744056'
    groups=[];pair=0
    for n in range(16):
        for opponent in ('v35','base'):
            group=[]
            for side in ('white','black'):
                group.append(dict(id=f'confirm-{opponent}-p{n}-{side}',phase='confirm',panel=opponent,lane=pair%3,pair=pair,arm='candidate',side=side,engine_seed=219000+2*pair,opponent_seed=219001+2*pair,opponent=opponent))
            groups.append(group);pair+=1
    jobs=[]
    for block in range(4):
        for group in groups[block*8:(block+1)*8]:jobs.extend(group)
        for side in ('white','black'):
            for arm in ('candidate','base'):
                jobs.append(dict(id=f'confirm-misty-p{block}-{side}-{arm}',phase='confirm',panel='misty',lane=(block+2)%3,pair=32+block,arm=arm,side=side,engine_seed=219200+2*block,opponent_seed=219201+2*block,opponent='misty'))
    assert len(jobs)==80 and len({j['id'] for j in jobs})==80
    assert Counter(j['panel'] for j in jobs)=={'v35':32,'base':32,'misty':16}
    for group in groups:
        assert {j['side'] for j in group}=={'white','black'} and len({j['lane'] for j in group})==1
    for p,h in deps.items():assert sha(Path(p))==h,('changed dependency',p)
    plan=dict(created_at=datetime.now(timezone.utc).isoformat(),dependencies=deps,jobs=jobs,lanes={'0':'0,1','1':'4,5','2':'6,7'},
        time_control=pilot['time_control'],game_wall_cap=pilot['game_wall_cap'],misty_version=pilot['misty_version'],
        model_sha256=pilot['model_sha256'],confidence=.25,projection=True,persistent=True,
        qualifying_pilot={'h2h_points':hh,'h2h_games':8,'misty_points':score,'misty_games_per_arm':4},
        gate='One fixed 80-game batch. All first attempts and no technical faults required. Each direct panel score >=0.50; pooled direct score >=0.60 and stratified colour-pair percentile-bootstrap 95% lower bound >0.50. Candidate Misty points >= exact-v37 control, eight games each. Passing earns a release review, not an arena Elo claim. Failure closes this frozen candidate without adding games or tuning to this batch.',
        interval='Direct panels each have 16 colour-paired seeds. Resample 16 whole pairs within each reference, then pool equally. Compute the exact empirical bootstrap distribution by polynomial convolution over pair points {0,0.5,1,1.5,2}; take 2.5%/97.5% quantiles. Do not treat colour-paired games as independent.',
        fault_policy='The reused runner stops a lane on its first technical fault; preserve all other first-attempt results. No automatic repeat or repair inside this batch. A fault disqualifies the promotion gate.',
        resume='Never repeat a started game automatically; reconcile original handles and first-attempt receipts.',
        limitations=pilot['limitations']+' A pooled local win rate against two references is not arena Elo; the Misty panel is a small matched control, not proof of non-inferiority.',
        turn_control=pilot['turn_control'],model_updates_during_batch=False)
    with (OUT/'plan.json').open('x') as f:json.dump(plan,f,indent=2)
    module().load()
    save(OUT/'queue-audit.json',dict(jobs=len(jobs),lanes=dict(Counter(j['lane'] for j in jobs)),panels=dict(Counter(j['panel'] for j in jobs)),unique_ids=True,worker_entrypoint=str(Path(__file__)),script_sha256=sha(Path(__file__))))
    print(json.dumps({'frozen':True,'jobs':len(jobs),'plan_sha256':sha(OUT/'plan.json')}))


def summarize():
    plan=module().load();rows=[]
    for job in plan['jobs']:
        p=OUT/'jobs'/job['id']/'result.json'
        if p.exists():
            r=json.loads(p.read_text());assert r['job']==job;rows.append(r)
    summary=dict(completed=len(rows),planned=80,faults=[r for r in rows if r['faults'] or r['exit']!=0 or r['score'] not in (0,.5,1)],panels={},decision='incomplete')
    for panel,arm in [('v35','candidate'),('base','candidate'),('misty','candidate'),('misty','base')]:
        rr=[r for r in rows if r['job']['panel']==panel and r['job']['arm']==arm and r['score'] is not None];s=[r['score'] for r in rr]
        summary['panels'][panel+'/'+arm]=dict(games=len(s),wins=s.count(1),draws=s.count(.5),losses=s.count(0),points=sum(s),score=sum(s)/len(s) if s else None)
    if len(rows)==80 and not summary['faults']:
        panel_points=[]
        for panel in ('v35','base'):
            rr=[r for r in rows if r['job']['panel']==panel];pairs={r['job']['pair'] for r in rr};assert len(pairs)==16
            points=[]
            for p in pairs:
                pair_rows=[r for r in rr if r['job']['pair']==p]
                assert len(pair_rows)==2 and {r['job']['side'] for r in pair_rows}=={'white','black'}
                points.append(sum(r['score'] for r in pair_rows))
            panel_points.append(points)
        interval=pair_interval(panel_points)
        a=summary['panels'];pooled=(a['v35/candidate']['points']+a['base/candidate']['points'])/64
        conditions=dict(each_reference_at_least_half=min(a['v35/candidate']['score'],a['base/candidate']['score'])>=.5,pooled_at_least_point6=pooled>=.6,paired_lower_above_half=interval[0]>.5,misty_at_least_control=a['misty/candidate']['points']>=a['misty/base']['points'])
        summary.update(pooled_direct_score=pooled,stratified_pair_interval_95=interval,conditions=conditions,decision='release_review' if all(conditions.values()) else 'close_frozen_candidate')
    elif summary['faults']:summary['decision']='technical_failure_no_promotion'
    save(OUT/'summary.json',summary);print(json.dumps(summary,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=('prepare','freeze','lane','worker','summarize'));ap.add_argument('--phase',default='confirm');ap.add_argument('--lane',type=int,choices=(0,1,2));ap.add_argument('--job');args=ap.parse_args()
    if args.command=='lane':assert args.phase=='confirm';module().lane(args.phase,args.lane)
    elif args.command=='worker':module().worker(args.job)
    else:globals()[args.command]()
