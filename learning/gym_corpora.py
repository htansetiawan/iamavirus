"""Cut the gym's decision corpora from labelled arena replays.

    python -m learning.gym_corpora --labels data/reports/taxonomy-all-teams.json --raw data/raw --out data/gym --per-corpus 300 --seed 1

Writes three seat files in the benchmark harness format (`id side result
reason opponent moves...`, moves up to and including the decision; result and
reason are synthetic so that `tools/benchmark_corpus.cc` evaluates exactly the
decision ply — they are harness plumbing, never outcome labels):

  strike-seats.txt   a top-six side's move that created a king threat the victim
                     could not see (tag king_threat_unseen), not the game's final move
  route-seats.txt    the first move of a top-six side's 2+-move maneuver through
                     squares the opponent never saw that ended in a capture
  giveaway-seats.txt our own move tagged sacrifice without a king hunt (any version)

The harness then reports, at those plies, whether the engine's choice matches
the real move, creates an unseen king threat, or leaves 3+ points en prise.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import random

import chess

TEAM_ID = "a2c35173659545c99752376a70418438"
TOP = ["Greek Gift", "Knight Vision", "Decent Chess Bot", "Strongly Invisible", "duck", "Instructors"]


def seat_line(r: dict, side: int, moves: list, label: str) -> str:
    opp = (r["black"] if side == 0 else r["white"]).replace(" ", "_")
    result = "0-1" if side == 0 else "1-0"  # synthetic: a loss for the seat, so the last own ply is evaluated
    return f"{r['id']} {'w' if side == 0 else 'b'} {result} King_capturable {label}:{opp} " + " ".join(moves)


def route_start(frames, k: int, side: int) -> int | None:
    """Frame index of the first unseen arrival in the chain that ends with the capture at frame k."""
    view_key = "black" if side == 0 else "white"  # the opponent's view
    cur = chess.parse_square(frames[k]["move"][:2])
    start = None
    j = k - 1
    while j >= 1:
        g = frames[j]
        if g["move"] and ((g["ply"] % 2 == 1) == (side == 0)) and chess.parse_square(g["move"][2:4]) == cur:
            if g[view_key][cur] == "?":
                start = j
                cur = chess.parse_square(g["move"][:2])
            else:
                break
        j -= 1
    return start


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--labels", default="data/reports/taxonomy-all-teams.json")
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/gym")
    ap.add_argument("--per-corpus", type=int, default=300)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    games = json.load(open(args.labels))["games"]
    strike, route, giveaway = [], [], []
    for g in games:
        for side_name, side in (("white", 0), ("black", 1)):
            team = g[side_name]
            for i, m in enumerate(g["moves"]):
                if m["side"] != side:
                    continue
                if team in TOP and "king_threat_unseen" in m["tags"] and "king_capture" not in m["tags"] and m["ply"] < g["plies"]:
                    strike.append((g["id"], side, m["ply"], team))
                if team in TOP and "fog_route" in m["tags"] and "capture" in m["tags"]:
                    route.append((g["id"], side, m["ply"], team))
                if (g["id"], side) and team == "IAmAVirus" and "sacrifice" in m["tags"] and "king_hunt_sacrifice" not in m["tags"]:
                    giveaway.append((g["id"], side, m["ply"], team))
    print(f"candidates: strikes {len(strike)}, routes {len(route)}, giveaways {len(giveaway)}")

    def balanced_sample(items, n):
        by = collections.defaultdict(list)
        for it in items:
            by[it[3]].append(it)
        out = []
        per = max(1, n // max(1, len(by)))
        for team, lst in by.items():
            rng.shuffle(lst)
            out.extend(lst[:per])
        rng.shuffle(out)
        return out[:n]

    os.makedirs(args.out, exist_ok=True)
    counts = collections.Counter()
    for name, items, kind in (("strike", strike, "strike"), ("route", route, "route"), ("giveaway", giveaway, "giveaway")):
        chosen = balanced_sample(items, args.per_corpus * (2 if kind == "route" else 1))
        lines = []
        for gid, side, ply, team in chosen:
            path = os.path.join(args.raw, "games", gid, "replay.json")
            try:
                r = json.load(open(path))
            except Exception:
                continue
            frames = r["frames"]
            k = next((i for i, f in enumerate(frames) if f["ply"] == ply), None)
            if k is None or not frames[k]["move"]:
                continue
            if kind == "route":
                start = route_start(frames, k, side)
                if start is None or k - start < 2:
                    continue  # need a maneuver of at least two unseen moves before the capture
                k = start
            moves = [frames[j]["move"] for j in range(1, k + 1)]
            if any(mv is None for mv in moves):
                continue
            lines.append(seat_line(r, side, moves, f"{kind}-{team.replace(' ', '_')}"))
            counts[kind] += 1
            if counts[kind] >= args.per_corpus:
                break
        open(os.path.join(args.out, f"{name}-seats.txt"), "w").write("\n".join(lines) + "\n")
        print(f"wrote {name}-seats.txt: {len(lines)} seats")


if __name__ == "__main__":
    main()
