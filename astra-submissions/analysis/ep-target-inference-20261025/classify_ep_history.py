#!/usr/bin/env python3
"""Test whether the previous own-side observation proves otherwise-missed EP."""
from __future__ import annotations

import argparse
import gzip
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def sq(text: str) -> int:
    return (ord(text[1]) - 49) * 8 + ord(text[0]) - 97


def uci(fr: int, to: int) -> str:
    return chr(97 + fr % 8) + str(fr // 8 + 1) + chr(97 + to % 8) + str(to // 8 + 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--positions", type=Path, default=Path(__file__).with_name("top-opponent-replay-move-set-audit.jsonl.gz"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--candidates-out", type=Path,
                    default=Path(__file__).with_name("ep-history-candidate-actions.jsonl"))
    args = ap.parse_args()
    summary = {"games": 0, "positions": 0, "candidate_additions": 0,
               "true_en_passant": 0, "false_en_passant": 0,
               "patch_missed_true_actions_recovered": 0,
               "patch_missed_true_actions_total": 0,
               "patch_missed_true_actions_remaining": 0,
               "examples_false": [], "examples_true": []}
    args.candidates_out.parent.mkdir(parents=True, exist_ok=True)
    candidates_file = args.candidates_out.open("w")
    with gzip.open(args.positions, "rt") as stream:
      groups = itertools.groupby(stream, key=lambda line: json.loads(line)["game"])
      for game_id, lines in groups:
        rows = [json.loads(line) for line in lines]
        summary["games"] += 1
        replay_path = ROOT / "data/raw/games" / game_id / "replay.json"
        replay = json.loads(replay_path.read_text())
        frames = replay["frames"]
        for row in rows:
            p = row["ply"]
            summary["positions"] += 1
            summary["patch_missed_true_actions_total"] += row["patched"]["missed_ep_count"]
            if p < 1:
                continue
            side = "white" if p % 2 == 0 else "black"
            us_white = side == "white"
            prior = frames[p - 1][side]
            view = frames[p][side]
            own = "P" if us_white else "p"
            enemy = "p" if us_white else "P"
            dr = 8 if us_white else -8
            ep_target = row["ep_target"]
            for fr in range(64):
                if view[fr] != own or fr // 8 != (4 if us_white else 3):
                    continue
                for df in (-1, 1):
                    if not 0 <= fr % 8 + df < 8:
                        continue
                    beside = fr + df
                    target = beside + dr
                    start = beside + 2 * dr
                    middle = beside + dr
                    if view[beside] != enemy or view[target] != "-":
                        continue
                    # The immediately preceding same-side observation is after
                    # our own last move and before the opponent's one move.
                    # If the enemy pawn was at home, transit and landing were
                    # empty, and it now occupies landing, the intervening move
                    # can only have been the two-square advance.
                    if prior[start] != enemy or prior[middle] != "-" or prior[beside] != "-":
                        continue
                    move = uci(fr, target)
                    summary["candidate_additions"] += 1
                    if ep_target == target:
                        summary["true_en_passant"] += 1
                        missing = move in row["patched"]["missed_moves"].split(",")
                        if missing:
                            summary["patch_missed_true_actions_recovered"] += 1
                        if len(summary["examples_true"]) < 20:
                            summary["examples_true"].append({"game": game_id, "ply": p, "move": move,
                                                             "would_recover_patch_miss": missing})
                    else:
                        missing = False
                        summary["false_en_passant"] += 1
                        if len(summary["examples_false"]) < 20:
                            summary["examples_false"].append({"game": game_id, "ply": p, "move": move,
                                                              "actual_ep_target": ep_target})
                    candidates_file.write(json.dumps({"game": game_id, "state_ply": p,
                                                      "move": move, "is_true_ep": ep_target == target,
                                                      "would_recover_patch_miss": missing},
                                                     separators=(",", ":")) + "\n")
    candidates_file.close()
    summary["patch_missed_true_actions_remaining"] = (summary["patch_missed_true_actions_total"] -
                                                       summary["patch_missed_true_actions_recovered"])
    summary["method"] = ("For consecutive own-side observations separated by the opponent's one move, "
                         "test visible enemy-pawn home square, transit square, and current landing square. "
                         "This is a replay-history candidate rule, not integrated code or strength evidence.")
    summary["candidate_actions"] = str(args.candidates_out.relative_to(ROOT)) if args.candidates_out.is_relative_to(ROOT) else str(args.candidates_out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
