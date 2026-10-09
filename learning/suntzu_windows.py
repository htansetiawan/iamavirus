"""SunTzu step 1: 8-move strategy windows from replays (chatroom note 027).

    python -m learning.suntzu_windows --games 3000 --output data/suntzu/windows-v1.npz

Each side of each game is cut into windows of WINDOW own moves. A window is
described by what the side *did* (move-taxonomy tags, which pieces moved, pawn
pushes toward the enemy king, heavy pieces aimed at the enemy king zone) and
the situation it was in (material and its trend, both kings' shelter classes,
phase). These vectors are what the residual codebook (learning/suntzu_rvq.py)
compresses into a hierarchy of strategy codes.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random

import chess
import numpy as np

from .move_taxonomy import KEYS, fen, label_game, material

WINDOW = 8
TOP = {"duck", "Decent Chess Bot", "Knight Vision", "Strongly Invisible", "Greek Gift", "Instructors",
       "Mist Opportunities", "TA Baseline S", "TA Baseline A", "TA Baseline P", "IAmAVirus"}
SHELTERS = ["center", "intact", "fianchetto", "luft", "one-gone", "open", "advanced", "walked-out"]
PIECES = "pnbrqk"


def shelter(board: chess.Board, color: bool) -> int:
    k = board.king(color)
    if k is None:
        return 7
    f, r = chess.square_file(k), chess.square_rank(k)
    home, fwd = (0, 1) if color == chess.WHITE else (7, -1)
    if abs(r - home) > 1:
        return 7
    if 2 <= f <= 5:
        return 0
    files = (5, 6, 7) if f >= 5 else (2, 1, 0)  # inner, middle, edge
    adv = []
    for ff in files:
        ranks = [(chess.square_rank(s) - home) * fwd for s in board.pieces(chess.PAWN, color) if chess.square_file(s) == ff]
        adv.append(min(ranks) if ranks else None)
    if adv == [1, 1, 1]:
        return 1
    if adv == [1, 2, 1]:
        return 2
    if adv == [1, 1, 2]:
        return 3
    missing = sum(a is None for a in adv)
    return 5 if missing >= 2 else 4 if missing == 1 else 6


def king_zone_pressure(board: chess.Board, color: bool) -> int:
    """Our rooks and queens that attack, or x-ray through one piece, a square next to the enemy king."""
    k = board.king(not color)
    if k is None:
        return 0
    zone = chess.SquareSet(chess.BB_KING_ATTACKS[k]) | chess.SquareSet([k])
    count = 0
    for sq in board.pieces(chess.ROOK, color) | board.pieces(chess.QUEEN, color):
        rays = board.attacks(sq)
        if rays & zone:
            count += 1
            continue
        for blocker in rays:  # x-ray: remove one blocker and look again
            if board.piece_at(blocker) is None:
                continue
            b = board.copy(stack=False)
            b.remove_piece_at(blocker)
            if b.attacks(sq) & zone:
                count += 1
                break
    return count


FEATURES = ([f"tag:{k}" for k in KEYS] + [f"moved:{p}" for p in PIECES] +
            ["pawn_storm", "king_zone_pressure", "material_diff", "material_trend", "phase"] +
            [f"own_shelter:{s}" for s in SHELTERS] + [f"enemy_shelter:{s}" for s in SHELTERS])


def windows_of(r: dict) -> list[tuple[np.ndarray, dict]]:
    frames = r["frames"]
    n = len(frames) - 1
    if n < 2 * WINDOW:
        return []
    labelled = label_game(r)
    boards = [chess.Board(fen(f["board"])) for f in frames]
    out = []
    for side, color in ((0, chess.WHITE), (1, chess.BLACK)):
        own = [m for m in labelled["moves"] if m["side"] == side]
        res = r.get("result")
        score = 0.5 if res == "1/2-1/2" else (1.0 if (res == "1-0") == (side == 0) else 0.0)
        name = r["white"] if side == 0 else r["black"]
        opp = r["black"] if side == 0 else r["white"]
        for start in range(0, len(own) - WINDOW + 1, WINDOW):
            chunk = own[start:start + WINDOW]
            first_ply, last_ply = chunk[0]["ply"], chunk[-1]["ply"]
            b0, b1 = boards[first_ply - 1], boards[min(last_ply, n)]
            v = np.zeros(len(FEATURES), np.float32)
            for m in chunk:
                for t in m["tags"]:
                    if t in KEYS:
                        v[KEYS.index(t)] += 1.0 / WINDOW
                if m["piece"] in PIECES:
                    v[len(KEYS) + PIECES.index(m["piece"])] += 1.0 / WINDOW
                if m["piece"] == "p":
                    ek = boards[m["ply"] - 1].king(not color)
                    if ek is not None and abs(chess.square_file(chess.parse_square(m["move"][:2])) - chess.square_file(ek)) <= 1:
                        v[len(KEYS) + 6] += 1.0 / WINDOW
            base = len(KEYS) + 7
            v[base] = king_zone_pressure(b1, color) / 2.0
            md0 = material(frames[first_ply - 1]["board"], side) - material(frames[first_ply - 1]["board"], 1 - side)
            md1 = material(frames[min(last_ply, n)]["board"], side) - material(frames[min(last_ply, n)]["board"], 1 - side)
            v[base + 1] = md0 / 10.0
            v[base + 2] = (md1 - md0) / 5.0
            v[base + 3] = first_ply / 100.0
            v[base + 4 + shelter(b0, color)] = 1.0
            v[base + 4 + 8 + shelter(b0, not color)] = 1.0
            out.append((v, {"game": r["id"], "team": name, "opponent": opp, "side": side, "ply": first_ply,
                            "score": score, "next_trend": 0.0}))
        # the next window's material trend, as an outcome signal for the decoder
        team_windows = [w for w in out if w[1]["side"] == side and w[1]["game"] == r["id"]]
        for a, b in zip(team_windows, team_windows[1:]):
            a[1]["next_trend"] = float(b[0][len(KEYS) + 9])
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--games", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--output", default="data/suntzu/windows-v1.npz")
    args = ap.parse_args(argv)
    paths = []
    for p in glob.glob(os.path.join(args.raw, "games", "*", "listing.json")):
        try:
            l = json.load(open(p))
        except Exception:
            continue
        if l.get("white") in TOP and l.get("black") in TOP:
            paths.append(p.replace("listing.json", "replay.json"))
    random.Random(args.seed).shuffle(paths)
    X, meta = [], []
    for i, rp in enumerate(paths[: args.games]):
        try:
            r = json.load(open(rp))
            for v, m in windows_of(r):
                X.append(v)
                meta.append(m)
        except Exception:
            continue
        if (i + 1) % 250 == 0:
            print(f"{i + 1} games, {len(X)} windows", flush=True)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    np.savez_compressed(args.output, X=np.array(X), features=np.array(FEATURES),
                        meta=np.array([json.dumps(m) for m in meta]))
    print(f"wrote {args.output}: {len(X)} windows x {len(FEATURES)} features from {min(len(paths), args.games)} games")


if __name__ == "__main__":
    main()
