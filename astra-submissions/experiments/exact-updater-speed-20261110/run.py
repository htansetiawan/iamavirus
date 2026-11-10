"""Whole-updater parity and timing for two exact v38 optimizations."""
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
from itertools import permutations
import json
import os
from pathlib import Path
import signal
from statistics import median, quantiles
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPERIMENTS = HERE.parent
ANALYSIS = ROOT/'astra-submissions/analysis'
OUT = ANALYSIS/HERE.name
PRIVATE = ROOT/'data/astra-spool'/HERE.name
BASE = EXPERIMENTS/'guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren/src'
OLD = EXPERIMENTS/'quiet-prior-sequential-20261110'
sys.path.insert(0, str(OLD))
from run import atomic, environment, stable

SOURCE = PRIVATE.parent/'compact-prior-sequential-20261110/plan.json'
NATIVE = PRIVATE.parent/'compact-prior-native-20261110'
ATTACK = PRIVATE.parent/'reverse-attacks-20261110'
ARMS = ('original','reverse','combined')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    with Path(path).open('x') as file:
        json.dump(value, file, indent=2, allow_nan=False)
        file.write('\n')


def build():
    a = read(ANALYSIS/'reverse-attacks-20261110/result.json')
    n = read(ANALYSIS/'compact-prior-native-20261110/result.json')
    assert all(a['conditions'].values()) and all(n['conditions'].values())
    assert sha(ATTACK/'board.c')==a['compiled']['source_sha256']
    assert sha(NATIVE/'movemodel.c')==n['compiled_hashes']['movemodel.c']
    text = (ATTACK/'board.c').read_text()
    marker = '\nint reference_attack('
    assert text.count(marker)==1
    (PRIVATE/'board.c').write_text(text[:text.index(marker)]+'\n')
    model = (NATIVE/'movemodel.c').read_text()
    suffix = '\n'+(EXPERIMENTS/'compact-prior-native-20261110/folded.c').read_text()
    assert model.endswith(suffix)
    (PRIVATE/'movemodel.c').write_text(model[:-len(suffix)])
    common = ['gcc','-O3','-std=c11','-ffp-contract=off','-pthread','-D_POSIX_C_SOURCE=199309L',
              '-I'+str(BASE),'-I'+str(OLD/'build'),str(OLD/'trace.c'),str(BASE/'belief.c')]
    commands = []
    for arm in ARMS:
        board = BASE/'board.c' if arm=='original' else PRIVATE/'board.c'
        model = PRIVATE/'movemodel.c' if arm=='combined' else BASE/'movemodel.c'
        command = common+[str(board),str(model),'-lm','-o',str(PRIVATE/arm)]
        subprocess.run(command, check=True, timeout=60)
        commands.append(command)
    return commands


def prepare():
    source = read(SOURCE)
    assert sha(SOURCE)==read(ANALYSIS/'compact-prior-sequential-20261110/plan-summary.json')['plan_sha256']
    groups = {team:[g for g in source['games'] if g['team']==team] for team in source['teams']}
    # Use the first and fifth frozen game per stratum for phase diversity.
    panel = [group[index] for index in (0,4) for group in groups.values()]
    assert len(panel)==16 and len({g['game'] for g in panel})==16
    for row in panel:
        assert sha(row['trace'])==source['dependencies'][row['trace']]
    PRIVATE.mkdir(exist_ok=False); OUT.mkdir(exist_ok=False)
    commands = build()
    pins = [Path(__file__), SOURCE, OLD/'run.py', OLD/'trace.c', OLD/'build/guard_predicates.h',
            *BASE.glob('*.[ch]'), BASE.parent/'data/history.bin', ATTACK/'board.c', NATIVE/'movemodel.c',
            ANALYSIS/'reverse-attacks-20261110/terminal-verification.json',
            ANALYSIS/'compact-prior-native-20261110/terminal-verification.json',
            *(PRIVATE/name for name in (*ARMS,'board.c','movemodel.c')),
            *(Path(g['trace']) for g in panel)]
    orders = list(permutations(ARMS))
    jobs = [dict(game=g['game'], arm=arm) for i,g in enumerate(panel) for arm in orders[i%len(orders)]]
    plan = dict(at=now(), panel=panel, jobs=jobs, seed=source['seeds'][0], cores=[0,1],
                child_timeout=180, total_timeout=1200, update_min=1000, cutoff_updates_min=100,
                total_cost_max=.85, game_median_max=.90, tail_ratio_max=1.10,
                dependencies={str(path):sha(path) for path in sorted(set(pins))}, commands=commands)
    save(PRIVATE/'plan.json', plan)
    summary = {key:plan[key] for key in ('at','seed','cores','child_timeout','total_timeout','update_min',
                                       'cutoff_updates_min','total_cost_max','game_median_max','tail_ratio_max')}
    summary.update(plan_sha256=sha(PRIVATE/'plan.json'), games=len(panel), jobs=len(jobs),
                   observer_v38_games=sum(g['own_observer'] for g in panel),
                   expected_updates=sum(g['rows'] for g in panel), pins=len(plan['dependencies']),
                   binaries={name:sha(PRIVATE/name) for name in ARMS},
                   scope='Fixed-cap native belief replay and read-only guard checks. First and fifth game per frozen 343 stratum. Original, reverse attack, and reverse attack with exact moved-piece visibility; learned weights disabled.')
    save(OUT/'plan-summary.json',summary)
    print(json.dumps(summary),flush=True)


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
                state['allocation'].append(dict(owner=owner, cores=cores, pid=os.getpid(), at=now(), purpose='whole updater exact timing'))
            else:
                state['allocation'] = [row for row in state['allocation'] if row['owner']!=owner]
            state['updated'] = now()
            atomic(path,state)
    change(True)
    try:
        yield
    finally:
        change(False)


