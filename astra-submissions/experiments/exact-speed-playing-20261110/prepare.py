"""Freeze a color-swapped real-clock test after the large-regime gate passes."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import py_compile
import shutil

from build import ANALYSIS, BUILD, EXPERIMENTS, HERE, OUT, ROOT, SHIP, now, read, save, sha

PREVIOUS = EXPERIMENTS/'last-only-fresh-pilot-20261110'
PREVIOUS_OUT = ANALYSIS/PREVIOUS.name
STRESS = ANALYSIS/'large-regime-exact-speed-20261110'


def main():
    assert not (OUT/'plan.json').exists()
    stress, verified = (read(STRESS/name) for name in ('result.json','terminal-verification.json'))
    assert verified['result_sha256']==sha(STRESS/'result.json') and verified['exit_code']==0
    assert stress['decision']=='exact_speed_full_clock_design_allowed' and all(stress['conditions'].values())
    build = read(OUT/'build.json')
    prior = read(PREVIOUS_OUT/'plan.json')
    old_result = read(PREVIOUS_OUT/'result.json')
    assert build['passed'] and build['changes']==['board.c','movemodel.c'] and len(build['preflight'])==8
    assert build['binaries']['v38']==prior['baseline_sha256']==sha(SHIP/'mist')
    assert old_result['points']==9 and old_result['gate_pass'] is False
    assert all(sha(path)==digest for path,digest in build['dependencies'].items())
    assert all(sha(path)==digest for path,digest in prior['dependencies'].items())

    spec = spec_from_file_location('fresh_paired_runner_stage',PREVIOUS/'prepare.py')
    staging = module_from_spec(spec)
    spec.loader.exec_module(staging)
    staging.verify_retry_classifier()
    staging.HERE = HERE
    generated = staging.stage_runner(BUILD)
    runner = BUILD/'runner'
    shutil.copyfile(PREVIOUS/'startup_retry.py',runner/'startup_retry.py')
    pilot = runner/'pilot.py'
    text = pilot.read_text()
    assert text.count("'last-only'")==2
    pilot.write_text(text.replace("'last-only'","'exact-speed'"))
    for path in (*generated,runner/'startup_retry.py'):
        py_compile.compile(str(path),doraise=True)

    jobs = []
    for pair in range(8):
        sides = ('white','black') if (pair//2)%2==0 else ('black','white')
        for side in sides:
            jobs.append(dict(id=f'speed-p{pair}-{side}', pair=pair, lane=pair%2, side=side,
                             engine_seed=3471110+2*pair, opponent_seed=3471111+2*pair))
    old_seeds = {job[key] for job in prior['jobs'] for key in ('engine_seed','opponent_seed')}
    new_seeds = {job[key] for job in jobs for key in ('engine_seed','opponent_seed')}
    assert len(new_seeds)==16 and old_seeds.isdisjoint(new_seeds)
    assert prior['gate']==dict(points=10, planned=16, technical_faults=0, all_completed_unless_irreversible_futility=True)
    # Inherit the known-good referee, resources and readiness protocol. Pins
    # cover the new build and both benchmark receipts in addition to the harness.
    deps = dict(prior['dependencies'], **build['dependencies'])
    extra = [Path(__file__), OUT/'build.json', *generated, runner/'startup_retry.py',
             PREVIOUS_OUT/'plan.json',PREVIOUS_OUT/'result.json',
             *(STRESS/name for name in ('plan-summary.json','result.json','terminal-verification.json'))]
    deps.update({str(path):sha(path) for path in extra})
    plan = dict(prior, at=now(), jobs=jobs, dependencies=deps,
                store=str(ROOT/'data/astra-spool'/HERE.name),
                candidate_sha256=build['binaries']['gcc'], previous_plan_sha256=sha(PREVIOUS_OUT/'plan.json'),
                source_changes=['src/board.c','src/movemodel.c'],
                source_mode='Standalone exact speed build. Deployed v38 build flags, stockfish, history, model weights, solver and launcher retained.',
                nearest_prior='335 used the same referee, lanes and 10/16 gate for the different last-only solver candidate. It closed at 9/16.',
                initial_position='Eight new standard-start seed pairs, swapped colors and balanced starting order on each lane.',
                release_constraint='Unnumbered local engine. Any later release must check the Fable archive sequence and receive its own qualified-opponent evidence.',
                next='All-gate pass allows a separate qualified-opponent comparison.')
    save(OUT/'plan.json',plan)
    print(dict(games=len(jobs), pins=len(deps), candidate=plan['candidate_sha256'], plan_sha256=sha(OUT/'plan.json')),flush=True)


if __name__=='__main__':
    main()
