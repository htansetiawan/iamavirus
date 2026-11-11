"""Post-hoc arithmetic on 417's saved native values; no engine invocation."""
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/"astra-submissions/analysis/decision-tradeoff-20261111"
PRIVATE=ROOT/"data/astra-spool/safe-recapture-20261111"
PREVIOUS=ROOT/"astra-submissions/analysis/safe-recapture-20261111"


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    with path.open("x") as f:json.dump(value,f,indent=1,sort_keys=True,allow_nan=False);f.write("\n")


def case(role):
    receipt=read(PREVIOUS/f"{role}-replay.json")
    for relative,expected in receipt["files"].items():assert sha(PRIVATE/relative)==expected,relative
    folder=PRIVATE/role;pop=read(folder/"population.json");target=json.loads((folder/"targets.jsonl").read_text())
    audit=next(r for r in read(PREVIOUS/"pair-review.json")["cases"] if r["role"]==role)
    assert target["solver_move"]==receipt["chosen"]
    assert len(pop["samples"])==len(pop["worlds"])==pop["count"]
    assert {s["index"] for s in pop["samples"]}==set(range(pop["count"]))
    assert len(audit["true_rule_state_indices"])==1
    actual=audit["true_rule_state_indices"][0]
    ordered=sorted(target["actions"],key=lambda a:a["q"],reverse=True)
    chosen=next(a for a in ordered if a["uci"]==receipt["chosen"])
    alternate=next(a for a in ordered if a["uci"]!=chosen["uci"])
    assert ordered[0]["uci"]==chosen["uci"]
    original_mass=math.fsum(s["weight"] for s in pop["samples"])
    samples=[dict(s,normalized_weight=s["weight"]/original_mass) for s in pop["samples"]]
    native_logw=[struct.unpack("f",struct.pack("f",w["logw"]))[0] for w in pop["worlds"]]
    native_weights=[math.exp(w) for w in native_logw];native_total=math.fsum(native_weights)
    assert max(abs(s["normalized_weight"]-native_weights[s["index"]]/native_total) for s in samples)<1e-12
    all_values=[]
    for action in target["actions"]:
        value=math.fsum(s["weight"]*next(a["value"] for a in s["actions"] if a["move"]==action["uci"]) for s in samples)
        assert abs(value-action["q"])<1e-9
        all_values.append(dict(move=action["uci"],probability=action["probability"],value=value))
    policy_value=math.fsum(a["probability"]*a["value"] for a in all_values)
    assert abs(policy_value-target["root_value"])<1e-9
    rows=[]
    for sample in samples:
        first=next(a for a in sample["actions"] if a["move"]==chosen["uci"])
        second=next(a for a in sample["actions"] if a["move"]==alternate["uci"])
        difference=first["value"]-second["value"]
        rows.append(dict(index=sample["index"],weight=sample["normalized_weight"],actual=sample["index"]==actual,
            chosen_value=first["value"],alternate_value=second["value"],difference=difference,
            contribution=sample["normalized_weight"]*difference,
            chosen_frontier=first["frontier"],alternate_frontier=second["frontier"]))
    gap=math.fsum(r["contribution"] for r in rows)
    assert gap>0 and abs(gap-(chosen["q"]-alternate["q"]))<1e-9
    high=max(rows,key=lambda r:r["difference"]);low=min(rows,key=lambda r:r["difference"])
    sensitivity=None
    if low["difference"]<0:
        mass=gap/(high["difference"]-low["difference"])
        assert mass<=high["weight"] and mass<=1-low["weight"]
        altered=[r["weight"]-mass if r["index"]==high["index"] else r["weight"]+mass if r["index"]==low["index"] else r["weight"] for r in rows]
        assert abs(math.fsum(altered)-1)<1e-12 and min(altered)>=0
        assert abs(math.fsum(w*r["difference"] for w,r in zip(altered,rows)))<1e-12
        sensitivity=dict(minimum_total_variation_to_tie=mass,donor_index=high["index"],recipient_index=low["index"],
            difference_range=high["difference"]-low["difference"],construction_weights=altered,
            proof="An amount TV of removed/added probability can reduce the expectation by at most TV*(max difference-min difference). This feasible two-state transfer attains that bound with values/continuations fixed.")
    elif len(rows)==1:
        sensitivity=dict(minimum_total_variation_to_tie=None,reason="One supported world with positive action difference; reweighting this support cannot change the rank.")
    else:raise AssertionError("Unimplemented sensitivity case; do not silently generalize the two-state proof")
    frontiers={}
    for name,uci in [("chosen",chosen["uci"]),("alternate",alternate["uci"])]:
        branches=[(s["normalized_weight"],next(a for a in s["actions"] if a["move"]==uci)) for s in samples]
        frontiers[name]=dict(move=uci,root_response_frontier_worlds=sum(a["frontier"] for _,a in branches),
            root_response_frontier_probability=math.fsum(w for w,a in branches if a["frontier"]),
            exported_reply_edges=sum(len(a["replies"]) for _,a in branches),
            exported_reply_frontier_edges=sum(r["frontier"] for _,a in branches for r in a["replies"]),
            policy_probability_cut_by_two_plies=math.fsum(w*(1 if a["frontier"] else math.fsum(r["probability"] for r in a["replies"] if r["frontier"])) for w,a in branches))
    return dict(role=role,game=receipt["game"],root_ply=receipt["root_ply"],worlds=len(rows),raw_chance_mass=original_mass,
        chosen=chosen["uci"],alternate=alternate["uci"],chosen_value=chosen["q"],alternate_value=alternate["q"],
        gap=gap,root_only_deviation_gap=max(a["value"] for a in all_values)-policy_value,
        final_root_advantages=[dict(move=a["move"],advantage=a["value"]-policy_value) for a in all_values],
        positive_worlds=sum(r["difference"]>0 for r in rows),negative_worlds=sum(r["difference"]<0 for r in rows),
        positive_contributions=math.fsum(r["contribution"] for r in rows if r["contribution"]>0),
        negative_contributions=math.fsum(r["contribution"] for r in rows if r["contribution"]<0),
        actual_world=next(r for r in rows if r["actual"]),per_world=rows,sensitivity=sensitivity,
        sufficient_opposed_expected_value_error_to_tie=gap/2,frontiers=frontiers,
        source_hashes={str(p):sha(p) for p in [folder/"population.json",folder/"targets.jsonl",PREVIOUS/"pair-review.json"]})


