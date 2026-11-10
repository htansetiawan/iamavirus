"""One fixed ordinary-cutoff sequential comparison; no search or refitting."""
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import time

import numpy as np
from prepare import ROOT, HERE, OUT, BUILD, BASE, sha, save

ARMS = ('original', 'zero', 'learned')
RISK = ('king1', 'kingt', 'queen1', 'queent')


def now(): return datetime.now(timezone.utc).isoformat()
def atomic(path, obj):
    path = Path(path); temporary = path.with_name('.' + path.name + '-tmp')
    temporary.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n'); os.replace(temporary, path)


def environment(arm):
    env = {k: v for k, v in os.environ.items() if not k.startswith(('MIST_', 'ASTRA_', 'FOW_', 'OMP_', 'MKL_', 'OPENBLAS_'))}
    env.update(MIST_THREADS='2', MIST_MODEL_FULL_BELOW='10000', MIST_MODEL_TEMP='2',
               MIST_HISTORY_TABLE=str(BASE / 'data/history.bin'), MIST_HISTORY_MIN='3', MIST_HISTORY_N0='4',
               ASTRA_CAPTURE_FIXED=str({'original': 0, 'zero': 1, 'learned': 2}[arm]),
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    return env


def stable(rows):
    return [{k: v for k, v in row.items() if k not in ('update_seconds', 'guard_seconds')} for row in rows]


def interval(plan, records, values, seed):
    groups = {team: [g['game'] for g in plan['games'] if g['team'] == team] for team in plan['teams']}
    aggregate = {g['game']: [0., 0] for g in plan['games']}
    for record, value in zip(records, values):
        item = aggregate[record['game']]; item[0] += float(value); item[1] += 1
    rng = np.random.default_rng(seed); estimates = []
    for _ in range(plan['bootstrap_draws']):
        selected = [members[int(i)] for members in groups.values() for i in rng.integers(len(members), size=len(members))]
        numerator = math.fsum(aggregate[g][0] for g in selected); denominator = sum(aggregate[g][1] for g in selected)
        assert denominator
        estimates.append(numerator / denominator)
    return np.quantile(estimates, [.025, .975]).tolist()


def aggregate(plan, cells):
    primary = []; times = {arm: [] for arm in ARMS}; collapsed = {arm: 0 for arm in ARMS}
    full_updates = {arm: 0 for arm in ARMS}; large_games = set(); guard_violations = 0
    for game in plan['games']:
        for seed_index, _ in enumerate(plan['seeds']):
            rows = {arm: cells[f"{game['game']}-s{seed_index}-{arm}"] for arm in ARMS}
            assert stable(rows['original']) == stable(rows['zero'])
            for arm in ARMS:
                assert len(rows[arm]) == game['rows']
                assert not any(not r['ever_capped'] and not r['matches'] for r in rows[arm]), 'pre-cap truth loss'
                collapsed[arm] += any(r['worlds'] == 0 for r in rows[arm])
                full_updates[arm] += sum(r['full_update'] for r in rows[arm])
                times[arm].extend(r['update_seconds'] for r in rows[arm])
                guard_violations += sum(r['guard_bad_moves'] for r in rows[arm])
            if any(r['decision'] and r['parents'] > 10000 for r in rows['original']): large_games.add(game['game'])
            for old, new in zip(rows['original'], rows['learned']):
                assert old['ply'] == new['ply']
                for key in ('decision', 'guard_applicable', 'king_label', 'queen_label'):
                    assert old[key] == new[key], key
                if old['decision'] and old['ply'] // 2 >= 8:
                    primary.append(dict(game=game['game'], team=game['team'], seed=seed_index,
                                        ply=old['ply'], original=old, learned=new))
    assert primary and guard_violations == 0
    deltas = {floor: [math.log(max(r['learned']['truth_share'], floor)) -
                      math.log(max(r['original']['truth_share'], floor)) for r in primary]
              for floor in (1e-9, 1e-12, 1e-15)}
    gain = math.fsum(deltas[1e-12]) / len(primary)
    groups = {}
    for team in plan['teams']:
        subset = [r for r in primary if r['team'] == team]
        groups[team] = dict(games=len({r['game'] for r in subset}), decisions=len(subset),
                            gain=math.fsum(math.log(max(r['learned']['truth_share'], 1e-12)) -
                                           math.log(max(r['original']['truth_share'], 1e-12)) for r in subset) / len(subset))
    risk_rows = [r for r in primary if r['original']['guard_applicable']]
    risk = {}; labels = {}
    for kind_index, kind in enumerate(RISK):
        label = 'king_label' if kind.startswith('king') else 'queen_label'
        differences = [(r['learned'][kind] - r['learned'][label]) ** 2 -
                       (r['original'][kind] - r['original'][label]) ** 2 for r in risk_rows]
        risk[kind] = dict(original=math.fsum((r['original'][kind] - r['original'][label]) ** 2 for r in risk_rows) / len(risk_rows),
                          learned=math.fsum((r['learned'][kind] - r['learned'][label]) ** 2 for r in risk_rows) / len(risk_rows),
                          delta=math.fsum(differences) / len(risk_rows),
                          interval95=interval(plan, risk_rows, differences, plan['seed'] + 10 + kind_index))
        labels[label] = len({(r['game'], r['ply']) for r in risk_rows if r['original'][label]})
    result = dict(primary=len(primary), distinct_primary=len({(r['game'], r['ply']) for r in primary}),
                  support={arm: sum(r[arm]['matches'] > 0 for r in primary) for arm in ('original', 'learned')},
                  mean_truth_nll={arm: -math.fsum(math.log(max(r[arm]['truth_share'], 1e-12)) for r in primary) / len(primary)
                                  for arm in ('original', 'learned')}, gain=gain,
                  interval95=interval(plan, primary, deltas[1e-12], plan['seed']),
                  sensitivity={str(floor): math.fsum(values) / len(values) for floor, values in deltas.items()},
                  by_team=groups, collapsed_case_seeds=collapsed, full_updates=full_updates,
                  large_regime_games=len(large_games), native_guard_brier=risk,
                  unique_positive_guard_events=labels, risk_rows=len(risk_rows),
                  risk_available={arm: sum(r[arm]['guard_available'] for r in risk_rows) for arm in ('original', 'learned')},
                  time={arm: dict(total=math.fsum(values), p95=float(np.quantile(values, .95)), maximum=max(values))
                        for arm, values in times.items()})
    gate = plan['gate']; t = result['time']
    conditions = dict(primary_coverage=result['primary'] >= gate['primary_min'] and result['distinct_primary'] >= gate['distinct_min'],
                      truth_support=result['support']['learned'] >= result['support']['original'],
                      gain=result['gain'] >= gate['gain'], confidence=result['interval95'][0] > 0,
                      floor_sensitivity=all(v >= 0 for v in result['sensitivity'].values()),
                      no_extra_collapse=collapsed['learned'] <= collapsed['original'],
                      regime_coverage=result['large_regime_games'] >= gate['large_games'] and full_updates['original'] >= gate['full_updates'],
                      priority_coverage=all(groups[name]['games'] >= gate['priority_games'] for name in plan['priority']),
                      priority_nonregression=all(groups[name]['gain'] >= 0 for name in plan['priority']),
                      total_cost=t['learned']['total'] <= gate['total_ratio'] * t['original']['total'],
                      p95_cost=t['learned']['p95'] <= max(gate['p95_floor'], gate['p95_ratio'] * t['original']['p95']),
                      guard_coverage=len(risk_rows) >= gate['risk_rows'] and all(v >= gate['positive_events'] for v in labels.values()),
                      guard_availability=result['risk_available']['learned'] >= result['risk_available']['original'],
                      guard_nonregression=all(v['delta'] <= gate['brier_tolerance'] for v in risk.values()))
    result.update(conditions=conditions, decision='real_clock_decision_design_allowed' if all(conditions.values()) else 'close_frozen_full_head_sequential',
                  scope=plan['scope'])
    return result


def main():
    plan = json.loads((OUT / 'plan.json').read_text())
    assert not (OUT / 'execution.json').exists(), 'run already attempted'
    for path, expected in plan['dependencies'].items(): assert sha(path) == expected, path
    os.sched_setaffinity(0, set(plan['cores']))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('fixed45-minute bound')))
    signal.alarm(plan['max_seconds'])
    started = time.monotonic(); state = dict(status='running', started_at=now(), pid=os.getpid(), completed=0, plan_sha256=sha(OUT / 'plan.json'))
    save(OUT / 'execution.json', state); cells = {}; manifest = []
    games = {g['game']: g for g in plan['games']}
    try:
        for job in plan['jobs']:
            name = job['name']; arm = job['arm']; game = games[job['game']]
            binary = BUILD / ('trace-original' if arm == 'original' else 'trace-adapter')
            def limit(): resource.setrlimit(resource.RLIMIT_AS, (plan['max_child_bytes'], plan['max_child_bytes']))
            tick = time.monotonic()
            with (OUT / (name + '.stdout')).open('x') as output, (OUT / (name + '.stderr')).open('x') as error:
                child = subprocess.Popen([str(binary), game['trace'], str(plan['seeds'][job['seed_index']])],
                                         stdout=output, stderr=error, env=environment(arm), start_new_session=True, preexec_fn=limit)
                try: code = child.wait(timeout=plan['child_seconds'])
                except BaseException:
                    if child.poll() is None:
                        os.killpg(child.pid, signal.SIGTERM)
                        try: child.wait(timeout=5)
                        except subprocess.TimeoutExpired: os.killpg(child.pid, signal.SIGKILL); child.wait()
                    raise
            item = dict(**job, code=code, seconds=time.monotonic()-tick,
                        stdout_sha256=sha(OUT / (name + '.stdout')), stderr_sha256=sha(OUT / (name + '.stderr')))
            manifest.append(item); atomic(OUT / 'calls.json', manifest)
            assert code == 0, name + ' failed; no retry'
            rows = [json.loads(line) for line in (OUT / (name + '.stdout')).read_text().splitlines()]
            assert len(rows) == game['rows'] and [r['ply'] for r in rows] == list(range(1, game['rows'] + 1))
            assert all(math.isfinite(r['truth_share']) and 0 <= r['truth_share'] <= 1 for r in rows)
            assert not any(not r['ever_capped'] and not r['matches'] for r in rows), 'pre-cap truth loss'
            assert not any(r['guard_bad_moves'] for r in rows), 'frontend-compatible action not legal on strided hypothesis'
            for r in rows:
                assert all(math.isfinite(r[k]) and 0 <= r[k] <= 1 for k in RISK)
            cells[name] = rows
            prefix = f"{game['game']}-s{job['seed_index']}-"
            if prefix + 'original' in cells and prefix + 'zero' in cells:
                assert stable(cells[prefix + 'original']) == stable(cells[prefix + 'zero']), 'zero control changed'
            state.update(completed=len(manifest), updated_at=now()); atomic(OUT / 'execution.json', state)
            assert sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()) <= plan['max_output_bytes']
            print(json.dumps(dict(completed=len(manifest), total=len(plan['jobs']), job=name)), flush=True)
        result = aggregate(plan, cells); result.update(at=now(), plan_sha256=sha(OUT / 'plan.json'), calls_sha256=sha(OUT / 'calls.json'))
        save(OUT / 'result.json', result); state.update(status='complete', decision=result['decision'])
        print(json.dumps(result, indent=2), flush=True)
    except BaseException as error:
        state.update(status='failed', error=repr(error)); raise
    finally:
        signal.alarm(0); state.update(ended_at=now(), seconds=time.monotonic()-started); atomic(OUT / 'execution.json', state)


if __name__ == '__main__': main()
