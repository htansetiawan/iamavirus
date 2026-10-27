"""The fresh confirmation set for the v36 decision contract (gate 2), built once.

Selection, frozen before the data existed (chatroom 164, decision contract):
  window   IAmAVirus v35 games created strictly after --window-start and before
           --window-end (the ledger records creation time; completion time is not
           recorded, so creation is the window's clock and is said so here)
  cohort   the fixed six plus Crimson Fog (--cohort), any opponent version
  exclude  every game id in the four earlier sets (--exclude-split split.json)
           and every game whose exact move trajectory (moves_sha256 in
           accepted.jsonl) occurs in those sets; within the window the earliest
           (created, id) per trajectory is kept
  failure  the first clean rook/minor loss in each lost game, lead >= -3
           before, recorded move not fatal, truth available (build_split.decisions)
  controls ordinary win/draw decisions and ordinary pre-event decisions of
           losses: from decision 6, spaced >= 4, at most 3 a game, every third
           loss (the same deterministic subsample), capped at --controls each
Writes fresh-failures.json, fresh-control.json, fresh-control-loss.json and
fresh-manifest.json (ids, games, coverage, exclusions, code hashes) to --out.
"""
import argparse, hashlib, json, os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_split import decisions, TOP6  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw"); ap.add_argument("out")
    ap.add_argument("--version", type=int, default=35)
    ap.add_argument("--window-start", default="2026-10-26T10:12:00")
    ap.add_argument("--window-end", default="2026-10-27T11:30:00")
    ap.add_argument("--cohort", default=",".join(TOP6 + ["Crimson Fog"]))
    ap.add_argument("--exclude-split", default=os.path.join(HERE, "split.json"))
    ap.add_argument("--controls", type=int, default=100)
    a = ap.parse_args()
    cohort = a.cohort.split(",")
    split = json.load(open(a.exclude_split))
    old_games = set()
    for name in ("calib", "oos", "control", "control-loss"):
        old_games |= {i.split(":")[0] for i in split[name]["ids"]}
    rows = [json.loads(l) for l in open(os.path.join(a.raw, "accepted.jsonl")) if l.strip()]
    by_id = {r["id"]: r for r in rows}
    old_traj = {by_id[g]["moves_sha256"] for g in old_games if g in by_id and by_id[g].get("moves_sha256")}
    games, excluded = [], {"id": 0, "trajectory_old": 0, "trajectory_window": 0, "no_created": 0}
    in_window = 0   # cohort games in the window before any exclusion
    for r in rows:
        for side, other in (("white", "black"), ("black", "white")):
            if r.get(side) != "IAmAVirus" or r.get(side + "Version") != a.version or r.get(other) not in cohort:
                continue
            created = r.get("createdAt") or ""
            if not created:
                excluded["no_created"] += 1; continue
            if not (a.window_start < created[:19] < a.window_end):
                continue
            in_window += 1
            if r["id"] in old_games:
                excluded["id"] += 1; continue
            if r.get("moves_sha256") in old_traj:
                excluded["trajectory_old"] += 1; continue
            s = {"1-0": 1, "0-1": 0}.get(r["result"], 0.5); s = s if side == "white" else 1 - s
            games.append((created, r["id"], side, r[other], r.get(other + "Version"), s, r.get("moves_sha256")))
    games.sort()
    seen = set(); kept = []
    for g in games:
        if g[6] in seen:
            excluded["trajectory_window"] += 1; continue
        seen.add(g[6]); kept.append(g)
    suites = {"fresh-failures": [], "fresh-control": [], "fresh-control-loss": []}
    missing = 0
    for created, gid, side, opp, oppv, s, _ in kept:
        try:
            if s == 0:
                for e in decisions(a.raw, gid, side, "piece"):
                    e.update(opponent=opp, opponent_version=oppv, created=created, version=a.version); suites["fresh-failures"].append(e)
                if len(suites["fresh-control-loss"]) < a.controls and int(gid[-1], 36) % 3 == 0:
                    for e in decisions(a.raw, gid, side, "control-loss"):
                        e.update(opponent=opp, opponent_version=oppv, created=created, version=a.version); suites["fresh-control-loss"].append(e)
            elif len(suites["fresh-control"]) < a.controls:
                for e in decisions(a.raw, gid, side, "control"):
                    e.update(opponent=opp, opponent_version=oppv, created=created, version=a.version); suites["fresh-control"].append(e)
        except FileNotFoundError:
            missing += 1
    os.makedirs(a.out, exist_ok=True)
    manifest = {"built": datetime.datetime.now(datetime.timezone.utc).isoformat(), "window": [a.window_start, a.window_end],
                "window_clock": "createdAt (creation time; completion time is not recorded)", "cohort": cohort, "version": a.version,
                "games_in_window": in_window, "games_after_exclusion": len(games), "games_kept": len(kept), "excluded": excluded, "replay_missing": missing,
                "code_sha256": {f: hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest() for f in ("build_split.py", "build_fresh.py")},
                "sets": {}}
    for name, entries in suites.items():
        json.dump(entries, open(os.path.join(a.out, name + ".json"), "w"))
        gids = sorted({e["game"] for e in entries})
        manifest["sets"][name] = {"decisions": len(entries), "games": len(gids), "ids": [f"{e['game']}:{e['k']}" for e in entries],
                                  "by_opponent": {o: sum(1 for e in entries if e["opponent"] == o) for o in cohort},
                                  "by_opponent_version": {f"{e['opponent']} v{e['opponent_version']}": 0 for e in entries},
                                  "by_colour": {c: sum(1 for e in entries if e["side"] == c) for c in ("white", "black")}}
        for e in entries:
            manifest["sets"][name]["by_opponent_version"][f"{e['opponent']} v{e['opponent_version']}"] += 1
        print(f"{name}: {len(entries)} decisions from {len(gids)} games; by opponent {manifest['sets'][name]['by_opponent']}; by colour {manifest['sets'][name]['by_colour']}")
    print(f"window games {in_window}, after exclusion {len(games)}, kept {len(kept)}, excluded {excluded}, replay missing {missing}")
    json.dump(manifest, open(os.path.join(a.out, "fresh-manifest.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
