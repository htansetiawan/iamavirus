"""Two observable proposals, followed by eight frozen action continuations."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

from branch import HERE, ROOT, PRIOR, BASE, base, commands, run, inspect
from preflight_branch import clean_env
from local_turn_control import cleanup_registry

OUT=ROOT/'astra-submissions/analysis/action-continuation-20261102'
PREVIOUS=ROOT/'astra-submissions/analysis/budget-continuation-20261102'


def now():return datetime.now(timezone.utc).isoformat()


def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def load():
    plan=json.loads((OUT/'plan.json').read_text())
    for path,digest in plan['deps'].items():assert base.sha(path)==digest,path
    for c in plan['cases']:assert base.sha(ROOT/c['prefix'])==c['prefix_sha256']
    return plan


def prepare():
    assert json.loads((OUT/'preflight.json').read_text())['passed']
    assert json.loads((OUT/'native-branch-preflight.json').read_text())['passed']
    previous=json.loads((PREVIOUS/'plan.json').read_text())
    cases=[dict(c,proposal_seed=2431102+2*i) for i,c in enumerate(previous['cases'][:2])]
    assert len(cases)==2 and all(c['kind']=='hash_selected' for c in cases)
    deps=[*HERE.glob('*.py'),HERE/'README.md',HERE/'build/proposer',OUT/'build.json',OUT/'preflight.json',OUT/'native-branch-preflight.json',
          PRIOR/'build/mist',PRIOR/'continuation.py',BASE/'bin/stockfish',BASE/'data/history.bin',
          base.REF,ROOT/'astra-submissions/tools/local_turn_control.py',ROOT/'learning/ingest.py',
          PREVIOUS/'plan.json',PREVIOUS/'review.json']
    plan=dict(at=now(),cases=cases,deps={str(p):base.sha(p) for p in deps},
              proposal_wall_seconds=180,job_wall_seconds=1000,batch_wall_seconds=5000,
              max_new_plies=64,lanes={'0':'0,1','1':'2,3'},replicate_seeds=[2432200,2432202],
              choice='Actual proposal action plus highest root-Q alternative among its view-legal CFR rows; tie by policy probability then original index. No truth or outcome chooses actions.',
              clock='Each action is charged the identical actual elapsed time measured on the one proposal run for that prefix.',
              scope='Two reused development groups, policy-conditioned action targets; not a playing-strength trial or training corpus.',
              stop='Technical failure or unsupported second proposal stops; no retries or substitute cases.',no_gpu=True)
    write(OUT/'plan.json',plan)
    print(json.dumps({'plan_sha256':base.sha(OUT/'plan.json'),'cases':[c['game'] for c in cases]}))


def proposal_worker(index):
    plan=load();case=plan['cases'][index];p=json.loads((ROOT/case['prefix']).read_text())
    directory=OUT/f'proposal-{index}';cmds=[]
    for side in (0,1):
        a=base.actor_prefix(p,side)
        cmds.append(['/usr/bin/env',f'FOW_SEED={case["proposal_seed"]+side}',
                     'MIST_FORCE_MOVES='+','.join(a['moves']),'ASTRA_PREFIX_CONTINUE=1',
                     'ASTRA_PREFIX_CLOCKS='+','.join(map(str,a['post_clocks'])),
                     'ASTRA_PROPOSAL=1',f'MIST_STOCKFISH={BASE/"bin/stockfish"}',
                     f'MIST_HISTORY_TABLE={BASE/"data/history.bin"}','MIST_MAX_SECONDS=10',str(HERE/'build/proposer')])
    game=base.run(p,cmds,directory,1)
    write(directory/'replay.json',game)
    actor=p['branch_ply']%2;text=game['privateDiagnostics'][('white','black')[actor]]
    rows=[dict(move=m,probability=float(prob),value=float(v),index=i)
          for i,(m,prob,v) in enumerate(re.findall(r'astra-proposal: (\w+) (\S+) (\S+)',text))]
    assert rows and len({r['move'] for r in rows})==len(rows)
    assert all(math.isfinite(r['value']) and math.isfinite(r['probability']) and r['probability']>=0 for r in rows)
    assert abs(sum(r['probability'] for r in rows)-1)<1e-9
    policy_value=float(re.search(r'astra-proposal-value: (\S+)',text)[1])
    assert abs(sum(r['probability']*r['value'] for r in rows)-policy_value)<1e-9
    legal=re.search(r'astra-view-legal:(.*)',text)[1].split()
    chosen=game['frames'][-1]['move']
    assert chosen in legal and chosen in {r['move'] for r in rows}
    alternatives=[r for r in rows if r['move'] in legal and r['move']!=chosen]
    assert alternatives,'No second supported action; do not replace prefix'
    alt=min(alternatives,key=lambda r:(-r['value'],-r['probability'],r['index']))
    charge=game['continuation']['steps'][-1]['actual_elapsed']
    checked=inspect(game,p,chosen,charge)
    write(directory/'proposal.json',dict(case=index,chosen=chosen,alternative=alt['move'],
          common_charge=charge,rows=rows,view_legal=legal,policy_value=policy_value,
          replay_sha256=base.sha(directory/'replay.json'),checked=checked))


def execute(command,directory,timeout,cores):
    directory.mkdir(exist_ok=False)
    write(directory/'started.json',dict(at=now(),command=command,cores=cores))
    proc=subprocess.Popen(['taskset','-c',cores,sys.executable,str(Path(__file__)),*command],
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                          env=clean_env(),start_new_session=True)
    write(directory/'handle.json',dict(at=now(),pid=proc.pid))
    expired=False
    try:stdout,stderr=proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:expired=True;proc.kill();stdout,stderr=proc.communicate()
    remaining=cleanup_registry(directory/'processes.json')
    (directory/'stdout.txt').write_text(stdout);(directory/'stderr.txt').write_text(stderr)
    result=dict(exit=proc.returncode,timeout=expired,unverified_groups=remaining,
                passed=proc.returncode==0 and not expired and not remaining)
    write(directory/'process-result.json',result)
    return result


def propose():
    plan=load();write(OUT/'proposals-started.json',dict(at=now(),pid=os.getpid()))
    for i in range(len(plan['cases'])):
        r=execute(['proposal-worker','--case',str(i)],OUT/f'proposal-{i}',plan['proposal_wall_seconds'],'0,1')
        print(json.dumps({'proposal':i,**r}),flush=True)
        if not r['passed']:raise SystemExit(1)


def freeze():
    plan=load();jobs=[];pins={}
    for index,case in enumerate(plan['cases']):
        directory=OUT/f'proposal-{index}'
        assert json.loads((directory/'process-result.json').read_text())['passed']
        proposal=json.loads((directory/'proposal.json').read_text())
        assert base.sha(directory/'replay.json')==proposal['replay_sha256']
        for name in ('proposal.json','replay.json','process-result.json'):pins[str(directory/name)]=base.sha(directory/name)
        for repeat,seed in enumerate(plan['replicate_seeds']):
            for a in ([0,1] if (repeat+index)%2==0 else [1,0]):
                jobs.append(dict(id=f'p{index}-a{a}-r{repeat}',case=index,lane=index,
                                 action=proposal['chosen' if a==0 else 'alternative'],arm=a,
                                 repeat=repeat,seed=seed+100*index,common_charge=proposal['common_charge']))
    frozen=dict(at=now(),plan_sha256=base.sha(OUT/'plan.json'),pins=pins,jobs=jobs)
    write(OUT/'branches.json',frozen)
    print(json.dumps({'branches_sha256':base.sha(OUT/'branches.json'),'jobs':jobs}))


def branches():
    plan=load();f=json.loads((OUT/'branches.json').read_text());assert f['plan_sha256']==base.sha(OUT/'plan.json')
    for p,h in f['pins'].items():assert base.sha(p)==h,p
    return plan,f


def worker(job_id):
    plan,f=branches();job=next(j for j in f['jobs'] if j['id']==job_id);case=plan['cases'][job['case']]
    p=json.loads((ROOT/case['prefix']).read_text());d=OUT/job['id']
    game=run(p,commands(p,job['action'],job['common_charge'],job['seed']),job['action'],job['common_charge'],d,plan['max_new_plies'])
    write(d/'replay.json',game)
    result=inspect(game,p,job['action'],job['common_charge'])
    for side,key in enumerate(('white','black')):
        a=base.actor_prefix(p,side);clocks=a['post_clocks'][:]
        if side==p['branch_ply']%2:
            clocks.append(p['frames'][-1]['clocks'][side]-job['common_charge']+p['timeControl']['incrementSeconds'])
        text=game['privateDiagnostics'][key]
        restored=[float(v) for v in re.findall(r'astra-prefix: decision=\d+ clock=([\d.]+)',text)]
        assert len(restored)==len(clocks) and all(abs(a-b)<2e-6 for a,b in zip(restored,clocks))
        expected=sum(s['side']==side and s['ply']>p['branch_ply'] for s in game['continuation']['steps'])
        assert sum(x.startswith('mist: n=') for x in text.splitlines())==expected
    winner=result['result'];actor=p['branch_ply']%2
    result.update(job=job,source=case['game'],replay_sha256=base.sha(d/'replay.json'),
                  actor_return=None if winner is None else (0 if winner=='1/2-1/2' else (1 if (winner=='1-0')==(actor==0) else -1)))
    write(d/'result.json',result)


def launch():
    plan,f=branches();write(OUT/'started.json',dict(at=now(),pid=os.getpid(),branches_sha256=base.sha(OUT/'branches.json')))
    start=time.monotonic();stop=threading.Event()
    def lane(index):
        for job in [j for j in f['jobs'] if j['lane']==index]:
            if stop.is_set():return
            if plan['batch_wall_seconds']-(time.monotonic()-start)<plan['job_wall_seconds']:stop.set();return
            d=OUT/job['id'];r=execute(['worker','--job',job['id']],d,plan['job_wall_seconds'],plan['lanes'][str(index)])
            if not r['passed']:stop.set()
            print(json.dumps({'job':job['id'],**r,**(json.loads((d/'result.json').read_text()) if r['passed'] else {})}),flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(lane,i) for i in (0,1)]
        for future in futures:future.result()
    attempts=[dict(job=j,**json.loads((OUT/j['id']/'process-result.json').read_text())) for j in f['jobs'] if (OUT/j['id']/'process-result.json').exists()]
    result=dict(at=now(),attempts=attempts,seconds=time.monotonic()-start,
                complete=len(attempts)==8 and all(a['passed'] for a in attempts))
    write(OUT/'summary.json',result);print(json.dumps(result),flush=True)
    if not result['complete']:raise SystemExit(1)


def review():
    plan,f=branches();summary=json.loads((OUT/'summary.json').read_text());assert summary['complete']
    pairs={};frames=0;rows=[]
    for j in f['jobs']:
        d=OUT/j['id'];r=json.loads((d/'result.json').read_text());game=json.loads((d/'replay.json').read_text())
        assert base.sha(d/'replay.json')==r['replay_sha256'] and r['job']==j
        p=json.loads((ROOT/plan['cases'][j['case']]['prefix']).read_text())
        actual=inspect(game,p,j['action'],j['common_charge'])
        assert all(r[k]==v for k,v in actual.items());frames+=actual['frames'];rows.append(r)
        pairs.setdefault((j['case'],j['repeat']),{})[j['arm']]=r
    comparisons=[]
    for (case,repeat),arms in sorted(pairs.items()):
        assert arms[0]['root_post_clocks']==arms[1]['root_post_clocks']
        a,b=arms[0]['actor_return'],arms[1]['actor_return']
        comparisons.append(dict(case=case,repeat=repeat,baseline_return=a,alternative_return=b,
                                advantage=None if a is None or b is None else b-a))
    write(OUT/'review.json',dict(at=now(),passed=True,frames=frames,rows=rows,comparisons=comparisons,
          summary_sha256=base.sha(OUT/'summary.json'),source_sha256=base.sha(__file__),
          scope='Two correlated development groups, four paired seeds. No confidence or strength claim.'))
    print(json.dumps({'passed':True,'frames':frames,'comparisons':comparisons}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('prepare','proposal-worker','propose','freeze','worker','launch','review'))
    parser.add_argument('--case',type=int);parser.add_argument('--job');a=parser.parse_args()
    if a.command=='proposal-worker':proposal_worker(a.case)
    elif a.command=='worker':worker(a.job)
    else:globals()[a.command]()
