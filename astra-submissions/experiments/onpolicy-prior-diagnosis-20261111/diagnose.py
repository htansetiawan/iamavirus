"""Compare both priors on all six earliest completed candidate game paths."""

from contextlib import contextmanager
from datetime import datetime, timezone
import ctypes
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPERIMENTS = HERE.parent
ANALYSIS = ROOT/'astra-submissions/analysis'
OUT = ANALYSIS/HERE.name
STORE = ROOT/'data/astra-spool'/HERE.name
PILOT = ANALYSIS/'compact-mass-playing-20261111'
LEGACY = EXPERIMENTS/'quiet-prior-sequential-20261110'
sys.path[:0] = [str(LEGACY),str(EXPERIMENTS/'deferred-prior-playing-20261111'),str(ROOT)]
from prepare import MoveList, NB, inspect_game, load_ref
from run import environment
from clock_audit import audit_game
from workload_checkpoint import decision_rows,update_counts
from learning import _native,ingest

ARMS = ('native','learned')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path,value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value,indent=2,allow_nan=False)+'\n')


def atomic(path,value):
    api = ROOT/'learning/api_client.py'
    from learning.api_client import atomic_write
    atomic_write(path,(json.dumps(value,indent=2,allow_nan=False)+'\n').encode())


def prepare():
    assert not OUT.exists() and not STORE.exists()
    pilot=read(PILOT/'plan.json')
    completed=[]
    for job in pilot['jobs']:
        path=Path(pilot['store'])/'jobs'/job['id']/'result.json'
        if path.exists():
            result=read(path)
            assert result['job']==job and result['exit_code']==0 and not result['faults']
            completed.append((result['ended_at'],job,result,path))
    completed.sort(key=lambda item:(item[0],item[1]['id']))
    assert len(completed)>=6
    selected=completed[:6]
    validator=EXPERIMENTS/'compact-mass-playing-20261111/build/native-validator.so'
    assert sha(validator)==pilot['dependencies'][str(validator)]
    _native.ensure_built=lambda verbose=True:validator
    frontend=ctypes.CDLL(str(NB/'adapter.so'))
    frontend.fow_init()
    frontend.view_moves.argtypes=[ctypes.c_char_p,ctypes.c_int,ctypes.c_uint64,ctypes.POINTER(MoveList)]
    ref=load_ref()
    OUT.mkdir()
    STORE.mkdir()
    games=[]
    for i,(_,job,result,result_path) in enumerate(selected):
        path=result_path.parent/'replay.json'
        assert sha(path)==result['replay_sha256']
        replay=read(path)
        states,errors=ingest.validate_replay(replay)
        assert not errors and len(states)==result['validated_frames']
        assert states[-1].outcome()==(result['result'],result['reason'])
        audit_game(replay,job)
        observer=int(job['side']=='black')
        counts=update_counts(replay,job['side'])
        assert counts['clock_thinnings']==counts['rebuilds']==0
        lines,bad,frames=inspect_game(ref,frontend,dict(replay,id=f'mass{i}'),observer)
        assert not bad
        trace=STORE/(job['id']+'.trace')
        trace.write_text('\n'.join(lines)+'\n')
        decisions=decision_rows(replay)[observer]
        live={str(row['ply']-1):dict(worlds=row['worlds'],capped=row['capped']) for row in decisions}
        games.append(dict(game=job['id'],side=job['side'],observer=observer,score=result['score'],
                          trace=str(trace),replay=str(path),receipt=str(result_path),frames=frames,
                          rows=len(lines)-1,live_counts=live))
    binaries=dict(native=str(ROOT/'data/astra-spool/deferred-prior-playing-20261111/rebuild-replay/v38'),
                  learned=str(ROOT/'data/astra-spool/compact-mass-playing-parity-20261111/gcc'))
    base_audit=read(ANALYSIS/'deferred-prior-playing-20261111/first-rebuild-replay.json')
    assert sha(binaries['native'])==base_audit['arm_sha256']['v38']
    cpp=read(PILOT/'trace-parity.json')
    assert sha(binaries['learned'])==cpp['dependencies'][binaries['learned']]
    files=[Path(__file__),PILOT/'plan.json',PILOT/'build.json',PILOT/'trace-parity.json',validator,NB/'adapter.so',
           LEGACY/'prepare.py',LEGACY/'run.py',LEGACY/'trace.c',ROOT.parent/'fow-starter/referee.py',
           EXPERIMENTS/'deferred-prior-playing-20261111/clock_audit.py',
           EXPERIMENTS/'deferred-prior-playing-20261111/workload_checkpoint.py',*binaries.values()]
    files.extend(Path(game[key]) for game in games for key in ('trace','replay','receipt'))
    jobs=[dict(game=game['game'],arm=arm) for i,game in enumerate(games)
          for arm in (ARMS if i%2==0 else ARMS[::-1])]
    plan=dict(at=now(),games=games,jobs=jobs,binaries=binaries,seed=0x6d6973742d63,
              cores=[6],child_seconds=180,wall_seconds=1500,
              dependencies={str(path):sha(path) for path in files},
              scope='Descriptive causal weighting comparison on the first six completed 357 paths, all results included. Recorded own moves and views only drive each updater. Both use native default sampler state and two updater threads. No wall thinning, search, rebuilding, fit, score-based selection or gate change. Compare reconstructed learned population sizes with live logs; those logs do not include weight fingerprints.')
    save(STORE/'plan.json',plan)
    save(OUT/'plan-summary.json',dict(at=now(),games=len(games),calls=len(jobs),frames=sum(g['frames'] for g in games),
         score=sum(g['score'] for g in games),plan_sha256=sha(STORE/'plan.json'),
         dependencies=len(plan['dependencies']),cores=plan['cores'],scope=plan['scope']))
    print((OUT/'plan-summary.json').read_text(),flush=True)


