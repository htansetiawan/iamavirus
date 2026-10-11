#!/usr/bin/env python3
"""Replay an archived Misty actor to one exact arena decision.

Earlier own moves are searched normally then forced to match the replay, so
the profile RNG and any engine state advance as in a live game. At the target
decision, the move is unforced and a debug-only trace records root values.
The injected trace runs after search and does not affect the decision.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

TEAM_ID = "a2c35173659545c99752376a70418438"


def instrument_bot(source: str) -> str:
    needle = """        try:
            size = strategy._engine.enumerator.size
"""
    inject = """        if os.environ.get("MISTY_DEBUG_ROOT") == "1" and not forced:
            engine = getattr(strategy, "_engine", None)
            solution = getattr(engine, "last_solution", None)
            if solution is None:
                detail = {"move": move.uci(), "solution": None,
                          "policy": getattr(strategy, "last_policy_action", None)}
            else:
                def encode_moves(table):
                    return sorted(((m.uci(), float(v)) for m, v in table.items()),
                                  key=lambda pair: (-pair[1], pair[0]))
                detail = {"move": move.uci(),
                          "policy": getattr(strategy, "last_policy_action", None),
                          "trace": (getattr(strategy, "trace_log", [])[-1]
                                    if getattr(strategy, "trace_log", []) else None),
                          "root_action_values": encode_moves(solution.action_values_at_root),
                          "root_strategy": encode_moves(solution.strategy_at_root)}
            print("misty-root: " + __import__("json").dumps(detail, sort_keys=True),
                  file=sys.stderr, flush=True)
        try:
            size = strategy._engine.enumerator.size
