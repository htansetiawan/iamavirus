"""Compare preserved observation mass with the two frozen replay controls."""
from contextlib import contextmanager
import fcntl
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import numpy as np

from build import ANALYSIS, HERE, OUT, PREVIOUS, ROOT, STORE, now, read, save, sha
import run as legacy

PARENT = ANALYSIS/PREVIOUS.name


def prepare():
    build = read(OUT/'build.json')
    original = read(PREVIOUS/'plan.json')
    prior = read(PARENT/'terminal-verification.json')
    assert prior['calls']==384 and prior['failed_conditions']==['priority_nonregression']
    assert prior['plan_sha256']==sha(PREVIOUS/'plan.json')
    assert all(sha(path)==digest for path,digest in build['dependencies'].items())
    assert build['preflight_rows']==140 and build['preserved_signature_changes']>0
    timed = [game['game'] for game in original['games'][:16]]
    assert len(timed)==16 and len({game['team'] for game in original['games'][:8]})==8
    jobs = []
    for number,game in enumerate(original['games']):
        for i in (number%2,1-number%2):
            arms = ('baseline','preserved') if game['game'] in timed else ('preserved',)
            if (number+i)%2:
                arms = arms[::-1]
            jobs.extend(dict(game=game['game'],seed_index=i,arm=arm) for arm in arms)
    assert len(jobs)==160
    pins = dict(build['dependencies'])
    extra = [Path(__file__),OUT/'build.json',PREVIOUS/'calls.json',PARENT/'result.json',PARENT/'terminal-verification.json',
             *(Path(game['trace']) for game in original['games'])]
    pins.update({str(path):sha(path) for path in extra})
    plan = dict(at=now(), games=original['games'], teams=original['teams'], priority=original['priority'],seeds=original['seeds'],
                gate=original['gate'],seed=3531111,bootstrap_draws=4000,cores=[2,3],jobs=jobs,paired_timing_games=timed,
                dependencies=pins,seconds_cap=2400,child_seconds=120,
                scope='Causal development ablation on the same 343 observations and both sampler states. Previous original and unconstrained compact outputs are reused with hash checks. Paired live timing on the first two games of each stratum. No new fit or opened 349 replay.')
    save(STORE/'plan.json',plan)
    summary = {key:plan[key] for key in ('at','teams','priority','gate','cores','seeds','seconds_cap','child_seconds','scope')}
    summary.update(plan_sha256=sha(STORE/'plan.json'),dependencies=len(pins),paired_timing_games=len(timed),
                   games=len(plan['games']),new_calls=len(jobs),baseline_reuse=128,unconstrained_reuse=128)
    save(OUT/'plan-summary.json',summary)
    print(json.dumps(summary,indent=2),flush=True)


@contextmanager
def lease(cores):
    path = ROOT/'chatroom/cores.json'
    owner = 'astra-'+HERE.name
    def change(take):
        with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            state = read(path)
            if take:
                assert all(not set(cores)&set(row['cores']) for row in state['allocation'])
                state['allocation'].append(dict(owner=owner,cores=cores,pid=os.getpid(),at=now(),purpose='powered observation mass ablation'))
            else:
                state['allocation'] = [row for row in state['allocation'] if row['owner']!=owner]
            state['updated'] = now()
            legacy.atomic(path,state)
    change(True)
    try:
        yield
    finally:
        change(False)


def read_rows(path, game):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows)==game['rows'] and [r['ply'] for r in rows]==list(range(1,len(rows)+1))
    assert all(0<=r['truth_share']<=1 and (r['ever_capped'] or r['matches']) and not r['guard_bad_moves'] for r in rows)
    return rows


def run_case(plan, game, job):
    label = f"{job['game']}-s{job['seed_index']}-{job['arm']}"
    stdout,stderr = (STORE/(label+'.'+suffix) for suffix in ('stdout','stderr'))
    candidate = job['arm']=='preserved'
    binary = STORE/'trace' if candidate else PREVIOUS/'build/trace-original'
    env = legacy.environment('original')
    if candidate:
        env['ASTRA_CAPTURE_FIXED'] = '3'
    with stdout.open('x') as output,stderr.open('x') as error:
        cmd = [str(binary),game['trace'],str(plan['seeds'][job['seed_index']])]
        proc = subprocess.Popen(cmd,stdout=output,stderr=error,env=env,start_new_session=True)
        try:
            code = proc.wait(timeout=plan['child_seconds'])
        except BaseException:
            if proc.poll() is None:
                os.killpg(proc.pid,signal.SIGKILL)
                proc.wait()
            raise
    assert code==0,(job,code)
    return read_rows(stdout,game),dict(**job,code=code,stdout_sha256=sha(stdout),stderr_sha256=sha(stderr))