@contextmanager
def lease(cores):
    owner='astra-'+HERE.name
    path=ROOT/'chatroom/cores.json'
    def change(take):
        with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            state=read(path)
            if take:
                assert all(not set(cores)&set(row['cores']) for row in state['allocation'])
                state['allocation'].append(dict(owner=owner,cores=cores,pid=os.getpid(),at=now(),purpose='six-path fixed prior diagnosis'))
            else:
                state['allocation']=[row for row in state['allocation'] if row['owner']!=owner]
            atomic(path,dict(state,updated=now()))
    change(True)
    try:
        yield
    finally:
        change(False)


def summarize(plan,cells):
    records=[]
    for game in plan['games']:
        old,new=(cells[game['game'],arm] for arm in ARMS)
        assert len(old)==len(new)==game['rows']
        for a,b in zip(old,new):
            assert all(a[key]==b[key] for key in ('ply','decision','guard_applicable','king_label','queen_label'))
        primary=[(a,b) for a,b in zip(old,new) if a['decision'] and a['ply']>=16]
        decision=[row for row in new if row['decision']]
        live=game['live_counts']
        mismatches=[dict(ply=row['ply'],live=live[str(row['ply'])],reconstructed=dict(worlds=row['worlds'],capped=row['ever_capped']))
                    for row in decision if row['worlds']!=live[str(row['ply'])]['worlds']
                    or row['ever_capped']!=live[str(row['ply'])]['capped']]
        records.append(dict(game=game['game'],score=game['score'],decisions=len(primary),
            mean_log_truth_gain=math.fsum(math.log(max(b['truth_share'],1e-12))-math.log(max(a['truth_share'],1e-12)) for a,b in primary)/len(primary),
            support={arm:sum(row['matches']>0 for row in cells[game['game'],arm] if row['decision'] and row['ply']>=16) for arm in ARMS},
            learned_live_counts_compared=len(decision),learned_live_count_mismatches=mismatches,
            final_decision={arm:next(row for row in reversed(cells[game['game'],arm]) if row['decision']) for arm in ARMS}))
    return records


def run():
    plan=read(STORE/'plan.json')
    assert not (OUT/'execution.json').exists()
    assert all(sha(path)==digest for path,digest in plan['dependencies'].items())
    os.sched_setaffinity(0,set(plan['cores']))
    state=dict(at=now(),status='running',completed=0,plan_sha256=sha(STORE/'plan.json'))
    save(OUT/'execution.json',state)
    games={game['game']:game for game in plan['games']}
    def timeout(*_):
        raise TimeoutError('fixed prior path diagnostic wall limit')
    signal.signal(signal.SIGALRM,timeout)
    signal.alarm(plan['wall_seconds'])
    started=time.monotonic()
    try:
        with lease(plan['cores']):
            cells,calls={},[]
            for job in plan['jobs']:
                game=games[job['game']]
                tag=job['game']+'-'+job['arm']
                env=environment('original')
                env['ASTRA_CAPTURE_FIXED']='3' if job['arm']=='learned' else '0'
                stdout,stderr=(STORE/(tag+'.'+name) for name in ('stdout','stderr'))
                with stdout.open('x') as output,stderr.open('x') as error:
                    completed=subprocess.run([plan['binaries'][job['arm']],game['trace'],str(plan['seed'])],
                                              env=env,stdout=output,stderr=error,timeout=plan['child_seconds'],check=True)
                rows=[json.loads(line) for line in stdout.read_text().splitlines()]
                assert len(rows)==game['rows'] and all(not row['guard_bad_moves'] for row in rows)
                cells[job['game'],job['arm']]=rows
                calls.append(dict(**job,code=completed.returncode,stdout_sha256=sha(stdout),stderr_sha256=sha(stderr)))
                atomic(STORE/'calls.json',calls)
                state['completed']=len(calls)
                atomic(OUT/'execution.json',state)
                print(json.dumps(dict(completed=len(calls),total=len(plan['jobs']))),flush=True)
            result=dict(at=now(),plan_sha256=state['plan_sha256'],calls_sha256=sha(STORE/'calls.json'),
                        records=summarize(plan,cells),scope=plan['scope'])
            save(OUT/'result.json',result)
            state.update(status='complete',result_sha256=sha(OUT/'result.json'))
            print(json.dumps(result),flush=True)
    except BaseException as exc:
        state.update(status='failed',error=repr(exc))
        raise
    finally:
        signal.alarm(0)
        atomic(OUT/'execution.json',dict(state,ended_at=now(),seconds=time.monotonic()-started))


if __name__=='__main__':
    {'prepare':prepare,'run':run}[sys.argv[1]]()
