#!/usr/bin/env python3
"""lambda for the v20 piece term, fitted as chatroom 159 says: our score against the fixed top
six after the first clean rook/minor loss, relative to the queen's 0.9.

    .venv/bin/python fable-submissions/analysis/v20-material-guard-20261027/fit_lambda.py data/raw

Over our v35 games against the fixed top six created up to 2026-10-19 23:59:59 UTC (the
calibration period), the first material event of ours: "queen" (our queen disappears and theirs
does not within two plies), "piece" (a rook, bishop or knight of ours disappears, the queen does
not, and our material falls by 3+ net within two plies), or "none". Score per class.
cost(e) = score(none) - score(e); lambda_piece = 0.9 * cost(piece) / cost(queen).
"""
import json, os, sys
sys.path.insert(0, os.path.expanduser("~/git/fowsearch-c/tools"))
from suite_build import material  # noqa: E402

TOP6 = {"Greek Gift", "Knight Vision", "Strongly Invisible", "Decent Chess Bot", "duck", "Instructors"}
END = sys.argv[2] if len(sys.argv) > 2 else "2026-10-19T23:59:59"


def counts(b64, white):
    c = {"q": 0, "r": 0, "b": 0, "n": 0}
    for ch in b64:
        if ch != "-" and ch.isupper() == white and ch.lower() in c:
            c[ch.lower()] += 1
    return c


def first_event(frames, w):
    for p in range(len(frames) - 2):
        if (p % 2 == 0) != w:
            continue
        c0, c2 = counts(frames[p]["board"], w), counts(frames[p + 2]["board"], w)
        t0, t2 = counts(frames[p]["board"], not w), counts(frames[p + 2]["board"], not w)
        if c2["q"] < c0["q"]:
            return "queen" if t2["q"] >= t0["q"] else "queen trade"
        swing = (material(frames[p]["board"], w) - material(frames[p]["board"], not w)) - (material(frames[p + 2]["board"], w) - material(frames[p + 2]["board"], not w))
        if any(c2[x] < c0[x] for x in "rbn") and swing >= 3:
            return "piece"
    return "none"


raw = sys.argv[1]
score = {}
for line in open(os.path.join(raw, "accepted.jsonl")):
    r = json.loads(line)
    for side, other in (("white", "black"), ("black", "white")):
        if r.get(side) == "IAmAVirus" and r.get(side + "Version") == 35 and r.get(other) in TOP6 and (r.get("createdAt") or "") <= END:
            s = {"1-0": 1, "0-1": 0}.get(r["result"], 0.5); s = s if side == "white" else 1 - s
            try:
                f = json.load(open(os.path.join(raw, "games", r["id"], "replay.json")))["frames"]
            except FileNotFoundError:
                continue
            score.setdefault(first_event(f, side == "white"), []).append(s)
out = {k: {"games": len(v), "score": round(sum(v) / len(v), 3)} for k, v in score.items()}
base = out["none"]["score"]
cost = {k: round(base - v["score"], 3) for k, v in out.items()}
lam = round(0.9 * cost["piece"] / cost["queen"], 3) if cost.get("queen") else None
out["cost"] = cost; out["lambda_piece"] = lam; out["period_end"] = END
print(json.dumps(out, indent=1))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lambda-fit.json"), "w"), indent=1)