"""
    if source.count(needle) != 1:
        raise RuntimeError("could not uniquely locate post-search insertion point")
    return source.replace(needle, inject)


def instrument_engine(source: str) -> str:
    """Log the raw solver action and final committed action."""
    marker = "        # === Stage 5: commit guards — material / royal / variant hooks /\n"
    before = '''        if os.environ.get("MISTY_DEBUG_ROOT") == "1":
            top = sorted(solution.action_values_at_root.items(),
                         key=lambda pair: (-float(pair[1]), pair[0].uci()))[:5]
            print("misty-engine-root: " + __import__("json").dumps(
                {"extracted_move": move.uci(),
                 "top_values": [(m.uci(), float(v)) for m, v in top]},
                sort_keys=True), file=__import__("sys").stderr, flush=True)
'''
    if source.count(marker) != 1:
        raise RuntimeError("could not uniquely locate EngineV2 commit guards")
    source = source.replace(marker, before + marker)
    checkpoints = [
        ("        # Variant commit guards — the royal guard, material checks, and vetoes\n",
         "after-material"),
        ("        if self.win_fast:\n",
         "after-variant"),
        ("        # Catastrophe prune (FOW_HV_PRUNE_FRAC / adaptive; default off): the FINAL\n",
         "after-win-fast"),
        ("        if self.queen_promo_tiebreak:\n",
         "after-catastrophe-prune"),
        ("        move = _apply_legal_move_mask(\n",
         "after-promotion-normalize"),
        ("        self.moves_chosen += 1\n",
         "after-legal-mask"),
    ]
    for marker, label in checkpoints:
        if source.count(marker) != 1:
            raise RuntimeError(f"could not uniquely locate EngineV2 stage {label}")
        line = (f'        if os.environ.get("MISTY_DEBUG_ROOT") == "1":\n'
                f'            print("misty-guard-stage: {label}:" + move.uci(),\n'
                f'                  file=__import__("sys").stderr, flush=True)\n')
        source = source.replace(marker, line + marker)
    old = "        self.moves_chosen += 1\n        return move\n\n    def _prefer_immediate_royal_capture"
    new = '''        self.moves_chosen += 1
        if os.environ.get("MISTY_DEBUG_ROOT") == "1":
            print("misty-engine-final: " + move.uci(),
                  file=__import__("sys").stderr, flush=True)
        return move

    def _prefer_immediate_royal_capture'''
    if source.count(old) != 1:
        raise RuntimeError("could not uniquely locate EngineV2 final return")
    source = source.replace(old, new)
    prune_call = "            move = self._catastrophe_prune(\n"
    prune_input = '''            if os.environ.get("MISTY_DEBUG_ROOT") == "1":
                _encode = lambda table: sorted(((m.uci(), float(v)) for m, v in table.items()))
                print("misty-prune-input: " + __import__("json").dumps(
                    {"move": move.uci(), "frac": _hv_frac, "adaptive": _hv_adaptive,
                     "values": _encode(solution.action_values_at_root),
                     "strategy": _encode(purified.strategy)},
                    sort_keys=True), file=__import__("sys").stderr, flush=True)
'''
    if source.count(prune_call) != 1:
        raise RuntimeError("could not uniquely locate catastrophe-prune call")
    source = source.replace(prune_call, prune_input + prune_call)

    step2 = "            # STEP 2 — KING. Redirect to the lowest-king-risk value-comparable move ONLY\n"
    risk_probe = '''            if os.environ.get("MISTY_DEBUG_ROOT") == "1":
                probes = [move, _c.Move.from_uci("e1d1"), _c.Move.from_uci("g2g7")]
                print("misty-prune-risk: " + __import__("json").dumps(
                    {"size": self.enumerator.size,
                     "sample": fens[:2],
                     "moves": [(m.uci(), hv_risk(m)) for m in probes]},
                    sort_keys=True), file=__import__("sys").stderr, flush=True)
'''
    if source.count(step2) != 1:
        raise RuntimeError("could not uniquely locate catastrophe prune king step")
    source = source.replace(step2, risk_probe + step2)
    return source


def run(args):
    game_path = args.games_root / args.game / "replay.json"
    game = json.loads(game_path.read_text())
    frames = game["frames"]
    idx = args.decision_frame
    if not 0 <= idx < len(frames) - 1:
        raise ValueError("decision frame must have a following recorded move")
    color = "white" if game.get("whitePlayerId") == TEAM_ID else "black"
    if game.get(color + "PlayerId") != TEAM_ID:
        raise ValueError("team is not a player in this replay")
    side = 0 if color == "white" else 1
    if not frames[idx + 1].get("move"):
        raise ValueError("target replay move is missing")

    forced = []
    for prior_idx in range(idx):
        move = frames[prior_idx + 1]["move"]
        mover = "white" if prior_idx % 2 == 0 else "black"
        if mover == color:
            forced.append(move)
    # Replay ply index parity is standard from the initial White-to-move frame.
    # Verify it against archive metadata rather than silently forcing the wrong side.
    if idx % 2 == 0:
        target_side = "white"
    else:
        target_side = "black"
    if target_side != color:
        raise ValueError(f"frame {idx} is {target_side} to move, but IAmAVirus is {color}")

    with tempfile.TemporaryDirectory(prefix="misty-v30-actor-") as temp_name:
        root = Path(temp_name)
        with zipfile.ZipFile(args.archive) as zf:
            zf.extractall(root)
        bot_path = root / "misty_bot.py"
        bot_path.write_text(instrument_bot(bot_path.read_text()))
        engine_path = root / "lib/fow_chess/engine_v2.py"
        engine_path.write_text(instrument_engine(engine_path.read_text()))
        stockfish = root / "bin/stockfish"
        if not stockfish.is_file():
            raise RuntimeError("archive has no Stockfish binary")
        stockfish.chmod(0o755)

        lines = ["fow", f"{'w' if color == 'white' else 'b'} 180 2", frames[0][color]]
        # The current position is delivered before its clock. Earlier choices
        # are searched by the actor and replaced by the exact historical moves.
        for i in range(idx):
            if ("white" if i % 2 == 0 else "black") == color:
                lines.append(str(frames[i]["clocks"][side]))
            lines.append(frames[i + 1][color])
        lines.append(str(frames[idx]["clocks"][side]))
        env = os.environ.copy()
        env.update({
            "PYTHONPATH": str(root / "lib") + os.pathsep + str(args.chess_site_packages)
            + os.pathsep + env.get("PYTHONPATH", ""),
            "PATH": str(root / "bin") + os.pathsep + env.get("PATH", ""),
            "FOW_STOCKFISH": str(stockfish),
            "FOW_REQUIRE_RUST": "1",
            "FOW_V2_CLOCK_TIME": "1",
            "FOW_V2_TIME_HARD_CAP_S": "4.0",
            "FOW_COMMIT_RISK_WORLDS": "200",
            "FOW_HV_PRUNE_WORLDS": "200",
            "FOW_SEED": str(args.seed),
            "FOW_DEBUG": "0",
            "MISTY_FORCE_MOVES": ",".join(forced),
            "MISTY_DEBUG_ROOT": "1",
        })
        # Fail closed before starting the protocol. The archive's native
        # extension is CPython-version-specific; silently continuing without
        # it can make the adapter emit fallback moves while still exiting 0.
        preflight = subprocess.run(
            [str(args.python), "-c",
             "import fow_rust.fow_rust; import numpy; print('native runtime ok')"],
            text=True, capture_output=True, cwd=root, env=env, timeout=30)
        if preflight.returncode != 0:
            raise RuntimeError(
                "actor runtime preflight failed; no decision was run: "
                + preflight.stderr.strip())
        command = [str(args.python), "-u", str(bot_path)]
        proc = subprocess.run(command, input="\n".join(lines) + "\n", text=True,
                              capture_output=True, timeout=args.timeout, cwd=root, env=env)
        root_lines = [line[len("misty-root: "):]
                      for line in proc.stderr.splitlines()
                      if line.startswith("misty-root: ")]
        engine_roots = [line[len("misty-engine-root: "):]
                        for line in proc.stderr.splitlines()
                        if line.startswith("misty-engine-root: ")]
        engine_finals = [line[len("misty-engine-final: "):]
                         for line in proc.stderr.splitlines()
                         if line.startswith("misty-engine-final: ")]
        prune_risks = [json.loads(line[len("misty-prune-risk: "):])
                       for line in proc.stderr.splitlines()
                       if line.startswith("misty-prune-risk: ")]
        prune_inputs = [json.loads(line[len("misty-prune-input: "):])
                        for line in proc.stderr.splitlines()
                        if line.startswith("misty-prune-input: ")]
        outputs = [line.removeprefix("move ") for line in proc.stdout.splitlines()
                   if line.startswith("move ")]
        diagnostic = json.loads(root_lines[-1]) if root_lines else None
        chosen = outputs[-1] if outputs else None
        fallback_lines = [line for line in proc.stderr.splitlines()
                          if "(fallback)" in line]
        if proc.returncode != 0 or fallback_lines or diagnostic is None:
            raise RuntimeError(
                "actor replay was invalid; refusing to label an adapter/fallback "
                f"move as a search decision (return={proc.returncode}, "
                f"fallback_lines={len(fallback_lines)}, trace={diagnostic is not None})")
        result = {
            "classification": "archived actor replay; prior choices forced to the recorded game",
            "game": args.game, "decision_frame": idx, "team_side": color,
            "opponent": game["black" if color == "white" else "white"],
            "recorded_move": frames[idx + 1]["move"], "actor_move": chosen,
            "prior_own_moves_forced": len(forced), "seed": args.seed,
            "clock_seconds_at_decision": frames[idx]["clocks"][side],
            "belief_size_at_decision": diagnostic,
            "engine_root_traces": [json.loads(line) for line in engine_roots],
            "engine_final_moves": engine_finals,
            "catastrophe_prune_risk": prune_risks,
            "catastrophe_prune_inputs": prune_inputs,
            "actor_return_code": proc.returncode,
            "stdout": proc.stdout, "stderr": proc.stderr,
            "archive_sha256": hashlib.sha256(args.archive.read_bytes()).hexdigest(),
            "replay_sha256": hashlib.sha256(game_path.read_bytes()).hexdigest(),
            "limitations": [
                "Search timing and sampled roots can vary with runtime scheduling.",
                "Previous moves are forced only after their full actor searches run.",
                "One replay reproduces a decision diagnostic, not a strength estimate.",
            ],
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in (
        "game", "decision_frame", "recorded_move", "actor_move",
        "prior_own_moves_forced", "belief_size_at_decision", "actor_return_code")}, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=Path, default=Path("fable-submissions/iamavirus-v30-misty-4s.zip"))
    ap.add_argument("--games-root", type=Path, default=Path("data/raw/games"))
    ap.add_argument("--game", required=True)
    ap.add_argument("--decision-frame", type=int, required=True)
    ap.add_argument("--python", type=Path, default=Path("/home/henrytan/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14"))
    ap.add_argument("--chess-site-packages", type=Path,
                    default=Path("/home/henrytan/git/fow-starter/.venv/lib/python3.12/site-packages"))
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    run(args)


if __name__ == "__main__":
    main()
