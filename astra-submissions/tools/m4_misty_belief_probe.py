#!/usr/bin/env python3
"""Replay v30 Misty's exact belief updates at selected decision plies.

The archive supplies its PEnumerator implementation and Rust state extension.
No strategy search is run: for these probes |P| stays below the configured
500,000 cap, so its belief state is independent of search-time RNG consumption.
This checks belief support, not move quality or the actor's search roots.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import zipfile

TEAM_ID = "a2c35173659545c99752376a70418438"


def install_archive(archive: Path, lib: Path):
    lib.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            name = info.filename
            if not name.startswith("lib/fow_chess/") and not name.startswith("lib/fow_rust/"):
                continue
            rel = Path(name).relative_to("lib")
            # Only package source and the Python extension are needed here.
            if rel.suffix not in (".py", ".so"):
                continue
            target = lib / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read(info))


def encoded_board(board):
    return "".join(board.piece_at(sq).symbol() if board.piece_at(sq) else "-"
                   for sq in range(64))


def observe(text, chess, own_capture=None, landing=None):
    visible = chess.SquareSet()
    pieces = {}
    for square, ch in enumerate(text):
        if ch == "?":
            continue
        visible.add(square)
        if ch != "-":
            pieces[square] = chess.Piece.from_symbol(ch)
    from fow_chess.observation import Observation
    return Observation(visibility_mask=visible, visible_pieces=pieces,
                       own_capture_square=own_capture,
                       opp_capture_landing_square=landing)


def own_squares(text, color):
    return {sq for sq, ch in enumerate(text)
            if ch not in "?-" and ch.isupper() == color}


def piece_at_fen_square(fen, square):
    placement = fen.split(" ", 1)[0]
    ranks = placement.split("/")
    file_index, rank_index = square & 7, square >> 3
    row = ranks[7 - rank_index]
    file = 0
    for ch in row:
        if ch.isdigit():
            file += int(ch)
        else:
            if file == file_index:
                return ch
            file += 1
    return None


def analyze_game(game_path, targets, cap, seed, referee, chess, PEnumerator, belief_fen):
    game = json.loads(game_path.read_text())
    frames = game["frames"]
    if game.get("whitePlayerId") == TEAM_ID:
        color = chess.WHITE
        color_name = "white"
        opponent = game["black"]
    elif game.get("blackPlayerId") == TEAM_ID:
        color = chess.BLACK
        color_name = "black"
        opponent = game["white"]
    else:
        raise ValueError(f"not an IAmAVirus game: {game.get('id')}")
    enumerator = PEnumerator(color, max_size=cap, rng=__import__("random").Random(seed),
                             use_rust_state=True)
    board = chess.Board()
    previous_view = frames[0][color_name]
    requested = dict(targets)
    results = []
    for ply in range(1, max(requested) + 1):
        frame = frames[ply]
        move = chess.Move.from_uci(frame["move"])
        assert move in referee.fow_moves(board), (game["id"], ply, move.uci())
        mover = board.turn
        view = frame[color_name]
        obs = observe(view, chess)
        if mover == color:
            enumerator.update_own_move(move, obs)
        else:
            lost = own_squares(previous_view, color) - own_squares(view, color)
            captured = next(iter(lost)) if len(lost) == 1 else None
            landing = (captured if captured is not None and captured in obs.visible_pieces
                       and obs.visible_pieces[captured].color != color else None)
            enumerator.update_opp_move(observe(view, chess, captured, landing))
        board.push(move)
        previous_view = view
        assert encoded_board(board) == frame["board"], (game["id"], ply, "board mismatch")
        assert referee.observation(board, color) == view, (game["id"], ply, "view mismatch")
        if ply not in requested:
            continue
        source_square = chess.parse_square(requested[ply])
        truth_fen = belief_fen(board)
        counts = Counter()
        truth_present = False
        for fen in enumerator.iter_positions():
            counts[piece_at_fen_square(fen, source_square)] += 1
            if fen == truth_fen:
                truth_present = True
        results.append({"decision_ply": ply, "side": color_name,
                        "source_square": requested[ply], "true_piece": board.piece_at(source_square).symbol()
                        if board.piece_at(source_square) else None,
                        "belief_size": enumerator.size,
                        "cap": cap, "cap_fires": enumerator.downsample_count,
                        "true_board_in_belief": truth_present,
                        "opponent_piece_counts_at_source": dict(
                            sorted(counts.items(), key=lambda item: item[0] or ""))})
    return {"game": game["id"], "opponent": opponent,
            "result": game.get("result"), "reason": game.get("reason"),
            "game_sha256": hashlib.sha256(game_path.read_bytes()).hexdigest(),
            "probes": results}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=Path, default=Path("fable-submissions/iamavirus-v30-misty-4s.zip"))
    ap.add_argument("--games-root", type=Path, default=Path("data/raw/games"))
    ap.add_argument("--kit", type=Path, default=Path("/home/henrytan/git/fow-starter"))
    ap.add_argument("--chess-site-packages", type=Path,
                    default=Path("/home/henrytan/git/fow-starter/.venv/lib/python3.12/site-packages"))
    ap.add_argument("--cap", type=int, default=500000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="misty-v30-belief-") as temp:
        lib = Path(temp) / "lib"
        install_archive(args.archive, lib)
        sys.path.insert(0, str(args.chess_site_packages))
        sys.path.insert(0, str(lib))
        # Avoid importing fow_chess.__init__, which eagerly imports search,
        # NumPy and Stockfish. This probe needs only the shipped belief code.
        package = types.ModuleType("fow_chess")
        package.__path__ = [str(lib / "fow_chess")]
        sys.modules["fow_chess"] = package
        import chess
        sys.path.insert(0, str(args.kit))
        import referee
        from fow_chess.p_enum.enumerator import PEnumerator
        from fow_chess.p_enum.fen import belief_fen
        archive_sha = hashlib.sha256(args.archive.read_bytes()).hexdigest()
        enumerator_path = lib / "fow_chess/p_enum/enumerator.py"
        rust_files = list((lib / "fow_rust").glob("*.so"))
        if not rust_files:
            raise RuntimeError("archive has no Rust extension")
        probes = [
            ("4bkwxxng", [(53, "e3")]),
            ("69nmui22", [(36, "f6"), (38, "c3")]),
        ]
        games = [analyze_game(args.games_root / gid / "replay.json", targets,
                              args.cap, args.seed, referee, chess, PEnumerator, belief_fen)
                 for gid, targets in probes]
        result = {"classification": "v30 Misty belief-update replay; exact P support, not search policy",
                  "archive": str(args.archive), "archive_sha256": archive_sha,
                  "profile": "v1.6 (adapter default)", "p_max_size": args.cap,
                  "seed_for_cap_resampling": args.seed,
                  "enumerator_source_sha256": hashlib.sha256(enumerator_path.read_bytes()).hexdigest(),
                  "rust_extension_sha256": hashlib.sha256(rust_files[0].read_bytes()).hexdigest(),
                  "referee_sha256": hashlib.sha256((args.kit / "referee.py").read_bytes()).hexdigest(),
                  "python_chess_version": chess.__version__, "games": games,
                  "limitations": [
                      "This replays the shipped belief updater and observations, not pick_move/search.",
                      "All recorded belief sizes are below the cap, so search-time RNG draws cannot change these P sets.",
                      "The 32-root search sample and strategy ranking are not reconstructed.",
                  ]}
    result["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"archive_sha256": result["archive_sha256"],
                      "games": [{"game": g["game"], "probes": g["probes"]}
                                for g in result["games"]]}, indent=2))


if __name__ == "__main__":
    main()
