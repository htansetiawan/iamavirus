"""Daily arena report: corpus growth, our results, and the move taxonomy.

    python -m learning.daily_report [--raw data/raw] [--out data/reports/daily] [--window-days 3]

Reads the ingested replays (learning.ingest) and the latest leaderboard
snapshot, and writes data/reports/daily/<date>.md, <date>.json and latest.md:

  1. corpus: games held, games created in the last 24 hours, the leaderboard;
  2. our results over 24 hours and 7 days by opponent, by our version, and
     against the teams rated above us by their version (a new opponent
     version shows up here first);
  3. the move taxonomy per team over the window (learning.move_taxonomy),
     with the change since the previous report;
  4. our games against the teams above us: our tags against theirs, and how
     our losses ended.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import glob
import json
import os

from learning import move_taxonomy as mt
from learning.top6_report import latest_leaderboard

US = "IAmAVirus"
TAGS = ["capture_unseen", "victim_walked_in", "fog_route", "king_threat", "king_threat_unseen",
        "walk_into_unseen", "queen_exposed_unseen", "sacrifice", "king_leaves_home", "king_move", "vision_gain"]
TA = ["TA Baseline S", "TA Baseline A", "TA Baseline P"]


def iso(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S")


def accepted_rows(raw: str) -> list[dict]:
    rows = {}
    with open(os.path.join(raw, "accepted.jsonl")) as f:
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            rows[r["id"]] = r
    return list(rows.values())


def our_score(r: dict) -> float | None:
    s = {"1-0": 1.0, "0-1": 0.0, "1/2-1/2": 0.5}.get(r.get("result"))
    if s is None:
        return None
    return s if r.get("white") == US else 1.0 - s


def record(rows: list[dict]) -> str:
    w = sum(our_score(r) == 1 for r in rows)
    d = sum(our_score(r) == 0.5 for r in rows)
    n = len(rows)
    return f"{w}-{d}-{n - w - d}" + (f" ({(w + d / 2) / n:.2f})" if n else "")


def results_table(ours: list[dict], key, title: str) -> list[str]:
    groups = collections.defaultdict(list)
    for r in ours:
        groups[key(r)].append(r)
    out = [f"| {title} | games | W-D-L (score) |", "|---|---|---|"]
    for k, rs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        out.append(f"| {k} | {len(rs)} | {record(rs)} |")
    return out


def opponent(r: dict) -> str:
    return r["black"] if r["white"] == US else r["white"]


def versions(r: dict) -> tuple:
    if r["white"] == US:
        return r.get("whiteVersion"), r.get("blackVersion")
    return r.get("blackVersion"), r.get("whiteVersion")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/reports/daily")
    ap.add_argument("--window-days", type=float, default=3)
    args = ap.parse_args(argv)
    now = dt.datetime.now(dt.timezone.utc)
    day, week, window = iso(now - dt.timedelta(days=1)), iso(now - dt.timedelta(days=7)), iso(now - dt.timedelta(days=args.window_days))
    rows = accepted_rows(args.raw)
    dated = [r for r in rows if r.get("createdAt")]
    fetched_at, board = latest_leaderboard(args.raw)
    players = sorted((p for p in (board or [])), key=lambda p: -(p.get("rating") or 0))
    our_rating = next((p.get("rating") for p in players if p.get("name") == US), None)
    above = [p["name"] for p in players if our_rating and (p.get("rating") or 0) > our_rating]
    md = [f"# Arena daily report, {now.strftime('%Y-%m-%d %H:%M UTC')}", ""]

    # 1. corpus
    last_day = [r for r in dated if r["createdAt"] >= day]
    md += ["## Corpus", "",
           f"- games held: **{len(rows)}** ({len(dated)} dated); created in the last 24 hours: **{len(last_day)}** "
           f"(ours {sum(US in (r['white'], r['black']) for r in last_day)})",
           f"- newest game: {max((r['createdAt'] for r in dated), default='?')[:16]}; leaderboard fetched {(fetched_at or '?')[:16]}", "",
           "| rank | team | rating | active version | games |", "|---|---|---|---|---|"]
    for i, p in enumerate(players[:12], 1):
        name = f"**{p['name']}**" if p["name"] == US else p["name"]
        md.append(f"| {i} | {name} | {p.get('rating', 0):.0f} | {p.get('activeVersion')} | {p.get('games')} |")

    # 2. our results
    ours = [r for r in dated if US in (r["white"], r["black"]) and our_score(r) is not None]
    o_day = [r for r in ours if r["createdAt"] >= day]
    o_week = [r for r in ours if r["createdAt"] >= week]
    md += ["", "## Our results", "", f"Last 24 hours: **{record(o_day)}** over {len(o_day)} games; last 7 days: {record(o_week)} over {len(o_week)}.", ""]
    md += results_table(o_day, lambda r: f"v{versions(r)[0]}", "our version (24 h)") + [""]
    md += results_table(o_day, opponent, "opponent (24 h)") + [""]
    md += results_table([r for r in o_week if opponent(r) in above], lambda r: f"{opponent(r)} v{versions(r)[1]}",
                        "teams above us, by their version (7 days)")

    # 3. taxonomy by team over the window
    labelled = []
    for path in mt.game_paths(args.raw, window):
        try:
            r = json.load(open(path))
        except Exception:
            continue
        if r.get("frames") and len(r["frames"]) >= 3:
            labelled.append(mt.label_game(r))
    teams = above + [US] + [t for t in TA if t not in above]
    tax = {}
    for team in teams:
        agg = mt.aggregate(labelled, lambda g, t=team: "white" if g["white"] == t else ("black" if g["black"] == t else None))
        if agg["games"]:
            tax[team] = {k: round(agg[k], 2) for k in TAGS} | {"games": agg["games"]}
    previous = sorted(glob.glob(os.path.join(args.out, "*.json")))
    prev = json.load(open(previous[-1])) if previous else {}
    prev_tax = prev.get("taxonomy", {})
    md += ["", f"## Move taxonomy, last {args.window_days:g} days ({len(labelled)} games, all teams)", "",
           "Rates per 100 moves; in brackets the change since the previous report "
           f"({prev.get('generated', 'none')[:16]}).", "",
           "| team | games | " + " | ".join(TAGS) + " |", "|---" * (len(TAGS) + 2) + "|"]
    for team, t in tax.items():
        cells = []
        for k in TAGS:
            d = t[k] - prev_tax[team][k] if team in prev_tax else None
            cells.append(f"{t[k]:.1f}" + (f" ({d:+.1f})" if d is not None and abs(d) >= 0.05 else ""))
        name = f"**{team}**" if team == US else team
        md.append(f"| {name} | {t['games']} | " + " | ".join(cells) + " |")

    # 4. us against the teams above us
    vs = [g for g in labelled if US in (g["white"], g["black"]) and ({g["white"], g["black"]} - {US}) <= set(above)]
    side_us = lambda g: "white" if g["white"] == US else "black"
    side_them = lambda g: "black" if g["white"] == US else "white"
    us_agg, them_agg = mt.aggregate(vs, side_us), mt.aggregate(vs, side_them)
    md += ["", f"## Us against the teams above us, last {args.window_days:g} days ({len(vs)} games)", "",
           "| tag | us | them |", "|---|---|---|"]
    for k in TAGS:
        md.append(f"| {k} | {us_agg[k]:.1f} | {them_agg[k]:.1f} |")
    lost = [r for r in ours if r["createdAt"] >= window and opponent(r) in above and our_score(r) == 0]
    reasons = collections.Counter(r.get("reason") for r in lost)
    md += ["", f"Our {len(lost)} losses to them ended: " + ", ".join(f"{k} {v}" for k, v in reasons.most_common()) + "."]

    os.makedirs(args.out, exist_ok=True)
    stamp = now.strftime("%Y-%m-%d")
    text = "\n".join(md) + "\n"
    for name in (f"{stamp}.md", "latest.md"):
        open(os.path.join(args.out, name), "w").write(text)
    json.dump({"generated": iso(now), "games_held": len(rows), "last_24h": len(last_day), "above": above,
               "our_24h": record(o_day), "our_7d": record(o_week), "taxonomy": tax,
               "us_vs_above": {"us": {k: round(us_agg[k], 2) for k in TAGS}, "them": {k: round(them_agg[k], 2) for k in TAGS}, "games": len(vs)}},
              open(os.path.join(args.out, f"{stamp}.json"), "w"), indent=1)
    print(os.path.join(args.out, f"{stamp}.md"))


if __name__ == "__main__":
    main()
