"""Confirm the unchanged powered-mass prior on the sealed later replay window."""

from contextlib import contextmanager
import ctypes
import fcntl
import hashlib
import json
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
SPOOL = ROOT/'data/astra-spool'
STORE = SPOOL/HERE.name
PARENT_NAME = 'compact-observation-mass-20261111'
SOURCE_NAME = 'later-replay-window-20261111'
SOURCE = SPOOL/SOURCE_NAME

sys.path.insert(0, str(EXPERIMENTS/PARENT_NAME))
import replay_ablation as development
from build import now, read, save, sha
from prepare import NB, REF, MoveList, inspect_game, load_ref

COLORS = ('white', 'black')
OWN = 'a2c35173659545c99752376a70418438'
ARMS = ('original', 'learned')


def choose(candidates):
    """Assign a trajectory to at most one stratum, filling scarce slots first."""
    assigned = {}

    def add(slot, visited):
        for item in candidates[slot[:2]]:
            game = item['game']
            if game in visited:
                continue
            visited.add(game)
            if game not in assigned or add(assigned[game], visited):
                assigned[game] = slot
                return True
        return False

    for team, color in sorted(candidates, key=lambda key: (len(candidates[key]), key)):
        for slot in range(4):
            add((team, color, slot), set())
    groups = {key: [] for key in candidates}
    for game, slot in assigned.items():
        groups[slot[:2]].append(next(row for row in candidates[slot[:2]] if row['game'] == game))
    return groups


