"""Read-out of the oracle decomposition (chatroom 178): scores by matchup and colour, pair
bootstraps, clocks, and the proof that the oracle applied on every decision of its side.
    .venv/bin/python fable-submissions/analysis/oracle-20261028/readout.py [--json OUT]
"""
import collections
import json
import random
import re
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MATCHUPS = ("oracle-vs-control", "oracle-vs-v35")


def rows():
    out = []
    for line in open(ROOT / "data/arena_local/games.jsonl"):
        d = json.loads(line)
        if d.get("matchup") in MATCHUPS:
            out.append(d)
    return out


def oracle_check(r):
    """From the replay's stderr excerpt: oracle lines, decisions at |P|=1, failures."""
    rep = json.load(open(ROOT / r["replay"]))
    side = r["a_colour"]  # a = the oracle side in both matchups
    txt = rep.get("privateDiagnostics", {}).get(side, "")
    lines = re.findall(r"mist: oracle v=\d+ \|P\| (\d+) -> (\d+) \((.*?)\)", txt)
    dec = re.findall(r"mist: n=\d+ \|P\|=(\d+) samples=", txt)
    other = rep.get("privateDiagnostics", {}).get("black" if side == "white" else "white", "")
    return {"oracle_lines": len(lines), "in_p": sum(1 for l in lines if l[2] == "truth in P"),
            "placed": sum(1 for l in lines if l[2] == "truth placed"),
            "kept": len(re.findall(r"belief kept", txt)),
            "decisions_seen": len(dec), "decisions_single": sum(1 for d in dec if d == "1"),
            "excerpt_full": len(txt) < 16384, "control_oracle_lines": len(re.findall(r"mist: oracle", other))}


def main():
    rs = rows()
    report = {"rows": len(rs), "attempts": dict(collections.Counter(r["attempt"] for r in rs))}
    for m in MATCHUPS:
        rr = [r for r in rs if r["matchup"] == m and r["attempt"] == "ok"]
        if not rr:
            continue
        d = {"games": len(rr), "points": sum(r["a_score"] for r in rr)}
        d["wdl"] = [sum(1 for r in rr if r["a_score"] == s) for s in (1.0, 0.5, 0.0)]
        for col in ("white", "black"):
            c = [r for r in rr if r["a_colour"] == col]
            d[col] = {"games": len(c), "points": sum(r["a_score"] for r in c),
                      "wdl": [sum(1 for r in c if r["a_score"] == s) for s in (1.0, 0.5, 0.0)]}
        d["reasons"] = dict(collections.Counter(r["reason"] for r in rr))
        d["forfeits"] = [(r["pair"], r["a_colour"], r["result"]) for r in rr if r["reason"] == "Time forfeit"]
        ac = [r["clocks"][0 if r["a_colour"] == "white" else 1] for r in rr]
        bc = [r["clocks"][1 if r["a_colour"] == "white" else 0] for r in rr]
        d["end_clock"] = {"oracle_min": round(min(ac), 1), "oracle_median": round(st.median(ac), 1),
                          "other_min": round(min(bc), 1), "other_median": round(st.median(bc), 1)}
        d["plies"] = {"wins": sorted(r["plies"] for r in rr if r["a_score"] == 1),
                      "losses": sorted(r["plies"] for r in rr if r["a_score"] == 0)}
        pairs = collections.defaultdict(float)
        for r in rr:
            pairs[r["pair"]] += r["a_score"]
        complete = [p for p in pairs if sum(1 for r in rr if r["pair"] == p) == 2]
        ps = [pairs[p] for p in complete]
        if ps:
            random.seed(1)
            bs = sorted(sum(random.choice(ps) for _ in ps) / (2 * len(ps)) for _ in range(10000))
            d["pair_bootstrap_score_95"] = [round(bs[250], 3), round(bs[9750], 3)]
            d["complete_pairs"] = len(ps)
        checks = [oracle_check(r) for r in rr]
        d["oracle_applied"] = {"games": len(checks),
                               "every_decision_single": sum(1 for c in checks if c["decisions_seen"] == c["decisions_single"]),
                               "truth_placed_total": sum(c["placed"] for c in checks),
                               "failures_total": sum(c["kept"] for c in checks),
                               "control_with_oracle_lines": sum(1 for c in checks if c["control_oracle_lines"]),
                               "excerpts_truncated": sum(1 for c in checks if not c["excerpt_full"])}
        report[m] = d
    print(json.dumps(report, indent=1))
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
