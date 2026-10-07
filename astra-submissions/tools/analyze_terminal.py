#!/usr/bin/env python3
"""Label a completed game's final decision, using public truth only offline.

Also validates every frame and all move/survival labels against the course
referee. This is a diagnosis, not a counterfactual match or a strength estimate.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from analyze_duck import attackers, rules, square, verify_with_referee


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--referee", type=Path, required=True)
    args = parser.parse_args()
    stored = args.replay.read_bytes()
    raw = gzip.decompress(stored) if args.replay.suffix == ".gz" else stored
    replay = json.loads(raw)
    if len(replay["frames"]) < 2:
        parser.error("a final played move is required")
    board = rules.Board()
    for frame in replay["frames"][1:-1]:
        board.push(frame["move"])
    before, final = replay["frames"][-2:]
    assert board.board_string() == before["board"]
    mover = board.side
    view = before["white" if mover == 0 else "black"]
    legal = board.legal_moves()
    safe = [move for move in legal if not board.move_loses_king(move)]
    after = board.copy()
    after.push(final["move"])
    king = after.king_square(mover)
    fatal = [] if king < 0 else [
        dict(square=square(s), piece=after.board_string()[s],
             hidden_at_decision=view[s] == "?")
        for s in attackers(after.board_string(), king, white=mover == 1)]
    report = dict(
        game=replay["id"], white_version=replay.get("whiteVersion"),
        black_version=replay.get("blackVersion"), result=replay["result"],
        reason=replay["reason"], source=str(args.replay),
        source_sha256=hashlib.sha256(raw).hexdigest(),
        stored_file_sha256=hashlib.sha256(stored).hexdigest(),
        referee_verification=verify_with_referee(replay, args.referee),
        final_decision=dict(ply=before["ply"], side="white" if mover == 0 else "black",
                            preceding_move=before["move"], move=final["move"],
                            legal_moves=legal, immediate_survival_moves=safe,
                            mover_loses_king=after.mover_lost(), fatal_attackers=fatal),
        caveats=["Truth is an offline label, not an input to the live bot.",
                 "Survival means immediate adjudication, not a winning continuation.",
                 "A hidden attack does not establish which scoring term caused it.",
                 "One game is not a strength estimate or a controlled comparison."])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in
                      ("game", "referee_verification", "final_decision")}, indent=2))


if __name__ == "__main__":
    main()
