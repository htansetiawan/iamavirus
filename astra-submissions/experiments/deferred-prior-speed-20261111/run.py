"""Score only opponent parents with at least one compatible successor."""
from importlib.util import module_from_spec, spec_from_file_location
from itertools import permutations
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ANALYSIS = ROOT/'astra-submissions/analysis'
STORE = ROOT/'data/astra-spool'
OUT = ANALYSIS/HERE.name
PRIVATE = STORE/HERE.name
EAGER = STORE/'exact-updater-speed-20261110'
STRESS = ANALYSIS/'large-regime-exact-speed-20261110'
STRESS_RAW = STORE/STRESS.name
BASE = HERE.parent/'guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren/src'
LEGACY = HERE.parent/'quiet-prior-sequential-20261110'
RUNNER = HERE.parent/EAGER.name/'run.py'
spec = spec_from_file_location('shared_exact_update_runner',RUNNER)
speed = module_from_spec(spec)
spec.loader.exec_module(speed)
read, save, sha = speed.read, speed.save, speed.sha
ARMS = ('original','eager','combined')


def deferred(source):
    """Preserve the likelihood denominator over the original legal list."""
    start = source.index('static void *opp_pass1(void *arg)')
    stop = source.index('\n/* Moves the `keep`',start)
    worker = source[start:stop]
    def replace(before,after):
        nonlocal worker
        assert worker.count(before)==1,before
        worker = worker.replace(before,after)

    replace('        Position p = b->items[i];',
            '        const Position *parent = &b->items[i];\n        Position p = *parent;')
    block = '''            move_logits(&p, &l, b->last_own, w->full, logit);
            float top = -INFINITY;
            for (int j = 0; j < l.count; ++j) if (logit[j] > top) top = logit[j];
            double z = 0;
            for (int j = 0; j < l.count; ++j) z += exp((double)(logit[j] - top));
            log_z = top + (float)log(z);'''
    history = '''            if (hist_table) {
                ++w->lookups;
                N = history_counts(b->hist ? b->hist[i] : 0, &l, hc);
                if (N < hist_min) N = 0; else ++w->hits;
            }'''
    replace('        if (model_on) {\n'+block+'\n'+history+'\n        }',
            '        int likelihood_ready = 0;\n        if (model_on && hist_table) {\n'
            +'\n'.join(line[4:] for line in history.splitlines()[1:-1])+'\n        }')
    accepted = '                if (memcmp(seen, w->view, 64) == 0) {\n'
    replace(accepted, accepted+'''                    /* No successor consumes scores for a rejected parent.
                     * Use the untouched parent and the entire legal list. */
                    if (model_on && !likelihood_ready) {
'''+ '\n'.join('            '+line for line in block.replace('move_logits(&p,','move_logits(parent,').splitlines())
        +'\n                        likelihood_ready = 1;\n                    }\n')
    return source[:start]+worker+source[stop:]


def compile_candidate():
    updated = PRIVATE/'belief.c'
    updated.write_text(deferred((BASE/'belief.c').read_text()))
    command = ['gcc','-O3','-std=c11','-ffp-contract=off','-pthread','-D_POSIX_C_SOURCE=199309L',
               '-I'+str(BASE),'-I'+str(LEGACY/'build'),str(LEGACY/'trace.c'),str(updated),
               str(EAGER/'board.c'),str(EAGER/'movemodel.c'),'-lm','-o',str(PRIVATE/'combined')]
    subprocess.run(command,check=True,timeout=60)
    return command


def preflight(panel, seed):
    results = []
    for game in panel[:3]:
        text = Path(game['trace']).read_text().splitlines()[:25]
        trace = PRIVATE/(game['game']+'.fixture')
        trace.write_text('\n'.join(text)+'\n')
        for setting in ('deployed','no_history','no_model'):
            env = speed.environment('original')
            if setting=='no_history':
                env.pop('MIST_HISTORY_TABLE')
            elif setting=='no_model':
                env['MIST_MODEL'] = '0'
            traces = []
            for arm in ('eager','combined'):
                proc = subprocess.run([str(PRIVATE/arm),str(trace),str(seed)],env=env,capture_output=True,
                                      text=True,check=True,timeout=20)
                rows = [json.loads(line) for line in proc.stdout.splitlines()]
                assert len(rows)==len(text)-1
                traces.append(speed.stable(rows))
            assert traces[0]==traces[1],setting
            results.append(dict(setting=setting,updates=len(traces[0])))
    return results


