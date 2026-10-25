#!/usr/bin/env python3
"""Trace v35's exact belief/risk/search response to held-out fatal choices.

Uses the immutable submitted zip, its build/run scripts, actor observations and
own previous actions only. Full boards are supplied through v35's diagnostic
MIST_TRUTH_SEQ variable; they are never sent on the bot protocol input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from learning import histories, ingest, rules

RISK_RE = re.compile(r"^mist: risk ([a-h][1-8][a-h][1-8][qrbn]?) ([0-9.]+) qrisk ([^/ ]+)/([^ ]+) mrisk ([^ ]+)(?: \(chosen\))?$")
TRUTH_RE = re.compile(r"^mist: truth v=(\d+) \|P\|=(\d+)(?:\(capped\))? (.*)$")
MOVE_RE = re.compile(r"^move ([a-h][1-8][a-h][1-8][qrbn]?)$")
PIECE_SYMBOLS = "PNBRQK"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def select_cases(rows: list[dict], per_opponent: int, seed: int, max_ply: int):
    rng = random.Random(seed)
    chosen = []
    for opponent in sorted({x["opponent"] for x in rows}):
        group = [x for x in rows if x["opponent"] == opponent and x["ply"] <= max_ply]
        # Balance king and non-king fatal choices before filling remaining slots.
        buckets = {True: [x for x in group if x["king_move"]],
                   False: [x for x in group if not x["king_move"]]}
        for items in buckets.values():
            items.sort(key=lambda x: (x["ply"], x["game"]))
            rng.shuffle(items)
            items.sort(key=lambda x: x["ply"])
        while group and sum(1 for x in chosen if x["opponent"] == opponent) < per_opponent:
            used = sum(1 for x in chosen if x["opponent"] == opponent)
            bucket = buckets[bool(used % 2)]
            if not bucket:
                bucket = buckets[not bool(used % 2)]
            if not bucket:
                break
            chosen.append(bucket.pop(0))
    return chosen


def parse_logs(stdout: str, stderr: str, target_view: int):
    moves = [m.group(1) for line in stdout.splitlines() if (m := MOVE_RE.match(line))]
    risk = {}
    for line in stderr.splitlines():
        m = RISK_RE.match(line)
        if m:
            risk[m.group(1)] = {
                "king_risk": float(m.group(2)), "queen_risk": m.group(3),
                "queen_risk_sharp": m.group(4), "material_risk": m.group(5),
                "chosen": "(chosen)" in line,
            }
    truth = []
    for line in stderr.splitlines():
        m = TRUTH_RE.match(line)
        if m and int(m.group(1)) == target_view:
            truth.append({"view": int(m.group(1)), "particles": int(m.group(2)), "report": m.group(3)})
    summary = [line for line in stderr.splitlines()
               if line.startswith(("mist: n=", "mist: king guard", "mist: queen guard",
                                   "mist: truth ", "mist: timing", "mist: played "))]
    return (moves[-1] if moves else None), risk, truth[-1] if truth else None, summary


def true_attackers_after(board, move: str, us: int):
    post = board.copy()
    post.push(move)
    king_sq = post.king_square(us)
    attackers = []
    for uci in post.legal_moves():
        dst = (ord(uci[2]) - 97) + 8 * (int(uci[3]) - 1)
        if dst != king_sq:
            continue
        src = (ord(uci[0]) - 97) + 8 * (int(uci[1]) - 1)
        piece = post.piece_at(src)
        symbol = PIECE_SYMBOLS[piece % 6]
        if piece // 6 == rules.BLACK:
            symbol = symbol.lower()
        attackers.append({"move": uci, "from": uci[:2], "piece": symbol})
    return attackers


def run_case(case: dict, replay: dict, binary_dir: Path, max_seconds: float,
             timeout: float, king_guard: float | None,
             no_history_table: bool = False):
    side = rules.WHITE if replay["white"] == "IAmAVirus" else rules.BLACK
    key = "white" if side == rules.WHITE else "black"
    states, problems = ingest.validate_replay(replay)
    if problems:
        raise ValueError(f"{case['game']}: invalid replay: {problems[:2]}")
    episode = histories.build_episode(replay, states, side, ingest.RULES_FINGERPRINT)
    try:
        target = episode.actor.decision_event_indices.index(case["ply"])
    except ValueError as exc:
        raise ValueError(f"{case['game']} ply {case['ply']} missing from actor decisions") from exc
    if episode.actor.own_actions[target] != case["move"]:
        raise ValueError(f"{case['game']} ply {case['ply']} actual move changed")
    truth_board = states[case["ply"]].board
    actor_view = replay["frames"][case["ply"]][key]
    actual_attackers = true_attackers_after(truth_board, case["move"], side)
    hidden_attackers = [a for a in actual_attackers if actor_view[(int(a["from"][1]) - 1) * 8 + ord(a["from"][0]) - 97] == "?"]
    opponent_move_context = []
    if case["ply"] > 0:
        last_move = replay["frames"][case["ply"]].get("move")
        before_view = replay["frames"][case["ply"] - 1][key]
        after_view = replay["frames"][case["ply"]][key]
        for attacker in actual_attackers:
            src, dst = attacker["from"], (last_move[2:4] if last_move else None)
            sq = lambda value: (int(value[1]) - 1) * 8 + ord(value[0]) - 97
            opponent_move_context.append({
                "last_move_before_our_decision": last_move,
                "last_move_destination_is_attacker_square": dst == attacker["from"] if dst else False,
                "attacker_square_seen_before_last_move": before_view[sq(src)] != "?",
                "attacker_square_seen_after_last_move": after_view[sq(src)] != "?",
                "last_move_origin_visibility_before": (
                    before_view[sq(last_move[:2])] != "?" if last_move else None
                ),
                "last_move_destination_visibility_after": (
                    after_view[sq(last_move[2:4])] != "?" if last_move else None
                ),
            })

    # The arena sends an observation after every ply, including both our own
    # post-move view and the opponent's reply view. The process consumes both
    # before it is asked to choose again.
    frames = replay["frames"][:case["ply"] + 1]
    views = [frame[key] for frame in frames]
    truth = [frame["board"] for frame in frames]
    forced = ",".join(episode.actor.own_actions[:target])
    prefix = f"fow\n{'white' if side == rules.WHITE else 'black'} 180 2\n"
    pieces = []
    for t, view in enumerate(views):
        pieces.append(view + "\n")
        if t % 2 == side:
            remaining = frames[t].get("clocks", [180.0, 180.0])[side]
            pieces.append(f"{remaining:.3f}\n")
    protocol = prefix + "".join(pieces)
    env = os.environ.copy()
    env.update({
        "FOW_SEED": "1", "MIST_CAP": "200000", "MIST_MAX_SECONDS": str(max_seconds),
        "MIST_FORCE_MOVES": forced, "MIST_TRUTH_SEQ": ",".join(truth),
        "MIST_RISK": "1", "MIST_TIMING": "1",
        "MIST_STOCKFISH": str((binary_dir / "bin/stockfish").resolve()),
        "MIST_HISTORY_TABLE": str((binary_dir / "data/history.bin").resolve()),
    })
    if no_history_table:
        # belief.c treats a missing/corrupt table as disabled and keeps the
        # fitted move model active. Use a guaranteed-absent path so callers
        # can isolate the static table without touching the archived data.
        env["MIST_HISTORY_TABLE"] = str(binary_dir / "data/history-disabled-for-probe.bin")
    if king_guard is not None:
        env["MIST_KING_GUARD"] = str(king_guard)
    proc = subprocess.run([str((binary_dir / "mist").resolve())], input=protocol,
                          text=True, capture_output=True, cwd=binary_dir, env=env,
                          timeout=timeout, check=False)
    if proc.returncode:
        raise RuntimeError(f"{case['game']} v35 exit={proc.returncode}: {proc.stderr[-1000:]}")
    move, risks, truth_row, summary = parse_logs(proc.stdout, proc.stderr, case["ply"])
    if not move:
        raise RuntimeError(f"{case['game']} v35 emitted no move: {proc.stdout[-1000:]}")
    safe_risks = {m: risks.get(m) for m in case["safe_alternatives"]}
    return {
        "game": case["game"], "opponent": case["opponent"], "ply": case["ply"],
        "recorded_outcome": case.get("outcome"),
        "actual_fatal_move": case["move"], "actual_is_king_move": case["king_move"],
        "true_board_safe_alternatives": case["safe_alternatives"],
        "true_attackers_after_actual_move": actual_attackers,
        "hidden_attackers_from_actor_view": hidden_attackers,
        "last_opponent_move_vs_attacker": opponent_move_context,
        "v35_replayed_choice": move, "replayed_choice_matches_actual": move == case["move"],
        "v35_truth_rank_at_target": truth_row,
        "chosen_move_risk": risks.get(move),
        "actual_move_risk": risks.get(case["move"]),
        "safe_alternative_risks": safe_risks,
        "minimum_logged_king_risk": min((x["king_risk"] for x in risks.values()), default=None),
        "risk_candidate_count": len(risks), "summary_lines": summary[-25:],
        "returncode": proc.returncode,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path, default=Path("fable-submissions/iamavirus-v35-mist-c-v14.zip"))
    p.add_argument("--audit", type=Path, default=Path("astra-submissions/analysis/standing-trend-20261024/king-choice-audit.json"))
    p.add_argument("--raw", type=Path, default=Path("data/raw"))
    p.add_argument("--binary-dir", type=Path, default=Path("/tmp/iamavirus-v35-exact-trace"))
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--per-opponent", type=int, default=2)
    p.add_argument("--seed", type=int, default=20261025)
    p.add_argument("--max-ply", type=int, default=150)
    p.add_argument("--max-seconds", type=float, default=10.0)
    p.add_argument("--king-guard", type=float, help="override MIST_KING_GUARD for isolated ablations")
    p.add_argument("--no-history-table", action="store_true",
                   help="disable only the archived lookup table; keep the fitted model active")
    p.add_argument("--timeout", type=float, default=600.0)
    args = p.parse_args()
    if not (args.binary_dir / "mist").exists():
        raise SystemExit("extract/build the supplied archive into --binary-dir first")
    audit = json.loads(args.audit.read_text())
    candidate_rows = audit.get("fatal_choices_with_safe_alternatives_examples", audit.get("examples"))
    if candidate_rows is None:
        raise SystemExit("audit must contain fatal_choices_with_safe_alternatives_examples or examples")
    cases = select_cases(candidate_rows,
                         args.per_opponent, args.seed, args.max_ply)
    outputs, errors = [], []
    for case in cases:
        try:
            replay_path = args.raw / "games" / case["game"] / "replay.json"
            replay = json.loads(replay_path.read_text())
            outputs.append(run_case(case, replay, args.binary_dir, args.max_seconds,
                                    args.timeout, args.king_guard, args.no_history_table))
        except Exception as exc:
            errors.append({"game": case["game"], "opponent": case["opponent"], "error": str(exc)})
    result = {
        "classification": "diagnostic replay of exact submitted v35 bytes; no alternative move is played",
        "archive": str(args.archive.resolve()), "archive_sha256": sha(args.archive),
        "binary_sha256": sha(args.binary_dir / "mist"), "audit_sha256": sha(args.audit),
        "parameters": {"per_opponent": args.per_opponent, "seed": args.seed,
                       "max_ply": args.max_ply, "max_seconds": args.max_seconds,
                       "MIST_KING_GUARD": args.king_guard,
                       "no_history_table": args.no_history_table,
                       "MIST_CAP": 200000, "MIST_RISK": True, "MIST_TIMING": True},
        "attempted": len(cases), "completed": len(outputs), "errors": errors,
        "traces": outputs,
        "limits": ["The true board is supplied only through v35's diagnostic stderr hook.",
                   "Recorded own moves are forced before the target choice; observed views recreate the actor input.",
                   "The opponent policy is not simulated because observations are replayed from recorded games.",
                   "A fresh process and deterministic local seed may not reproduce the arena's hidden RNG.",
                   "A changed move is not branched into a new game; this traces belief and selection only."],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"attempted": len(cases), "completed": len(outputs), "errors": errors,
                      "traces": [{"game": r["game"], "opp": r["opponent"], "ply": r["ply"],
                                  "truth": r["v35_truth_rank_at_target"],
                                  "actual_risk": r["actual_move_risk"],
                                  "alt_risks": r["safe_alternative_risks"],
                                  "choice": r["v35_replayed_choice"]} for r in outputs]}, indent=2))


if __name__ == "__main__":
    main()
