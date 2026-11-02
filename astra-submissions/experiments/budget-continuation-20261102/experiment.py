"""Frozen twelve-run policy-budget study; reuse the verified 241 mechanics."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PRIOR=HERE.parent/'private-continuation-20261102'
OUT=ROOT/'astra-submissions/analysis/budget-continuation-20261102'
REFRESH=ROOT/'astra-submissions/analysis/arena-refresh-20261102-residual'
sys.path.insert(0,str(PRIOR))
from build import BASE,ZIP
from continuation import REF,actor_prefix,prefix,run,sha,validate_prefix
from local_turn_control import cleanup_registry
sys.path.insert(0,str(ROOT))
from learning import ingest


def now():return datetime.now(timezone.utc).isoformat()


def write(p,value):
    with p.open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def clean_env():
    e={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_','OMP_','OPENBLAS_','MKL_'))}
    e.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    return e


def prepare():
    OUT.mkdir(exist_ok=True)
    previous=ROOT/'astra-submissions/analysis/private-continuation-20261102'
    assert json.loads((previous/'review.json').read_text())['passed']
    used={r['game'] for r in json.loads((previous/'plan.json').read_text())['cases']}
    failure_cases=[('updro1eg',94),('g9nruayl',78)]
    used|={g for g,_ in failure_cases}
    manifest=json.loads((REFRESH/'manifest.json').read_text())
    top={p['name'] for p in json.loads((REFRESH/'standings.json').read_text())['players'] if p['rank']<=12}
    eligible=[]
    for gid,digest in manifest['sha256'].items():
        if gid in used:continue
        path=ROOT/'data/raw/games'/gid/'replay.json';assert sha(path)==digest
        r=json.loads(path.read_text())
        if r['white'] in top and r['black'] in top and len(r['frames'])>34:
            eligible.append((hashlib.sha256(('242-prefix:'+gid).encode()).hexdigest(),gid))
    chosen=[(gid,32+i,'hash_selected') for i,(_,gid) in enumerate(sorted(eligible)[:2])]
    chosen += [(gid,ply,'post_hoc_failure') for gid,ply in failure_cases]
    cases=[];jobs=[]
    for index,(gid,branch,kind) in enumerate(chosen):
        path=ROOT/'data/raw/games'/gid/'replay.json';r=json.loads(path.read_text());p=prefix(r,branch)
        state=validate_prefix(p);pref=OUT/f'prefix-{index}.json';write(pref,p)
        case=dict(id=f'p{index}',game=gid,branch_ply=branch,kind=kind,seed=2421102+2*index,
            prefix=str(pref.relative_to(ROOT)),prefix_sha256=sha(pref),source_replay_sha256=sha(path),
            state=state,lane=index%2)
        cases.append(case)
        arms=['cheap','normal','normal_repeat'];arms=arms[index%3:]+arms[:index%3]
        for arm in arms:
            jobs.append(dict(id=f'p{index}-{arm}',case=index,arm=arm,lane=index%2,
                max_seconds=1. if arm=='cheap' else 10.,seed=case['seed']))
    dependencies=[*HERE.glob('*.py'),HERE/'README.md',PRIOR/'continuation.py',PRIOR/'build/mist',
        previous/'build.json',previous/'preflight.json',previous/'review.json',REF,
        BASE/'bin/stockfish',BASE/'data/history.bin',ZIP,ROOT/'astra-submissions/tools/local_turn_control.py',
        ROOT/'learning/ingest.py',REFRESH/'manifest.json',REFRESH/'standings.json']
    plan=dict(at=now(),cases=cases,jobs=jobs,deps={str(p):sha(p) for p in dependencies},
        max_continuation_plies=64,job_wall_seconds=1000,batch_wall_seconds=7200,lanes={'0':'0,1','1':'2,3'},
        selection='Two SHA256(242-prefix:id) unused refresh top12 games, then the two predeclared post-hoc residual failures; not a strength cohort.',
        repeats='One planned normal-budget repeat per prefix, same seed. Never retry a job.',
        stop='Any technical fault stops new jobs. In-flight jobs finish within their original caps and remain recorded.',
        measures=['clock and private-history correctness','cost per natural terminal and new decision','censoring','first-action agreement','cheap/normal outcome difference','normal/repeat outcome difference'],
        inference='Four selected prefixes cannot establish population equivalence or strength. No model fit, bulk generation, gate relaxation or release follows automatically.',
        no_gpu=True)
    write(OUT/'plan.json',plan)
    print(json.dumps({'plan_sha256':sha(OUT/'plan.json'),'jobs':len(jobs),'cases':[{k:c[k] for k in ('game','branch_ply','kind')} for c in cases]}))


def load():
    p=json.loads((OUT/'plan.json').read_text())
    for name,h in p['deps'].items():assert sha(name)==h,name
    for c in p['cases']:assert sha(ROOT/c['prefix'])==c['prefix_sha256']
    return p


def worker(job_id):
    plan=load();job=next(j for j in plan['jobs'] if j['id']==job_id);case=plan['cases'][job['case']]
    p=json.loads((ROOT/case['prefix']).read_text());commands=[]
    for side in (0,1):
        a=actor_prefix(p,side)
        commands.append(['/usr/bin/env',f'FOW_SEED={job["seed"]+side}',
            f'MIST_FORCE_MOVES={",".join(a["moves"])}','ASTRA_PREFIX_CONTINUE=1',
            f'ASTRA_PREFIX_CLOCKS={",".join(map(str,a["post_clocks"]))}',
            f'MIST_STOCKFISH={BASE/"bin/stockfish"}',f'MIST_HISTORY_TABLE={BASE/"data/history.bin"}',
            f'MIST_MAX_SECONDS={job["max_seconds"]}',str(PRIOR/'build/mist')])
    game=run(p,commands,OUT/job_id,plan['max_continuation_plies'])
    write(OUT/job_id/'replay.json',game)


def inspect(plan,job,directory):
    case=plan['cases'][job['case']];p=json.loads((ROOT/case['prefix']).read_text())
    game=json.loads((directory/'replay.json').read_text());states,errors=ingest.validate_replay(game)
    assert not errors,errors
    assert not game.get('failedSide') and not game.get('warnings'),game['reason']
    b=case['branch_ply'];frames=game['frames'];steps=game['continuation']['steps']
    assert len(frames)>b+1 and len(steps)==len(frames)-1
    assert all(g[k]==f[k] for g,f in zip(frames[:b+1],p['frames']) for k in ('board','white','black','move','clocks'))
    assert len(game['continuation']['prefix_observations'])==2*(b+1)
    for side,key in enumerate(('white','black')):
        a=actor_prefix(p,side);text=game['privateDiagnostics'][key]
        restored=[float(x) for x in re.findall(r'astra-prefix: decision=\d+ clock=([\d.]+)',text)]
        assert restored==a['post_clocks']
        searched=sum(line.startswith('mist: n=') for line in text.splitlines())
        # A valid first-move terminal need not give the other side a new turn.
        assert searched==sum(s['side']==side and not s['prefix'] for s in steps)
        views=[e for e in game['protocol']['events'] if e['side']==key and e['direction']=='input' and len(e['text'])==64]
        last=max(s['ply'] for s in steps if s['side']==side)
        assert [e['ply'] for e in views]==list(range(last+1))
        for e in views:assert e['text']==frames[e['ply']][key]
    assert not game['protocol']['truncated']
    for i,s in enumerate(steps):
        side=i%2;assert s['ply']==i and s['side']==side and s['move']==frames[i+1]['move']
        assert abs(s['reported_clock']-frames[i]['clocks'][side])<2e-6
        assert abs(frames[i+1]['clocks'][1-side]-frames[i]['clocks'][1-side])<2e-6
        if i>=b:
            expect=frames[i]['clocks'][side]-s['actual_elapsed']+game['timeControl']['incrementSeconds']
            assert abs(frames[i+1]['clocks'][side]-expect)<2e-6
    if game['censored']:
        assert game['result']=='*' and states[-1].outcome() is None and len(frames)-1==b+plan['max_continuation_plies']
    else:assert states[-1].outcome()==(game['result'],game['reason'])
    c=game['continuation']
    return dict(case=case['id'],arm=job['arm'],source=case['game'],branch_ply=b,new_plies=len(frames)-1-b,
        first_move=frames[b+1]['move'],natural_result=None if game['censored'] else game['result'],
        censored=game['censored'],reason=game['reason'],wall_seconds=c['wall_seconds'],
        warmup_seconds=c['prefix_cpu_charged_seconds'],continuation_seconds=c['continuation_charged_seconds'],
        replay_sha256=sha(directory/'replay.json'),validated_frames=len(states),final_clocks=frames[-1]['clocks'])


def launch():
    plan=load();write(OUT/'started.json',dict(at=now(),pid=os.getpid(),plan_sha256=sha(OUT/'plan.json')))
    started=time.monotonic();stop=threading.Event()
    def lane(index):
        for job in [j for j in plan['jobs'] if j['lane']==index]:
            if stop.is_set():return
            if plan['batch_wall_seconds']-(time.monotonic()-started)<plan['job_wall_seconds']:
                stop.set();return
            directory=OUT/job['id'];directory.mkdir(exist_ok=False)
            write(directory/'started.json',dict(at=now(),job=job))
            proc=subprocess.Popen(['taskset','-c',plan['lanes'][str(index)],sys.executable,str(Path(__file__)),'worker','--job',job['id']],
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True,env=clean_env())
            write(directory/'handle.json',dict(at=now(),pid=proc.pid));timeout=False
            try:stdout,stderr=proc.communicate(timeout=plan['job_wall_seconds'])
            except subprocess.TimeoutExpired:timeout=True;proc.kill();stdout,stderr=proc.communicate()
            unverified=cleanup_registry(directory/'processes.json')
            (directory/'stdout.txt').write_text(stdout);(directory/'stderr.txt').write_text(stderr)
            row=dict(job=job,exit=proc.returncode,timeout=timeout,unverified_groups=unverified)
            try:
                assert proc.returncode==0 and not timeout and not unverified,row
                row.update(inspect(plan,job,directory));row['passed']=True
            except Exception as e:row.update(passed=False,error=repr(e));stop.set()
            write(directory/'result.json',row);print(json.dumps(row),flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(lane,i) for i in (0,1)]
        for f in futures:f.result()
    rows=[json.loads((OUT/j['id']/'result.json').read_text()) for j in plan['jobs'] if (OUT/j['id']/'result.json').exists()]
    complete=len(rows)==len(plan['jobs']) and all(r['passed'] for r in rows)
    report=dict(at=now(),complete=complete,planned=len(plan['jobs']),attempted=len(rows),rows=rows,
        seconds=time.monotonic()-started,scope='Budget/target sensitivity and cost, not strength or confirmation of cheap labels.')
    write(OUT/'summary.json',report);print(json.dumps({'complete':complete,'attempted':len(rows),'seconds':report['seconds']}),flush=True)
    if not complete:raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('prepare','launch','worker'));p.add_argument('--job');a=p.parse_args()
    if a.command=='worker':worker(a.job)
    else:globals()[a.command]()
