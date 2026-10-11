#!/usr/bin/env python3
"""Find realized hidden queen forks with an earlier king-preemption option.

Offline retrospective screen only. It uses full replay boards to discover a
motif, then checks every move with the course Fog of War referee. A match is
not evidence that the actor could know the hidden board or that preemption
would improve game value. The output is for independent-case curation.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


TEAM_ID = "a2c35173659545c99752376a70418438"
TOP_SIX = {"Greek Gift", "Knight Vision", "Decent Chess Bot",
           "Strongly Invisible", "duck", "Instructors"}


def board_from_frame(board, frames, upto):
    for i in range(1, upto + 1):
        board.push_uci(frames[i]["move"])
    encoded = ''.join(board.piece_at(sq).symbol() if board.piece_at(sq) else '-'
                      for sq in range(64))
    assert encoded == frames[upto]["board"], (upto, encoded, frames[upto]["board"])
    return board


def hidden_forks(board, defender, referee, chess):
    """Enumerate enemy queen moves that invisibly attack defender king + rook/queen."""
    attacker = not defender
    seen = referee.observation(board, defender)
    queens = [sq for sq, piece in board.piece_map().items()
              if piece.color == attacker and piece.piece_type == chess.QUEEN]
    probe = board.copy(stack=True)
    probe.turn = attacker
    result = []
    for move in referee.fow_moves(probe):
        if move.from_square not in queens:
            continue
        after = probe.copy(stack=True)
        after.push(move)
        king = after.king(defender)
        if king is None or not after.is_attacked_by(attacker, king):
            continue
        attacked_major = [sq for sq, piece in after.piece_map().items()
                          if piece.color == defender
                          and piece.piece_type in (chess.QUEEN, chess.ROOK)
                          and after.is_attacked_by(attacker, sq)]
        if not attacked_major:
            continue
        dest_observation = referee.observation(after, defender)[move.to_square]
        result.append({"uci": move.uci(), "from": chess.square_name(move.from_square),
                       "to": chess.square_name(move.to_square),
                       "source_hidden": seen[move.from_square] == '?',
                       "destination_observation_after": dest_observation,
                       "attacked_major": sorted(chess.square_name(sq) for sq in attacked_major),
                       "observation_at_source": seen[move.from_square]})
    return result


def preemptions(board, defender, targets, referee, chess):
    """Check referee-legal king moves against the same and all remaining forks."""
    reps = Counter({referee.position_key(board): 1})
    out = []
    for move in referee.fow_moves(board):
        piece = board.piece_at(move.from_square)
        if piece is None or piece.piece_type != chess.KING:
            continue
        after = board.copy(stack=True)
        after.push(move)
        result = referee.outcome(after, Counter({referee.position_key(after): 1}))
        if result and result[0] not in ('1/2-1/2',):
            continue
        remain = hidden_forks(after, defender, referee, chess)
        neutralized = [f["uci"] for f in targets if not any(
            x["uci"] == f["uci"] for x in remain)]
        if neutralized:
            out.append({"move": move.uci(), "remaining_hidden_forks": len(remain),
                        "neutralized_observed_forks": neutralized,
                        "all_hidden_forks_neutralized": len(remain) == 0})
    return out


def survival_profile(board_after_defender, queen_uci, defender, referee, chess):
    """Count referee-legal, nonterminal replies after the same queen move."""
    attacker = not defender
    state = board_after_defender.copy(stack=True)
    state.turn = attacker
    queen_move = chess.Move.from_uci(queen_uci)
    if queen_move not in referee.fow_moves(state):
        return {"queen_move_legal": False, "reply_count": 0,
                "immediate_survival_replies": [], "still_forks_king_and_major": False}
    state.push(queen_move)
    queen_square = queen_move.to_square
    attacks = state.attacks(queen_square)
    king = state.king(defender)
    major_targets = sorted(chess.square_name(sq) for sq, piece in state.piece_map().items()
                           if piece.color == defender
                           and piece.piece_type in (chess.QUEEN, chess.ROOK)
                           and sq in attacks)
    king_attacked = king in attacks if king is not None else False
    replies = []
    for move in referee.fow_moves(state):
        after = state.copy(stack=True)
        after.push(move)
        result = referee.outcome(after, Counter({referee.position_key(after): 1}))
        winner = None
        if result and result[0] != '1/2-1/2':
            winner = 'white' if result[0] == '1-0' else 'black'
        if winner != ('white' if attacker else 'black'):
            replies.append(move.uci())
    return {"queen_move_legal": True, "reply_count": len(referee.fow_moves(state)),
            "king_attacked_after_queen_move": king_attacked,
            "major_targets_attacked_after_queen_move": major_targets,
            "still_forks_king_and_major": king_attacked and bool(major_targets),
            "immediate_survival_replies": replies}


def analyze_game(game, referee, chess):
    frames = game.get("frames", [])
    if len(frames) < 4:
        return []
    hits = []
    board = referee.FowBoard()
    for ply in range(0, len(frames) - 3):
        if ply:
            board.push_uci(frames[ply]["move"])
        side = board.turn
        side_name = "white" if side else "black"
        side_id = game.get(side_name + "PlayerId")
        if side_id != TEAM_ID:
            continue
        actual_own = frames[ply + 1].get("move")
        actual_queen = frames[ply + 2].get("move")
        if not actual_own or not actual_queen:
            continue
        root_forks = hidden_forks(board, side, referee, chess)
        if not root_forks:
            continue
        defender_move = chess.Move.from_uci(actual_own)
        if defender_move not in referee.fow_moves(board):
            continue
        after_own = board.copy(stack=True)
        after_own.push(defender_move)
        post_forks = hidden_forks(after_own, side, referee, chess)
        actual = [f for f in post_forks if f["uci"] == actual_queen]
        if not actual or not any(f["source_hidden"] for f in actual):
            continue
        # Require the same hidden queen-fork move to have been available at the
        # earlier decision. This excludes traps created only by our chosen move
        # and queens that were already visible to us before that move.
        root_actual = [f for f in root_forks if f["uci"] == actual_queen
                       and f["source_hidden"]]
        if not root_actual:
            continue
        actions = preemptions(board, side, root_forks, referee, chess)
        if not actions:
            continue
        # Check exact outcome after the historical defender response when it is
        # present in the replay; this is a terminal-rule label, not evaluation.
        after_actual = after_own.copy(stack=True)
        queen_move = chess.Move.from_uci(actual_queen)
        if queen_move not in referee.fow_moves(after_actual):
            continue
        after_actual.push(queen_move)
        next_move = frames[ply + 3].get("move")
        terminal = None
        if next_move:
            response = chess.Move.from_uci(next_move)
            if response in referee.fow_moves(after_actual):
                after_actual.push(response)
                terminal = referee.outcome(after_actual, Counter({referee.position_key(after_actual): 1}))
        if not all(f["source_hidden"] for f in actual):
            continue
        if not any(a["all_hidden_forks_neutralized"] for a in actions):
            # Still retain a partial preemption result for later human review.
            pass
        actual_profile = survival_profile(after_own, actual_queen, side, referee, chess)
        for option in actions:
            hypothetical = board.copy(stack=True)
            km = chess.Move.from_uci(option["move"])
            hypothetical.push(km)
            option["same_queen_move_survival"] = survival_profile(
                hypothetical, actual_queen, side, referee, chess)
        hits.append({"game": game.get("id"), "white": game.get("white"),
                     "black": game.get("black"), "whiteVersion": game.get("whiteVersion"),
                     "blackVersion": game.get("blackVersion"), "ply": ply,
                     "defender": side_name, "opponent": game.get("black" if side else "white"),
                     "defender_move": actual_own, "actual_hidden_queen_fork": actual[0],
                     "hidden_forks_before_defender_move": root_forks,
                     "preemptive_king_moves": actions,
                     "historical_response": next_move, "response_outcome": terminal,
                     "actual_line_immediate_survival": actual_profile})
    return hits


def list_candidates(root, limit, outcome_filter):
    found = []
    for path in root.glob("*/listing.json"):
        try:
            row = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if row.get("reason") != "King capturable" or row.get("result") not in ("0-1", "1-0"):
            continue
        if row.get("whitePlayerId") == TEAM_ID:
            side, opp = "white", row.get("black")
        elif row.get("blackPlayerId") == TEAM_ID:
            side, opp = "black", row.get("white")
        else:
            continue
        if row.get(side + "Version") != 30 or opp not in TOP_SIX:
            continue
        ours_won = (row.get("result") == "1-0") == (side == "white")
        if outcome_filter == "loss" and ours_won:
            continue
        if outcome_filter == "win" and not ours_won:
            continue
        path_replay = path.parent / "replay.json"
        if path_replay.is_file():
            found.append((row.get("createdAt", ""), path_replay))
    found.sort(reverse=True)
    return [p for _, p in found[:limit]]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--games-root", type=Path, default=Path("data/raw/games"))
    ap.add_argument("--game", type=Path, action="append", default=[])
    ap.add_argument("--kit", type=Path, default=Path("/home/henrytan/git/fow-starter"))
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--outcome", choices=("loss", "win", "all"), default="loss",
                    help="Filter v30 top-six decisive games by our outcome")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    sys.path.insert(0, str(args.kit))
    import chess
    import referee
    paths = args.game or list_candidates(args.games_root, args.limit, args.outcome)
    matches = []
    checked = []
    for path in paths:
        game = json.loads(path.read_text())
        if game.get("reason") != "King capturable":
            continue
        # Validate every recorded move and position before scanning it.
        board = referee.FowBoard()
        frames = game["frames"]
        for ply in range(1, len(frames)):
            move = chess.Move.from_uci(frames[ply]["move"])
            assert move in referee.fow_moves(board), (game.get("id"), ply, move.uci())
            board.push(move)
            encoded = ''.join(board.piece_at(sq).symbol() if board.piece_at(sq) else '-'
                              for sq in range(64))
            assert encoded == frames[ply]["board"], (game.get("id"), ply, "board mismatch")
            assert referee.observation(board, chess.WHITE) == frames[ply]["white"]
            assert referee.observation(board, chess.BLACK) == frames[ply]["black"]
        checked.append({"id": game.get("id"), "plies": len(frames) - 1,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        matches.extend(analyze_game(game, referee, chess))
    result = {"classification": "offline retrospective discovery scan; not a policy or Elo test",
              "team_id": TEAM_ID, "team_version": 30, "outcome_filter": args.outcome,
              "games_checked": len(checked),
              "frames_checked": sum(g["plies"] + 1 for g in checked),
              "matches": matches, "game_hashes": checked,
              "referee_sha256": hashlib.sha256((args.kit / "referee.py").read_bytes()).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "limitations": ["full replay truth is used only to detect candidate motifs",
                  "hidden square at the current frame is not proof the bot's posterior supported it",
                  "one-ply fork presence and immediate survival do not establish continuation value",
                  "potential forks in winner's games are not included in this loss-only cohort"]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("outcome_filter", "games_checked", "frames_checked", "matches")}, indent=2))


if __name__ == "__main__":
    main()