def prepare():
    reviewed = read(STRESS/'terminal-verification.json')
    previous = read(STRESS/'result.json')
    assert sha(STRESS/'result.json')==reviewed['result_sha256']
    assert [name for name,value in previous['conditions'].items() if not value]==['aggregate_cost']
    plan = read(STRESS_RAW/'plan.json')
    assert sha(STRESS_RAW/'plan.json')==reviewed['plan_sha256']
    assert all(sha(path)==digest for path,digest in plan['dependencies'].items())
    eager_plan = read(EAGER/'plan.json')
    for name in ('board.c','movemodel.c'):
        assert sha(EAGER/name)==eager_plan['dependencies'][str(EAGER/name)]
    OUT.mkdir(exist_ok=False); PRIVATE.mkdir(exist_ok=False)
    for arm,file in (('original','original'),('eager','combined')):
        (PRIVATE/arm).symlink_to(STRESS_RAW/file)
    command = compile_candidate()
    checked = preflight(plan['panel'],plan['seed'])
    orders = list(permutations(ARMS))
    jobs = [dict(game=g['game'],arm=arm) for i,g in enumerate(plan['panel']) for arm in orders[i%len(orders)]]
    deps = [Path(__file__),RUNNER,STRESS/'result.json',STRESS/'terminal-verification.json',STRESS_RAW/'plan.json',
            EAGER/'board.c',EAGER/'movemodel.c',LEGACY/'trace.c',LEGACY/'build/guard_predicates.h',*BASE.glob('*.[ch]'),
            BASE.parent/'data/history.bin',*(PRIVATE/name for name in (*ARMS,'belief.c')),
            *(Path(g['trace']) for g in plan['panel'])]
    plan.update(at=speed.now(),jobs=jobs,incremental_ratio_max=.97,dependencies={str(p):sha(p) for p in sorted(set(deps))},
                compile=command)
    save(PRIVATE/'plan.json',plan)
    summary = {key:plan[key] for key in ('at','seed','cores','child_timeout','total_timeout','update_min',
        'cutoff_updates_min','total_cost_max','game_median_max','tail_ratio_max','incremental_ratio_max')}
    summary.update(plan_sha256=sha(PRIVATE/'plan.json'),games=len(plan['panel']),jobs=len(jobs),pins=len(deps),
                   preflight_cases=len(checked),preflight_rows=sum(row['updates'] for row in checked),
                   binaries={arm:sha(PRIVATE/arm) for arm in ARMS},
                   scope='Development comparison on the 346 large-regime panel. Original v38, exact eager 346, and exact deferred. Same aggregate/tail and coverage thresholds; require 3% additional improvement in all updates and large-mode updates versus eager.')
    save(OUT/'plan-summary.json',summary)
    print(json.dumps(summary,indent=2),flush=True)


def run():
    speed.HERE,speed.OUT,speed.PRIVATE,speed.ARMS = HERE,OUT,PRIVATE,ARMS
    original_summary = speed.summarize
    def summarize(plan,games,cases):
        result = original_summary(plan,games,cases)
        combined,eager = (result['metrics'][arm]['seconds'] for arm in ('combined','eager'))
        relative = {key:combined[key]/eager[key] for key in ('all','large')}
        result['incremental_ratio_vs_eager'] = relative
        result['conditions']['incremental_cost'] = all(r<=plan['incremental_ratio_max'] for r in relative.values())
        result['decision'] = ('exact_deferred_full_clock_design_allowed' if all(result['conditions'].values())
                              else 'close_exact_deferred_speed_gate')
        return result
    speed.summarize = summarize
    speed.run()


if __name__=='__main__':
    {'prepare':prepare,'run':run}[sys.argv[1]]()
