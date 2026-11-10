"""Reuse the first pilot's audited harness with fresh pairs and startup checking."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import py_compile
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = HERE.parent/'last-only-pilot-20261110'
EVIDENCE = ROOT/'astra-submissions/analysis'
OUT = EVIDENCE/HERE.name
PRIOR = EVIDENCE/PREVIOUS.name
SMOKE = EVIDENCE/'native-stockfish-precheck-20261110'


def sha(path):
    with Path(path).open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def substitute(source, before, after):
    if source.count(before) != 1:
        raise ValueError(f'Unexpected archived source near {before!r}')
    return source.replace(before, after)


def stage_runner(build):
    runner = build/'runner'
    runner.mkdir()
    source = (PREVIOUS/'pilot.py').read_text()
    changes = [
        ('HERE=Path(__file__).resolve().parent;', 'HERE=Path(__file__).resolve().parents[2];'),
        ("OUT=ROOT/'astra-submissions/analysis/last-only-pilot-20261110'", f"OUT=ROOT/'astra-submissions/analysis/{HERE.name}'"),
        ("OWNER='astra-last-only-pilot-20261110'", f"OWNER='astra-{HERE.name}'"),
        ('from local_turn_control import run_controlled,cleanup_registry,group_members',
         'from local_turn_control import cleanup_registry,group_members\n'
         'sys.path.insert(0, str(HERE))\nfrom startup_retry import play'),
        ('game=run_controlled(ref,white,black,', 'game=play(ref,white,black,verify_cleanup=cleanup,'),
        ("frames=game['frames'];assert 1<=len(frames)<=1001", "frames=game['frames'];assert 1<=len(frames)<=1001\n"
         " readiness=[(r['side'],r['status']) for r in game.get('localNativeStockfishReadiness',[])]\n"
         " if readiness!=[('white','ready'),('black','ready')]:\n"
         "  faults.append('native Stockfish readiness: '+game['reason'])"),
        ("str(HERE/'review.py')", "str(Path(__file__).with_name('review.py'))"),
    ]
    for before, after in changes:
        source = substitute(source, before, after)
    (runner/'pilot.py').write_text(source)

    review = (PREVIOUS/'review.py').read_text()
    review = substitute(review, 'from local_turn_control import group_members',
                        'from local_turn_control import group_members\nfrom startup_retry import audit_rejection')
    review = substitute(review, 'for job in plan[\'jobs\']:',
                        "retried=[]\n for job in plan['jobs']:")
    review = substitute(review, "  if (directory/'aborted.json').exists():",
                        "  if audit_rejection(directory,job['id'],180):retried.append(job['id'])\n"
                        "  if (directory/'aborted.json').exists():")
    review = substitute(review, "   # Independent native C++ rules/observation checker, separate from producer's course walk.",
                        "   assert [(r['side'],r['status']) for r in game['localNativeStockfishReadiness']]==[('white','ready'),('black','ready')]\n"
                        "   # Independent native C++ rules/observation checker, separate from producer's course walk.")
    review = substitute(review, 'result=dict(at=', 'result=dict(retried_setups=retried,at=')
    (runner/'review.py').write_text(review)
    for name in ('pilot.py', 'review.py'):
        py_compile.compile(str(runner/name), doraise=True)
    return [runner/'pilot.py', runner/'review.py']


def verify_retry_classifier():
    sys.path[:0] = [str(HERE), str(ROOT/'astra-submissions/tools')]
    from startup_retry import retryable
    smoke = json.loads((SMOKE/'plan.json').read_text())
    result = json.loads((SMOKE/'result.json').read_text())
    source = Path(smoke['private_store'])
    for case in result['cases']:
        raw = source/case['case']/'game.json'
        assert sha(raw) == case['source_sha256']
        game = json.loads(raw.read_text())
        assert retryable(game, 3) == (case['case'] != 'healthy')
        if case['case'] != 'healthy':
            game['protocol']['events'].append(dict(ply=0, direction='input', text='?'*64))
            assert not retryable(game, 3)


def main():
    plan = json.loads((PRIOR/'plan.json').read_text())
    prior_result = json.loads((PRIOR/'result.json').read_text())
    assert prior_result['status'] == 'technical_failure' and prior_result['games'] == 1
    readiness = json.loads((SMOKE/'terminal-verification.json').read_text())
    assert readiness['terminal_exit_code'] == 0 and readiness['failed_backends_rejected_before_play'] == 3
    for path, digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    verify_retry_classifier()

    build = HERE/'build'
    build.mkdir(exist_ok=False)
    for name in ('candidate', 'base', 'referee.py', 'native-validator.so'):
        (build/name).symlink_to(PREVIOUS/'build'/name)
    generated = stage_runner(build)
    jobs = []
    for pair in range(8):
        sides = ('white', 'black') if (pair//2)%2 == 0 else ('black', 'white')
        for side in sides:
            jobs.append(dict(id=f'fresh-p{pair}-{side}', pair=pair, lane=pair%2, side=side,
                             engine_seed=3351110+2*pair, opponent_seed=3351111+2*pair))
    old_seeds = {j[key] for j in plan['jobs'] for key in ('engine_seed', 'opponent_seed')}
    new_seeds = {j[key] for j in jobs for key in ('engine_seed', 'opponent_seed')}
    assert len(new_seeds) == 16 and not old_seeds & new_seeds
    assert plan['gate']['points'] == 10 and plan['gate']['planned'] == 16
    plan.update(at=datetime.now(timezone.utc).isoformat(), jobs=jobs,
                store=str(ROOT/'data/astra-spool'/HERE.name),
                nearest_prior='332 stopped for a pregame reference fallback. 333 diagnosed startup and 334 validated early readiness refusal.',
                initial_position='Standard start, eight new seed pairs, color swap preserves both engine seeds. Two White-first and two Black-first pairs on each lane.',
                startup_retry='One replacement for a preserved early native backend refusal with untouched clocks and initialization-only protocol. Keep the same seed and use the first played result.',
                startup_retry_limit_per_leg=1,
                futility='Stop scheduling when points plus unplayed legs cannot reach 10. Finish active legs. An unresolved technical failure closes the batch.',
                previous_plan_sha256=sha(PRIOR/'plan.json'))
    extra = [*generated, HERE/'startup_retry.py', Path(__file__), PRIOR/'plan.json',
             PRIOR/'terminal-verification.json', SMOKE/'plan.json', SMOKE/'terminal-verification.json',
             ROOT/'astra-submissions/tools/native_stockfish_readiness.py']
    plan['dependencies'].update({str(path):sha(path) for path in extra})
    OUT.mkdir(exist_ok=False)
    (OUT/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    print(json.dumps(dict(games=len(jobs), pins=len(plan['dependencies']),
        plan_sha256=sha(OUT/'plan.json'), classifier_receipts=4, rejected_post_observation_controls=3)))

if __name__ == '__main__':
    main()
