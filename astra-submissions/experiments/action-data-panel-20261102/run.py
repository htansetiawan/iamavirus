"""Frozen distinct-source acquisition using the verified 243 branch worker."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OLD=HERE.parent/'action-continuation-20261102'
OUT=ROOT/'astra-submissions/analysis/action-data-panel-20261102'
REFRESH=OUT.parent/'arena-refresh-20261102-actions'
LANES={'0':'0,1','1':'4,5'}
sys.path.insert(0,str(OLD))
import experiment as pilot
from branch import base,BASE,PRIOR,inspect
from local_turn_control import cleanup_registry
from input_contract import actor_history,critic_input,digest,VERSION

# Reuse the already-tested worker and dependency loader against this new plan.
# No original file or binary changes; each job has its own Python process.
pilot.OUT=OUT


def now():return datetime.now(timezone.utc).isoformat()


def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def select():
    preflight=json.loads((OUT/'input-preflight.json').read_text())
    assert preflight['passed'] and preflight['source_sha256']==base.sha(HERE/'input_contract.py')
    manifest=json.loads((REFRESH/'manifest.json').read_text())
    assert json.loads((REFRESH/'taxonomy-integrity.json').read_text())['all_checks_pass']
    old_end=json.loads((OUT.parent/'arena-refresh-20261102-residual/execution.json').read_text())['ended']
    top={p['name'] for p in json.loads((REFRESH/'standings.json').read_text())['players'] if p['rank']<=12}
    previous=[]
    for family in ('private-continuation-20261102','budget-continuation-20261102'):
        previous+=json.loads((OUT.parent/family/'plan.json').read_text())['cases']
    excluded={c['game'] for c in previous};seen_sequences=set()
    for gid in excluded:
        replay=json.loads((ROOT/'data/raw/games'/gid/'replay.json').read_text())
        seen_sequences.add(hashlib.sha256(' '.join(f['move'] for f in replay['frames'][1:]).encode()).hexdigest())
    games=[];available={}
    for gid,h in manifest['sha256'].items():
        path=ROOT/'data/raw/games'/gid/'replay.json';assert base.sha(path)==h
        r=json.loads(path.read_text())
        if (gid in excluded or datetime.fromisoformat(r['createdAt'].replace('Z','+00:00'))<datetime.fromisoformat(old_end)
                or r['white'] not in top or r['black'] not in top):continue
        sequence=hashlib.sha256(' '.join(f['move'] for f in r['frames'][1:]).encode()).hexdigest()
        games.append((gid,r,h,sequence))
    cases=[];used=set();observation_groups={}
    for phase in (64,48,32,16):
        for side in (0,1):
            ply=phase+side
            pool=[g for g in games if len(g[1]['frames'])>ply+1 and min(g[1]['frames'][ply]['clocks'])>20]
            pool.sort(key=lambda g:hashlib.sha256(f'244:{phase}:{side}:{g[0]}'.encode()).hexdigest())
            available[f'{phase}/{side}']=len(pool);chosen=[]
            for gid,r,h,seq in pool:
                if gid in used or seq in seen_sequences:continue
                p=base.prefix(r,ply);state=base.validate_prefix(p)
                index=len(cases);path=OUT/f'prefix-{index}.json';write(path,p)
                history=actor_history(p);shape=dict(history);shape.pop('own_turn_clocks');shape.pop('own_post_move_clocks')
                case=dict(id=f'p{index}',game=gid,branch_ply=ply,phase=phase,side=side,
                          prefix=str(path.relative_to(ROOT)),prefix_sha256=base.sha(path),source_replay_sha256=h,
                          source_trajectory_sha256=seq,actor_history_sha256=digest(history),
                          observable_history_without_clocks_sha256=digest(shape),state=state,
                          proposal_seed=2441102+2*index,lane=index%len(LANES))
                cases.append(case);chosen.append(gid);used.add(gid);seen_sequences.add(seq)
                observation_groups.setdefault(case['observable_history_without_clocks_sha256'],[]).append(gid)
                if len(chosen)==2:break
            assert len(chosen)==2,('insufficient fixed bucket; no outcome-based replacement',phase,side,len(chosen))
    deps=[*HERE.glob('*.py'),HERE/'README.md',OUT/'input-preflight.json',*OLD.glob('*.py'),
          OLD/'build/proposer',PRIOR/'build/mist',PRIOR/'continuation.py',BASE/'bin/stockfish',BASE/'data/history.bin',
          base.REF,ROOT/'astra-submissions/tools/local_turn_control.py',ROOT/'learning/ingest.py',
          REFRESH/'manifest.json',REFRESH/'standings.json',REFRESH/'taxonomy-integrity.json']
    plan=dict(at=now(),cases=cases,deps={str(p):base.sha(p) for p in deps},available=available,
              source_games=len(games),excluded_prior_ids=sorted(excluded),minimum_completion_time=old_end,
              observable_history_groups=observation_groups,input_contract=VERSION,
              proposal_wall_seconds=180,proposal_batch_seconds=1800,job_wall_seconds=1000,batch_wall_seconds=18000,
              max_new_plies=64,lanes=LANES,
              minimum_supported=8,minimum_phases=3,replicate_seeds=[2442200,2442202],
              choice='Current proposal choice plus highest-Q different view-legal CFR action; ties by probability and original index.',
              unsupported='Record no CFR root, front-end fallback, or fewer than two supported actions. Do not substitute sources.',
              scope='Balanced new development sources, normal-budget v37/v37 continuations. No model fit, strength claim or automatic deployment.',
              source_use='All actors, actions and replicas of each original trajectory stay in one development group.',no_gpu=True)
    write(OUT/'plan.json',plan)
    print(json.dumps({'plan_sha256':base.sha(OUT/'plan.json'),'cases':len(cases),'available':available}))


def proposal_worker(index):
    plan=pilot.load();case=plan['cases'][index];p=json.loads((ROOT/case['prefix']).read_text())
    d=OUT/f'proposal-{index}';cmds=[]
    for side in (0,1):
        a=base.actor_prefix(p,side)
        cmds.append(['/usr/bin/env',f'FOW_SEED={case["proposal_seed"]+side}',
                     'MIST_FORCE_MOVES='+','.join(a['moves']),'ASTRA_PREFIX_CONTINUE=1',
                     'ASTRA_PREFIX_CLOCKS='+','.join(map(str,a['post_clocks'])),
                     'ASTRA_PROPOSAL=1',f'MIST_STOCKFISH={BASE/"bin/stockfish"}',
                     f'MIST_HISTORY_TABLE={BASE/"data/history.bin"}','MIST_MAX_SECONDS=10',str(OLD/'build/proposer')])
    game=base.run(p,cmds,d,1);write(d/'replay.json',game)
    assert len(game['frames'])==case['branch_ply']+2
    chosen=game['frames'][-1]['move'];charge=game['continuation']['steps'][-1]['actual_elapsed']
    checked=inspect(game,p,chosen,charge)
    text=game['privateDiagnostics'][('white','black')[case['side']]]
    rows=[dict(move=m,probability=float(prob),value=float(v),index=i)
          for i,(m,prob,v) in enumerate(re.findall(r'astra-proposal: (\w+) (\S+) (\S+)',text))]
    legal=re.search(r'astra-view-legal:(.*)',text)[1].split()
    result=dict(case=index,chosen=chosen,common_charge=charge,rows=rows,view_legal=legal,
                checked=checked,replay_sha256=base.sha(d/'replay.json'))
    if not rows:result.update(supported=False,reason='no CFR root; single move or fallback')
    else:
        assert len({r['move'] for r in rows})==len(rows)
        assert all(math.isfinite(r['value']) and math.isfinite(r['probability']) and r['probability']>=0 for r in rows)
        value=float(re.search(r'astra-proposal-value: (\S+)',text)[1]);result['policy_value']=value
        assert abs(sum(r['probability'] for r in rows)-1)<1e-9
        assert abs(sum(r['probability']*r['value'] for r in rows)-value)<1e-9
        alternatives=[r for r in rows if r['move'] in legal and r['move']!=chosen]
        if chosen not in legal or chosen not in {r['move'] for r in rows}:result.update(supported=False,reason='chosen action outside observable CFR rows')
        elif not alternatives:result.update(supported=False,reason='no second supported action')
        else:
            alt=min(alternatives,key=lambda r:(-r['value'],-r['probability'],r['index']))
            result.update(supported=True,alternative=alt['move'])
            result['input_sha256']={m:digest(critic_input(p,m,result)) for m in (chosen,alt['move'])}
    write(d/'proposal.json',result)


def execute(command,directory,timeout,cores):
    directory.mkdir(exist_ok=False);write(directory/'started.json',dict(at=now(),command=command,cores=cores))
    proc=subprocess.Popen(['taskset','-c',cores,sys.executable,str(Path(__file__)),*command],
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=pilot.clean_env(),start_new_session=True)
    write(directory/'handle.json',dict(at=now(),pid=proc.pid));expired=False;error=None
    try:stdout,stderr=proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:expired=True;proc.kill();stdout,stderr=proc.communicate()
    except BaseException as e:error=repr(e);proc.kill();stdout,stderr=proc.communicate()
    remaining=cleanup_registry(directory/'processes.json')
    (directory/'stdout.txt').write_text(stdout);(directory/'stderr.txt').write_text(stderr)
    result=dict(exit=proc.returncode,timeout=expired,error=error,unverified_groups=remaining,
                passed=proc.returncode==0 and not expired and not error and not remaining)
    write(directory/'process-result.json',result);return result


def stage(proposal):
    plan=pilot.load();kind='proposals' if proposal else 'branches'
    if proposal:jobs=[dict(id=f'proposal-{i}',case=i,lane=c['lane']) for i,c in enumerate(plan['cases'])]
    else:_,f=pilot.branches();jobs=f['jobs']
    write(OUT/f'{kind}-started.json',dict(at=now(),pid=os.getpid(),plan_sha256=base.sha(OUT/'plan.json')))
    start=time.monotonic();stop=threading.Event();limit=plan['proposal_wall_seconds' if proposal else 'job_wall_seconds']
    cap=plan['proposal_batch_seconds' if proposal else 'batch_wall_seconds']
    def lane(index):
        for job in [j for j in jobs if j['lane']==index]:
            if stop.is_set():return
            if cap-(time.monotonic()-start)<limit:stop.set();return
            cmd=['proposal-worker','--case',str(job['case'])] if proposal else ['worker','--job',job['id']]
            d=OUT/job['id'];r=execute(cmd,d,limit,plan['lanes'][str(index)])
            if not r['passed']:stop.set()
            detail=json.loads((d/('proposal.json' if proposal else 'result.json')).read_text()) if r['passed'] else {}
            print(json.dumps({'job':job['id'],**r,**{k:detail[k] for k in ('supported','reason','chosen','alternative','actor_return','censored','new_plies') if k in detail}}),flush=True)
    with ThreadPoolExecutor(max_workers=len(plan['lanes'])) as pool:
        futures=[pool.submit(lane,int(i)) for i in plan['lanes']]
        for future in futures:future.result()
    attempts=[dict(job=j,**json.loads((OUT/j['id']/'process-result.json').read_text())) for j in jobs if (OUT/j['id']/'process-result.json').exists()]
    result=dict(at=now(),attempts=attempts,seconds=time.monotonic()-start,planned=len(jobs),
                complete=len(attempts)==len(jobs) and all(a['passed'] for a in attempts))
    write(OUT/f'{kind}-summary.json',result);print(json.dumps({'stage':kind,'complete':result['complete'],'attempts':len(attempts),'seconds':result['seconds']}),flush=True)
    if not result['complete']:raise SystemExit(1)


def freeze():
    plan=pilot.load();assert json.loads((OUT/'proposals-summary.json').read_text())['complete']
    jobs=[];pins={};supported=[];unsupported=[]
    for index,case in enumerate(plan['cases']):
        d=OUT/f'proposal-{index}';r=json.loads((d/'proposal.json').read_text())
        assert base.sha(d/'replay.json')==r['replay_sha256']
        for name in ('proposal.json','replay.json','process-result.json'):pins[str(d/name)]=base.sha(d/name)
        if not r['supported']:unsupported.append(dict(case=index,reason=r['reason']));continue
        supported.append(index)
        for repeat,seed in enumerate(plan['replicate_seeds']):
            for arm in ([0,1] if (index+repeat)%2==0 else [1,0]):
                jobs.append(dict(id=f'p{index}-a{arm}-r{repeat}',case=index,lane=case['lane'],
                                 action=r['chosen' if arm==0 else 'alternative'],arm=arm,repeat=repeat,
                                 seed=seed+100*index,common_charge=r['common_charge']))
    colours={plan['cases'][i]['side'] for i in supported};phases={plan['cases'][i]['phase'] for i in supported}
    coverage=dict(supported=supported,unsupported=unsupported,colours=sorted(colours),phases=sorted(phases),
                  advance=len(supported)>=plan['minimum_supported'] and len(colours)==2 and len(phases)>=plan['minimum_phases'])
    write(OUT/'proposal-coverage.json',coverage)
    assert coverage['advance'],'Coverage gate failed; do not substitute or launch branches'
    write(OUT/'branches.json',dict(at=now(),plan_sha256=base.sha(OUT/'plan.json'),pins=pins,jobs=jobs))
    print(json.dumps({'branches_sha256':base.sha(OUT/'branches.json'),'jobs':len(jobs),'coverage':coverage}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('select','proposal-worker','propose','freeze','worker','launch'))
    p.add_argument('--case',type=int);p.add_argument('--job');a=p.parse_args()
    if a.command=='proposal-worker':proposal_worker(a.case)
    elif a.command=='worker':pilot.worker(a.job)
    elif a.command=='propose':stage(True)
    elif a.command=='launch':stage(False)
    else:globals()[a.command]()
