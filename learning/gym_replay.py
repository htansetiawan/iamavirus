"""Gym at arena fidelity: run a real bot binary at each corpus decision.

    python -m learning.gym_replay data/gym/strike-seats.txt --bot build/v15plus/bot --model releases/v1 \
        --workers 4 --threads 2 --cores 0-7 --output data/reports/gym/arena/strike-v15.json
    # ceiling variants: --clock fixed:1000 --env FOW_TIME_DIVISOR=1 FOW_TIME_CAP=30 FOW_TIME_CAP_HARD=30 FOW_TIME_RESERVE=0
    #                   --oracle  (feed the true board instead of the side's view: perfect information)

A seat line is `id side result reason label moves...` (learning/gym_corpora.py);
its last move is the decision. The bot is fed exactly the observations its side
received in the arena (or the true boards with --oracle), its earlier moves are
forced (FOW_FORCE_MOVES with FOW_FORCE_FAST, so they cost only belief updates),
and at the decision it gets the real remaining clock from the replay (or a
fixed one) and decides with its normal machinery: hybrid mode, the packaged
model, two matrix-cell threads by default, as in the arena.

The chosen move is scored on the true board with the course rules
(learning/rules.py): exact match with the recorded move; strike (after the move
we attack their king from a square they cannot see); giveaway (a piece of ours
capturable for a net gain of 3+ points); queen en prise (net 5+ on the queen);
king lost (the move leaves our king capturable).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import chess

from . import rules

ROOT = Path(__file__).resolve().parents[1]
VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


def board_fen(board64: str, turn: bool) -> str:
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
    return "/".join(rows) + (" w" if turn else " b") + " - - 0 1"


def position_at(board_text: str, side: int, prefix: list[str]) -> "rules.Board":
    """The true position before our decision, from the replay's board string; castling rights and
    the en passant square are derived from the recorded move prefix."""
    moved = {rules.square_index(m[:2]) for m in prefix}
    touched = moved | {rules.square_index(m[2:4]) for m in prefix}
    castling = 0
    for rook, king, symbol, king_symbol in ((0, 4, "R", "K"), (7, 4, "R", "K"), (56, 60, "r", "k"), (63, 60, "r", "k")):
        if king not in moved and rook not in touched and board_text[rook] == symbol and board_text[king] == king_symbol:
            castling |= 1 << rook
    en_passant = -1
    if prefix:
        last = prefix[-1]
        a, b = rules.square_index(last[:2]), rules.square_index(last[2:4])
        if board_text[b] in "Pp" and abs(b - a) == 16:
            en_passant = (a + b) // 2
    return rules.Board.from_board_string(board_text, side, castling, en_passant)


def score_move(board_text: str, prefix: list[str], move: str, side: int) -> dict:
    """Metrics of `move` played by `side` in the true position `board_text` (reached by `prefix`)."""
    board = position_at(board_text, side, prefix)
    if move not in board.legal_moves():
        return {"legal": False}
    board.push(move)
    enemy = 1 - side
    after = chess.Board(board_fen(board.board_string(), enemy == 0))
    us_col = chess.WHITE if side == 0 else chess.BLACK
    them_col = not us_col
    they_see = board.visible(enemy)
    out = {"legal": True, "strike": False, "giveaway": False, "queen_en_prise": False, "king_lost": False}
    our_king = after.king(us_col)
    if our_king is not None and after.attackers(them_col, our_king):
        out["king_lost"] = True
    their_king = after.king(them_col)
    if their_king is not None:
        for sq in after.attackers(us_col, their_king):
            if not (they_see >> sq) & 1:
                out["strike"] = True
                break
    best = 0
    for sq in chess.SquareSet(after.occupied_co[us_col]):
        piece = after.piece_at(sq)
        if piece.piece_type == chess.KING:
            continue
        attackers = after.attackers(them_col, sq)
        if not attackers:
            continue
        cheapest = min(VALUE[after.piece_at(a).piece_type] for a in attackers)
        defended = bool(after.attackers(us_col, sq))
        net = VALUE[piece.piece_type] - (cheapest if defended else 0)
        best = max(best, net)
        if piece.piece_type == chess.QUEEN and net >= 5:
            out["queen_en_prise"] = True
    out["giveaway"] = best >= 3
    return out


def modeled_clock(decision: int, base: float = 180.0, inc: float = 2.0, cap: float = 7.0, divisor: float = 20.0,
                  reserve: float = 10.0, share: float = 0.8, book: int = 5) -> float:
    """Our clock before our `decision`-th move (1-based) under the v15 schedule, as the arena
    replays show it (spend matches the budget formula within 0.1 s; the book answers ~5 moves)."""
    clock = base
    for d in range(1, decision):
        if d <= book:
            spend = 0.05
        else:
            spare = clock - reserve
            spend = max(0.05, min(spare / divisor + inc * share, cap, spare * 0.5))
        clock = clock - spend + inc
    return clock


def run_seat(line: str, args, cores: str) -> dict:
    f = line.split()
    gid, side_txt, label, moves = f[0], f[1], f[4], f[5:]
    side = 0 if side_txt == "w" else 1
    key = "white" if side == 0 else "black"
    frames = json.loads((Path(args.raw) / "games" / gid / "replay.json").read_text())["frames"]
    k = len(moves)
    record = {"id": gid, "side": side, "label": label, "ply": k - 1, "real": moves[-1]}
    if k >= len(frames) or frames[k]["move"] != moves[-1]:
        record["error"] = "seat does not match the replay"
        return record
    forced = [moves[i] for i in range(k - 1) if i % 2 == side]
    script = ["fow", f"{'w' if side == 0 else 'b'} 180 2"]
    for t in range(k):
        script.append(frames[t]["board"] if args.oracle else frames[t][key])
        if t % 2 == side:
            decision = t // 2 + 1
            if args.clock == "replay" and "clocks" in frames[t]:
                script.append(f"{frames[t]['clocks'][side]:.6f}")
            elif args.clock.startswith("fixed:"):
                script.append(args.clock.split(":", 1)[1])
            else:
                script.append(f"{modeled_clock(decision):.6f}")
    env = dict(os.environ, FOW_MODE=args.mode, FOW_MODEL_DIR=str(Path(args.model).resolve()), FOW_SEED=str(args.seed),
               FOW_FORCE_MOVES=" ".join(forced), FOW_FORCE_FAST="1", FOW_CELL_THREADS=str(args.threads))
    for kv in args.env or []:
        name, value = kv.split("=", 1)
        env[name] = value
    if args.inject_real:
        env["FOW_INJECT_MOVE"] = moves[-1]
    started = time.time()
    try:
        out = subprocess.run(["taskset", "-c", cores, str(Path(args.bot).resolve())], input="\n".join(script) + "\n",
                             capture_output=True, text=True, env=env, timeout=args.timeout, cwd=str(ROOT))
    except subprocess.TimeoutExpired:
        record["error"] = "timeout"
        return record
    moves_out = [l.split()[1] for l in out.stdout.splitlines() if l.startswith("move ")]
    if len(moves_out) != len(forced) + 1:
        record["error"] = f"expected {len(forced) + 1} moves, got {len(moves_out)}"
        record["stderr_tail"] = out.stderr[-400:]
        return record
    choice = moves_out[-1]
    record["choice"] = choice
    record["seconds"] = round(time.time() - started, 2)
    decision_lines = [l for l in out.stderr.splitlines() if " n=" in l and " mode=" in l]
    if decision_lines:
        fields = dict(tok.split("=", 1) for tok in decision_lines[-1].split() if "=" in tok)
        record["engine"] = {k2: fields.get(k2) for k2 in ("mode", "nodes", "spent", "short", "hyp", "budget", "book", "inj")}
    record["match"] = choice == moves[-1]
    record.update({f"choice_{k2}": v for k2, v in score_move(frames[k - 1]["board"], moves[:-1], choice, side).items()})
    record.update({f"real_{k2}": v for k2, v in score_move(frames[k - 1]["board"], moves[:-1], moves[-1], side).items()})
    return record


def parse_cores(text: str) -> list[int]:
    out = []
    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def summarize(records: list[dict]) -> dict:
    ok = [r for r in records if "choice" in r]
    n = len(ok) or 1
    def rate(key):
        return round(100.0 * sum(1 for r in ok if r.get(key)) / n, 1)
    return {"seats": len(records), "scored": len(ok), "errors": len(records) - len(ok),
            "match": rate("match"), "strike": rate("choice_strike"), "giveaway": rate("choice_giveaway"),
            "queen_en_prise": rate("choice_queen_en_prise"), "king_lost": rate("choice_king_lost"),
            "real_strike": rate("real_strike"), "real_giveaway": rate("real_giveaway"),
            "injected": round(100.0 * sum(1 for r in ok if (r.get("engine") or {}).get("inj") == "1") / n, 1),
            "mean_seconds": round(sum(r.get("seconds", 0) for r in ok) / n, 2)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("seats")
    ap.add_argument("--bot", default="build/v15plus/bot")
    ap.add_argument("--model", default="releases/v1")
    ap.add_argument("--mode", default="hybrid")
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--cores", default="0-7")
    ap.add_argument("--clock", default="model", help="model (our v15 clock at that decision) | replay | fixed:SECONDS")
    ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--inject-real", action="store_true",
                    help="give the recorded move a guaranteed matrix row (needs a bot with FOW_INJECT_MOVE)")
    ap.add_argument("--env", nargs="*")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    lines = [l for l in Path(args.seats).read_text().splitlines() if l.strip()]
    if args.limit:
        lines = lines[: args.limit]
    cores = parse_cores(args.cores)
    per = max(1, len(cores) // args.workers)
    slots = [",".join(str(c) for c in cores[i * per:(i + 1) * per]) for i in range(args.workers)]
    records = [None] * len(lines)
    started = time.time()
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        free = list(slots)
        futures = {}
        it = iter(enumerate(lines))
        def submit_next():
            try:
                i, line = next(it)
            except StopIteration:
                return False
            slot = free.pop()
            futures[pool.submit(run_seat, line, args, slot)] = (i, slot)
            return True
        for _ in range(len(slots)):
            if not submit_next():
                break
        while futures:
            done, _ = cf.wait(list(futures), return_when=cf.FIRST_COMPLETED)
            for fut in done:
                i, slot = futures.pop(fut)
                try:
                    records[i] = fut.result()
                except Exception as error:  # keep going; record the failure
                    records[i] = {"line": lines[i][:60], "error": repr(error)}
                free.append(slot)
                submit_next()
    summary = summarize([r for r in records if r is not None])
    summary["wall_seconds"] = round(time.time() - started, 1)
    summary["config"] = {k: v for k, v in vars(args).items() if k not in ("output",)}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps({"summary": summary, "records": records}, indent=1))
    print(json.dumps({k: v for k, v in summary.items() if k != "config"}))


if __name__ == "__main__":
    main()
