#!/usr/bin/env python3
"""Select a reproducible, recent, per-opponent replay sample from accepted.jsonl."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("index", type=Path)
    ap.add_argument("--teams", nargs="+", required=True)
    ap.add_argument("--start-date", required=True, help="inclusive YYYY-MM-DD")
    ap.add_argument("--end-date", required=True, help="inclusive YYYY-MM-DD")
    ap.add_argument("--per-team", type=int, default=800)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    teams = set(a.teams)
    eligible = {team: [] for team in teams}
    by_id = {}
    with a.index.open() as f:
        for line in f:
            row = json.loads(line)
            gid = row.get("id")
            date = (row.get("createdAt") or "")[:10]
            if not gid or not (a.start_date <= date <= a.end_date):
                continue
            actors = {row.get("white"), row.get("black")} & teams
            if not actors:
                continue
            record = {"id": gid, "createdAt": row.get("createdAt"), "white": row.get("white"),
                      "black": row.get("black"), "whitePlayerId": row.get("whitePlayerId"),
                      "blackPlayerId": row.get("blackPlayerId"), "targetTeams": sorted(actors)}
            by_id.setdefault(gid, record)
            for team in actors:
                eligible[team].append(record)
    selected = set()
    quotas = {}
    for team, rows in eligible.items():
        rows.sort(key=lambda x: (x["createdAt"], x["id"]), reverse=True)
        by_day = defaultdict(list)
        for row in rows: by_day[row["createdAt"][:10]].append(row)
        days = sorted(by_day, reverse=True)
        take = []
        # Round-robin across dates so a high-volume latest day cannot consume
        # the entire team quota.
        while len(take) < a.per_team and days:
            remaining = []
            for day in days:
                if by_day[day] and len(take) < a.per_team:
                    take.append(by_day[day].pop(0))
                if by_day[day]: remaining.append(day)
            days = remaining
        selected_dates = [r["createdAt"] for r in take]
        quotas[team] = {"eligible": len(rows), "selected": len(take),
                        "earliest_selected": min(selected_dates) if take else None,
                        "latest_selected": max(selected_dates) if take else None}
        selected.update(r["id"] for r in take)
    rows = [by_id[g] for g in selected]
    rows.sort(key=lambda x: (x["createdAt"], x["id"]))
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")
    report = {"index": str(a.index), "start_date": a.start_date, "end_date": a.end_date,
              "requested_per_team": a.per_team, "teams": quotas,
              "unique_games": len(rows), "games_by_date": dict(sorted(Counter(r["createdAt"][:10] for r in rows).items())),
              "selected_ids_sha256": __import__("hashlib").sha256("\n".join(r["id"] for r in rows).encode()).hexdigest(),
              "output": str(out)}
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
