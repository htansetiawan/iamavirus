import json
import os
from pathlib import Path
import subprocess
from settings import HERE,ROOT,OUT,now,sha,unique


def main():
    os.sched_setaffinity(0,{2,3});OUT.mkdir(exist_ok=False);(HERE/'build').mkdir(exist_ok=False)
    old=OUT.parent/'posterior-fit-20261102';original=json.loads((old/'plan.json').read_text())
    deps=original['dependencies'].copy()
    for p,h in deps.items():assert sha(Path(p))==h,p
    # Keep every source frozen; the old test manifest remains provenance, never a data input.
    games=[g for g in original['games'] if g['split'] in ('train','validation')]
    assert len(games)==480
    build=subprocess.run(['gcc','-O3','-std=c11','-shared','-fPIC',str(HERE/'residual.c'),'-o',str(HERE/'build/residual.so')],capture_output=True,text=True,timeout=60)
    (OUT/'build.log').write_text(build.stdout+build.stderr);build.check_returncode()
    pre=subprocess.run([str(ROOT/'.venv/bin/python'),str(HERE/'preflight.py')],capture_output=True,text=True,timeout=90)
    (OUT/'preflight.stdout').write_text(pre.stdout);(OUT/'preflight.stderr').write_text(pre.stderr);pre.check_returncode()
    for p in list(HERE.glob('*.py'))+[HERE/'README.md',HERE/'residual.c',HERE/'build/residual.so',old/'plan.json',old/'selection.json',old/'train-data.json',old/'validation-data.json']:
        deps[str(p)]=sha(p)
    plan={**original,'at':now(),'games':games,'dependencies':deps,'seed':2321102,
          'wall_seconds':2700,'device':'cpu','objectives':['actor','posterior'],'forms':['linear','quadratic'],
          'scope':'Development capacity screen on reused231 train/validation only. No old test access, fresh test or strength claim.',
          'gate':dict(baseline_gain=.10,linear_posterior_gain=.05,quadratic_actor_gain=.05,
                      late_min_gain=-.02,surprise_min_gain=-.02,min_surprise=20,all_min_gain=0.,max_support_failures=0),
          'preflight':json.loads(pre.stdout)}
    for key in ('inventory','test_cutoff','snapshot','source_parent_commit'):plan.pop(key,None)
    plan['inventory']={'train':400,'validation':80,'test':0}
    plan['source_parent_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    unique(OUT/'plan.json',plan)
    print(json.dumps(dict(plan_sha256=sha(OUT/'plan.json'),games=len(games),preflight=plan['preflight'])),flush=True)


if __name__=='__main__':main()
