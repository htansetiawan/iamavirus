#!/usr/bin/env python3
"""Frozen whole-trajectory belief gate; no search, training, or retry."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

os.environ['OPENBLAS_NUM_THREADS'] = '1'
import numpy as np

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/full-prior-posterior-20261102'
BUILD = HERE / 'build'
COST = HERE.parent / 'full-prior-cost-20261102/build-r2'
COST_OUT = ROOT / 'astra-submissions/analysis/full-prior-cost-20261102/r2'
BASE = HERE.parent / 'queen-terminal-backport-20261102/build-r2/base'
REF = ROOT.parent / 'fow-starter/referee.py'
FRESH = ROOT / 'astra-submissions/analysis/fresh-taxonomy-20261101/cases.json'
PRIOR = ROOT / 'astra-submissions/analysis/deployed-prior-comparison-20261102/plan.json'
TEAMS = ('Instructors', 'duck', 'HYPOTHERMIA', 'Greek Gift', 'Knight Vision', 'Strongly Invisible')
ARMS = ('original', 'optimized', 'full')
sys.path.insert(0, str(ROOT))
from learning.compare_archives import kill_tree


def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, obj): p.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')
def unique(p, obj):
    with p.open('x') as f: json.dump(obj, f, indent=2, allow_nan=False); f.write('\n')


def environment(arm):
    e = {k: v for k, v in os.environ.items() if not k.startswith(('MIST_', 'ASTRA_', 'FOW_', 'OMP_', 'OPENBLAS_', 'MKL_'))}
    e.update(MIST_THREADS='2', MIST_MODEL_TEMP='2', MIST_MODEL_FULL_BELOW='1000000000' if arm == 'full' else '10000',
             MIST_HISTORY_TABLE=str(BASE / 'data/history.bin'), OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    return e


def limits(): resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3, 3 * 1024**3))


def call(name, command, arm='original'):
    start = time.monotonic()
    p = subprocess.Popen(list(map(str, command)), env=environment(arm), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, start_new_session=True, preexec_fn=limits)
    error = None
    try: stdout, stderr = p.communicate(timeout=120)
    except BaseException as e:
        kill_tree(p.pid); stdout, stderr = p.communicate(); error = f'{type(e).__name__}: {e}'
    for suffix, text in [('stdout', stdout), ('stderr', stderr)]:
        with (OUT / (name + '.' + suffix)).open('x') as f: f.write(text)
    receipt = dict(command=list(map(str, command)), returncode=p.returncode, error=error, elapsed=time.monotonic() - start,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(), stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest())
    unique(OUT / (name + '-receipt.json'), receipt)
    assert p.returncode == 0 and error is None, receipt
    return stdout


def prepare():
    os.sched_setaffinity(0, {2, 3}); BUILD.mkdir(exist_ok=False)
    cost = json.loads((COST_OUT / 'result.json').read_text()); assert cost['decision'] == 'broader_posterior_design_allowed'
    pins = json.loads((COST_OUT / 'plan.json').read_text())
    for p, h in pins['dependencies'].items(): assert sha(Path(p)) == h, p
    assert sha(REF) == '2f82ac292bfad29bcb2d701b73c060d1ca8281378b4598f08a620fe5c97255be'
    spec = importlib.util.spec_from_file_location('full_prior_referee', REF)
    ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
    excluded = {r['game'] for r in json.loads(FRESH.read_text())['cases']}
    excluded.update(r['game'] for r in json.loads(PRIOR.read_text())['games'])
    accepted_path = ROOT / 'data/raw/accepted.jsonl'; payload = accepted_path.read_bytes()
    index = {r['id']: r for r in map(json.loads, payload.splitlines())}
    eligible = [r for r in index.values() if '2026-11-01' <= (r.get('createdAt') or '') < '2026-11-01T20:00'
                and r['id'] not in excluded and 'IAmAVirus' in (r.get('white'), r.get('black'))]
    games = []
    for team in TEAMS:
        choices = sorted([r for r in eligible if team in (r['white'], r['black'])],
                         key=lambda r: hashlib.sha256(('full-prior226:' + r['id']).encode()).hexdigest())
        assert len(choices) >= 4, (team, len(choices))
        for r in choices[:4]:
            path = ROOT / 'data/raw/games' / r['id'] / 'replay.json'; rp = json.loads(path.read_text())
            us = 0 if rp['white'] == 'IAmAVirus' else 1; board = ref.FowBoard(); lines = [f"game {r['id']} {us}"]
            frames = rp['frames']; assert rp.get('rulesVersion') == 'fow-v1'
            for ply, frame in enumerate(frames):
                assert frame['ply'] == ply
                if ply:
                    move = ref.chess.Move.from_uci(frame['move']); assert move in ref.fow_moves(board)
                    board.push(move)
                observed = ref.make_frame(board, frame['clocks'])
                for key in ('board', 'white', 'black'): assert observed[key] == frame[key], (r['id'], ply, key)
                if ply == 0 or ply == len(frames) - 1: continue
                mover = (ply - 1) % 2; side = 0 if board.turn else 1
                who, action = ('us', frame['move']) if mover == us else ('them', '-')
                view = frame[('white', 'black')[us]]; ep = board.ep_square if board.ep_square is not None else -1
                lines.append(f"{who} {action} {view} {frame['board']} {side} {board.castling_rights:x} {ep} {board.halfmove_clock}")
            trace = OUT / (r['id'] + '.trace'); trace.write_text('\n'.join(lines) + '\n')
            games.append(dict(game=r['id'], team=team, us=us, our_version=rp.get(('white', 'black')[us] + 'Version'),
                opponent_version=rp.get(('black', 'white')[us] + 'Version'), created_at=rp['createdAt'],
                replay_sha256=sha(path), trace=str(trace), trace_sha256=sha(trace), validated_frames=len(frames)))
    assert len({g['game'] for g in games}) == 24
    for name, source in [('original', COST / 'original/src'), ('optimized', COST / 'sparse/src')]:
        call('build-' + name, ['gcc', '-std=c11', '-O2', '-pthread', '-D_POSIX_C_SOURCE=199309L', '-I', source,
            HERE / 'trace.c', *[source / n for n in ('board.c', 'belief.c', 'movemodel.c')], '-lm', '-o', BUILD / name])
    fixture = OUT / 'fixture.trace'; fixture.write_text('\n'.join(Path(games[0]['trace']).read_text().splitlines()[:7]) + '\n')
    fixture_rows = {}
    for arm in ARMS:
        binary = BUILD / ('original' if arm == 'original' else 'optimized')
        fixture_rows[arm] = [json.loads(x) for x in call('fixture-' + arm, [binary, fixture], arm).splitlines()]
        assert len(fixture_rows[arm]) == 6 and all(r['matches'] > 0 for r in fixture_rows[arm])
    stable = lambda rows: [{k: v for k, v in r.items() if k != 'update_seconds'} for r in rows]
    assert stable(fixture_rows['original']) == stable(fixture_rows['optimized'])
    unique(OUT / 'preflight.json', dict(fixture=fixture_rows, referee_frames=sum(g['validated_frames'] for g in games)))
    jobs = []
    for i, g in enumerate(games):
        for arm in ARMS[i % 3:] + ARMS[:i % 3]: jobs.append(dict(game=g['game'], arm=arm, name=g['game'] + '-' + arm))
    deps = [Path(__file__), HERE / 'trace.c', HERE / 'README.md', REF, BASE / 'data/history.bin',
            COST_OUT / 'result.json', COST_OUT / 'plan.json', FRESH, PRIOR, OUT / 'preflight.json',
            BUILD / 'original', BUILD / 'optimized', ROOT / 'learning/compare_archives.py']
    for source in (COST / 'original/src', COST / 'sparse/src'): deps += list(source.glob('*.[ch]'))
    deps += [Path(g['trace']) for g in games]
    plan = dict(created=now(), games=games, jobs=jobs, excluded_ids=sorted(excluded), accepted_sha256=hashlib.sha256(payload).hexdigest(),
                dependencies={str(p): sha(p) for p in deps}, bootstrap_seed=2261102, bootstrap_draws=2000,
                gate=dict(minimum_gain_nats=.15, lower_ci_above=0, minimum_large_regime_games=6,
                          total_time_ratio_at_most=1.2, p95_ratio_at_most=1.5, p95_floor_seconds=.1, support_must_not_decline=True),
                primary='Our decision frames with ply//2>=8; missing/zero share floored1e-12; no clock thinning or recovery.',
                parent_wall_seconds=2700, child_wall_seconds=120, memory_bytes=3 * 1024**3, cores=[2, 3],
                scope='Capped-posterior development gate, not timed policy or Elo; one observer per game; no test-outcome tuning.')
    unique(OUT / 'plan.json', plan)
    print(json.dumps(dict(games=len(games), jobs=len(jobs), frames=sum(g['validated_frames'] for g in games), plan_sha256=sha(OUT / 'plan.json'))), flush=True)


def summarize(plan, cells):
    primary = []; total_times = {a: [] for a in ARMS}; large_games = set()
    for g in plan['games']:
        rows = {a: cells[g['game'] + '-' + a] for a in ARMS}
        for a in ARMS:
            assert len(rows[a]) == g['validated_frames'] - 2
            assert not any(r['matches'] == 0 and not r['ever_capped'] for r in rows[a]), (g, a, 'uncapped support lost')
            total_times[a].extend(r['update_seconds'] for r in rows[a])
        stable = lambda rr: [{k: v for k, v in r.items() if k != 'update_seconds'} for r in rr]
        assert stable(rows['original']) == stable(rows['optimized']), (g, 'optimization parity')
        if any(r['parents'] > 10000 for r in rows['original'] if r['decision']): large_games.add(g['game'])
        for old, new in zip(rows['original'], rows['full']):
            assert old['ply'] == new['ply']
            if not old['decision'] or old['ply'] // 2 < 8: continue
            primary.append(dict(game=g['game'], team=g['team'], ply=old['ply'], original=old, full=new))
    assert primary
    def gain(r, floor): return math.log(max(r['full']['truth_share'], floor)) - math.log(max(r['original']['truth_share'], floor))
    game_groups = {t: [g['game'] for g in plan['games'] if g['team'] == t] for t in TEAMS}
    aggregates = {g['game']: (math.fsum(gain(r, 1e-12) for r in primary if r['game'] == g['game']),
                             sum(r['game'] == g['game'] for r in primary)) for g in plan['games']}
    rng = np.random.default_rng(plan['bootstrap_seed']); draws = []
    for _ in range(plan['bootstrap_draws']):
        chosen = [group[int(i)] for group in game_groups.values() for i in rng.integers(len(group), size=len(group))]
        numerator = math.fsum(aggregates[g][0] for g in chosen); denominator = sum(aggregates[g][1] for g in chosen)
        assert denominator; draws.append(numerator / denominator)
    summary = dict(primary_decisions=len(primary), games=len(plan['games']), large_regime_games=len(large_games),
        support={a: sum(r[a]['matches'] > 0 for r in primary) for a in ('original', 'full')},
        mean_truth_nll={a: -math.fsum(math.log(max(r[a]['truth_share'], 1e-12)) for r in primary) / len(primary) for a in ('original', 'full')},
        gain_nats=math.fsum(gain(r, 1e-12) for r in primary) / len(primary), interval95=np.quantile(draws, [.025, .975]).tolist(),
        gain_sensitivity={str(f): math.fsum(gain(r, f) for r in primary) / len(primary) for f in (1e-9, 1e-12, 1e-15)},
        update_seconds={a: dict(total=sum(v), p95=float(np.quantile(v, .95)), maximum=max(v)) for a, v in total_times.items()},
        exact_control_fingerprints=True,
        by_team={t: dict(decisions=sum(r['team'] == t for r in primary), gain_nats=float(np.mean([gain(r, 1e-12) for r in primary if r['team'] == t]))) for t in TEAMS})
    gate = plan['gate']; timing = summary['update_seconds']
    conditions = dict(support=summary['support']['full'] >= summary['support']['original'],
        gain=summary['gain_nats'] >= gate['minimum_gain_nats'], interval=summary['interval95'][0] > gate['lower_ci_above'],
        large_regime=summary['large_regime_games'] >= gate['minimum_large_regime_games'],
        total_time=timing['full']['total'] <= gate['total_time_ratio_at_most'] * timing['original']['total'],
        p95_time=timing['full']['p95'] <= max(gate['p95_floor_seconds'], gate['p95_ratio_at_most'] * timing['original']['p95']))
    summary.update(conditions=conditions, decision='timed_decision_design_allowed' if all(conditions.values()) else 'close_full_prior_configuration', scope=plan['scope'])
    unique(OUT / 'summary.json', summary); print(json.dumps(summary, indent=2), flush=True)


def run():
    plan = json.loads((OUT / 'plan.json').read_text()); os.sched_setaffinity(0, set(plan['cores']))
    for p, h in plan['dependencies'].items(): assert sha(Path(p)) == h, p
    state = dict(started=now(), pid=os.getpid(), status='running', completed=0, plan_sha256=sha(OUT / 'plan.json'))
    unique(OUT / 'execution.json', state)
    def expired(*_): raise TimeoutError('45-minute total cap')
    signal.signal(signal.SIGALRM, expired); signal.alarm(plan['parent_wall_seconds']); cells = {}
    try:
        games = {g['game']: g for g in plan['games']}
        for job in plan['jobs']:
            arm = job['arm']; binary = BUILD / ('original' if arm == 'original' else 'optimized')
            stdout = call(job['name'], [binary, games[job['game']]['trace']], arm)
            rows = [json.loads(x) for x in stdout.splitlines()]; cells[job['name']] = rows
            assert len(rows) == games[job['game']]['validated_frames'] - 2
            assert not any(r['matches'] == 0 and not r['ever_capped'] for r in rows)
            stable = lambda rr: [{k: v for k, v in r.items() if k != 'update_seconds'} for r in rr]
            if all(job['game'] + '-' + a in cells for a in ('original', 'optimized')):
                assert stable(cells[job['game'] + '-original']) == stable(cells[job['game'] + '-optimized'])
            state['completed'] += 1; save(OUT / 'execution.json', state)
            print(json.dumps(dict(completed=state['completed'], job=job['name'], updates=len(rows), update_seconds=sum(r['update_seconds'] for r in rows))), flush=True)
        summarize(plan, cells); state['status'] = 'complete'
    except BaseException as e: state.update(status='failed', error=f'{type(e).__name__}: {e}'); raise
    finally: signal.alarm(0); state['ended'] = now(); save(OUT / 'execution.json', state)


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('prepare', 'run')
    globals()[sys.argv[1]]()