def run_game(plan, job, game):
    stem = PRIVATE/(job['game']+'-'+job['arm'])
    stdout, stderr = stem.with_suffix('.stdout'), stem.with_suffix('.stderr')
    command = [str(PRIVATE/job['arm']),game['trace'],str(plan['seed'])]
    with stdout.open('x') as output, stderr.open('x') as error:
        proc = subprocess.Popen(command,stdout=output,stderr=error,env=environment('original'),start_new_session=True)
        try:
            code = proc.wait(timeout=plan['child_timeout'])
        except BaseException:
            if proc.poll() is None:
                os.killpg(proc.pid,signal.SIGKILL)
                proc.wait()
            raise
    assert code==0,(job,code)
    rows = [json.loads(line) for line in stdout.read_text().splitlines()]
    assert len(rows)==game['rows'] and all(not r['guard_bad_moves'] for r in rows)
    return rows, dict(**job, code=code, stdout_sha256=sha(stdout), stderr_sha256=sha(stderr))


def summarize(plan, games, cases):
    counts = Counter()
    elapsed = {arm: {'all':[], 'full':[], 'large':[], 'guard':[]} for arm in ARMS}
    by_game = {arm:[] for arm in ARMS[1:]}
    for name, game in games.items():
        peers = cases[name]
        assert sequentially_equal(peers)
        sums = {arm:sum(r['update_seconds'] for r in peers[arm]) for arm in ARMS}
        assert sums['original']>0
        for arm in ARMS[1:]:
            by_game[arm].append(sums[arm]/sums['original'])
        for arm,rows in peers.items():
            for row in rows:
                elapsed[arm]['all'].append(row['update_seconds'])
                if row['guard_applicable']:
                    elapsed[arm]['guard'].append(row['guard_seconds'])
                if row['decision'] and row['full_update']:
                    elapsed[arm]['full'].append(row['update_seconds'])
                if row['decision'] and row['parents']>10000:
                    elapsed[arm]['large'].append(row['update_seconds'])
        counts.update(updates=len(peers['original']), games=1, v38_observers=game['own_observer'])
    baseline = elapsed['original']
    counts.update(full=len(baseline['full']), large=len(baseline['large']), guard=len(baseline['guard']))
    metrics = {}
    for arm,times in elapsed.items():
        totals = {key:sum(values) for key,values in times.items()}
        ratios = {key:totals[key]/sum(baseline[key]) for key in totals}
        metrics[arm] = dict(seconds=totals, ratio=ratios, p95=quantiles(times['all'],n=20,method='inclusive')[18])
        if arm!='original':
            metrics[arm]['median_game_ratio']=median(by_game[arm])
            metrics[arm]['faster_games']=sum(x<1 for x in by_game[arm])
    combined = metrics['combined']
    conditions = dict(parity=True, coverage=counts['updates']>=plan['update_min'] and min(counts['full'],counts['large'])>=plan['cutoff_updates_min'],
                      aggregate_cost=combined['ratio']['all']<=plan['total_cost_max'],
                      median_game_cost=combined['median_game_ratio']<=plan['game_median_max'],
                      tail_cost=combined['p95']<=plan['tail_ratio_max']*metrics['original']['p95'])
    return dict(counts=dict(counts), metrics=metrics, conditions=conditions,
                decision='exact_speed_full_clock_design_allowed' if all(conditions.values()) else 'close_exact_speed_gate')


def sequentially_equal(peers):
    original = stable(peers['original'])
    return all(stable(peers[arm])==original for arm in ARMS[1:] if arm in peers)


def run():
    plan = read(PRIVATE/'plan.json')
    assert sha(PRIVATE/'plan.json')==read(OUT/'plan-summary.json')['plan_sha256']
    for path,digest in plan['dependencies'].items():
        assert sha(path)==digest,path
    os.sched_setaffinity(0,set(plan['cores']))
    def timeout(*_):
        raise TimeoutError('whole-updater gate expired')
    signal.signal(signal.SIGALRM,timeout)
    receipt = dict(status='running',started_at=now(),plan_sha256=sha(PRIVATE/'plan.json'))
    start = time.monotonic()
    with lease(plan['cores']):
        save(OUT/'execution.json',receipt)
        signal.alarm(plan['total_timeout'])
        try:
            games = {g['game']:g for g in plan['panel']}
            cases = {name:{} for name in games}
            calls = []
            for job in plan['jobs']:
                name,arm = job['game'],job['arm']
                cases[name][arm], row = run_game(plan,job,games[name])
                if 'original' in cases[name]:
                    assert sequentially_equal(cases[name]),(name,arm)
                calls.append(row)
                atomic(PRIVATE/'calls.json',calls)
                if len(cases[name])==len(ARMS):
                    print(json.dumps(dict(completed=len(calls),total=len(plan['jobs']))),flush=True)
            result = summarize(plan,games,cases)
            result.update(at=now(),plan_sha256=receipt['plan_sha256'],calls_sha256=sha(PRIVATE/'calls.json'))
            save(OUT/'result.json',result)
            receipt.update(status='complete',result_sha256=sha(OUT/'result.json'))
        except BaseException as error:
            receipt.update(status='failed',error=repr(error))
            raise
        finally:
            signal.alarm(0)
            atomic(OUT/'execution.json',dict(**receipt,ended_at=now(),seconds=time.monotonic()-start))


if __name__=='__main__':
    {'prepare':prepare,'run':run}[sys.argv[1]]()
