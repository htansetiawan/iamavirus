"""Move taxonomy v0: label every move of both sides in arena replays.

    python -m learning.move_taxonomy --versions 13 14 15 --opponents top6.json [--raw data/raw] [--json out.json]
    python -m learning.move_taxonomy --all-games --limit 400     # every ingested game, both sides, no team filter

Each move gets tags computed from the true boards and both sides' views in the
replay frames (`board`, `white`, `black`, `move`, `ply`). The point is to
describe what kinds of moves each side makes, so that the kinds we never make
and the kinds that beat us become named capabilities with a number attached.

Tags (S = mover, O = opponent; "unseen" means the square shows '?' in the
relevant side's view at that time):
  capture, capture_unseen (O could not see the capturer before the capture),
  victim_walked_in (O's previous move put the victim there), long_strike
  (slider capture from 3+ squares), fog_route (the capturer reached its square
  through moves O never saw; depth = number of such consecutive moves),
  king_threat (after the move S attacks O's king), king_threat_unseen (and O
  cannot see the attacker), king_capture, sacrifice (S gives 3+ points net over
  the next two plies), king_hunt_sacrifice (a sacrifice followed by S's king
  capture within 8 plies), forcing_chain (capture answered by capture, chain
  length 3+), vision_gain / vision_loss (S's visible squares change by 3+),
  king_move, castle, king_leaves_home (king beyond its second rank), queen_raid
  (queen enters O's half), queen_exposed_unseen (after the move S's queen is
  attacked by a piece S cannot see), walk_into_unseen (a non-capture that puts
  a piece worth 3+ on a square attacked by a piece S cannot see), back_rank_bare
  (S's king on its home rank with no other S piece on that rank while O still
  has a rook or queen).
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os

import chess

TEAM_ID = "a2c35173659545c99752376a70418438"
VALUE = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 0}


def material(board: str, colour: int) -> int:
    return sum(VALUE[c.lower()] for c in board if c != "-" and (c.isupper() == (colour == 0)))


def fen(board64: str) -> str:
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
    return "/".join(rows) + " w - - 0 1"


def visible(view: str) -> int:
    return 64 - view.count("?")


def label_game(r: dict) -> dict:
    """Per-side tag counts for one replay, plus per-move records."""
    frames = r["frames"]
    n = len(frames) - 1
    boards = [chess.Board(fen(f["board"])) for f in frames]
    mats = {0: [material(f["board"], 0) for f in frames], 1: [material(f["board"], 1) for f in frames]}
    view_key = {0: "white", 1: "black"}
    counts = {0: collections.Counter(), 1: collections.Counter()}
    moves_out = []
    # The referee ends the game when a king can be captured, before the capture
    # is played, so the winner's king capture is the ply after the last frame.
    king_capture_ply = {0: None, 1: None}
    if r.get("reason") == "King capturable":
        if r.get("result") == "1-0":
            king_capture_ply[0] = n + 1
        elif r.get("result") == "0-1":
            king_capture_ply[1] = n + 1
    for k in range(1, n + 1):
        f = frames[k]
        mv = f["move"]
        if not mv:
            continue
        p = f["ply"]
        S = 0 if p % 2 == 1 else 1
        O = 1 - S
        before, after = boards[k - 1], boards[k]
        src, dst = chess.parse_square(mv[:2]), chess.parse_square(mv[2:4])
        s_col = chess.WHITE if S == 0 else chess.BLACK
        o_col = chess.BLACK if S == 0 else chess.WHITE
        piece = before.piece_at(src)
        ptype = piece.symbol().lower() if piece else "?"
        victim = before.piece_at(dst)
        tags = []
        viewS_before, viewS_after = frames[k - 1][view_key[S]], f[view_key[S]]
        viewO_before, viewO_after = frames[k - 1][view_key[O]], f[view_key[O]]
        counts[S]["moves"] += 1
        if victim is not None:
            tags.append("capture")
            vtype = victim.symbol().lower()
            if viewO_before[src] == "?":
                tags.append("capture_unseen")
            if k >= 2 and frames[k - 1]["move"] and chess.parse_square(frames[k - 1]["move"][2:4]) == dst:
                tags.append("victim_walked_in")
            if ptype in "brq" and chess.square_distance(src, dst) >= 3:
                tags.append("long_strike")
            # fog route: how many of this piece's previous arrivals O never saw
            depth, cur, j = 0, src, k - 1
            while j >= 1:
                g = frames[j]
                if g["move"] and ((g["ply"] % 2 == 1) == (S == 0)) and chess.parse_square(g["move"][2:4]) == cur:
                    if g[view_key[O]][cur] == "?":
                        depth += 1
                        cur = chess.parse_square(g["move"][:2])
                    else:
                        break
                j -= 1
            if depth >= 1:
                tags.append("fog_route")
                counts[S]["fog_route_depth_total"] += depth
            # forcing chain: alternating captures from here
            chain = 1
            j = k + 1
            while j <= n and frames[j]["move"] and boards[j - 1].piece_at(chess.parse_square(frames[j]["move"][2:4])):
                chain += 1
                j += 1
            if chain >= 3:
                tags.append("forcing_chain")
        else:
            tags.append("quiet")
        # king threat after the move
        oking = after.king(o_col)
        if oking is not None and after.attackers(s_col, oking):
            tags.append("king_threat")
            if k == n and king_capture_ply[S] == n + 1:
                tags.append("king_capture")
            attackers = after.attackers(s_col, oking)
            if any(viewO_after[a] == "?" for a in attackers):
                tags.append("king_threat_unseen")
        # sacrifice: S gives >= 3 net over the next two plies
        if k + 1 <= n:
            loss = mats[S][k - 1] - mats[S][min(k + 1, n)]
            gain = mats[O][k - 1] - mats[O][min(k + 2, n)]
            if loss - gain >= 3:
                tags.append("sacrifice")
                if king_capture_ply[S] is not None and 0 < king_capture_ply[S] - k <= 8:
                    tags.append("king_hunt_sacrifice")
        dv = visible(viewS_after) - visible(viewS_before)
        if dv >= 3:
            tags.append("vision_gain")
        elif dv <= -3:
            tags.append("vision_loss")
        counts[S]["vision_total"] += visible(viewS_after)
        if ptype == "k":
            tags.append("king_move")
            if mv in ("e1g1", "e1c1", "e8g8", "e8c8") and chess.square_distance(src, dst) == 2:
                tags.append("castle")
            rank = chess.square_rank(dst)
            if (S == 0 and rank >= 2) or (S == 1 and rank <= 5):
                tags.append("king_leaves_home")
        if ptype == "q":
            rank = chess.square_rank(dst)
            if (S == 0 and rank >= 4) or (S == 1 and rank <= 3):
                tags.append("queen_raid")
        # after the move: S's queen attacked by an unseen piece; a piece walked into an unseen attacker
        for q in after.pieces(chess.QUEEN, s_col):
            att = after.attackers(o_col, q)
            if att and any(viewS_after[a] == "?" for a in att):
                tags.append("queen_exposed_unseen")
                break
        if victim is None and piece is not None and VALUE[ptype] >= 3 and ptype != "k":
            att = after.attackers(o_col, dst)
            if att and any(viewS_after[a] == "?" for a in att):
                tags.append("walk_into_unseen")
        sking = after.king(s_col)
        if sking is not None:
            home = 0 if S == 0 else 7
            if chess.square_rank(sking) == home:
                others = [sq for sq in chess.SquareSet(chess.BB_RANKS[home]) if sq != sking and after.piece_at(sq) and after.piece_at(sq).color == s_col]
                heavy = after.pieces(chess.ROOK, o_col) | after.pieces(chess.QUEEN, o_col)
                if not others and heavy:
                    tags.append("back_rank_bare")
        for t in tags:
            counts[S][t] += 1
        moves_out.append({"ply": p, "side": S, "move": mv, "piece": ptype, "tags": tags})
    return {"id": r["id"], "white": r["white"], "black": r["black"], "result": r["result"], "plies": n,
            "counts": {"white": dict(counts[0]), "black": dict(counts[1])}, "moves": moves_out}


KEYS = ["capture", "capture_unseen", "victim_walked_in", "long_strike", "fog_route", "forcing_chain",
        "king_threat", "king_threat_unseen", "sacrifice", "king_hunt_sacrifice", "vision_gain", "vision_loss",
        "king_move", "castle", "king_leaves_home", "queen_raid", "queen_exposed_unseen", "walk_into_unseen", "back_rank_bare"]


def aggregate(labelled, side_of) -> dict:
    """Per-100-move rates for the side selected by side_of(game) -> 'white'|'black'|None."""
    total = collections.Counter()
    games = 0
    for g in labelled:
        side = side_of(g)
        if side is None:
            continue
        games += 1
        c = g["counts"][side]
        for k, v in c.items():
            total[k] += v
    moves = total["moves"] or 1
    out = {"games": games, "moves": total["moves"], "visible_mean": total["vision_total"] / moves}
    for k in KEYS:
        out[k] = 100.0 * total[k] / moves
    out["capture_unseen_share"] = total["capture_unseen"] / (total["capture"] or 1)
    out["fog_route_depth_mean"] = total["fog_route_depth_total"] / (total["fog_route"] or 1)
    return out


def game_paths(raw: str, since: str | None = None) -> list[str]:
    """replay.json paths of the ingested games, created at or after `since`
    (ISO UTC) when given; the dates come from accepted.jsonl, so only the
    selected replays are opened"""
    if since is None:
        return sorted(glob.glob(os.path.join(raw, "games", "*", "replay.json")))
    ids = set()
    with open(os.path.join(raw, "accepted.jsonl")) as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if (row.get("createdAt") or "") >= since:
                ids.add(row["id"])
    paths = (os.path.join(raw, "games", i, "replay.json") for i in sorted(ids))
    return [p for p in paths if os.path.exists(p)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--versions", type=int, nargs="*", default=None, help="our arena versions to include")
    ap.add_argument("--opponents", default=None, help="JSON list of opponent names to include")
    ap.add_argument("--all-games", action="store_true", help="no team filter: every ingested game")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--json", default=None)
    ap.add_argument("--by-team", action="store_true", help="aggregate by team name over all included games")
    ap.add_argument("--min-games", type=int, default=20)
    ap.add_argument("--since", default=None, help="only games created at or after this UTC time (ISO, e.g. 2026-10-09)")
    args = ap.parse_args()
    opponents = set(json.load(open(args.opponents))) if args.opponents else None
    labelled, roles = [], []
    for path in game_paths(args.raw, args.since):
        try:
            r = json.load(open(path))
        except Exception:
            continue
        if not r.get("frames") or len(r["frames"]) < 3:
            continue
        ours = None
        if r.get("whitePlayerId") == TEAM_ID:
            ours, ver, opp = "white", r.get("whiteVersion"), r.get("black")
        elif r.get("blackPlayerId") == TEAM_ID:
            ours, ver, opp = "black", r.get("blackVersion"), r.get("white")
        if not args.all_games:
            if ours is None:
                continue
            if args.versions and ver not in args.versions:
                continue
            if opponents is not None and opp not in opponents:
                continue
        labelled.append(label_game(r))
        roles.append(ours)
        if args.limit and len(labelled) >= args.limit:
            break
    if args.by_team:
        teams = collections.Counter()
        for g in labelled:
            teams[g["white"]] += 1
            teams[g["black"]] += 1
        print(f"games {len(labelled)}; per-team rates per 100 moves (teams with >= {args.min_games} games)")
        header = ["team", "games", "visible"] + KEYS + ["capt_unseen_share", "fog_depth"]
        print(" | ".join(header))
        for team, cnt in teams.most_common():
            if cnt < args.min_games:
                continue
            agg = aggregate(labelled, lambda g, t=team: "white" if g["white"] == t else ("black" if g["black"] == t else None))
            row = [team, str(agg["games"]), f"{agg['visible_mean']:.1f}"] + [f"{agg[k]:.1f}" for k in KEYS] + [f"{agg['capture_unseen_share']:.2f}", f"{agg['fog_route_depth_mean']:.2f}"]
            print(" | ".join(row))
        if args.json:
            json.dump({"games": labelled}, open(args.json, "w"))
        return
    us = aggregate(labelled, lambda g: roles[labelled.index(g)])
    them = aggregate(labelled, lambda g: ("black" if roles[labelled.index(g)] == "white" else "white") if roles[labelled.index(g)] else None)
    print(f"games {len(labelled)}; rates per 100 moves (us | them)")
    print(f"{'tag':24} {'us':>8} {'them':>8}")
    print(f"{'visible squares (mean)':24} {us['visible_mean']:8.1f} {them['visible_mean']:8.1f}")
    for k in KEYS:
        print(f"{k:24} {us[k]:8.1f} {them[k]:8.1f}")
    print(f"{'capture_unseen_share':24} {us['capture_unseen_share']:8.2f} {them['capture_unseen_share']:8.2f}")
    print(f"{'fog_route_depth_mean':24} {us['fog_route_depth_mean']:8.2f} {them['fog_route_depth_mean']:8.2f}")
    if args.json:
        json.dump({"games": labelled, "us": us, "them": them}, open(args.json, "w"))


if __name__ == "__main__":
    main()
