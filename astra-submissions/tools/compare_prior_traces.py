#!/usr/bin/env python3
"""Compare exact belief traces and referee-label each chosen move."""
import argparse
import json
import re
import statistics
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from learning import ingest


def parse_truth(trace):
    report = trace.get("v35_truth_rank_at_target", {}).get("report", "")
    m = re.search(r"share=([0-9.]+) rank=(\d+)", report)
    return (float(m.group(1)), int(m.group(2))) if m else (None, None)


def summarize(path, raw):
    data = json.loads(Path(path).read_text())
    results = {}
    for trace in data["traces"]:
        game = trace["game"]
        replay_path = Path(raw) / "games" / game / "replay.json"
        replay = json.loads(replay_path.read_text())
        states, problems = ingest.validate_replay(replay)
        if problems:
            raise ValueError(f"invalid replay {game}: {problems[:2]}")
        ply = trace["ply"]
        choice = trace["v35_replayed_choice"]
        board = states[ply].board
        us = board.side
        fatal = board.move_loses_king(choice)
        next_turn_captures = []
        if not fatal:
            after = board.copy()
            after.push(choice)
            for reply in after.legal_moves():
                branch = after.copy()
                branch.push(reply)
                if branch.king_square(us) < 0:
                    next_turn_captures.append(reply)
        share, rank = parse_truth(trace)
        results[(game, ply)] = {
            "game": game, "opponent": trace["opponent"], "ply": ply,
            "recorded_outcome": trace.get("recorded_outcome"),
            "recorded_move": trace["actual_fatal_move"], "choice": choice,
            "choice_is_recorded_fatal_move": choice == trace["actual_fatal_move"],
            "choice_is_referee_fatal": fatal, "choice_is_known_safe_alt": choice in trace["true_board_safe_alternatives"],
            "opponent_reply_count": 0 if fatal else len(after.legal_moves()),
            "opponent_replies_capturing_our_king": next_turn_captures,
            "truth_mass": share, "truth_rank": rank,
            "belief_particles": (trace.get("v35_truth_rank_at_target") or {}).get("particles"),
        }
    return data, results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("baseline")
    ap.add_argument("candidate")
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    base_meta, base = summarize(a.baseline, a.raw)
    cand_meta, cand = summarize(a.candidate, a.raw)
    keys = sorted(set(base) | set(cand))
    joined = []
    for key in keys:
        x, y = base.get(key), cand.get(key)
        joined.append({"baseline": x, "candidate": y,
                       "choice_changed": bool(x and y and x["choice"] != y["choice"]),
                       "fatality_changed": bool(x and y and x["choice_is_referee_fatal"] != y["choice_is_referee_fatal"]),
                       "truth_rank_changed": bool(x and y and x["truth_rank"] != y["truth_rank"]),
                       "truth_mass_changed": bool(x and y and x["truth_mass"] != y["truth_mass"])} )
    def agg(rows):
        rs = [x for x in rows if x is not None]
        masses = [x["truth_mass"] for x in rs if x["truth_mass"] is not None]
        ranks = [x["truth_rank"] for x in rs if x["truth_rank"] is not None]
        return {"positions": len(rs),
                "referee_fatal_choices": sum(x["choice_is_referee_fatal"] for x in rs),
                "known_safe_alt_choices": sum(x["choice_is_known_safe_alt"] for x in rs),
                "moves_allowing_immediate_king_capture_reply": sum(bool(x["opponent_replies_capturing_our_king"]) for x in rs),
                "changed_from_recorded_fatal": sum(not x["choice_is_recorded_fatal_move"] for x in rs),
                "median_truth_mass": statistics.median(masses) if masses else None,
                "median_truth_rank": statistics.median(ranks) if ranks else None}
    report = {"classification": "fixed-prefix diagnostic on selected replay cases; exact own-move and one-reply king-capture labels, no strength claim",
              "baseline_sha256": base_meta["binary_sha256"],
              "candidate_sha256": cand_meta["binary_sha256"],
              "baseline": agg(base.values()), "candidate": agg(cand.values()),
              "positions_in_both": sum(1 for k in keys if k in base and k in cand),
              "per_position": joined,
              "limits": ["Targeted loss cases, not a random sample.",
                         "Opponent replies are enumerated on the true board only to detect immediate king capture; no reply policy or deeper continuation is simulated.",
                         "Material, win probability and longer-term value are not measured."]}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k:v for k,v in report.items() if k != "per_position"}, indent=2))


if __name__ == "__main__": main()
