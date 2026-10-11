#!/usr/bin/env python3
"""Bounded cold/searched-prefix M4 diagnostic, with referee truth checks.

This is an offline decision probe, not an Elo or real-clock match estimate.
Run with fow-starter/.venv/bin/python (python-chess is a referee dependency).
It consumes cached public completed-game replays, never live observations.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import tempfile


def inputs(game, decision):
    side = "white" if game["white"] == "IAmAVirus" else "black"
    protocol = game.get("protocol")
    if not protocol or protocol.get("truncated"):
        raise ValueError("A complete recorded protocol is required")
    lines, played = [], []
    for event in protocol["events"]:
        if event["side"] != side:
            continue
        if event["direction"] == "input":
            lines.append(event["text"])
        elif event["text"].startswith("move "):
            played.append(event["text"][5:])
    decision = decision or len(played)
    clocks = [i for i, line in enumerate(lines) if re.fullmatch(r"[0-9.]+", line)]
    if not 1 <= decision <= min(len(played), len(clocks)):
        raise ValueError("Target decision is missing")
    return side, decision, played, "\n".join(lines[:clocks[decision - 1] + 1]) + "\n"


def parse_metrics(stderr):
    rows = []
    for line in stderr.splitlines():
        if not line.startswith("mist-m4: ") or "ok=" not in line:
            continue
        row = {k: float(v) if "." in v else int(v)
               for k, v in re.findall(r"(\w+)=(-?\d+(?:\.\d+)?)", line)}
        row["prefix"] = line.startswith("mist-m4: prefix")
        rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("replays", nargs="+", type=Path)
    ap.add_argument("--binary", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--kit", type=Path, default=Path.home()/"git/fow-starter")
    ap.add_argument("--decision", type=int)
    ap.add_argument("--seconds", type=float, default=.5)
    ap.add_argument("--iterations", type=int, default=40)
    ap.add_argument("--seed", type=int, default=21)
    ap.add_argument("--parents", type=int, help="Fixed replay parent cap, >=2000; avoids clock-dependent thinning")
    ap.add_argument("--samples", type=int, help="Root sample target, 1..4096")
    ap.add_argument("--audit-belief", action="store_true", help="Compare truth with post-decision belief export")
    ap.add_argument("--witnesses", action="store_true", help="Enable experimental tactical root witnesses")
    ap.add_argument("--stockfish", type=Path, help="Optional bounded external leaf evaluator")
    ap.add_argument("--child-alternates", action="store_true", help="Fresh root heuristic from best rules-adjudicated child (automatic with Stockfish)")
    ap.add_argument("--mode", choices=["cold", "warm", "both"], default="both")
    args = ap.parse_args()
    sys.path.insert(0, str(args.kit))
    import referee
    import chess
    args.out.mkdir(parents=True, exist_ok=True)
    binary = args.binary.resolve()
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    modes = ["cold", "warm"] if args.mode == "both" else [args.mode]
    results = []
    for path in args.replays:
        game = json.loads(path.read_text())
        side, decision, played, feed = inputs(game, args.decision)
        ply = 2*(decision - 1) + (side == "black")
        board = referee.FowBoard()
        repetitions = Counter({referee.position_key(board): 1})
        for frame in game["frames"][1:ply+1]:
            board.push_uci(frame["move"])
            repetitions[referee.position_key(board)] += 1
        encoded = "".join(board.piece_at(s).symbol() if board.piece_at(s) else "-" for s in range(64))
        if encoded != game["frames"][ply]["board"]:
            raise ValueError(f"Replay reconstruction mismatch: {path} ply {ply}")
        true_legal = list(referee.fow_moves(board))
        true_safe = []
        for move in true_legal:
            child = board.copy(); child.push(move)
            counts = repetitions.copy(); counts[referee.position_key(child)] += 1
            ending = referee.outcome(child, counts)
            if not ending or ending[0] != ("0-1" if side == "white" else "1-0"):
                true_safe.append(move.uci())
        for mode in modes:
            env = dict(os.environ, MIST_FORCE_MOVES=",".join(played[:decision-1]),
                       MIST_REPLAY_WARM="1" if mode == "warm" else "0",
                       MIST_MAX_SECONDS=str(args.seconds), MIST_M4_ITERATIONS=str(args.iterations),
                       FOW_SEED=str(args.seed), MIST_SEARCH="m4", MIST_M4_DUMP_PLY=str(ply))
            env["MIST_M4_WITNESSES"] = "1" if args.witnesses else "0"
            env.pop("MIST_STOCKFISH", None)
            if args.stockfish: env["MIST_STOCKFISH"] = str(args.stockfish.resolve())
            env["MIST_M4_ALT_CHILDREN"] = "1" if args.child_alternates else "0"
            if args.parents is not None: env["MIST_REPLAY_PARENTS"] = str(args.parents)
            if args.samples is not None: env["MIST_SAMPLES"] = str(args.samples)
            belief_dump = tempfile.TemporaryDirectory(prefix="m4-belief-")
            dump_path = Path(belief_dump.name)/"belief.txt"
            if args.audit_belief: env["MIST_REPLAY_BELIEF_DUMP"] = str(dump_path)
            start = time.monotonic()
            proc = subprocess.run([str(binary)], input=feed, capture_output=True, text=True,
                                  env=env, timeout=max(60, decision*args.seconds*3))
            name = f"{game['id']}-d{decision}-{mode}"
            (args.out/(name+".stderr")).write_text(proc.stderr)
            (args.out/(name+".stdout")).write_text(proc.stdout)
            moves = [line[5:] for line in proc.stdout.splitlines() if line.startswith("move ")]
            row = {"game": game["id"], "side": side, "decision": decision, "ply": ply,
                   "mode": mode, "played": played[decision-1], "returncode": proc.returncode,
                   "true_legal_count": len(true_legal), "true_safe_moves": true_safe,
                   "unavoidable_immediate_loss": not true_safe,
                   "elapsed": time.monotonic()-start, "prefix_exact": moves[:decision-1] == played[:decision-1],
                   "outputs": len(moves), "chosen": moves[-1] if len(moves) == decision else None,
                   "metrics": parse_metrics(proc.stderr)}
            roots = re.findall(r"m4-root: board=(\S+) ep=(-?\d+) castle=([0-9a-f]+) halfmove=(\d+) group=(\d+) reach=(\S+) value=(\S+) chosen_fatal=([01])", proc.stderr)
            row["dumped_current_roots"] = len(roots)
            row["true_board_roots"] = sum(r[0] == encoded for r in roots)
            exact = [r for r in roots if r[0] == encoded and int(r[1]) == (board.ep_square if board.ep_square is not None else -1)
                     and int(r[2],16) == board.castling_rights and int(r[3]) == board.halfmove_clock]
            row["true_state_roots"] = len(exact)
            row["true_state_reach"] = sum(float(r[5]) for r in exact)
            row["all_root_reach"] = sum(float(r[5]) for r in roots)
            row["chosen_fatal_roots"] = sum(int(r[7]) for r in roots)
            row["chosen_fatal_reach"] = sum(float(r[5]) for r in roots if int(r[7]))
            row["chosen_fatal_share"] = (row["chosen_fatal_reach"]/row["all_root_reach"]
                                         if row["all_root_reach"] > 0 else None)
            row["action_profiles"] = [dict(move=m, policy=float(p), played=float(q),
                                           fatal=float(f), raw=float(v)) for m,p,q,f,v in re.findall(
                r"m4-action: move=(\S+) policy=(\S+) played=(\S+) fatal=(\S+) raw=(\S+)",proc.stderr)]
            eval_line = re.search(r"m4-eval: (.*)", proc.stderr)
            if eval_line:
                row["evaluation"] = {k:float(v) for k,v in re.findall(r"(\w+)=(\S+)",eval_line.group(1))}
            row["prefix_evaluation"] = [
                {k:float(v) for k,v in re.findall(r"(\w+)=(\S+)", line)}
                for line in re.findall(r"m4-prefix-eval: (.*)", proc.stderr)]
            witness_line = re.search(r"m4-witness: (.*)",proc.stderr)
            if witness_line:
                row["witness_metrics"] = {k:int(v) for k,v in re.findall(r"(\w+)=(\d+)",witness_line.group(1))}
            if args.audit_belief and dump_path.exists():
                total = truth = tactical_mass = 0.0; count = matches = boards = tactical = 0
                for line in dump_path.read_text().splitlines():
                    state,ep,castle,halfmove,logw = line.split()
                    count += 1; weight = math.exp(float(logw)); total += weight
                    boards += state == encoded
                    if (state == encoded and int(ep) == (board.ep_square if board.ep_square is not None else -1)
                            and int(castle,16) == board.castling_rights):
                        tactical += 1; tactical_mass += weight
                    if (state == encoded and int(ep) == (board.ep_square if board.ep_square is not None else -1)
                            and int(castle,16) == board.castling_rights and int(halfmove) == board.halfmove_clock):
                        matches += 1; truth += weight
                row["belief_count"] = count; row["belief_true_states"] = matches
                row["belief_true_boards"] = boards; row["belief_tactical_states"] = tactical
                row["belief_tactical_share"] = tactical_mass/total if total else None
                row["belief_truth_share"] = truth/total if total else None
            belief_dump.cleanup()
            if row["chosen"]:
                move = chess.Move.from_uci(row["chosen"])
                row["legal"] = move in referee.fow_moves(board)
                if row["legal"]:
                    child = board.copy(); child.push(move)
                    counts = repetitions.copy(); counts[referee.position_key(child)] += 1
                    ending = referee.outcome(child, counts)
                    row["true_outcome"] = ending
                    row["immediate_loss"] = bool(ending and ending[0] == ("0-1" if side == "white" else "1-0"))
            results.append(row)
            report = {"binary": str(binary), "sha256": digest, "seconds": args.seconds,
                      "iteration_cap": args.iterations, "seed": args.seed,
                      "fixed_parent_cap": args.parents, "sample_target": args.samples,
                      "tactical_witnesses": args.witnesses,
                      "stockfish": str(args.stockfish.resolve()) if args.stockfish else None,
                      "stockfish_sha256": hashlib.sha256(args.stockfish.read_bytes()).hexdigest() if args.stockfish else None,
                      "child_alternates": bool(args.child_alternates or args.stockfish),
                      "classification": "offline diagnostic, no Elo inference", "rows": results}
            (args.out/"results.json").write_text(json.dumps(report, indent=2)+"\n")
            print(json.dumps({k:v for k,v in row.items() if k not in ("metrics", "action_profiles")}), flush=True)


if __name__ == "__main__":
    main()
