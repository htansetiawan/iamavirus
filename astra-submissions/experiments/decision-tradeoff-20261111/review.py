"""Independent dot products and a linear-program check of saved-value sensitivity."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import scipy
from scipy.optimize import linprog

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"astra-submissions/analysis/decision-tradeoff-20261111"


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    result=json.loads((OUT/"result.json").read_text());checks=[]
    for case in result["cases"]:
        for path,expected in case["source_hashes"].items():assert sha(path)==expected,path
        population=json.loads(Path(next(p for p in case["source_hashes"] if p.endswith("population.json"))).read_text())
        target=json.loads(Path(next(p for p in case["source_hashes"] if p.endswith("targets.jsonl"))).read_text())
        assert [r["index"] for r in case["per_world"]]==[s["index"] for s in population["samples"]]
        weights=np.array([s["weight"] for s in population["samples"]],dtype=float);weights/=weights.sum()
        chosen=np.array([next(a["value"] for a in s["actions"] if a["move"]==case["chosen"]) for s in population["samples"]])
        alternate=np.array([next(a["value"] for a in s["actions"] if a["move"]==case["alternate"]) for s in population["samples"]])
        delta=chosen-alternate;gap=float(weights@delta);assert abs(gap-case["gap"])<1e-12
        assert np.allclose(weights*delta,[r["contribution"] for r in case["per_world"]],rtol=0,atol=1e-12)
        alternatives=[a for a in target["actions"] if a["uci"]!=case["chosen"]]
        assert max(alternatives,key=lambda a:a["q"])["uci"]==case["alternate"]
        n=len(weights);objective=np.r_[np.zeros(n),np.full(n,.5)]
        # Variables q (new distribution), t (absolute deviations).
        inequalities=[np.r_[delta,np.zeros(n)]];bounds=[0.]
        for i in range(n):
            plus=np.zeros(2*n);plus[i]=1;plus[n+i]=-1;inequalities.append(plus);bounds.append(weights[i])
            minus=np.zeros(2*n);minus[i]=-1;minus[n+i]=-1;inequalities.append(minus);bounds.append(-weights[i])
        optimum=linprog(objective,A_ub=np.array(inequalities),b_ub=np.array(bounds),
            A_eq=np.array([np.r_[np.ones(n),np.zeros(n)]]),b_eq=np.array([1.]),bounds=(0,None),method="highs")
        claimed=case["sensitivity"]["minimum_total_variation_to_tie"]
        if claimed is None:assert optimum.status==2
        else:
            assert optimum.success and abs(optimum.fun-claimed)<1e-10
            assert abs(.5*np.abs(optimum.x[:n]-weights).sum()-claimed)<1e-10
            assert abs(optimum.x[:n]@delta)<1e-10
        e=case["sufficient_opposed_expected_value_error_to_tie"]
        assert abs((float(weights@chosen)-e)-(float(weights@alternate)+e))<1e-12
        assert abs(case["root_only_deviation_gap"])<1e-9
        checks.append(dict(role=case["role"],numpy_gap=gap,linear_program_status=optimum.status,
            linear_program_minimum_tv=float(optimum.fun) if optimum.success else None,
            analytic_tv_matches_independent_lp=claimed is not None,one_world_infeasible_control=claimed is None,
            opposed_value_error_tie_checked=True))
    receipt=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,cases=checks,
        python=sys.version,numpy=np.__version__,scipy=scipy.__version__,
        source_sha256=sha(__file__),result_sha256=sha(OUT/"result.json"),
        scope="Numerical and optimization check only; no native engine, new sample, model, policy or game. LP changes a mathematical distribution while saved values remain fixed.")
    with (OUT/"numeric-review.json").open("x") as f:json.dump(receipt,f,indent=1,sort_keys=True,allow_nan=False);f.write("\n")
    print(json.dumps(dict(passed=True,cases=checks)))


if __name__=="__main__":main()
