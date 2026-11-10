"""Same-belief paired traces for the first two losses in the unchanged live panel."""
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/guard-loss-review-20261110'
PANEL = ROOT/'astra-submissions/analysis/guard-opponent-bounded-20261110'
CONTROLS = HERE.parent/'guard-controls-20261109'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def helper():
    sys.path.insert(0, str(CONTROLS))
    spec = importlib.util.spec_from_file_location('paired_loss_trace', CONTROLS/'run.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUT = OUT
    return module


def prepare():
    OUT.mkdir(exist_ok=False)
    losses = []
    for path in PANEL.glob('jobs/*/result.json'):
        result = json.loads(path.read_text())
        if result['job']['arm'] == 'candidate' and not result['faults'] and result['score'] == 0:
            losses.append((result['finished'], path, result))
    chosen = sorted(losses)[:2]
    assert {p.parent.name for _, p, _ in chosen} == {'p0-white-candidate', 'p0-black-candidate'}
    cases, paths = [], [Path(__file__), CONTROLS/'run.py', CONTROLS/'prepare.py']
    control_plan_path = ROOT/'astra-submissions/analysis/guard-controls-20261109/plan.json'
    control_plan = json.loads(control_plan_path.read_text())
    deps = dict(control_plan['dependencies'])
    for _, path, result in chosen:
        replay = path.parent/'replay.json'
        game = json.loads(replay.read_text())
        terminal = len(game['frames'])-2
        for ply in [terminal-2, terminal]:
            cases.append(dict(id=f'{path.parent.name}-{ply}', game=game['id'], side=result['job']['side'],
                ply=ply, kind='preceding' if ply < terminal else 'terminal', opponent='bounded-local-Misty',
                replay_path=str(replay), replay_sha256=sha(replay), actual=game['frames'][ply+1]['move']))
        paths.extend([path, replay])
    paths.extend([control_plan_path, PANEL/'plan.json'])
    deps.update({str(p): sha(p) for p in paths})
    plan = dict(at=datetime.now(timezone.utc).isoformat(), cases=cases, dependencies=deps,
                core=6, actor_seed=2701109, per_arm_search_seconds=2.5, per_case_seconds=150, total_seconds=660,
                selection='First two completed normal candidate losses; final own decision and one own decision earlier.',
                procedure='Reuse the verified same-belief paired guard helper. Alternate arm order; both arms share '
                          'belief/sample seed. Historical own observations, clocks and own moves only enter the actor. '
                          'True-board labels are computed after it exits.',
                scope='Retrospective failure diagnosis on four selected positions, not new strength evidence. '
                      'One core can thin differently from the live two-core games. No retries, new policy or threshold tuning. '
                      'The 32-game panel, seeds, tested bytes and promotion gate stay fixed.')
    write(OUT/'plan.json', plan)
    print(json.dumps(dict(prepared=True, cases=len(cases), pins=len(deps))), flush=True)


def run():
    plan = json.loads((OUT/'plan.json').read_text())
    for path, digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    os.sched_setaffinity(0, {6})
    os.nice(10)
    module = helper()
    start = time.monotonic()
    write(OUT/'started.json', dict(at=datetime.now(timezone.utc).isoformat(), pid=os.getpid()))
    rows, error = [], None
    try:
        for i, case in enumerate(plan['cases']):
            assert time.monotonic()-start+plan['per_case_seconds'] < plan['total_seconds']
            row = module.one(case, i, OUT/'jobs'/case['id'], plan['per_arm_search_seconds'])
            rows.append(dict(id=case['id'], kind=case['kind'], actual=case['actual'],
                             base_move=row['arms']['base']['move'], candidate_move=row['arms']['candidate']['move'],
                             base_fatal=row['arms']['base']['fatal'], candidate_fatal=row['arms']['candidate']['fatal'],
                             same_belief_pair=row['exercised'], result_sha256=sha(OUT/'jobs'/case['id']/'result.json')))
            print(json.dumps(rows[-1]), flush=True)
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        write(OUT/'completion.json', dict(at=datetime.now(timezone.utc).isoformat(), completed=len(rows),
              error=error, elapsed_seconds=time.monotonic()-start, rows=rows, scope=plan['scope']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'run'))
    globals()[parser.parse_args().action]()
