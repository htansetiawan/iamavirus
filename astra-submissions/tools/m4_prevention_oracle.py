#!/usr/bin/env python3
"""Rules-exact, full-information diagnostic for earlier prevention positions.

After a candidate own move, enumerate every legal opponent reply. Record replies
that win immediately or leave no next own move avoiding immediate loss. This is
a short-horizon adversarial oracle, not an opponent policy or an Elo estimate.
It never feeds truth to a bot. Terminal draws and wins stop the branch.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--kit", type=Path, default=Path.home()/"git/fow-starter")
    parser.add_argument("--all-legal", action="store_true", help="Audit every candidate at each reported decision")
    args = parser.parse_args()
    sys.path.insert(0, str(args.kit))
    import chess
    import referee
    game = json.loads(args.replay.read_text())
    cases = {}
    for path in args.reports:
        report = json.loads(path.read_text())
        for row in report["rows"]:
            if row["game"] != game["id"]:
                continue
            for kind in ("played", "chosen"):
                move = row.get(kind)
                if move:
                    cases.setdefault((row["ply"], row["side"], move), []).append(
                        {"report": str(path), "mode": row["mode"], "kind": kind})
    if args.all_legal:
        for ply, side in sorted({(ply, side) for ply, side, _ in cases}):
            board = referee.FowBoard()
            for frame in game["frames"][1:ply+1]:
                board.push_uci(frame["move"])
            for move in referee.fow_moves(board):
                cases.setdefault((ply, side, move.uci()), []).append({"kind": "all_legal"})
    output = []
    for (ply, side, uci), sources in sorted(cases.items()):
        board = referee.FowBoard()
        counts = Counter({referee.position_key(board): 1})
        for frame in game["frames"][1:ply+1]:
            board.push_uci(frame["move"])
            counts[referee.position_key(board)] += 1
        actual = ''.join(board.piece_at(i).symbol() if board.piece_at(i) else '-' for i in range(64))
        assert actual == game["frames"][ply]["board"]
        loss = "0-1" if side == "white" else "1-0"
        assert board.turn == (side == "white")
        move = chess.Move.from_uci(uci)
        row = {"game": game["id"], "ply": ply, "side": side, "move": uci, "sources": sources}
        row["legal"] = move in referee.fow_moves(board)
        if not row["legal"]:
            output.append(row)
            continue
        board.push(move)
        counts[referee.position_key(board)] += 1
        ending = referee.outcome(board, counts)
        row["immediate_outcome"] = ending
        row["immediate_loss"] = bool(ending and ending[0] == loss)
        forcing = []
        replies = 0
        if ending is None:
            for reply in referee.fow_moves(board):
                replies += 1
                child = board.copy(); child.push(reply)
                after = counts.copy(); after[referee.position_key(child)] += 1
                terminal = referee.outcome(child, after)
                if terminal:
                    if terminal[0] == loss:
                        forcing.append({"reply": reply.uci(), "outcome": terminal, "next_safe": 0})
                    continue
                safe = legal = 0
                for escape in referee.fow_moves(child):
                    legal += 1
                    next_board = child.copy(); next_board.push(escape)
                    final = after.copy(); final[referee.position_key(next_board)] += 1
                    result = referee.outcome(next_board, final)
                    if not result or result[0] != loss:
                        safe += 1
                if not safe:
                    forcing.append({"reply": reply.uci(), "next_legal": legal, "next_safe": safe})
        row.update(opponent_replies=replies, forcing_replies=forcing,
                   loses_within_next_own_turn=row["immediate_loss"] or bool(forcing))
        output.append(row)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = {"classification": "full-information short-horizon oracle; no Elo inference",
              "all_legal": args.all_legal,
              "replay_sha256": hashlib.sha256(args.replay.read_bytes()).hexdigest(),
              "referee_sha256": hashlib.sha256((args.kit/'referee.py').read_bytes()).hexdigest(),
              "rows": output}
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps([{k:v for k,v in row.items() if k != "sources"} for row in output]), flush=True)


if __name__ == "__main__":
    main()