def prepare():
    assert not OUT.exists() and not STORE.exists()
    parent = ANALYSIS/PARENT_NAME
    parent_plan = read(development.STORE/'plan.json')
    parent_audit = read(parent/'terminal-verification.json')
    assert parent_audit['plan_sha256'] == sha(development.STORE/'plan.json')
    assert parent_audit['result_sha256'] == sha(parent/'result.json')
    assert parent_audit['decision'] == 'fresh_confirmation_design_allowed'
    assert all(sha(path) == digest for path, digest in parent_plan['dependencies'].items())

    source_summary = ANALYSIS/SOURCE_NAME/'result.json'
    source_audit = ANALYSIS/SOURCE_NAME/'terminal-verification.json'
    sealed = SOURCE/'cohort.json'
    source_receipt = read(source_audit)
    assert source_receipt['result_sha256'] == sha(source_summary)
    assert sha(sealed) == read(source_summary)['cohort_sha256'] == source_receipt['cohort_sha256']
    cohort = read(sealed)
    assert len(cohort['games']) == 99
    historical = {row['sequence_sha256'] for row in parent_plan['games']}
    assert historical.isdisjoint(row['sequence_sha256'] for row in cohort['games'])

    adapter = NB/'adapter.so'
    assert sha(adapter) == read(development.PREVIOUS/'plan.json')['dependencies'][str(adapter)]
    frontend = ctypes.CDLL(str(adapter))
    frontend.fow_init()
    frontend.view_moves.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_uint64, ctypes.POINTER(MoveList)]
    referee = load_ref()
    teams = parent_plan['teams']
    candidates = {(team, color): [] for team in teams for color in range(2)}
    excluded = []
    for entry in cohort['games']:
        game = entry['game']
        listing = entry['listing']
        names = [listing[color] for color in COLORS]
        if not any(name in teams for name in names) or names[0] == names[1]:
            continue
        raw = SOURCE/'games'/game/'replay.json'
        assert sha(raw) == entry['replay_sha256']
        replay = read(raw)
        assert all(replay[key] == listing[key] for key in ('id', 'createdAt', *COLORS))
        assert len(replay['frames']) == entry['frames'] and replay['rulesVersion'] == 'fow-v1'
        moves = ' '.join(frame['move'] for frame in replay['frames'][1:])
        assert hashlib.sha256(moves.encode()).hexdigest() == entry['sequence_sha256']
        for color in range(2):
            team = names[color^1]
            if team not in teams:
                continue
            lines, unsupported, frames = inspect_game(referee, frontend, replay, color)
            if unsupported:
                excluded.append(dict(game=game, team=team, observer=color, actions=unsupported))
                continue
            own = listing[COLORS[color]+'PlayerId'] == OWN
            candidates[(team, color)].append(dict(game=game, team=team, observer=color,
                own_observer=own, frames=frames, rows=len(lines)-1, lines=lines, raw=str(raw),
                sequence_sha256=entry['sequence_sha256'], created_at=listing['createdAt']))
    for items in candidates.values():
        items.sort(key=lambda row: (not row['own_observer'],
            hashlib.sha256(('mass-confirm355:'+row['sequence_sha256']).encode()).digest()))
    groups = choose(candidates)
    counts = {team: sum(len(groups[(team, color)]) for color in range(2)) for team in teams}
    assert sum(counts.values()) >= 63 and min(counts.values()) >= 7 and min(map(len, groups.values())) >= 3
    games = []
    for i in range(4):
        for key in groups:
            if i < len(groups[key]):
                games.append(groups[key][i])
    assert len({row['sequence_sha256'] for row in games}) == len(games)
    STORE.mkdir()
    OUT.mkdir()
    for game in games:
        trace = STORE/(game['game']+'.trace')
        trace.write_text('\n'.join(game.pop('lines'))+'\n')
        game['trace'] = str(trace)
    seeds = [3551111, 3551111 ^ 0x9e3779b97f4a7c15]
    assert set(seeds).isdisjoint(parent_plan['seeds'])
    jobs = []
    for i, game in enumerate(games):
        for seed in (i%2, 1-i%2):
            order = ARMS if (i//2+seed)%2 == 0 else ARMS[::-1]
            jobs.extend(dict(game=game['game'], seed_index=seed, arm=arm) for arm in order)
    binaries = dict(original=str(development.PREVIOUS/'build/trace-original'),
                    learned=str(development.STORE/'trace'))
    expected = read(parent/'build.json')
    assert sha(binaries['learned']) == expected['binary_sha256']
    assert sha(binaries['original']) == parent_plan['dependencies'][binaries['original']]
    dependencies = dict(parent_plan['dependencies'])
    extra = [Path(__file__), REF, adapter, sealed, source_summary, source_audit,
             development.STORE/'plan.json', parent/'result.json', parent/'terminal-verification.json',
             *binaries.values(), *(row[key] for row in games for key in ('raw', 'trace'))]
    dependencies.update({str(path): sha(path) for path in extra})
    scope = ('Fixed prospective replay confirmation on the sealed 349 games. Selection uses metadata and '
             'rules/frontend eligibility only. All paired timing uses the same invocation order balance '
             'and original baseline. Two fresh fixed RNG states. No search, clock thinning or recovery.')
    plan = dict(at=now(), games=games, teams=teams, priority=parent_plan['priority'], seeds=seeds,
                gate=parent_plan['gate'], seed=3551112, bootstrap_draws=4000, jobs=jobs,
                dependencies=dependencies, binaries=binaries, cores=[2,3], scope=scope,
                wall_seconds=3600, child_seconds=120, byte_cap=128*1024**2)
    save(STORE/'plan.json',plan)
    save(OUT/'plan-summary.json',dict(at=now(), plan_sha256=sha(STORE/'plan.json'),
         source_sha256=sha(sealed), source_games=len(cohort['games']), games=len(games),
         own_observer=sum(row['own_observer'] for row in games), frames=sum(row['frames'] for row in games),
         by_team=counts, by_team_color={team:{COLORS[c]:len(groups[(team,c)]) for c in range(2)} for team in teams},
         frontend_exclusions=excluded, jobs=len(jobs), dependencies=len(dependencies),
         binary_sha256={arm:sha(path) for arm,path in binaries.items()},
         **{k:plan[k] for k in ('gate','cores','seeds','scope','wall_seconds','child_seconds','byte_cap')}))
    print((OUT/'plan-summary.json').read_text(),flush=True)


def scored(plan, game, job):
    arm = job['arm']
    tag = f"{job['game']}-s{job['seed_index']}-{arm}"
    stdout, stderr = (STORE/(tag+'.'+suffix) for suffix in ('stdout','stderr'))
    env = development.legacy.environment('original')
    if arm == 'learned':
        env['ASTRA_CAPTURE_FIXED'] = '3'
    command = [plan['binaries'][arm], game['trace'], str(plan['seeds'][job['seed_index']])]
    with stdout.open('x') as output, stderr.open('x') as error:
        proc = subprocess.Popen(command,stdout=output,stderr=error,env=env,start_new_session=True)
        try:
            code = proc.wait(timeout=plan['child_seconds'])
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid,signal.SIGKILL)
                proc.wait()
    assert code == 0, (job,code)
    rows = development.read_rows(stdout,game)
    return tag, rows, dict(**job, code=code, stdout_sha256=sha(stdout), stderr_sha256=sha(stderr))


