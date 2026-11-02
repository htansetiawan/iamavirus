import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from build import HERE,ROOT,OUT


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def unique(p,value):
    with Path(p).open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def main():
    tests=json.loads((OUT/'value-tests.json').read_text());assert tests['conditional_value_oracle_cases']==640 and tests['solver_iteration_byte_parity']==1200
    assert len(json.loads((OUT/'runtime-tests.json').read_text()))==8
    assert not (OUT/'selection-sanitized.stderr').read_text() and not (OUT/'sanitized-values.stderr').read_text()
    for name in ('selection-optimized.stdout','selection-sanitized.stdout'):assert json.loads((OUT/name).read_text())['q_selection_cases']==253
    assert '2000' in (OUT/'sanitized-values.stdout').read_text()
    expected=ROOT/'astra-submissions/experiments/queen-terminal-backport-20261102/build-r2/base/mist'
    assert sha(expected)==sha(HERE/'build/base/mist')=='14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd'
    cases_path=ROOT/'astra-submissions/analysis/fresh-taxonomy-20261101/cases.json'
    cases=json.loads(cases_path.read_text())['cases'];assert len(cases)==51
    oracle_path=ROOT/'astra-submissions/experiments/persistent-response-20261101/review.py'
    spec=importlib.util.spec_from_file_location('qexp_oracle_preflight',oracle_path);oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
    dependencies={}
    for name in ('build-pins.json','diagnostic-pins.json'):dependencies.update(json.loads((OUT/name).read_text()))
    pins=[*HERE.glob('*.py'),*HERE.glob('*.c'),*HERE.glob('*.h'),HERE/'README.md',cases_path,
        ROOT/'astra-submissions/tools/fresh_taxonomy_gate.py',oracle_path,oracle.REFPATH,
        ROOT/'astra-submissions/analysis/deeprl-table-audit-20261025/run_engine_probe.py',
        ROOT/'learning/rules.py',ROOT/'learning/ingest.py',expected,
        HERE/'build/base/bin/stockfish',HERE/'build/base/data/history.bin',
        HERE/'build/candidate/build.sh',HERE/'build/candidate/run.sh']
    for p in pins:dependencies[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)]=sha(p)
    for k,h in dependencies.items():assert sha(ROOT/k)==h,k
    for c in cases:assert sha(Path(c['replay_path']))==c['replay_sha256']
    plan=dict(at=now(),source_parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        seed=2341102,cores=[2,3],per_search_seconds=2.5,prefix_max_seconds=10,case_wall_cap=120,wall_cap=2700,
        arms=['off','on'],order='alternate by case; identical frozen belief and guard exclusions',cases=cases,
        dependencies=dependencies,truth_to_actor=False,gpu=False,
        gate=dict(min_exercised_pairs=20,max_additional_fatal=1,max_additional_material_ge2=2,
                  technical_failures=0,illegal_choices=0,recall_failures=0),
        scope='Reused development diagnostics; paired identical input belief, not strength; no parameter selection.',
        full_game_followup=dict(conditional_on_replay_and_review_pass=True,pairs=8,opponent='exact v37',
            time_control='180+2',seed_base=2341200,minimum_points_for_opponent_gate=10,wall_cap=14400))
    unique(OUT/'plan.json',plan);print(json.dumps({'plan_sha256':sha(OUT/'plan.json'),'cases':len(cases),'games':len({c['game'] for c in cases}),'source_files':len(dependencies)}))


if __name__=='__main__':main()