def collect_controls(plan):
    old_calls = {row['name']:row for row in read(PREVIOUS/'calls.json')}
    original, learned = {},{}
    for game in plan['games']:
        for i in range(len(plan['seeds'])):
            prefix = f"{game['game']}-s{i}"
            for arm, destination in (('original',original),('learned',learned)):
                name = prefix+'-'+arm
                path = PREVIOUS/(name+'.stdout')
                assert old_calls[name]['code']==0 and old_calls[name]['stdout_sha256']==sha(path)
                destination[prefix] = read_rows(path,game)
    return original,learned


def compare(plan, original, unconstrained, preserved, timed):
    cells = {}
    effects = {name:[] for name in plan['teams']}
    for game in plan['games']:
        for i in range(len(plan['seeds'])):
            label = f"{game['game']}-s{i}"
            cells[label+'-original'] = cells[label+'-zero'] = original[label]
            cells[label+'-learned'] = preserved[label]
            for unrestricted,new in zip(unconstrained[label],preserved[label]):
                assert unrestricted['ply']==new['ply'] and unrestricted['decision']==new['decision']
                if new['decision'] and new['ply']>=16:
                    effects[game['team']].append(math.log(max(new['truth_share'],1e-12))-math.log(max(unrestricted['truth_share'],1e-12)))
    result = legacy.aggregate(plan,cells)
    matched = {key:[] for key in ('original','preserved')}
    for label,rows in timed.items():
        matched['original'].extend(row['update_seconds'] for row in rows)
        matched['preserved'].extend(row['update_seconds'] for row in preserved[label])
    assert len(timed)==len(plan['paired_timing_games'])*len(plan['seeds'])
    m = {key:dict(total=math.fsum(rows),p95=float(np.quantile(rows,.95))) for key,rows in matched.items()}
    g = plan['gate']
    result['conditions']['total_cost'] = m['preserved']['total']<=g['total_ratio']*m['original']['total']
    result['conditions']['p95_cost'] = m['preserved']['p95']<=max(g['p95_floor'],g['p95_ratio']*m['original']['p95'])
    result['decision'] = ('fresh_confirmation_design_allowed' if all(result['conditions'].values())
                          else 'close_observed_mass_configuration')
    return dict(**result, gain_vs_unconstrained={team:math.fsum(values)/len(values) for team,values in effects.items()},
                paired_time=m,paired_timing_calls=len(timed),reused_control_trajectories=2*len(original))


def run():
    plan = read(STORE/'plan.json')
    digest = sha(STORE/'plan.json')
    assert digest==read(OUT/'plan-summary.json')['plan_sha256']
    assert all(sha(path)==expected for path,expected in plan['dependencies'].items())
    os.sched_setaffinity(0,set(plan['cores']))
    with lease(plan['cores']):
        status = dict(status='running',started_at=now(),completed=0,plan_sha256=digest)
        save(OUT/'execution.json',status)
        started = time.monotonic()
        def timeout(*_):
            raise TimeoutError('observed mass ablation expired')
        signal.signal(signal.SIGALRM,timeout)
        signal.alarm(plan['seconds_cap'])
        try:
            original, unrestricted = collect_controls(plan)
            preserved, timed, calls = {},{},[]
            games = {game['game']:game for game in plan['games']}
            for job in plan['jobs']:
                label = f"{job['game']}-s{job['seed_index']}"
                rows, receipt = run_case(plan,games[job['game']],job)
                if job['arm']=='baseline':
                    assert legacy.stable(rows)==legacy.stable(original[label]),label
                    timed[label] = rows
                else:
                    preserved[label] = rows
                calls.append(receipt)
                status['completed'] = len(calls)
                legacy.atomic(STORE/'calls.json',calls)
                legacy.atomic(OUT/'execution.json',status)
                if len(calls)%8==0:
                    print(json.dumps(dict(completed=len(calls),total=len(plan['jobs']))),flush=True)
            result = compare(plan,original,unrestricted,preserved,timed)
            result.update(at=now(),plan_sha256=digest,calls_sha256=sha(STORE/'calls.json'))
            save(OUT/'result.json',result)
            status.update(status='complete',result_sha256=sha(OUT/'result.json'))
            print(json.dumps({k:result[k] for k in ('decision','gain','conditions','gain_vs_unconstrained')}),flush=True)
        except BaseException as error:
            status.update(status='failed',error=repr(error))
            raise
        finally:
            signal.alarm(0)
            legacy.atomic(OUT/'execution.json',dict(**status,ended_at=now(),seconds=time.monotonic()-started))


if __name__=='__main__':
    {'prepare':prepare,'run':run}[sys.argv[1]]()
