"""Freeze equal-clock comparison only after the exact kernel and integration gates."""
import importlib.util
import json
from pathlib import Path
import subprocess
from search_common import HERE,ROOT,OUT,sha,now,unique


def main():
    kernel=OUT.parent
    assert json.loads((kernel/'summary.json').read_text())['gate_pass']
    assert json.loads((OUT/'preflight.json').read_text())['passed']
    cases_path=ROOT/'astra-submissions/analysis/fresh-taxonomy-20261101/cases.json'
    cases=json.loads(cases_path.read_text())['cases'];assert len(cases)==51
    oracle_path=HERE.parent/'persistent-response-20261101/review.py'
    spec=importlib.util.spec_from_file_location('sparse_search_oracle',oracle_path)
    oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
    dependencies=json.loads((kernel/'search-build.json').read_text())['pins']
    pins=[*HERE.glob('search*.py'),HERE/'build_search_pair.py',HERE/'search_pair.c',
          kernel/'summary.json',kernel/'plan.json',kernel/'build.json',OUT/'preflight.json',cases_path,
          ROOT/'astra-submissions/tools/fresh_taxonomy_gate.py',oracle_path,oracle.REFPATH,
          ROOT/'learning/rules.py',ROOT/'learning/ingest.py',HERE/'build/base/mist',HERE/'build/fast/mist']
    for p in pins: dependencies[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)]=sha(p)
    for p,h in dependencies.items(): assert sha(ROOT/p)==h,p
    for c in cases: assert sha(c['replay_path'])==c['replay_sha256']
    plan=dict(at=now(),source_parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
              seed=2541102,cores=[0,1],per_search_seconds=2.5,prefix_max_seconds=10,
              case_wall_cap=120,wall_cap=2700,arms=['off','on'],cases=cases,dependencies=dependencies,
              order='Alternating first arm; same belief, guard mask, sample seed and root action set.',
              truth_to_actor=False,gpu=False,
              gate=dict(min_exercised_pairs=20,min_median_node_ratio=1.05,max_additional_fatal=1,
                        max_additional_material_ge2=2,technical_failures=0,illegal_choices=0),
              scope='Reused development decisions, not held-out strength. Stockfish worker state is shared across '
                    'the two calls; order rotates but TT/leaf values are not held identical. Timing includes '
                    'post-search diagnostics, while search budgets are equal.',
              full_game_followup=dict(conditional_on_replay_and_review_pass=True,pairs=8,opponent='exact v37',
                                      time_control='180+2',seed_base=2541200,minimum_points_for_opponent_gate=10,
                                      wall_cap=14400))
    unique(OUT/'plan.json',plan)
    print(json.dumps(dict(plan_sha256=sha(OUT/'plan.json'),cases=len(cases),files=len(dependencies))))


if __name__=='__main__':main()
