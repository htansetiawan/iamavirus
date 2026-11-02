import json
import os
from pathlib import Path
import subprocess
from settings import HERE,ROOT,OUT,now,sha,unique


def main():
    os.sched_setaffinity(0,{2,3});OUT.mkdir(exist_ok=False)
    previous=OUT.parent/'posterior-capacity-20261102'
    old=json.loads((previous/'plan.json').read_text());deps=old['dependencies'].copy()
    for path,digest in deps.items():assert sha(Path(path))==digest,path
    test=subprocess.run([str(ROOT/'.venv/bin/python'),str(HERE/'test_bound.py')],capture_output=True,text=True,timeout=60)
    (OUT/'preflight.stdout').write_text(test.stdout);(OUT/'preflight.stderr').write_text(test.stderr);test.check_returncode()
    for p in list(HERE.glob('*.py'))+[HERE/'README.md',previous/'selection.json',previous/'validation-data.json',previous/'validation-scores.jsonl.gz']:
        deps[str(p)]=sha(p)
    plan=dict(at=now(),games=[g for g in old['games'] if g['split']=='validation'],dependencies=deps,
        seed=2331102,cores=[2,3],wall_seconds=1200,max_feature_bytes=2*1024**3,train_cases_per_game=12,
        previous_selection=str(previous/'selection.json'),previous_data=str(previous/'validation-data.json'),
        previous_scores=str(previous/'validation-scores.jsonl.gz'),preflight=json.loads(test.stdout),
        scope='Scoring-feature equivalence on fixed incoming development beliefs; no training or strength claim.',
        witness_limit=6,witness_surprise_limit=6)
    assert len(plan['games'])==80
    unique(OUT/'plan.json',plan)
    print(json.dumps(dict(plan_sha256=sha(OUT/'plan.json'),games=len(plan['games']),preflight=plan['preflight'])),flush=True)


if __name__=='__main__':main()
