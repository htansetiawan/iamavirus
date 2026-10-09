"""Compare pinned Misty Python rules/visibility with the MIT course referee.

Loads only the supplied source modules, not Misty's package initializer, search,
Stockfish, or Rust extension. This is a rules audit, not a strength benchmark.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import chess


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--misty-source", type=Path, required=True)
    ap.add_argument("--referee", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    paths = {"rules": args.misty_source / "src/fow_chess/rules.py",
             "visibility": args.misty_source / "src/fow_chess/visibility.py"}
    rules = module("misty_rules_audit", paths["rules"]).ChessRules()
    vis = module("misty_visibility_audit", paths["visibility"])
    ref = module("course_referee_audit", args.referee)
    counts = Counter()
    mismatches = []
    terminal_differences = []

    def check(board, label, expected_views=None):
        other = chess.Board(board.fen(en_passant="fen"))
        ours = {m.uci() for m in ref.fow_moves(board)}
        theirs = {m.uci() for m in rules.pseudo_legal_moves(other)}
        counts["move_lists"] += 1
        if ours != theirs:
            mismatches.append({"where": label, "kind": "moves",
                               "course_only": sorted(ours-theirs), "misty_only": sorted(theirs-ours)})
        for color, side in [(chess.WHITE, "white"), (chess.BLACK, "black")]:
            observed = ref.observation(board, color)
            if expected_views is not None:
                assert observed == expected_views[side]
            seen = vis._visible_squares_py(other, color)
            rendered = "".join((other.piece_at(s).symbol() if other.piece_at(s) else "-")
                               if s in seen else "?" for s in range(64))
            counts["views"] += 1
            if observed != rendered:
                mismatches.append({"where": label, "kind": side + "_view",
                    "different_squares": [chess.square_name(s) for s in range(64) if observed[s] != rendered[s]]})

    games = json.loads((args.corpus / "games.json").read_text())["games"]
    counts["games"] = len(games)
    for game in games:
        replay = json.loads((args.corpus / "games" / game["id"] / "replay.json").read_text())
        board = ref.FowBoard()
        repetitions = Counter({ref.position_key(board): 1})
        for frame in replay["frames"]:
            if frame["move"]:
                board.push(board.parse_uci(frame["move"]))
                repetitions[ref.position_key(board)] += 1
            true_board = "".join(board.piece_at(s).symbol() if board.piece_at(s) else "-"
                                 for s in range(64))
            assert true_board == frame["board"], (game["id"], frame["ply"])
            check(board, f'{game["id"]}:{frame["ply"]}', frame)
            counts["replay_frames"] += 1
        course_end = ref.outcome(board, repetitions)
        assert course_end == (game["result"], game["reason"])
        misty_end = rules.is_terminal(chess.Board(board.fen(en_passant="fen")))
        if bool(course_end) != misty_end:
            terminal_differences.append({"game": game["id"], "course_reason": course_end[1],
                                         "misty_chessrules_terminal": misty_end})
    # Minimal edge cases extend the natural replay sample, including EP whose
    # orthodox legality is suppressed by check and castling through attack.
    edges = {
        "castle_into_attack": "k5r1/8/8/8/8/8/8/4K2R w K - 0 1",
        "castle_out_of_check": "k3r3/8/8/8/8/8/8/4K2R w K - 0 1",
        "castle_through_attack": "k4r2/8/8/8/8/8/8/4K2R w K - 0 1",
        "queenside_castle": "7k/8/8/8/8/8/8/R3K3 w Q - 0 1",
        "ep_while_in_check": "k3r3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
        "adjacent_kings": "8/8/8/8/8/8/4k3/4K3 w - - 0 1",
        "promotion": "4k3/P7/8/8/8/8/8/4K3 w - - 0 1",
    }
    for label, fen in edges.items():
        check(ref.FowBoard(fen), label)
    tree_path = args.misty_source / "tree.json"
    commit = (json.loads(tree_path.read_text())["sha"] if tree_path.exists() else
              subprocess.check_output(["git", "-C", str(args.misty_source), "rev-parse", "HEAD"],
                                      text=True).strip())
    payload = {"misty_commit": commit, "python_chess_version": chess.__version__,
        "source_sha256": {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()},
        "referee_sha256": hashlib.sha256(args.referee.read_bytes()).hexdigest(),
        "counts": dict(counts), "edge_cases": list(edges), "mismatches": mismatches,
        "terminal_differences": terminal_differences,
        "scope": "Python ChessRules move lists and Python visibility only. Native Rust, full search, protocol capture metadata, cap behavior and playing strength are not exercised. ChessRules terminal only recognizes absent kings; course early king exposure and draw adjudication must be handled explicitly. Misty also has a king_capture_imminent leaf/guard helper; this audit does not test that search path."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"counts": payload["counts"], "move_or_view_mismatches": len(mismatches),
                      "terminal_difference_reasons": dict(Counter(x["course_reason"] for x in terminal_differences))}))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
