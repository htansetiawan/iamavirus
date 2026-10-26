#!/usr/bin/env python3
"""Paired comparison of two suite_run result files for the v20 piece guard.

    python3 report.py BASELINE.json CANDIDATE.json [label]

For the loss sets: repeat rate of the recorded losing move, cp loss on the true board (mean,
median), fatal rate (king capturable after the chosen move, where a safe move existed), truth in
P, and how often the piece term vetoed the recorded move. For the control sets: how often the
piece term vetoed the move that was actually played, how often the chosen move changed, and the
cp loss with and without the term (a false veto costs centipawns on the true board).
"""
import json, statistics as st, sys


def load(p):
    d = json.load(open(p)); rs = d["results"] if isinstance(d, dict) else d
    return {r["id"]: r for r in rs if "error" not in r}


A, B = load(sys.argv[1]), load(sys.argv[2]); label = sys.argv[3] if len(sys.argv) > 3 else ""
ids = [i for i in A if i in B]
n = len(ids)
def rate(d, key): return sum(bool(d[i].get(key)) for i in ids) / max(1, n)
def cps(d): return [d[i]["cp_loss"] for i in ids if d[i].get("cp_loss") is not None]
cp_a, cp_b = cps(A), cps(B)
paired = [(A[i]["cp_loss"], B[i]["cp_loss"]) for i in ids if A[i].get("cp_loss") is not None and B[i].get("cp_loss") is not None]
better = sum(1 for a, b in paired if b < a - 100); worse = sum(1 for a, b in paired if b > a + 100)
safe = [i for i in ids if A[i].get("safe", True)]
fa = sum(bool(A[i].get("fatal")) for i in safe); fb = sum(bool(B[i].get("fatal")) for i in safe)
print(f"{label} n={n} paired decisions")
print(f"  repeat of the recorded move: A {rate(A,'repeat'):.3f}  B {rate(B,'repeat'):.3f}")
print(f"  changed move (A vs B chose differently): {sum(A[i]['move'] != B[i]['move'] for i in ids) / max(1,n):.3f}")
print(f"  cp loss on the true board: A mean {st.mean(cp_a):.0f} med {st.median(cp_a):.0f} | B mean {st.mean(cp_b):.0f} med {st.median(cp_b):.0f} | B better by 100+ in {better}, worse in {worse} of {len(paired)}")
print(f"  fatal (safe move existed): A {fa}/{len(safe)}  B {fb}/{len(safe)}")
print(f"  piece guard fired (any veto): A {rate(A,'pguard'):.3f}  B {rate(B,'pguard'):.3f};  vetoed the recorded move: B {rate(B,'pveto_played'):.3f}")
tl = [i for i in ids if "truth_lost" in A[i]]
if tl:
    print(f"  truth in P at the decision: {sum(not A[i]['truth_lost'] for i in tl)}/{len(tl)}")