def main():
    OUT.mkdir(exist_ok=False)
    assert read(PREVIOUS/"pair-review.json")["passed"]
    result=dict(at=datetime.now(timezone.utc).isoformat(),source_sha256=sha(__file__),analysis_type="Post-hoc arithmetic on saved417outputs, not a preregistered strength experiment.",
        cases=[case(role) for role in ["loss","control"]],
        antecedents=["054same-tree tradeoffs already exist; settling screen stays closed","055historical Stockfish context sensitivity is not a measured current error bar","213root-only value gaps are not whole-tree/whole-game best-response gaps;203mixingpilot remains closed","237/238/249learned-value/student quality failures remain closed","417/418correctness and reach findings unchanged"],
        limits=["Same saved tree and both continuation policies throughout; no new native engine, replay, sample, model, fit or game.","Values are approximate solver utilities, not calibrated win probabilities, Elo or definitive true-position values.","Local one-decision deviation gap is not exploitability/Nash convergence or a global best response.","Frozen-value sensitivity changes hypothetical chance weights or expected values analytically; an actual re-solve changes continuations and can behave differently.","Frontier counts describe exported first two plies only. They do not prove an evaluation error, inferior compute allocation or the outcome of extra search.","No new raw data, GPU, candidate ZIP/version, production source/default/service or website deployment."])
    save(OUT/"result.json",result)
    print(json.dumps({c["role"]:{k:c[k] for k in ["worlds","chosen","alternate","gap","actual_world","sensitivity","frontiers"]} for c in result["cases"]}))


if __name__=="__main__":main()
