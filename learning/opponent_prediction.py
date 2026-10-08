"""Gym metric for the opponent model: how well a move prior predicts what strong
bots actually play.

    python -m learning.opponent_prediction --teams top6 --limit 600

For each move by a selected team, score every legal move of the mover on the
true board with the engine's hand prior (uniform base, capture x2.5, giveaway
x0.06, attacks-the-enemy-king x3.0 — the v5 hand prior, mirrored here in
Python) and with the uniform prior, and report top-1 / top-4 hit rates and
log-loss. The true board is the best case for a level-0 prior; the v17
level-2 model must beat this on the same moves while scoring on the mover's own
belief instead.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os

import chess

TEAM_ID = "a2c35173659545c99752376a70418438"
TOP = {"Greek Gift", "Knight Vision", "Decent Chess Bot", "Strongly Invisible", "duck", "Instructors"}
VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


def fen(board64: str, turn: chess.Color) -> str:
    rows = []
    for r in range(7, -1, -1):
        row, empty = "", 0
        for f in range(8):
            c = board64[r * 8 + f]
            if c == "-":
                empty += 1
            else:
                if empty:
                    row += str(empty)
                    empty = 0
                row += c
        if empty:
            row += str(empty)
        rows.append(row)
    return "/".join(rows) + (" w" if turn == chess.WHITE else " b") + " - - 0 1"


def fow_legal_moves(board: chess.Board):
    """Fog-of-war legality: pseudo-legal moves (no check rule), king captures allowed."""
    return list(board.pseudo_legal_moves)


def hand_prior(board: chess.Board, move: chess.Move) -> float:
    mover = board.turn
    weight = 1.0
    victim = board.piece_at(move.to_square)
    captured = VALUE[victim.piece_type] if victim else 0
    if victim or board.is_en_passant(move):
        weight *= 2.5
    board.push(move)
    moved = board.piece_at(move.to_square)
    value = VALUE[moved.piece_type] if moved else 0
    our_attackers = board.attackers(not mover, move.to_square)
    defended = bool(board.attackers(mover, move.to_square))
    if our_attackers and not defended and value > captured:
        weight *= 0.06
    enemy_king = board.king(not mover)
    if enemy_king is not None and move.to_square in board.attackers(mover, enemy_king):
        weight *= 3.0
    board.pop()
    return weight


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--teams", default="top6", help="top6 | us | TA | all")
    ap.add_argument("--limit", type=int, default=600, help="games to scan")
    args = ap.parse_args()
    stats = collections.defaultdict(lambda: collections.Counter())
    scanned = 0
    for path in sorted(glob.glob(os.path.join(args.raw, "games", "*", "replay.json"))):
        try:
            r = json.load(open(path))
        except Exception:
            continue
        frames = r.get("frames") or []
        if len(frames) < 3:
            continue
        names = {0: r["white"], 1: r["black"]}
        ids = {0: r.get("whitePlayerId"), 1: r.get("blackPlayerId")}

        def group(side):
            if ids[side] == TEAM_ID:
                return "us"
            if names[side] in TOP:
                return "top6"
            if names[side].startswith("TA Baseline"):
                return "TA"
            return "other"

        wanted = {0: group(0), 1: group(1)}
        if args.teams != "all" and args.teams not in wanted.values():
            continue
        scanned += 1
        if scanned > args.limit:
            break
        for k in range(1, len(frames)):
            f = frames[k]
            if not f["move"]:
                continue
            side = 0 if f["ply"] % 2 == 1 else 1
            g = wanted[side]
            if args.teams != "all" and g != args.teams:
                continue
            board = chess.Board(fen(frames[k - 1]["board"], chess.WHITE if side == 0 else chess.BLACK))
            try:
                real = chess.Move.from_uci(f["move"])
            except Exception:
                continue
            legal = fow_legal_moves(board)
            if real not in legal or len(legal) < 2:
                continue
            weights = {m: hand_prior(board, m) for m in legal}
            total = sum(weights.values())
            ranked = sorted(legal, key=lambda m: -weights[m])
            rank = ranked.index(real)
            st = stats[g]
            st["moves"] += 1
            st["top1"] += rank == 0
            st["top4"] += rank < 4
            st["logloss_hand"] += -math.log(max(1e-9, weights[real] / total))
            st["logloss_uniform"] += math.log(len(legal))
            st["legal"] += len(legal)
            # how often the real move is a capture / attacks the king (the prior's own features)
            st["real_capture"] += board.piece_at(real.to_square) is not None
    for g, st in stats.items():
        m = st["moves"] or 1
        print(f"{g:5} moves {st['moves']:6} legal/move {st['legal']/m:5.1f} | hand prior: top-1 {100*st['top1']/m:5.1f}%  top-4 {100*st['top4']/m:5.1f}%  log-loss {st['logloss_hand']/m:5.2f} | uniform log-loss {st['logloss_uniform']/m:5.2f} (top-4 would be {100*4/(st['legal']/m):4.1f}%) | real move is a capture {100*st['real_capture']/m:4.1f}%")


if __name__ == "__main__":
    main()
