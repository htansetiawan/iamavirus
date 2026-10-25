#!/usr/bin/env python3
"""Select a color/outcome-stratified random control set from v35 arena games.

The sample is one recorded, nonfatal decision per distinct v35 game. It is for
measuring immediate true-board king-fatality collateral from the king guard;
it is neither a random arena sample nor an Elo estimate because outcomes and
opponents are deliberately stratified.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from learning import ingest, rules

TEAM_ID = "a2c35173659545c99752376a70418438"
DEFAULT_OPPONENTS = (
    "Greek Gift", "Knight Vision", "Strongly Invisible",
    "Decent Chess Bot", "Crimson Fog", "Instructors", "duck",
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--exclude", type=Path, action="append", default=[])
    ap.add_argument("--per-color-outcome", type=int, default=5)
    ap.add_argument("--max-ply", type=int, default=80)
    ap.add_argument("--seed", type=int, default=20261025)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    excluded = set()
    for path in args.exclude:
        doc = json.loads(path.read_text())
        if "examples" in doc:
            excluded.update(x["game"] for x in doc["examples"])
        if "rows" in doc:
            excluded.update(x["game"] for x in doc["rows"])

    paths = sorted(subprocess.check_output(
        ["rg", "-l", '"whiteVersion": 35|"blackVersion": 35',
         str(args.raw / "games"), "--glob", "replay.json"], text=True
    ).splitlines())
    buckets: dict[tuple[str, str, str], list[Path]] = collections.defaultdict(list)
    for name in paths:
        path = Path(name)
        game = path.parent.name
        if game in excluded:
            continue
        replay = json.loads(path.read_text())
        white = (replay.get("whitePlayerId") == TEAM_ID
                 and replay.get("whiteVersion") == 35)
        black = (replay.get("blackPlayerId") == TEAM_ID
                 and replay.get("blackVersion") == 35)
        if white == black:
            continue
        our_color = "white" if white else "black"
        opponent = replay["black"] if white else replay["white"]
        if opponent not in DEFAULT_OPPONENTS or replay["result"] == "1/2-1/2":
            continue
        outcome = "win" if ((replay["result"] == "1-0") == white) else "loss"
        buckets[(opponent, outcome, our_color)].append(path)

    cases = []
    selected_games = set()
    for opponent in DEFAULT_OPPONENTS:
        for outcome in ("win", "loss"):
            for color in ("white", "black"):
                pool = buckets[(opponent, outcome, color)]
                rng.shuffle(pool)
                got = 0
                for path in pool:
                    if got >= args.per_color_outcome:
                        break
                    game = path.parent.name
                    if game in selected_games:
                        continue
                    replay = json.loads(path.read_text())
                    states, problems = ingest.validate_replay(replay)
                    if problems:
                        raise ValueError(f"{game}: invalid replay: {problems[:2]}")
                    white = color == "white"
                    side = rules.WHITE if white else rules.BLACK
                    frames = replay.get("frames", [])
                    # Each candidate index is the observation before our
                    # action. White acts from even plies; Black from odd.
                    eligible = [ply for ply in range(min(args.max_ply, len(frames) - 1))
                                if (ply % 2 == 0) == white and frames[ply + 1].get("move")]
                    rng.shuffle(eligible)
                    choice = None
                    for ply in eligible:
                        move = frames[ply + 1]["move"]
                        board = states[ply].board
                        # Keep only historically nonfatal decisions before
                        # filling a cell; do not silently lose a sampled slot.
                        if not board.move_loses_king(move):
                            choice = (ply, move, board)
                            break
                    if choice is None:
                        continue
                    ply, move, board = choice
                    safe_alternatives = [m for m in board.legal_moves()
                                         if m != move and not board.move_loses_king(m)]
                    king_square = board.king_square(side)
                    king_name = (chr(97 + king_square % 8) + str(king_square // 8 + 1)
                                 if king_square is not None else None)
                    cases.append({"game": game, "opponent": opponent,
                                  "outcome": outcome, "color": color,
                                  "ply": ply, "move": move,
                                  "replay_sha256": sha(path),
                                  "king_move": move[:2] == king_name,
                                  "safe_alternatives": sorted(safe_alternatives)})
                    selected_games.add(game)
                    got += 1

    counts = collections.Counter((x["opponent"], x["outcome"], x["color"])
                                 for x in cases)
    result = {
        "classification": "color/outcome-stratified random v35 decisions; immediate king-fatality collateral diagnostic, not Elo",
        "seed": args.seed,
        "per_color_outcome_requested": args.per_color_outcome,
        "max_ply": args.max_ply,
        "excluded_games": sorted(excluded),
        "selection": "one random nonfatal eligible decision per distinct game; exact IAmAVirus v35 version; top-six Oct25 teams plus duck; stratified by final win/loss and color; sorted source paths and seeded shuffle",
        "count": len(cases),
        "counts": {"|".join(k): v for k, v in sorted(counts.items())},
        "examples": cases,
        "limits": ["Opponent and final-outcome strata are deliberate, so aggregate rates are not deployment frequencies.",
                   "At most one decision per game; other actions in that game are not independent.",
                   "Only immediate true-board king fatality is scored; no counterfactual game continuation is evaluated."],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"count": len(cases), "counts": result["counts"],
                      "excluded_games": len(excluded), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
