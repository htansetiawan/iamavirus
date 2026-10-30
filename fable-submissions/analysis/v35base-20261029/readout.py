"""Read-out of the v35-base lanes (chatroom 182 addendum): piece guard off: the true world forced into the sampled
belief at a fixed share (MIST_ORACLE_SHARE), against the frozen v35. Scores by matchup and
colour with pair bootstraps, clocks, forfeits, the truth's natural share on every decision,
and the proof that the forced share applied on every decision of the oracle side.
    .venv/bin/python fable-submissions/analysis/v35base-20261029/readout.py [--json OUT] [--smoke]
"""
import json
import random
import re
import statistics as st
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MATCHUPS = {"natural-v35base": 0.0, "share20-v35base": 0.2, "natural-v23": 0.0}
SMOKE = {"smoke-share20": 0.2}
LINE = re.compile(r"mist: oracle v=\d+ \|P\|=(\d+) natural=([0-9.]+) (?:forced=([0-9.]+)|observed) \((.*?)\)")


def rows(names):
    out = []
    for line in open(ROOT / "data/arena_local/games.jsonl"):
        d = json.loads(line)
        if d.get("matchup") in names:
            out.append(d)
    return out


def oracle_check(r, share):
    """From the replay's stderr excerpt: oracle lines, the truth's natural share, forced share."""
    rep = json.load(open(ROOT / r["replay"]))
    side = r["a_colour"]  # a = the oracle side in every matchup
    pd = rep.get("privateDiagnostics", {})
    txt = pd.get(side, "")
    other = pd.get("black" if side == "white" else "white", "")
    lines = LINE.findall(txt)
    dec = re.findall(r"mist: n=\d+ \|P\|=", txt)
    forced = [float(l[2]) for l in lines if l[2]]
    return {"oracle_lines": len(lines), "decisions_seen": len(dec),
            "in_p": sum(1 for l in lines if l[3] == "truth in P"),
            "placed": sum(1 for l in lines if l[3] == "truth placed"),
            "lost": sum(1 for l in lines if l[3] == "truth lost"),
            "kept": len(re.findall(r"belief kept", txt)),
            "forced_off": sum(1 for f in forced if abs(f - share) > 1e-3),
            "naturals": [float(l[1]) for l in lines],
            "excerpt_full": len(txt) < 16384,
            "other_oracle_lines": len(re.findall(r"mist: oracle", other)),
            "piece_guard_lines": len(re.findall(r"mist: piece guard", txt))}


def pair_bootstrap(rr, n=2000, seed=1):
    pairs = {}
    for r in rr:
        pairs.setdefault(r["pair"], []).append(r["a_score"])
    means = [sum(v) / len(v) for v in pairs.values()]
    rng = random.Random(seed)
    boots = sorted(st.mean(rng.choices(means, k=len(means))) for _ in range(n))
    return [round(boots[int(0.025 * n)], 3), round(boots[int(0.975 * n) - 1], 3)], sum(1 for v in pairs.values() if len(v) == 2)


def summary(rr, share):
    d = {"games": len(rr), "points": sum(r["a_score"] for r in rr)}
    d["wdl"] = [sum(1 for r in rr if r["a_score"] == x) for x in (1.0, 0.5, 0.0)]
    for col in ("white", "black"):
        c = [r for r in rr if r["a_colour"] == col]
        d[col] = {"games": len(c), "points": sum(r["a_score"] for r in c),
                  "wdl": [sum(1 for r in c if r["a_score"] == x) for x in (1.0, 0.5, 0.0)]}
    d["score"] = round(d["points"] / len(rr), 3) if rr else None
    d["reasons"] = dict(Counter(r["reason"] for r in rr))
    d["forfeits"] = [r["replay"] for r in rr if any(k in r["reason"].lower() for k in ("time", "forfeit", "clock"))]
    ac = [r["clocks"][0 if r["a_colour"] == "white" else 1] for r in rr]
    oc = [r["clocks"][1 if r["a_colour"] == "white" else 0] for r in rr]
    if rr:
        d["end_clock"] = {"oracle_min": round(min(ac), 1), "oracle_median": round(st.median(ac), 1),
                          "v35_min": round(min(oc), 1), "v35_median": round(st.median(oc), 1)}
        d["plies"] = {"wins": sorted(r["plies"] for r in rr if r["a_score"] == 1.0),
                      "losses": sorted(r["plies"] for r in rr if r["a_score"] == 0.0)}
        d["pair_bootstrap_score_95"], d["complete_pairs"] = pair_bootstrap(rr)
    checks = [oracle_check(r, share) for r in rr]
    nat = [x for c in checks for x in c["naturals"]]
    d["oracle_applied"] = {"games": len(checks),
                           "oracle_lines": sum(c["oracle_lines"] for c in checks),
                           "decisions_seen": sum(c["decisions_seen"] for c in checks),
                           "games_every_decision_covered": sum(1 for c in checks if c["oracle_lines"] >= c["decisions_seen"]),
                           "truth_in_p": sum(c["in_p"] for c in checks),
                           "truth_placed": sum(c["placed"] for c in checks),
                           "truth_lost": sum(c["lost"] for c in checks),
                           "failures_belief_kept": sum(c["kept"] for c in checks),
                           "forced_share_off": sum(c["forced_off"] for c in checks),
                           "v35_with_oracle_lines": sum(1 for c in checks if c["other_oracle_lines"]),
                           "piece_guard_lines": sum(c["piece_guard_lines"] for c in checks),
                           "excerpts_truncated": sum(1 for c in checks if not c["excerpt_full"])}
    if nat:
        d["natural_share"] = {"decisions": len(nat), "median": round(st.median(nat), 5), "mean": round(st.mean(nat), 5),
                              "below_0.001": round(sum(1 for x in nat if x < 0.001) / len(nat), 3),
                              "below_0.01": round(sum(1 for x in nat if x < 0.01) / len(nat), 3),
                              "at_least_0.2": round(sum(1 for x in nat if x >= 0.2) / len(nat), 3),
                              "at_least_0.5": round(sum(1 for x in nat if x >= 0.5) / len(nat), 3)}
    return d


def main():
    names = SMOKE if "--smoke" in sys.argv else MATCHUPS
    out = {"rows": 0, "attempts": {}}
    allrows = rows(names)
    out["rows"] = len(allrows)
    out["attempts"] = dict(Counter(r["attempt"] for r in allrows))
    for name, share in names.items():
        rr = [r for r in allrows if r["matchup"] == name and r["attempt"] == "ok"]
        out[name] = summary(rr, share)
    text = json.dumps(out, indent=1)
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(text)
    for name in names:
        d = out[name]
        if d["games"]:
            print(f"{name}: {d['games']} games {'-'.join(map(str, d['wdl']))} score {d['score']} "
                  f"W {d['white']['points']}/{d['white']['games']} B {d['black']['points']}/{d['black']['games']} "
                  f"pairs95 {d.get('pair_bootstrap_score_95')} natural median {d.get('natural_share', {}).get('median')} "
                  f"lost {d['oracle_applied']['truth_lost']} off {d['oracle_applied']['forced_share_off']} leak {d['oracle_applied']['v35_with_oracle_lines']}")
        else:
            print(f"{name}: no games")


if __name__ == "__main__":
    main()
