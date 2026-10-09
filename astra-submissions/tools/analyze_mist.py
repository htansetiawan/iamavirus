"""Reproducible Mist replay anatomy using the course's exact FOW referee.

All truth-board labels are retrospective. They are not deployment features.
Reads a frozen public-API games page and cached replays; makes no requests.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics

import chess

TEAM = "Mist Opportunities"
VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
          chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


def board_string(board):
    return "".join(board.piece_at(s).symbol() if board.piece_at(s) else "-" for s in range(64))


def side_name(color):
    return "white" if color else "black"


def material(board, color):
    return sum(len(board.pieces(p, color)) * value for p, value in VALUES.items())


def safe_moves(board):
    """Truth-board one-ply survival, including castling/EP; not a fog oracle."""
    color = board.turn
    result = []
    for move in board.generate_pseudo_legal_moves():
        after = board.copy(stack=False)
        after.push(move)
        king = after.king(color)
        if king is not None and not after.is_attacked_by(not color, king):
            result.append(move.uci())
    return result


def describe_attackers(board, target_color, obs):
    king = board.king(target_color)
    if king is None:
        return []
    return [{"piece": board.piece_at(s).symbol(), "square": chess.square_name(s),
             "hidden": obs[s] == "?"}
            for s in board.attackers(not target_color, king)]


def wdl(rows):
    return {"games": len(rows), "wins": sum(r["score"] == 1 for r in rows),
            "draws": sum(r["score"] == .5 for r in rows),
            "losses": sum(r["score"] == 0 for r in rows)}


def analyze(replay, referee):
    color = replay["white"] == TEAM
    side, other = side_name(color), side_name(not color)
    score = .5 if replay["result"] == "1/2-1/2" else float((replay["result"] == "1-0") == color)
    frames = replay["frames"]
    board = referee.FowBoard()
    repetitions = Counter({referee.position_key(board): 1})
    row = {"id": replay["id"], "side": side, "version": replay[side + "Version"],
           "opponent": replay[other], "opponent_version": replay[other + "Version"],
           "createdAt": replay["createdAt"], "score": score, "reason": replay["reason"],
           "plies": len(frames) - 1, "castles": [], "moves": [], "captures": [],
           "threats": [], "king_capture_opportunities": [], "terminal": None,
           "opponent_advanced_kingside_pawn_first_ply": None,
           "opponent_two_advanced_kingside_pawns_first_ply": None}
    differences = [0]
    assert frames[0]["board"] == board_string(board)
    for view in ("white", "black"):
        assert frames[0][view] == referee.observation(board, view == "white")
    for ply in range(1, len(frames)):
        before, after = frames[ply - 1], frames[ply]
        assert after["ply"] == ply
        mover = board.turn
        mover_side = side_name(mover)
        move = board.parse_uci(after["move"])
        piece = board.piece_at(move.from_square)
        castle = board.is_castling(move)
        captured_square = move.to_square
        if board.is_en_passant(move):
            captured_square += -8 if mover else 8
        captured = board.piece_at(captured_square)
        was_attacked = board.is_attacked_by(not mover, board.king(mover))
        king_options = [m.uci() for m in board.generate_pseudo_legal_moves()
                        if board.piece_at(m.from_square).piece_type == chess.KING and board.is_capture(m)]
        if mover == color and king_options:
            hidden_fatal = []
            for uci in king_options:
                trial = board.copy(stack=False)
                trial.push(trial.parse_uci(uci))
                cover = describe_attackers(trial, mover, before[mover_side])
                if cover and all(a["hidden"] for a in cover):
                    hidden_fatal.append({"move": uci, "cover": cover})
            row["king_capture_opportunities"].append({"ply": ply, "options": king_options,
                "chosen": move.uci() in king_options, "played": move.uci(),
                "hidden_fatal_options": hidden_fatal,
                "has_safe_alternative": bool(safe_moves(board))})
        saved = board.copy(stack=False)
        board.push(move)
        assert board_string(board) == after["board"], (replay["id"], ply, "board")
        for view in ("white", "black"):
            assert after[view] == referee.observation(board, view == "white"), (replay["id"], ply, view)
        repetitions[referee.position_key(board)] += 1
        end = referee.outcome(board, repetitions)
        if ply < len(frames) - 1:
            assert end is None, (replay["id"], ply, end)
        elif replay["reason"] in ("King capturable", "Threefold repetition", "50-move rule", "No legal moves"):
            assert end == (replay["result"], replay["reason"]), (replay["id"], end)

        mist_king = board.king(color)
        differences.append(material(board, color) - material(board, not color))
        if captured:
            victim_side = side_name(not mover)
            previous_decision = frames[ply - 2] if ply >= 2 else before
            prev_move = chess.Move.from_uci(before["move"]) if before["move"] else None
            row["captures"].append({"ply": ply, "move": move.uci(), "by_mist": mover == color,
                "piece": piece.symbol(), "victim": captured.symbol(),
                "hidden_before_capture": before[victim_side][move.from_square] == "?",
                "hidden_at_victim_previous_decision": previous_decision[victim_side][move.from_square] == "?",
                "victim_just_moved_to_capture_square": prev_move is not None and prev_move.to_square == captured_square,
                "king_capture": piece.piece_type == chess.KING})
        if mover == color:
            elapsed = before["clocks"][0 if color else 1] + replay["timeControl"]["incrementSeconds"] - after["clocks"][0 if color else 1]
            assert elapsed >= -.002, (replay["id"], ply, elapsed)
            row["moves"].append({"ply": ply, "move": move.uci(), "piece": piece.symbol(),
                "elapsed": max(0, elapsed), "king": chess.square_name(mist_king),
                "capture": bool(captured), "castle": castle,
                "was_king_attacked": was_attacked,
                "visible_squares": 64 - before[side].count("?")})
            if castle:
                row["castles"].append({"ply": ply, "move": move.uci()})
        # Both directions, with visibility from the defender's actual reply view.
        attackers = describe_attackers(board, not mover, after[side_name(not mover)])
        own_king_safe = not board.is_attacked_by(not mover, board.king(mover))
        if attackers and own_king_safe and ply + 1 < len(frames):
            next_board = board.copy(stack=False)
            next_board.push(next_board.parse_uci(frames[ply + 1]["move"]))
            reply_failed = next_board.is_attacked_by(mover, next_board.king(not mover))
            row["threats"].append({"ply": ply, "move": move.uci(), "by_mist": mover == color,
                "attackers": attackers, "all_attackers_hidden": all(a["hidden"] for a in attackers),
                "reply_failed": reply_failed, "safe_replies": safe_moves(board)})
        if any(c["move"] in ("e1g1", "e8g8") for c in row["castles"]):
            storm_pawns = [s for s in board.pieces(chess.PAWN, not color)
                           if chess.square_file(s) >= 5 and
                           (chess.square_rank(s) <= 3 if color else chess.square_rank(s) >= 4)]
            for count, key in [(1, "opponent_advanced_kingside_pawn_first_ply"),
                               (2, "opponent_two_advanced_kingside_pawns_first_ply")]:
                if len(storm_pawns) >= count and row[key] is None:
                    row[key] = ply
        if end and end[1] == "King capturable":
            row["terminal"] = {"ply": ply, "loser": mover_side, "move": move.uci(),
                "piece": piece.symbol(), "capture": captured.symbol() if captured else None,
                "king_capture": bool(captured) and piece.piece_type == chess.KING,
                "king_already_attacked": was_attacked,
                "attackers_before": describe_attackers(saved, mover, before[mover_side]),
                "attackers_after": describe_attackers(board, mover, before[mover_side]),
                "safe_alternatives": safe_moves(saved),
                "mist_material_margin": differences[-1]}
    row["led_by3"] = any(min(differences[i:i+4]) >= 3 for i in range(len(differences) - 3))
    row["behind_by3"] = any(max(differences[i:i+4]) <= -3 for i in range(len(differences) - 3))
    row["final_material_margin"] = differences[-1]
    row["final_mist_clock"] = frames[-1]["clocks"][0 if color else 1]
    if row["terminal"]:
        t = row["terminal"]
        for attacker in t["attackers_after"]:
            sq = chess.parse_square(attacker["square"])
            placed = t["ply"]
            while placed > 0 and frames[placed - 1]["board"][sq] == attacker["piece"]:
                placed -= 1
            visible = [f["ply"] for f in frames[placed:t["ply"]]
                       if f[t["loser"]][sq] == attacker["piece"]]
            attacker["stationary_since_ply"] = placed
            attacker["last_visible_while_stationary"] = max(visible) if visible else None
    return row


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[f'{row["opponent"]} v{row["opponent_version"]}'].append(row)
    opening = {}
    for side in ("white", "black"):
        games = [r for r in rows if r["side"] == side]
        opening[side] = {"games": len(games), "first_ten_moves": [dict(Counter(
            r["moves"][i]["move"] for r in games if len(r["moves"]) > i)) for i in range(10)],
            "five_move_sequences": dict(Counter(" ".join(m["move"] for m in r["moves"][:5]) for r in games))}
    all_moves = [m for r in rows for m in r["moves"]]
    post_opening = [m for m in all_moves if m["ply"] > 24]
    result = {"record": wdl(rows), "by_opponent": {k: wdl(v) for k, v in sorted(groups.items())},
        "by_color": {s: wdl([r for r in rows if r["side"] == s]) for s in ("white", "black")},
        "opening": opening, "castled_games": sum(bool(r["castles"]) for r in rows),
        "castling_types": dict(Counter(c["move"] for r in rows for c in r["castles"])),
        "castling_plies": dict(Counter(c["ply"] for r in rows for c in r["castles"])),
        "own_moves": len(all_moves), "post_ply24_moves": len(post_opening),
        "post_ply24_piece_counts": dict(Counter(m["piece"].lower() for m in post_opening)),
        "king_destinations_white": dict(Counter(m["move"][2:4] for r in rows if r["side"] == "white" for m in r["moves"] if m["piece"].lower() == "k")),
        "king_destinations_black": dict(Counter(m["move"][2:4] for r in rows if r["side"] == "black" for m in r["moves"] if m["piece"].lower() == "k")),
        "median_move_seconds": statistics.median(m["elapsed"] for m in all_moves),
        "max_move_seconds": max(m["elapsed"] for m in all_moves),
        "min_final_clock": min(r["final_mist_clock"] for r in rows),
        "by_outcome": {}}
    for label, score in [("wins", 1), ("draws", .5), ("losses", 0)]:
        group = [r for r in rows if r["score"] == score]
        result["by_outcome"][label] = {"games": len(group),
            "median_plies": statistics.median(r["plies"] for r in group) if group else None,
            "led_by3": sum(r["led_by3"] for r in group), "behind_by3": sum(r["behind_by3"] for r in group),
            "kingside_advanced_pawn": sum(r["opponent_advanced_kingside_pawn_first_ply"] is not None for r in group),
            "kingside_two_advanced_pawns": sum(r["opponent_two_advanced_kingside_pawns_first_ply"] is not None for r in group)}
    result["threats"] = {}
    for label, by_mist in [("by_mist", True), ("against_mist", False)]:
        threats = [t for r in rows for t in r["threats"] if t["by_mist"] == by_mist]
        result["threats"][label] = {"total": len(threats), "hidden": sum(t["all_attackers_hidden"] for t in threats),
            "reply_failed": sum(t["reply_failed"] for t in threats),
            "by_visibility": {visibility: {
                "with_safe_reply": sum(bool(t["safe_replies"]) and t["all_attackers_hidden"] == hidden for t in threats),
                "avoidable_reply_failures": sum(bool(t["safe_replies"]) and t["reply_failed"] and t["all_attackers_hidden"] == hidden for t in threats),
                "no_safe_reply": sum(not t["safe_replies"] and t["all_attackers_hidden"] == hidden for t in threats)}
                for visibility, hidden in [("all_attackers_hidden", True), ("some_attacker_visible", False)]}}
    result["terminal"] = {}
    for label, score in [("mist_losses", 0), ("mist_wins", 1)]:
        ts = [r["terminal"] for r in rows if r["score"] == score and r["terminal"]]
        result["terminal"][label] = {"games": len(ts), "with_safe_alternative": sum(bool(t["safe_alternatives"]) for t in ts),
            "not_previously_attacked": sum(not t["king_already_attacked"] for t in ts),
            "king_captures": sum(t["king_capture"] for t in ts),
            "avoidable_king_captures": sum(t["king_capture"] and bool(t["safe_alternatives"]) for t in ts)}
    result["king_captures"] = {"opportunity_turns": sum(len(r["king_capture_opportunities"]) for r in rows),
        "chosen_turns": sum(o["chosen"] for r in rows for o in r["king_capture_opportunities"])}
    traps = [o for r in rows for o in r["king_capture_opportunities"]
             if o["hidden_fatal_options"] and o["has_safe_alternative"]]
    result["king_captures"].update({"hidden_fatal_offers_with_safe_alternative": len(traps),
        "hidden_fatal_offers_chosen": sum(any(c["move"] == o["played"] for c in o["hidden_fatal_options"]) for o in traps)})
    return result


def tactical_cases(rows):
    cases = []
    for row in rows:
        terminal = row["terminal"]
        if terminal and row["opponent"] == "IAmAVirus" and row["score"] == 1:
            cases.append({"game": row["id"], "kind": "our_hidden_king_failure",
                "decision_ply": terminal["ply"], "side": terminal["loser"],
                "chosen": terminal["move"], "surviving_alternatives": terminal["safe_alternatives"],
                "attackers": terminal["attackers_after"]})
        for offer in row["king_capture_opportunities"]:
            if offer["hidden_fatal_options"] and offer["has_safe_alternative"]:
                cases.append({"game": row["id"], "kind": "mist_hidden_bait_opportunity",
                    "decision_ply": offer["ply"], "side": row["side"], "chosen": offer["played"],
                    "fatal_options": offer["hidden_fatal_options"],
                    "accepted_fatal_bait": any(c["move"] == offer["played"] for c in offer["hidden_fatal_options"])})
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--referee", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("course_referee", args.referee)
    referee = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(referee)
    listing = json.loads((args.corpus / "games.json").read_text())
    assert listing["nextCursor"] is None, "Expected complete frozen snapshot"
    rows = []
    for game in listing["games"]:
        path = args.corpus / "games" / game["id"] / "replay.json"
        raw = path.read_bytes()
        replay = json.loads(raw)
        for key in ("id", "white", "black", "result", "whiteVersion", "blackVersion"):
            assert replay[key] == game[key], (game["id"], key)
        row = analyze(replay, referee)
        row["replay_sha256"] = hashlib.sha256(raw).hexdigest()
        rows.append(row)
    assert len(rows) == listing["summary"]["total"]
    assert len({r["id"] for r in rows}) == len(rows)
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_at": (args.corpus / "fetched_at.txt").read_text().strip(),
        "corpus": str(args.corpus), "referee": str(args.referee),
        "referee_sha256": hashlib.sha256(args.referee.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "validation": {"replays": len(rows), "frames": sum(r["plies"] + 1 for r in rows),
            "checks": ["pseudo-legal moves", "full boards", "both observations", "terminal rules", "listing identity"]},
        "summary": summarize(rows),
        "against_i_am_a_virus": summarize([r for r in rows if r["opponent"] == "IAmAVirus"]),
        "games": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.output.with_name("summary.json").write_text(json.dumps(
        {k: v for k, v in payload.items() if k != "games"}, indent=2) + "\n")
    args.output.with_name("tactical-cases.json").write_text(json.dumps({
        "snapshot_at": payload["snapshot_at"],
        "usage": "Replay diagnostics, not an independent evaluation set for models trained on these games. "
                 "Load full observation/action history; do not initialize a recurrent policy at the final board. "
                 "decision_ply is the move being chosen; the decision frame is ply-1. "
                 "True boards, hidden cover and safe alternatives are audit/training labels only. "
                 "Bait offers include repeated turns: split and weight by whole game.",
        "cases": tactical_cases(rows)}, indent=2) + "\n")
    print(json.dumps({"validation": payload["validation"], "record": payload["summary"]["record"]}, indent=2))


if __name__ == "__main__":
    main()
