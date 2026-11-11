"""Freeze one complete-engine comparison against the exact active v38 bytes."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import py_compile
import shutil

from stage import ANALYSIS, BUILD, CONFIRM, EXPERIMENTS, HERE, OUT, ROOT, SHIP, now, read, save, sha

PREVIOUS = ANALYSIS/'deferred-prior-playing-20261111'
FRESH = EXPERIMENTS/'last-only-fresh-pilot-20261110'


def main():
    assert not (OUT/'plan.json').exists()
    build = read(OUT/'build.json')
    parity = read(OUT/'trace-parity.json')
    confirmed = read(CONFIRM/'terminal-verification.json')
    assert build['passed'] and len(build['preflight']) == 8
    assert parity['passed'] and len(parity['calls']) == 12 and parity['verified_rows'] == 1428
    assert confirmed['decision'] == 'full_clock_integration_design_allowed' and not confirmed['failed']
    old = read(PREVIOUS/'plan.json')
    prior = read(PREVIOUS/'result.json')
    assert prior['plan_sha256'] == sha(PREVIOUS/'plan.json') and not prior['gate_pass']
    assert prior['status'] == 'closed_futility' and (prior['wins'],prior['losses']) == (4,7)
    for record in (old, build, parity):
        assert all(sha(path)==digest for path,digest in record['dependencies'].items())
    assert sha(SHIP/'mist') == old['baseline_sha256'] == build['binaries']['v38']
    assert sha(BUILD/'candidate/mist') == build['binaries']['gcc']

    spec = spec_from_file_location('mass_playing_harness_stage', FRESH/'prepare.py')
    staging = module_from_spec(spec)
    spec.loader.exec_module(staging)
    staging.verify_retry_classifier()
    staging.HERE = HERE
    generated = staging.stage_runner(BUILD)
    runner = BUILD/'runner'
    shutil.copyfile(FRESH/'startup_retry.py',runner/'startup_retry.py')
    pilot = runner/'pilot.py'
    source = pilot.read_text()
    assert source.count("'last-only'")==2
    pilot.write_text(source.replace("'last-only'","'compact-mass'"))
    for path in (*generated,runner/'startup_retry.py'):
        py_compile.compile(str(path),doraise=True)

    jobs = []
    for pair in range(8):
        order = ('white','black') if (pair//2)%2==0 else ('black','white')
        for side in order:
            jobs.append(dict(id=f'mass-p{pair}-{side}',pair=pair,lane=pair%2,side=side,
                             engine_seed=3571110+2*pair,opponent_seed=3571111+2*pair))
    keys = ('engine_seed','opponent_seed')
    seeds = {job[key] for job in jobs for key in keys}
    earlier = {job[key] for path in (PREVIOUS/'plan.json',ANALYSIS/'last-only-fresh-pilot-20261110/plan.json')
               for job in read(path)['jobs'] for key in keys}
    assert len(seeds)==16 and seeds.isdisjoint(earlier)
    pins = dict(old['dependencies'])
    for record in (build, parity):
        for path, digest in record['dependencies'].items():
            assert path not in pins or pins[path] == digest, path
            pins[path] = digest
    extra = [Path(__file__),FRESH/'prepare.py',OUT/'build.json',OUT/'trace-parity.json',
             CONFIRM/'result.json',CONFIRM/'terminal-verification.json',
             PREVIOUS/'plan.json',PREVIOUS/'result.json',*generated,runner/'startup_retry.py']
    pins.update({str(path):sha(path) for path in extra})
    plan = dict(old,at=now(),jobs=jobs,dependencies=pins,store=str(ROOT/'data/astra-spool'/HERE.name),
                candidate_sha256=build['binaries']['gcc'],previous_plan_sha256=sha(PREVIOUS/'plan.json'),
                source_changes=['src/'+name for name in build['changes']]+['run.sh'],
                source_mode='Fixed compact prior with powered observation mass preserved; original v38 board, solver, guards, time and assets.',
                nearest_prior='343 unrestricted compact failed priority nonregression. 353 development and 355 independent mass-preserving prior pass. 351 closed speed-only at 4–7.',
                test_basis=dict(confirmed_posterior=True,complete_engine_compiler_parity=True,
                                previous_speed_playing_gate_pass=False),
                initial_position='Eight fresh standard-start color pairs, with starting colors balanced per lane.',
                release_constraint='Unnumbered local test. Later release requires qualified-opponent evidence and current Fable+1 mapping.',
                next='All-gate pass permits a separate qualified-opponent comparison.')
    assert plan['gate']==dict(points=10,planned=16,technical_faults=0,all_completed_unless_irreversible_futility=True)
    save(OUT/'plan.json',plan)
    print(dict(jobs=len(jobs),pins=len(pins),candidate=plan['candidate_sha256'],plan_sha256=sha(OUT/'plan.json')),flush=True)


if __name__=='__main__':
    main()
