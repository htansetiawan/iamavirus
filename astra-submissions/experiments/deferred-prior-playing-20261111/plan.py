"""Measure playing strength of the verified combined exact engine."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import py_compile
import shutil

from stage import ANALYSIS, BUILD, HERE, OUT, ROOT, SHIP, TEST, now, read, save, sha

FRESH = HERE.parent/'last-only-fresh-pilot-20261110'
FRESH_OUT = ANALYSIS/FRESH.name
REQUIRED = ('parity','coverage','aggregate_cost','median_game_cost','tail_cost')


def main():
    assert not (OUT/'plan.json').exists()
    result, audit = (read(TEST/name) for name in ('result.json','terminal-verification.json'))
    assert audit['exit_code']==0 and audit['result_sha256']==sha(TEST/'result.json')
    assert audit['conditions']==result['conditions'] and result['decision']=='close_exact_deferred_speed_gate'
    assert all(result['conditions'][name] for name in REQUIRED) and not result['conditions']['incremental_cost']
    old = read(FRESH_OUT/'plan.json')
    build = read(OUT/'build.json')
    assert len(build['preflight'])==8 and build['passed'] and old['baseline_sha256']==build['binaries']['v38']==sha(SHIP/'mist')
    assert old['gate']==dict(points=10,planned=16,technical_faults=0,all_completed_unless_irreversible_futility=True)
    assert all(sha(path)==digest for dependencies in (old['dependencies'],build['dependencies']) for path,digest in dependencies.items())

    spec = spec_from_file_location('deferred_speed_runner_stage',FRESH/'prepare.py')
    staging = module_from_spec(spec); spec.loader.exec_module(staging)
    staging.verify_retry_classifier()
    staging.HERE = HERE
    generated = staging.stage_runner(BUILD)
    runner = BUILD/'runner'
    shutil.copyfile(FRESH/'startup_retry.py',runner/'startup_retry.py')
    pilot = runner/'pilot.py'
    text = pilot.read_text()
    assert text.count("'last-only'")==2
    pilot.write_text(text.replace("'last-only'","'deferred-speed'"))
    for path in (*generated,runner/'startup_retry.py'):
        py_compile.compile(str(path),doraise=True)

    jobs = []
    for pair in range(8):
        order = ('white','black') if (pair//2)%2==0 else ('black','white')
        for side in order:
            jobs.append(dict(id=f'deferred-p{pair}-{side}',pair=pair,lane=pair%2,side=side,
                             engine_seed=3511110+2*pair,opponent_seed=3511111+2*pair))
    keys = ('engine_seed','opponent_seed')
    seeds = {job[key] for job in jobs for key in keys}
    assert len(seeds)==16 and seeds.isdisjoint(job[key] for job in old['jobs'] for key in keys)
    extra = [Path(__file__),OUT/'build.json',*generated,runner/'startup_retry.py',FRESH_OUT/'plan.json',
             *(TEST/name for name in ('plan-summary.json','result.json','terminal-verification.json'))]
    pins = dict(old['dependencies'],**build['dependencies'])
    pins.update({str(path):sha(path) for path in extra})
    plan = dict(old, at=now(), jobs=jobs, dependencies=pins, store=str(ROOT/'data/astra-spool'/HERE.name),
                candidate_sha256=build['binaries']['gcc'],previous_plan_sha256=sha(FRESH_OUT/'plan.json'),
                source_changes=['src/'+name for name in build['changes']],
                source_mode='Standalone exact deferred speed build; deployed v38 flags, model, solver, launcher and assets.',
                nearest_prior='335 closed a different solver at 9/16. 348 missed its incremental threshold while the combined engine met the full runtime gate.',
                test_basis=dict(aggregate_runtime_pass=True, exact_parity=True, incremental_gate_pass=False,
                                adjudication='Measure playing strength of the complete engine. The failed incremental hypothesis remains closed.'),
                initial_position='Eight fresh standard-start color pairs, with balanced starting colors per lane.',
                release_constraint='Unnumbered local test. Later release requires qualified-opponent evidence and the Fable +1 version check.',
                next='All-gate pass allows a separate qualified-opponent comparison.')
    save(OUT/'plan.json',plan)
    print(dict(games=len(jobs),pins=len(pins),candidate=plan['candidate_sha256'],plan_sha256=sha(OUT/'plan.json')),flush=True)


if __name__=='__main__':
    main()
