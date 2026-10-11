#!/usr/bin/env python3
"""Regression checks for two exact public queen-fork replay certificates."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "astra-submissions" / "tools"))
from m4_scan_hidden_queen_forks import analyze_game

KIT = Path("/home/henrytan/git/fow-starter")
sys.path.insert(0, str(KIT))
import chess
import referee


def load(game_id):
    return json.loads((ROOT / "data/raw/games" / game_id / "replay.json").read_text())


def main():
    instructors = analyze_game(load("4bkwxxng"), referee, chess)
    line = next(x for x in instructors if x["ply"] == 53)
    assert line["actual_hidden_queen_fork"]["uci"] == "e3e7"
    assert line["actual_line_immediate_survival"]["immediate_survival_replies"] == ["f8g8"]
    king_preemption = next(x for x in line["preemptive_king_moves"] if x["move"] == "f8g8")
    assert king_preemption["same_queen_move_survival"]["still_forks_king_and_major"] is False
    assert len(king_preemption["same_queen_move_survival"]["immediate_survival_replies"]) == 40
    assert tuple(line["response_outcome"]) == ("1-0", "King capturable")

    duck = analyze_game(load("69nmui22"), referee, chess)
    line = next(x for x in duck if x["ply"] == 36)
    assert line["actual_hidden_queen_fork"]["uci"] == "f6c3"
    assert line["historical_response"] == "g2g7"
    assert tuple(line["response_outcome"]) == ("0-1", "King capturable")
    assert set(line["actual_line_immediate_survival"]["immediate_survival_replies"]) == {
        "e1f1", "e1d1", "c1d2"}
    king_preemption = next(x for x in line["preemptive_king_moves"] if x["move"] == "e1d1")
    assert king_preemption["same_queen_move_survival"]["still_forks_king_and_major"] is False
    assert len(king_preemption["same_queen_move_survival"]["immediate_survival_replies"]) == 35
    print("PASS: Instructors fork has 1/37 survival replies; Duck fork has 3/23; "
          "the exact preemptions remove the king attack and expand safe replies.")


if __name__ == "__main__":
    main()
