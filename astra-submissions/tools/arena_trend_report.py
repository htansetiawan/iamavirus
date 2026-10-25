#!/usr/bin/env python3
"""Summarize saved daily arena standings and move-taxonomy trend snapshots.

This reads only existing daily reports. It does not fetch the API and cannot
claim current standings beyond the final report included in the input folder.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*([0-9.]+)\s*\|\s*(\d+)\s*\|")
WATCH = ("IAmAVirus", "Greek Gift", "Knight Vision", "Strongly Invisible",
         "Decent Chess Bot", "Mist Opportunities", "Instructors", "duck",
         "HYPOTHERMIA")


def read_day(json_path: Path):
    day = json_path.stem
    md_path = json_path.with_suffix(".md")
    data = json.loads(json_path.read_text())
    table = {}
    for line in md_path.read_text().splitlines():
        match = ROW.match(line)
        if match:
            rank, name, rating, version = match.groups()
            table[name.replace("**", "")] = {
                "rank": int(rank), "rating": float(rating), "version": int(version)
            }
    return day, data, table


def build_report(report_dir: Path):
    days = [read_day(p) for p in sorted(report_dir.glob("2026-10-*.json"))
            if p.with_suffix(".md").exists()]
    if len(days) < 2:
        raise ValueError("need at least two paired daily JSON/Markdown reports")
    first_day, _, first_table = days[0]
    last_day, last_data, last_table = days[-1]
    teams = {}
    for name in WATCH:
        if name not in first_table or name not in last_table:
            continue
        start, end = first_table[name], last_table[name]
        teams[name] = {
            "start": start, "end": end,
            "rating_change": round(end["rating"] - start["rating"], 1),
            "rank_change": start["rank"] - end["rank"],
        }
    tax = last_data.get("taxonomy", {})
    ours = tax.get("IAmAVirus", {})
    above = [name for name in last_data.get("above", []) if name in tax]
    metrics = ("king_move", "king_leaves_home", "king_threat", "king_threat_unseen",
               "walk_into_unseen", "vision_gain", "capture_unseen")
    peer = {m: sum(tax[n].get(m, 0) for n in above) / len(above)
            for m in metrics} if above else {}
    deltas = {m: round(ours.get(m, 0) - peer.get(m, 0), 3) for m in metrics}
    return {
        "classification": "saved-report trend summary; not a live API fetch or causal analysis",
        "first_report": first_day, "last_report": last_day,
        "reports": len(days), "rank_rating_versions": teams,
        "last_snapshot_generated": last_data.get("generated"),
        "our_24h": last_data.get("our_24h"), "our_7d": last_data.get("our_7d"),
        "last_taxonomy_games": ours.get("games"),
        "latest_us_minus_above_average_per_100_moves": deltas,
        "latest_taxonomy_us": {m: ours.get(m) for m in metrics},
        "latest_taxonomy_above_average": peer,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, default=Path("data/reports/daily"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(args.reports)
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
