"""Frozen matched Misty comparison, reusing the audited turn-isolated harness."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
CANDIDATE=HERE.parent/'sf-allchildren-20261102';EVIDENCE=ROOT/'astra-submissions/analysis/sf-allchildren-20261102/full-games'
OUT=ROOT/'astra-submissions/analysis/sf-opponent-20261108'
MISTY=HERE.parent/'stable-mix-20261101/build/misty'
LEGACY=HERE.parent/'sparse-cfr-20261102/full_games.py'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest,rules

def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def command(arm,seed):
    assert arm in ('base','candidate','misty')
    path=MISTY/'run.sh' if arm=='misty' else CANDIDATE/'build'/arm/'run.sh'
    return ['/usr/bin/env',f'FOW_SEED={seed}','/bin/bash',str(path)]
def inspect(job,directory):
    game=json.loads((directory/'replay.json').read_text());states,errors=ingest.validate_replay(game);faults=list(errors)
    if 'failedSide' in game:faults.append('bot failure: '+game['failedSide']+' '+game['reason'])
    if game.get('warnings'):faults.append('capture warning')
    if game['result'] not in ('1-0','0-1','1/2-1/2'):faults.append('non-game result')
    ours=game.get('privateDiagnostics',{}).get(job['side'],'')
    if 'mist: stockfish ready' not in ours:faults.append('our Stockfish initialization missing')
    if 'astra-solver-pair' in ours:faults.append('diagnostic engine in full game')
    controls=game.get('localTurnControl',{}).get('controls',[])
    if len(controls)!=2 or any(not any(e['op']=='freeze' for e in c['events']) for c in controls):faults.append('missing turn isolation')
    score=.5 if game['result']=='1/2-1/2' else float((game['result']=='1-0')==(job['side']=='white')) if game['result'] in ('1-0','0-1') else None
    return dict(job=job,result=game['result'],reason=game['reason'],score=score,faults=faults,
                plies=len(game['frames'])-1,final_clocks=game['frames'][-1]['clocks'],
                replay_sha256=sha(directory/'replay.json'),validated_frames=len(states))

spec=importlib.util.spec_from_file_location('sf_opponent_legacy',LEGACY);legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
legacy.HERE=CANDIDATE;legacy.ROOT=ROOT;legacy.OUT=OUT;legacy.EVIDENCE=EVIDENCE;legacy.__file__=__file__
legacy.command=command;legacy.inspect=inspect

def prepare():
    review=json.loads((EVIDENCE/'independent-review.json').read_text());assert review['gate_pass'] and review['completed']==16 and not review['live_owned_processes']
    OUT.mkdir(exist_ok=False)
    old=json.loads((ROOT/'astra-submissions/analysis/stable-mix-20261101/plan.json').read_text())
    deps={p:h for p,h in old['dependencies'].items() if '/fable-persist/' in p or '/build/misty/' in p}
    version=subprocess.check_output(['/home/henrytan/fable-persist/scratchpad/misty/venv/bin/python','-c','import importlib.metadata; print(importlib.metadata.version("misty-chess"))'],text=True).strip()
    assert version==old['misty_version']=='0.1.3'
    previous=json.loads((EVIDENCE/'plan.json').read_text())
    for p,h in previous['dependencies'].items():assert sha(p)==h,p
    # Pin production binaries and launchers rather than inheriting unrelated
    # development scripts whose formatting can change during package work.
    paths=[Path(__file__),HERE/'README.md',LEGACY,legacy.RUNNER,CANDIDATE/'build/referee.py',
           EVIDENCE/'independent-review.json',EVIDENCE/'plan.json',ROOT/'astra-submissions/tools/local_turn_control.py',
           CANDIDATE/'build/base/mist',CANDIDATE/'build/candidate/mist',CANDIDATE/'build/base/run.sh',CANDIDATE/'build/candidate/run.sh',
           CANDIDATE/'build/candidate/src/stockfish',CANDIDATE.parent/'queen-terminal-backport-20261102/build-r2/base/bin/stockfish',
           CANDIDATE.parent/'queen-terminal-backport-20261102/build-r2/base/data/history.bin',ROOT/'learning/ingest.py',ROOT/'learning/rules.py']
    deps.update({str(p):sha(p) for p in paths})
    for p,h in deps.items():assert sha(p)==h,p
    jobs=[]
    for block in range(8):
        for side in ('white','black'):
            arms=('base','candidate') if (block+(side=='black'))%2==0 else ('candidate','base')
            for arm in arms:
                jobs.append(dict(id=f'sf257-b{block}-{side}-{arm}',phase='misty',lane=block%2,pair=block,arm=arm,side=side,
                       engine_seed=2572000+2*block,opponent_seed=2572001+2*block,opponent='misty'))
    plan=dict(created_at=now(),dependencies=deps,jobs=jobs,lanes={'0':'0,1','1':'2,3'},
          time_control={'base':180,'increment':2,'max_plies':1000},game_wall_cap=2450,batch_wall_cap=14400,
          misty_version=version,gate={'games':32,'candidate_min_points':8,'candidate_min_advantage_points':2,'technical_faults':0},
          order='8 seed blocks, both colors, alternate first arm within block; 16 games per arm',
          limitations='Authentic local Misty package, not verified current arena bytes. Seeds may not control every variation. Small development gate, not Elo.',
          gpu=False,truth_to_actor=False,candidate_scorer_sha256=previous['candidate_scorer_sha256'],baseline_scorer_sha256=previous['baseline_scorer_sha256'])
    write(OUT/'plan.json',plan);legacy.module().load();print(json.dumps(dict(planned_games=32,version=version,pins=len(deps),plan_sha256=sha(OUT/'plan.json'))),flush=True)

def smoke():
    legacy.module().load();os.sched_setaffinity(0,{0,1});rows=[]
    try:
        for arm in ('base','candidate','misty'):
            for side in (0,1):
                b=rules.Board();feed=['fow',('w' if not side else 'b')+' 180 2',b.observation(side)]
                if side:b.push('d2d4');feed.append(b.observation(side))
                feed.append('180');e=legacy.module().clean_env();e['MIST_MAX_SECONDS']='.1'
                r=subprocess.run(command(arm,2572000),input='\n'.join(feed)+'\n',capture_output=True,text=True,env=e,timeout=60)
                row=dict(arm=arm,side=side,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr);rows.append(row)
                moves=[s[5:] for s in r.stdout.splitlines() if s.startswith('move ')]
                assert r.returncode==0 and len(moves)==1 and moves[0] in b.legal_moves(),row
                if arm!='misty':assert 'mist: stockfish ready' in r.stderr
        write(OUT/'smoke.json',dict(passed=True,rows=rows));print(json.dumps(dict(passed=True,calls=len(rows))),flush=True)
    except BaseException as exc:write(OUT/'smoke.json',dict(passed=False,error=repr(exc),rows=rows));raise

def summarize():
    plan=legacy.module().load();rows=[]
    for j in plan['jobs']:
        p=OUT/'jobs'/j['id']/'result.json'
        if p.exists():r=json.loads(p.read_text());assert r['job']==j;rows.append(r)
    stats={}
    for arm in ('base','candidate'):
        scores=[r['score'] for r in rows if r['job']['arm']==arm and r['score'] is not None]
        stats[arm]=dict(games=len(scores),wins=scores.count(1),draws=scores.count(.5),losses=scores.count(0),points=sum(scores))
    faults=[r for r in rows if r['faults'] or r['exit']]
    decision='incomplete'
    if faults:decision='technical_failure_no_promotion'
    elif len(rows)==32:
        decision='final_package_review' if stats['candidate']['points']>=8 and stats['candidate']['points']-stats['base']['points']>=2 else 'close_unchanged_candidate'
    result=dict(at=now(),completed=len(rows),planned=32,arms=stats,faults=faults,decision=decision)
    (OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('prepare','smoke','start','worker','lane','summarize'));p.add_argument('--job');p.add_argument('--lane',type=int,choices=(0,1));a=p.parse_args()
    if a.command in ('prepare','smoke','summarize'):globals()[a.command]()
    elif a.command=='start':assert json.loads((OUT/'smoke.json').read_text())['passed'];legacy.start()
    elif a.command=='worker':legacy.module().worker(a.job)
    else:legacy.lane(a.lane)
