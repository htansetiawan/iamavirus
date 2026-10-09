"""How much say the network had in a matchup's decisions, from the local arena replays.

    python -m learning.decision_stats v18rl120p100-vs-v17 v18rl120-vs-v17 [--builds data/arena_local/builds]

Reads side A's decision lines from data/arena_local/builds/<matchup>-p*-{a,b}-white.json
(the bot's stderr kept in privateDiagnostics; the referee keeps the tail, so this is a
sample of each game's later decisions) and reports, over hybrid decisions that were not
book moves: how often the chosen move was the policy's top move, and the mean policy
probability of the chosen move. Without the policy prior v17's engine played the
network's favourite on 22% of decisions; with FOW_POLICY_PRIOR=100, 50% (note 019).
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import statistics
from pathlib import Path

LINE = re.compile(r" cp=([0-9.eE+-]+).* cands=(\S*) move=(\S+)")


def matchup_stats(matchup: str, builds: Path) -> dict:
    decisions = top1 = 0
    chosen = []
    for path in glob.glob(str(builds / f"{matchup}-p*-*-white.json")):
        side = "white" if path.endswith("-a-white.json") else "black"
        replay = json.loads(Path(path).read_text())
        text = (replay.get("privateDiagnostics") or {}).get(side) or ""
        for line in text.splitlines():
            if "mode=hybrid" not in line or "book=1" in line:
                continue
            m = LINE.search(line)
            if not m or not m.group(2):
                continue
            first = m.group(2).split(",")[0].split(":")[0]
            decisions += 1
            top1 += first == m.group(3)
            chosen.append(float(m.group(1)))
    return {"matchup": matchup, "decisions": decisions,
            "policy_top1_share": round(top1 / decisions, 3) if decisions else None,
            "chosen_policy_mean": round(statistics.mean(chosen), 3) if chosen else None}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("matchups", nargs="+")
    ap.add_argument("--builds", type=Path, default=Path("data/arena_local/builds"))
    args = ap.parse_args(argv)
    for matchup in args.matchups:
        print(json.dumps(matchup_stats(matchup, args.builds)))


if __name__ == "__main__":
    main()
