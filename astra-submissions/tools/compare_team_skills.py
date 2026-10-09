"""Descriptive, version-specific comparison on a common opponent/color panel.

Uses public replay truth only for retrospective labels. No policy or training
data is generated. Results characterize behavior, not private implementations.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import chess
from learning.move_taxonomy import fen, label_game, material

VERSIONS = {"Greek Gift": {16}, "Knight Vision": {29}, "Decent Chess Bot": {4},
            "Strongly Invisible": {35}, "duck": {5}, "Instructors": {4},
            "IAmAVirus": {20, 21}}
OPPONENTS = {"TA Baseline A": 5, "TA Baseline S": 3, "TA Baseline P": 5}
TAGS = ["king_threat", "king_threat_unseen", "queen_raid", "long_strike",
        "capture_unseen", "fog_route", "sacrifice", "walk_into_unseen",
        "vision_gain", "king_move", "queen_exposed_unseen"]


def score(replay, side):
    if replay["result"] == "1/2-1/2":
        return 0.5
    return float((replay["result"] == "1-0") == (side == "white"))


def inspect_game(replay, side):
    lab = label_game(replay)
    frames = replay["frames"]
    color = chess.WHITE if side == "white" else chess.BLACK
    side_index = 0 if side == "white" else 1
    other = "black" if side == "white" else "white"
    phases = collections.defaultdict(collections.Counter)
    events = []
    for move in lab["moves"]:
        if move["side"] != side_index:
            continue
        p = move["ply"]
        before, after = frames[p - 1], frames[p]
        b, a = chess.Board(fen(before["board"])), chess.Board(fen(after["board"]))
        king = b.king(not color)
        visible = 64 - before[side].count("?")
        saw_king = king is not None and before[side][king] != "?"
        tags = list(move["tags"])
        if "king_threat" in tags and not saw_king:
            tags.append("threat_to_previously_unseen_king")
        # A response failure includes forced losses. It does not prove the
        # opponent overlooked an available escape.
        if "king_threat" in tags and p + 1 < len(frames):
            ownking = a.king(color)
            if ownking is not None and not a.attackers(not color, ownking):
                tags.append("threat_with_reply")
                reply = chess.Board(fen(frames[p + 1]["board"]))
                enemyking = reply.king(not color)
                if enemyking is not None and reply.attackers(color, enemyking):
                    tags.append("threat_reply_failed")
        for phase in ("all", "opening" if p < 30 else "middle" if p < 70 else "late"):
            c = phases[phase]
            c["moves"] += 1
            c["visible_sum"] += visible
            c["king_visible"] += saw_king
            c.update(tags)
        if "king_threat_unseen" in tags:
            events.append({"ply": p, "move": move["move"], "tags": tags})
    # Full four-ply windows only; incomplete tails are not sustained leads.
    differences = [material(f["board"], side_index) - material(f["board"], 1 - side_index)
                   for f in frames]
    led = any(min(differences[k:k + 4]) >= 3 for k in range(len(differences) - 3))
    behind = any(max(differences[k:k + 4]) <= -3 for k in range(len(differences) - 3))
    return {"id": replay["id"], "team": replay[side], "version": replay[side + "Version"],
            "opponent": replay[other], "opponent_version": replay[other + "Version"],
            "side": side, "createdAt": replay["createdAt"], "score": score(replay, side),
            "plies": len(frames) - 1, "phases": dict(phases),
            "led_by3": led, "behind_by3": behind, "unseen_threat_examples": events,
            "replay_sha256": hashlib.sha256(json.dumps(replay, sort_keys=True).encode()).hexdigest()}


def summarize(rows):
    groups = collections.defaultdict(list)
    for row in rows:
        groups[row["opponent"], row["side"]].append(row)
    output = {"games": len(rows), "stratum_sizes": {f"{a}/{b}": len(v) for (a, b), v in groups.items()},
              "raw_wdl": [sum(r["score"] == s for r in rows) for s in (1.0, 0.5, 0.0)],
              "standardized_score": statistics.mean(statistics.mean(r["score"] for r in rs)
                                                    for rs in groups.values()), "phases": {}}
    for phase in ("all", "opening", "middle", "late"):
        strata = []
        for rs in groups.values():
            vals = collections.defaultdict(list)
            for r in rs:
                c = r["phases"].get(phase, {})
                n = c.get("moves", 0)
                if not n:
                    continue
                for tag in TAGS + ["threat_to_previously_unseen_king"]:
                    vals[tag].append(100 * c.get(tag, 0) / n)
                vals["visible_mean"].append(c["visible_sum"] / n)
                vals["king_visible_pct"].append(100 * c.get("king_visible", 0) / n)
            if vals:
                strata.append({k: statistics.mean(v) for k, v in vals.items()})
        output["phases"][phase] = {k: statistics.mean(s[k] for s in strata) for k in strata[0]} if strata else {}
    output["raw_conversion"] = {"led_by3_games": sum(r["led_by3"] for r in rows),
        "wins_after_lead3": sum(r["led_by3"] and r["score"] == 1 for r in rows),
        "behind_by3_games": sum(r["behind_by3"] for r in rows),
        "score_after_deficit3": sum(r["score"] for r in rows if r["behind_by3"]),
        "median_win_plies": statistics.median([r["plies"] for r in rows if r["score"] == 1])
                            if any(r["score"] == 1 for r in rows) else None}
    return output


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, default=ROOT / "data/raw/games")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--cutoff", default="2026-10-09T14:39:52.549508596+00:00")
    ap.add_argument("--per-stratum", type=int, default=20)
    args = ap.parse_args()
    buckets = collections.defaultdict(list)
    direct = collections.defaultdict(list)
    for p in args.raw.glob("*/listing.json"):
        try:
            r = json.loads(p.read_text())
        except (OSError, ValueError):
            continue  # a concurrent downloader may be writing the listing
        if r["createdAt"] > args.cutoff:
            continue
        for side, other in (("white", "black"), ("black", "white")):
            t = r[side]
            if r.get(side + "Version") not in VERSIONS.get(t, set()):
                continue
            if r.get(other + "Version") == OPPONENTS.get(r[other], -1):
                buckets[t, r[other], side].append((r["createdAt"], p.parent / "replay.json", side))
            if t == "Greek Gift" and r.get(other + "Version") in VERSIONS.get(r[other], set()):
                direct[r[other]].append((p.parent / "replay.json", side))
    games = []
    for key, group in sorted(buckets.items()):
        for _, path, side in sorted(group, reverse=True)[:args.per_stratum]:
            r = json.loads(path.read_text())
            games.append(inspect_game(r, side))
    by_team = {t: summarize([g for g in games if g["team"] == t]) for t in VERSIONS}
    head_to_head = {}
    for t, rows in direct.items():
        replays = [(json.loads(p.read_text()), side) for p, side in rows]
        scores = [score(r, side) for r, side in replays]
        head_to_head[t] = {"games": len(scores), "wdl": [scores.count(s) for s in (1., .5, 0.)],
                           "score": statistics.mean(scores),
                           "game_ids": [r["id"] for r, _ in replays]}
        if t in ("duck", "Instructors", "Knight Vision"):
            head_to_head[t]["same_games_skills"] = {
                "Greek Gift": summarize([inspect_game(r, side) for r, side in replays]),
                t: summarize([inspect_game(r, "black" if side == "white" else "white")
                              for r, side in replays])}
    result = {"created_at": datetime.now(timezone.utc).isoformat(), "cutoff": args.cutoff,
              "versions": {k: sorted(v) for k, v in VERSIONS.items()}, "opponents": OPPONENTS,
              "per_stratum_cap": args.per_stratum, "teams": by_team,
              "greek_current_version_head_to_head_in_local_corpus": head_to_head, "games": games,
              "taxonomy_source_sha256": hashlib.sha256((ROOT / "learning/move_taxonomy.py").read_bytes()).hexdigest(),
              "method": "Newest up to 20 games in each team/opponent/color stratum. Per-game rates averaged within stratum, then equal weight per stratum. Phases condition on games reaching that phase. Direct head-to-head uses all available current-version games through cutoff.",
              "limits": ["Descriptive, not causal or a proof of private algorithms.",
                         "Availability-limited local corpus, not a census of the arena.",
                         "Current versions and opponent/color matched; date, openings and board difficulty still differ.",
                         "Two-ply sacrifice tag also includes deliberate investments; not always a blunder.",
                         "Shared taxonomy uses board snapshots: en passant captures are not fully labeled.",
                         "Raw conversion counts are not standardized; small samples and selection effects remain."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"games": len(games), "output": str(args.output),
                      "head_to_head": {k: {a: b for a, b in v.items() if a != "game_ids"} for k, v in head_to_head.items()}}))


if __name__ == "__main__":
    main()
