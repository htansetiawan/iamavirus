"""Curate our own arena games into a labelled decision table and a loss taxonomy.

    python -m learning.curate --raw data/raw --output gold

Every decision IAmAVirus made in every cached arena game becomes one row with
truth-derived labels: how many legal moves were safe on the true board, whether
the move we played lost the king, what material it exposed to the opponent's
best immediate capture and whether that capturer was hidden from us, what the
opponent actually did next, and how the game ended. Lost games get a terminal
class and a "first decisive error" ply. The table is the gold data for the
danger head, for opponent modelling and for deciding what to fix next; the
taxonomy report says where the losses come from, by version and opponent.

Outputs (committed, unlike data/):
    gold/iamavirus-decisions.jsonl.gz    one row per decision
    gold/iamavirus-games.jsonl           one row per game with its terminal class
    reports/IAmAVirus replay analysis.md the taxonomy and tables
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
import sys
from pathlib import Path

from . import ingest, rules

TEAM = "a2c35173659545c99752376a70418438"
VALUE = [1, 3, 3, 5, 9, 100]  # king counted as 100 for exposure arithmetic
PIECE = "PNBRQK"


def material(board: rules.Board, color: int) -> int:
    return sum(VALUE[board.piece_at(s) % 6] for s in range(64)
               if board.piece_at(s) >= 0 and board.piece_at(s) // 6 == color and board.piece_at(s) % 6 != 5)


def best_capture(board: rules.Board, side: int) -> tuple[int, str | None]:
    """The opponent's best immediate net capture against `side` after `side` moved
    (board.side is the opponent). Net = victim value minus the capturer's value
    if `side` can recapture the destination. Returns (net, uci)."""
    best, best_move = 0, None
    for uci in board.legal_moves():
        to = rules.square_index(uci[2:4])
        victim = board.piece_at(to)
        if victim < 0:
            if board.en_passant == to and board.piece_at(rules.square_index(uci[:2])) % 6 == 0:
                victim_value = 1
            else:
                continue
        else:
            victim_value = VALUE[victim % 6]
        after = board.copy()
        after.push(uci)
        capturer_value = VALUE[after.piece_at(to) % 6]
        recapture = after.is_attacked(to, side)
        net = victim_value - (capturer_value if recapture else 0)
        if net > best:
            best, best_move = net, uci
    return best, best_move


def classify_game(rows: list[dict], lost: bool, reason: str) -> dict:
    if not lost:
        return {"terminal_class": "won-or-drawn", "first_error_ply": None}
    if reason != "King capturable":
        return {"terminal_class": f"technical:{reason}", "first_error_ply": None}
    last = rows[-1]
    if last["played_loses_king"]:
        if last["king_moved"]:
            cls = "king-moved-into-hidden-attack" if last["king_attacker_hidden"] else "king-moved-into-visible-attack"
        else:
            cls = "exposed-king-to-hidden-attack" if last["king_attacker_hidden"] else "exposed-king-to-visible-attack"
        if last["safe_moves"] == 0:
            cls = "already-lost-no-safe-move"
    else:
        cls = "lost-on-opponent-move"
    # First decisive error: the last of our decisions that exposed >= 3 points
    # to a capture that then happened, or the fatal move itself.
    first_error = last["ply"]
    for row in rows:
        if row["exposure"] >= 3 and row["material_swing_next"] <= -3:
            first_error = row["ply"]
            break
    return {"terminal_class": cls, "first_error_ply": first_error}


def curate(raw: Path, output: Path, reports: Path) -> dict:
    store = ingest.RawStore(raw)
    games_out = []
    decisions_out = []
    for line in store.accepted.read_text().splitlines():
        meta = json.loads(line)
        if TEAM not in (meta.get("whitePlayerId"), meta.get("blackPlayerId")):
            continue
        rep = json.loads((store.games / meta["id"] / "replay.json").read_text())
        states, problems = ingest.validate_replay(rep)
        if problems:
            continue
        frames = rep["frames"]
        side = 0 if rep["whitePlayerId"] == TEAM else 1
        other = side ^ 1
        version = rep["whiteVersion"] if side == 0 else rep["blackVersion"]
        opponent = rep["black"] if side == 0 else rep["white"]
        opp_version = rep["blackVersion"] if side == 0 else rep["whiteVersion"]
        result = rep["result"]
        lost = (result == "0-1") == (side == 0) and result != "1/2-1/2"
        won = (result == "1-0") == (side == 0) and result != "1/2-1/2"
        rows = []
        for t in range(side, len(frames) - 1, 2):
            board = states[t].board
            move = frames[t + 1]["move"]
            legal = board.legal_moves()
            safe = [m for m in legal if not board.move_loses_king(m)]
            view = frames[t]["white" if side == 0 else "black"]
            after = states[t + 1].board
            king = after.king_square(side)
            loses = after.mover_lost()
            king_attacker_hidden = None
            if loses and king >= 0:
                # squares of enemy pieces attacking the king; hidden if unseen in our view
                attackers = []
                for sq in range(64):
                    p = after.piece_at(sq)
                    if p >= 0 and p // 6 == other:
                        bs = list(after.board_string())
                        for o in range(64):
                            q = after.piece_at(o)
                            if q >= 0 and q // 6 == other and o != sq:
                                bs[o] = "-"
                        if rules.Board.from_board_string("".join(bs), other).is_attacked(king, other):
                            attackers.append(sq)
                king_attacker_hidden = all(view[sq] == "?" for sq in attackers) if attackers else None
            exposure, exposure_move = best_capture(after, side) if not loses else (0, None)
            exposure_hidden = None
            if exposure_move:
                exposure_hidden = view[rules.square_index(exposure_move[:2])] == "?"
            mover = board.piece_at(rules.square_index(move[:2])) % 6
            opp_reply = frames[t + 2]["move"] if t + 2 < len(frames) else None
            swing = None
            if t + 2 < len(frames):
                before = material(board, side) - material(board, other)
                after2 = states[t + 2].board
                swing = (material(after2, side) - material(after2, other)) - before
            row = {
                "game": meta["id"], "version": version, "opponent": opponent, "opponent_version": opp_version,
                "side": "w" if side == 0 else "b", "ply": t, "move": move, "piece": PIECE[mover],
                "legal_moves": len(legal), "safe_moves": len(safe), "played_loses_king": loses,
                "king_moved": mover == 5, "king_attacker_hidden": king_attacker_hidden,
                "exposure": exposure, "exposure_capture": exposure_move, "exposure_hidden": exposure_hidden,
                "opponent_reply": opp_reply, "material_swing_next": swing,
                "plies_to_end": len(frames) - 1 - t, "result": "L" if lost else "W" if won else "D",
                "view": view, "board": frames[t]["board"],
            }
            rows.append(row)
        klass = classify_game(rows, lost, rep["reason"]) if rows else {"terminal_class": "no-decisions", "first_error_ply": None}
        games_out.append({"game": meta["id"], "version": version, "opponent": opponent, "opponent_version": opp_version,
                          "side": "w" if side == 0 else "b", "result": "L" if lost else "W" if won else "D",
                          "reason": rep["reason"], "plies": len(frames) - 1, "created": rep.get("createdAt"), **klass})
        decisions_out += rows
    output.mkdir(parents=True, exist_ok=True)
    with gzip.open(output / "iamavirus-decisions.jsonl.gz", "wt") as handle:
        for row in decisions_out:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")
    (output / "iamavirus-games.jsonl").write_text("\n".join(json.dumps(g) for g in games_out) + "\n")
    summary = summarize(games_out, decisions_out)
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "IAmAVirus replay analysis.md").write_text(render(summary, games_out, decisions_out))
    return summary


def summarize(games, decisions) -> dict:
    by_version = collections.defaultdict(collections.Counter)
    taxonomy = collections.defaultdict(collections.Counter)
    for g in games:
        by_version[g["version"]][g["result"]] += 1
        if g["result"] == "L":
            taxonomy[g["version"]][g["terminal_class"]] += 1
    decision_stats = collections.defaultdict(lambda: collections.Counter())
    for d in decisions:
        v = d["version"]
        decision_stats[v]["decisions"] += 1
        if d["played_loses_king"]:
            decision_stats[v]["fatal"] += 1
            if d["safe_moves"] > 0:
                decision_stats[v]["fatal_with_safe_alternative"] += 1
        if d["exposure"] >= 3:
            decision_stats[v]["exposed_3plus"] += 1
            if d["exposure_hidden"]:
                decision_stats[v]["exposed_3plus_hidden"] += 1
            if d["material_swing_next"] is not None and d["material_swing_next"] <= -3:
                decision_stats[v]["exposed_3plus_punished"] += 1
    return {"games": len(games), "decisions": len(decisions),
            "by_version": {v: dict(c) for v, c in sorted(by_version.items())},
            "loss_taxonomy": {v: dict(c) for v, c in sorted(taxonomy.items())},
            "decision_stats": {v: dict(c) for v, c in sorted(decision_stats.items())}}


def render(summary, games, decisions) -> str:
    lines = ["# IAmAVirus replay analysis", "",
             f"{summary['games']} arena games of IAmAVirus (all versions), {summary['decisions']} of our decisions, "
             "labelled from the true board offline (`learning/curate.py`; rows in `gold/`).", "",
             "## Record by version", "", "| version | W | D | L |", "|---|---|---|---|"]
    for v, c in summary["by_version"].items():
        lines.append(f"| {v} | {c.get('W', 0)} | {c.get('D', 0)} | {c.get('L', 0)} |")
    lines += ["", "## How the losses end (terminal class, by version)", "",
              "| version | " + " | ".join(sorted({k for c in summary['loss_taxonomy'].values() for k in c})) + " |"]
    classes = sorted({k for c in summary['loss_taxonomy'].values() for k in c})
    lines.append("|---|" + "---|" * len(classes))
    for v, c in summary["loss_taxonomy"].items():
        lines.append(f"| {v} | " + " | ".join(str(c.get(k, 0)) for k in classes) + " |")
    lines += ["", "## Decision-level hazards, by version", "",
              "| version | decisions | fatal moves | fatal with a safe alternative | exposed ≥3 to a capture | …capturer hidden | …and punished next ply |",
              "|---|---|---|---|---|---|---|"]
    for v, c in summary["decision_stats"].items():
        lines.append(f"| {v} | {c.get('decisions', 0)} | {c.get('fatal', 0)} | {c.get('fatal_with_safe_alternative', 0)} | "
                     f"{c.get('exposed_3plus', 0)} | {c.get('exposed_3plus_hidden', 0)} | {c.get('exposed_3plus_punished', 0)} |")
    # Opponent table
    by_opp = collections.defaultdict(collections.Counter)
    for g in games:
        by_opp[g["opponent"]][g["result"]] += 1
    lines += ["", "## Record by opponent (all versions)", "", "| opponent | W | D | L |", "|---|---|---|---|"]
    for o, c in sorted(by_opp.items(), key=lambda kv: -sum(kv[1].values())):
        lines.append(f"| {o} | {c.get('W', 0)} | {c.get('D', 0)} | {c.get('L', 0)} |")
    # Worst exposures list
    punished = [d for d in decisions if d["exposure"] >= 5 and d["material_swing_next"] is not None and d["material_swing_next"] <= -5]
    lines += ["", f"## Decisions that handed over 5+ points and were punished ({len(punished)})", "",
              "| game | ver | ply | move | exposure | capturer hidden | opponent reply | result |", "|---|---|---|---|---|---|---|---|"]
    for d in sorted(punished, key=lambda d: -d["exposure"])[:40]:
        lines.append(f"| {d['game']} | {d['version']} | {d['ply']} | {d['piece']}{d['move']} | {d['exposure']} | "
                     f"{d['exposure_hidden']} | {d['opponent_reply']} | {d['result']} |")
    lines += ["", "## Reading", "",
              "- `fatal moves` are moves that left our king capturable on the true board; `fatal with a safe alternative` "
              "is the subset where the position still had a safe move, i.e. a decision failure rather than a lost position.",
              "- `exposed ≥3` counts moves after which the opponent had an immediate capture netting at least three points "
              "(one-ply exchange arithmetic); `capturer hidden` means that piece's square was unseen in our view at the "
              "decision, i.e. a belief failure rather than a search failure.",
              "- Rows carry the full view and true board, so any of these decisions can be replayed through any bot mode "
              "with `python -m learning.replay_bot <game> --plies <ply>`."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path, default=Path("gold"))
    parser.add_argument("--reports", type=Path, default=Path("reports"))
    args = parser.parse_args(argv)
    summary = curate(args.raw, args.output, args.reports)
    print(json.dumps({k: summary[k] for k in ("games", "decisions", "by_version")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