@contextmanager
def lease(cores):
    path = ROOT/'chatroom/cores.json'
    owner = 'astra-'+HERE.name

    def update(take):
        with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            state = read(path)
            if take:
                assert all(not set(cores)&set(row['cores']) for row in state['allocation'])
                state['allocation'].append(dict(owner=owner,cores=cores,pid=os.getpid(),
                                                 at=now(),purpose='fresh compact prior confirmation'))
            else:
                state['allocation'] = [row for row in state['allocation'] if row['owner'] != owner]
            development.legacy.atomic(path,dict(state,updated=now()))
    update(True)
    try:
        yield
    finally:
        update(False)


def run():
    plan = read(STORE/'plan.json')
    digest = sha(STORE/'plan.json')
    assert digest == read(OUT/'plan-summary.json')['plan_sha256']
    assert all(sha(path) == value for path,value in plan['dependencies'].items())
    assert not (OUT/'execution.json').exists()
    os.sched_setaffinity(0,set(plan['cores']))
    games = {game['game']:game for game in plan['games']}
    with lease(plan['cores']):
        status = dict(status='running',started_at=now(),completed=0,plan_sha256=digest)
        save(OUT/'execution.json',status)
        started = time.monotonic()
        def timeout(*_):
            raise TimeoutError('fresh posterior confirmation exceeded its wall limit')
        signal.signal(signal.SIGALRM,timeout)
        signal.alarm(plan['wall_seconds'])
        try:
            cells, calls = {}, []
            for job in plan['jobs']:
                tag, rows, receipt = scored(plan,games[job['game']],job)
                cells[tag] = rows
                if job['arm'] == 'original':
                    cells[tag.removesuffix('original')+'zero'] = rows
                calls.append(receipt)
                status['completed'] = len(calls)
                development.legacy.atomic(STORE/'calls.json',calls)
                development.legacy.atomic(OUT/'execution.json',status)
                assert sum(path.stat().st_size for path in STORE.iterdir()) <= plan['byte_cap']
                if len(calls)%8 == 0:
                    print(json.dumps(dict(completed=len(calls),total=len(plan['jobs']))),flush=True)
            result = development.legacy.aggregate(plan,cells)
            result.update(at=now(),plan_sha256=digest,calls_sha256=sha(STORE/'calls.json'),
                arms=dict(original='v38 native prior',learned='fixed compact, powered observation mass preserved',
                          zero='internal alias for the original arm'),
                decision='full_clock_integration_design_allowed' if all(result['conditions'].values())
                         else 'close_fixed_mass_prior_confirmation')
            save(OUT/'result.json',result)
            status.update(status='complete',result_sha256=sha(OUT/'result.json'))
            print(json.dumps({key:result[key] for key in ('decision','gain','conditions')}),flush=True)
        except BaseException as exc:
            status.update(status='failed',error=repr(exc))
            raise
        finally:
            signal.alarm(0)
            development.legacy.atomic(OUT/'execution.json',dict(**status,ended_at=now(),seconds=time.monotonic()-started))


if __name__ == '__main__':
    {'prepare':prepare,'run':run}[sys.argv[1]]()
