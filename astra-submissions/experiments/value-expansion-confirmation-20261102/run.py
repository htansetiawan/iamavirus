"""Conditional confirmation of the immutable experiment-234 playing binary.

Preparing and freezing this queue do not authorize starting it: the original
16-game pilot must finish and pass, and its handles must be reconciled first.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/value-expansion-confirmation-20261102'
PARENT = HERE.parent / 'value-expansion-20261102'
PILOT = ROOT / 'astra-submissions/analysis/value-expansion-20261102/full-games'
OLD = HERE.parent / 'persistent-confirmation-20261102'
RUNNER = HERE.parent / 'persistent-response-20261101/bench.py'
MISTY = HERE.parent / 'persistent-response-20261101/build/misty'
sys.path[:0] = [str(ROOT), str(ROOT / 'astra-submissions/tools')]
from learning import ingest, rules


def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, value):
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(p)


def imported(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def command(arm, seed):
    directories = {'candidate': PARENT / 'build/candidate', 'base': PARENT / 'build/base',
                   'v35': OLD / 'build/v35', 'misty': MISTY}
    return ['/usr/bin/env', f'FOW_SEED={seed}', f'MIST_EXPANSION_Q={int(arm == "candidate")}',
            '/bin/bash', str(directories[arm] / 'run.sh')]


def module():
    m = imported('q_confirmation_runner', RUNNER)
    m.HERE = PARENT; m.OUT = OUT; m.__file__ = str(Path(__file__))
    m.command = command
    return m


def design():
    OUT.mkdir(exist_ok=False)
    prior = json.loads((PILOT / 'plan.json').read_text())
    old = json.loads((ROOT / 'astra-submissions/analysis/persistent-confirmation-20261102/plan.json').read_text())
    deps = dict(prior['dependencies'])
    for name, digest in old['dependencies'].items():
        if '/fable-persist/' in name: deps[name] = digest
    for p in [Path(__file__), HERE / 'verify.py', OLD / 'run.py', OLD / 'build/v35/mist',
              OLD / 'build/v35/run.sh', OLD / 'build/v35/bin/stockfish',
              OLD / 'build/v35/data/history.bin', MISTY / 'run.sh', MISTY / 'misty_bot.py',
              ROOT / 'fable-submissions/iamavirus-v35-mist-c-v14.zip',
              ROOT / 'astra-submissions/analysis/persistent-confirmation-20261102/preparation.json',
              ROOT / 'learning/ingest.py', ROOT / 'learning/rules.py', PILOT / 'plan.json']:
        deps[str(p)] = sha(p)
    oldprep = json.loads((ROOT / 'astra-submissions/analysis/persistent-confirmation-20261102/preparation.json').read_text())
    assert sha(OLD / 'build/v35/mist') == oldprep['v35_binary_sha256']
    assert sha(ROOT / 'fable-submissions/iamavirus-v35-mist-c-v14.zip') == oldprep['v35_archive_sha256']
    for p, h in deps.items(): assert sha(p) == h, p
    jobs = []
    for block in range(4):
        for n in range(block * 4, (block + 1) * 4):
            for oi, opponent in enumerate(('v35', 'base')):
                pair = 2 * n + oi
                for side in ('white', 'black'):
                    jobs.append(dict(id=f'qconfirm-{opponent}-p{n}-{side}', phase='confirm', panel=opponent,
                        lane=(n + oi) % 2, pair=pair, arm='candidate', side=side,
                        engine_seed=2345000 + 2 * pair, opponent_seed=2345001 + 2 * pair, opponent=opponent))
        # A four-game block uses one core pair and fixed seeds in both arms.
        # Alternate arm order to limit temporal ordering effects.
        for side in ('white', 'black'):
            for arm in (('candidate', 'base') if block % 2 == 0 else ('base', 'candidate')):
                jobs.append(dict(id=f'qconfirm-misty-p{block}-{side}-{arm}', phase='confirm', panel='misty',
                    lane=block % 2, pair=32 + block, arm=arm, side=side,
                    engine_seed=2345200 + 2 * block, opponent_seed=2345201 + 2 * block, opponent='misty'))
    assert len(jobs) == len({j['id'] for j in jobs}) == 80
    assert Counter(j['lane'] for j in jobs) == {0: 40, 1: 40}
    assert Counter(j['panel'] for j in jobs) == {'v35': 32, 'base': 32, 'misty': 16}
    design = dict(created_at=now(), dependencies=deps, jobs=jobs, lanes={'0': '2,3', '1': '4,5'},
        time_control=prior['time_control'], game_wall_cap=2450, batch_wall_cap=43200,
        trigger='All 16 original experiment234 games complete, >=10 points, no faults; original lane handles terminal and owned bot groups reconciled. Publish and verify frozen queue on both mirrors before launch.',
        gate='32 games vs v35 and 32 vs v37; each score >=0.50, pooled score >=0.60 and stratified whole-colour-pair percentile-bootstrap 95% lower bound >0.50. Misty matched control on at least three of four complete valid blocks; candidate points >= v37 points in those blocks. No candidate, baseline, harness, or integrity fault. Passing earns release review only.',
        misty_fault_rule='A recorded Misty-only time/protocol forfeit invalidates its entire four-game matched block for both arms. Retain the first attempt, run the other scheduled jobs, never replace or credit the forfeit as strength. Fewer than three fully valid blocks makes confirmation inconclusive. All other technical faults disqualify and stop new jobs; already-running attempts may finish.',
        interval='Reuse the independently tested exact empirical paired-bootstrap convolution from persistent-confirmation run.py. Sixteen colour pairs per reference; resample within each reference and pool equally. Pilot results excluded.',
        limitations='Misty0.1.3 is an authentic local engine, not verified arena bytes or a substitute for Instructors/duck/HYPOTHERMIA. Seeds need not control all Misty randomness. Historical Misty-only clock fault motivates the predeclared block exclusion. Small Misty panel is a safeguard, not a non-inferiority claim. No arena Elo claim.',
        known_at_design='Original pilot partially observed (six completed games, four wins); candidate and initial gate unchanged. This confirmation uses independent new seeds.',
        model_updates_during_batch=False, repeat_started_game=False, gpu=False,
        candidate_binary_sha256=sha(PARENT / 'build/candidate/mist'))
    with (OUT / 'design.json').open('x') as f: json.dump(design, f, indent=2); f.write('\n')
    print(json.dumps(dict(jobs=80, frozen_for_execution=False, design_sha256=sha(OUT / 'design.json'))))


def smoke():
    design = json.loads((OUT / 'design.json').read_text())
    for p, h in design['dependencies'].items(): assert sha(p) == h, p
    m = module(); rows = []
    feed = 'fow\nw 180 2\n' + rules.Board().observation(0) + '\n180\n'
    for arm in ('candidate', 'base', 'v35', 'misty'):
        env = m.clean_env(); env['MIST_MAX_SECONDS'] = '.5'
        r = subprocess.run(command(arm, 2344990), input=feed, text=True, capture_output=True,
                           env=env, cwd='/tmp', timeout=60)
        row = dict(arm=arm, exit=r.returncode, stdout=r.stdout, stderr=r.stderr)
        rows.append(row); save(OUT / 'smoke.json', rows)
        moves = [x[5:] for x in r.stdout.splitlines() if x.startswith('move ')]
        assert r.returncode == 0 and r.stdout.splitlines()[0] == 'ready'
        assert len(moves) == 1 and moves[0] in rules.Board().legal_moves(), row
        assert ('astra-expansion-q ' in r.stderr) == (arm == 'candidate'), row
    print(json.dumps(dict(smokes_passed=len(rows), strength_evidence=False)))


def freeze():
    plan = json.loads((OUT / 'design.json').read_text()); deps = plan['dependencies']
    assert len(json.loads((OUT / 'smoke.json').read_text())) == 4
    assert json.loads((OUT / 'verification.json').read_text())['passed']
    pilot = json.loads((PILOT / 'plan.json').read_text()); results = []
    for job in pilot['jobs']:
        p = PILOT / 'jobs' / job['id'] / 'result.json'; r = json.loads(p.read_text())
        assert r['job'] == job and r['exit'] == 0 and not r['faults']
        assert sha(p.parent / 'replay.json') == r['replay_sha256']
        results.append(r); deps[str(p)] = sha(p)
    assert len(results) == 16 and sum(r['score'] for r in results) >= 10
    terminal = json.loads((PILOT / 'terminal.json').read_text())
    assert terminal['lane_exit_codes'] == {'0': 0, '1': 0} and terminal['owned_groups_terminal']
    for p in (OUT / 'design.json', OUT / 'smoke.json', OUT / 'verification.json', PILOT / 'terminal.json'):
        deps[str(p)] = sha(p)
    for p, h in deps.items(): assert sha(p) == h, p
    plan.update(frozen_at=now(), qualifying_pilot_points=sum(r['score'] for r in results))
    with (OUT / 'plan.json').open('x') as f: json.dump(plan, f, indent=2); f.write('\n')
    print(json.dumps(dict(frozen=True, plan_sha256=sha(OUT / 'plan.json'))))


def start():
    module().load()
    receipt = json.loads((OUT / 'publication.json').read_text())
    assert receipt['plan_sha256'] == sha(OUT / 'plan.json') and receipt['both_git_refs_verified']
    with (OUT / 'batch-start.json').open('x') as f: json.dump(dict(at=now(), monotonic=time.monotonic()), f)


def inspect(job, directory):
    game = json.loads((directory / 'replay.json').read_text())
    states, errors = ingest.validate_replay(game); faults = list(errors)
    misty_side = 'black' if job['side'] == 'white' else 'white'
    misty_failure = job['opponent'] == 'misty' and game.get('failedSide') == misty_side
    if 'failedSide' in game and not misty_failure: faults.append('bot failure: ' + game['failedSide'] + ' ' + game['reason'])
    if game['result'] not in ('1-0', '0-1', '1/2-1/2'): faults.append('non-game result')
    if game.get('warnings'): faults.append('capture warning')
    for side in ('white', 'black'):
        text = game.get('privateDiagnostics', {}).get(side, '')
        reports = [s for s in text.splitlines() if s.startswith('astra-expansion-q ')]
        enabled = job['arm'] == 'candidate' and side == job['side']
        if bool(reports) != enabled: faults.append('unexpected expansion diagnostics')
        if enabled:
            import re
            stats = [dict(re.findall(r'(\w+)=([\d.]+)', s)) for s in reports]
            if not any(int(s['scored']) > 0 for s in stats): faults.append('expansion unexercised')
            if any(int(s['recall_failures']) for s in stats): faults.append('information-set reach inconsistency')
    controls = game.get('localTurnControl', {}).get('controls', [])
    if len(controls) != 2 or any(not any(e['op'] == 'freeze' for e in c['events']) for c in controls): faults.append('missing turn isolation')
    score = .5 if game['result'] == '1/2-1/2' else float((game['result'] == '1-0') == (job['side'] == 'white')) if game['result'] in ('1-0', '0-1') else None
    return dict(job=job, result=game['result'], reason=game['reason'], score=score,
                faults=faults, opponent_fault=misty_failure, plies=len(game['frames']) - 1,
                final_clocks=game['frames'][-1]['clocks'], replay_sha256=sha(directory / 'replay.json'), validated_frames=len(states))


def lane(lane_id):
    m = module(); plan = m.load(); started = json.loads((OUT / 'batch-start.json').read_text())
    lock = (OUT / f'lane{lane_id}.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for job in [j for j in plan['jobs'] if j['lane'] == lane_id]:
        if (OUT / 'fault-stop.json').exists(): raise RuntimeError('another lane recorded a technical fault')
        d = OUT / 'jobs' / job['id']; d.mkdir(parents=True, exist_ok=True)
        if (d / 'result.json').exists():
            r = json.loads((d / 'result.json').read_text()); assert r['job'] == job and r['exit'] == 0 and not r['faults']; continue
        remaining = plan['batch_wall_cap'] - (time.monotonic() - started['monotonic'])
        if remaining <= 1: raise RuntimeError('whole-batch wall cap')
        with (d / 'started.json').open('x') as f: json.dump(dict(at=now(), job=job, parent_pid=os.getpid(), plan_sha256=sha(OUT / 'plan.json')), f)
        begin = time.monotonic()
        p = subprocess.Popen(['taskset', '-c', plan['lanes'][str(lane_id)], sys.executable, str(Path(__file__)), 'worker', '--job', job['id']],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=m.clean_env(), start_new_session=True)
        save(d / 'handle.json', dict(pid=p.pid, at=now(), pid_scope='original exec namespace'))
        try: stdout, stderr = p.communicate(timeout=min(remaining, plan['game_wall_cap'])); timeout = False
        except subprocess.TimeoutExpired: timeout = True; p.kill(); stdout, stderr = p.communicate()
        unverified = m.cleanup_registry(d / 'processes.json')
        (d / 'stdout.txt').write_text(stdout); (d / 'stderr.txt').write_text(stderr)
        if p.returncode or timeout or unverified or not (d / 'replay.json').exists():
            result = dict(job=job, score=None, opponent_fault=False, faults=[f'worker exit={p.returncode} timeout={timeout} unverified={unverified}'])
        else: result = inspect(job, d)
        result.update(exit=p.returncode, elapsed_seconds=time.monotonic() - begin, finished=now())
        save(d / 'result.json', result); print(json.dumps(result), flush=True)
        if result['faults']:
            try:
                with (OUT / 'fault-stop.json').open('x') as f: json.dump(dict(job=job['id'], at=now(), faults=result['faults']), f)
            except FileExistsError: pass
            raise RuntimeError(result['faults'])


def calculate(plan, rows):
    summary = dict(completed=len(rows), planned=80, decision='incomplete', panels={})
    bad = [r for r in rows if r['faults'] or r['exit'] != 0 or r['score'] not in (0, .5, 1)]
    invalid = {r['job']['pair'] for r in rows if r.get('opponent_fault')}
    valid_blocks = [p for p in range(32, 36) if p not in invalid and sum(r['job']['panel'] == 'misty' and r['job']['pair'] == p for r in rows) == 4]
    for panel, arm in [('v35', 'candidate'), ('base', 'candidate'), ('misty', 'candidate'), ('misty', 'base')]:
        rr = [r for r in rows if r['job']['panel'] == panel and r['job']['arm'] == arm and r['score'] is not None
              and (panel != 'misty' or r['job']['pair'] in valid_blocks)]
        scores = [r['score'] for r in rr]
        summary['panels'][panel + '/' + arm] = dict(games=len(rr), wins=scores.count(1), draws=scores.count(.5), losses=scores.count(0), points=sum(scores))
    summary.update(faults=bad, invalid_misty_blocks=sorted(invalid), valid_misty_blocks=valid_blocks)
    if bad: summary['decision'] = 'technical_failure_no_promotion'
    elif len(rows) == 80:
        pair_points = []
        for panel in ('v35', 'base'):
            rr = [r for r in rows if r['job']['panel'] == panel]; pairs = sorted({r['job']['pair'] for r in rr}); assert len(pairs) == 16
            values = []
            for p in pairs:
                group = [r for r in rr if r['job']['pair'] == p]
                assert len(group) == 2 and {r['job']['side'] for r in group} == {'white', 'black'}
                values.append(sum(r['score'] for r in group))
            pair_points.append(values)
        interval = imported('q_confirm_interval', OLD / 'run.py').pair_interval(pair_points)
        a = summary['panels']; pooled = (a['v35/candidate']['points'] + a['base/candidate']['points']) / 64
        conditions = dict(each_reference_at_least_half=min(a['v35/candidate']['points'], a['base/candidate']['points']) >= 16,
            pooled_at_least_point6=pooled >= .6, paired_lower_above_half=interval[0] > .5,
            enough_valid_misty_blocks=len(valid_blocks) >= 3, misty_at_least_control=a['misty/candidate']['points'] >= a['misty/base']['points'])
        summary.update(pooled_direct_score=pooled, stratified_pair_interval_95=interval, conditions=conditions,
            decision='release_review' if all(conditions.values()) else 'inconclusive_opponent_panel' if len(valid_blocks) < 3 else 'close_frozen_candidate')
    return summary


def summarize():
    plan = module().load(); rows = []
    for job in plan['jobs']:
        p = OUT / 'jobs' / job['id'] / 'result.json'
        if p.exists():
            r = json.loads(p.read_text()); assert r['job'] == job; rows.append(r)
    result = calculate(plan, rows); save(OUT / 'summary.json', result); print(json.dumps(result, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('command', choices=('design', 'smoke', 'freeze', 'start', 'lane', 'worker', 'summarize'))
    ap.add_argument('--lane', type=int, choices=(0, 1)); ap.add_argument('--job'); a = ap.parse_args()
    if a.command == 'worker': module().worker(a.job)
    elif a.command == 'lane': lane(a.lane)
    else: globals()[a.command]()
