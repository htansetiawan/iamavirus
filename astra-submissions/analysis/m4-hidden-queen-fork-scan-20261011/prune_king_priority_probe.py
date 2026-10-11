#!/usr/bin/env python3
"""Reproduce v30's one-world catastrophe-prune ordering conflict.

Loads the exact archived prune implementation in a temporary directory,
reconstructs the recorded actor root values, then compares the original order
with a royal-survival-first candidate. This is a one-position counterfactual,
not a strength evaluation.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random
import sys
import tempfile
import zipfile

import chess


class OneWorldEnumerator:
    def __init__(self, fen: str):
        self.fen = fen
        self.size = 1

    def sample_root_fens(self, *, n: int, rng):
        return [self.fen]


def king_risk(fen: str, move: chess.Move, side: chess.Color) -> float:
    from fow_chess.cfr.leaf_eval import king_capture_imminent

    board = chess.Board(fen)
    if move not in board.pseudo_legal_moves:
        return 1.0
    board.push(move)
    return float(king_capture_imminent(board, side) is not None)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=Path, default=Path("fable-submissions/iamavirus-v30-misty-4s.zip"))
    ap.add_argument("--actor-trace", type=Path, default=Path(
        "astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/actor-69nmui22-frame38-prune-risk.json"))
    args = ap.parse_args()
    trace = json.loads(args.actor_trace.read_text())
    guard_input = trace["catastrophe_prune_inputs"][-1]
    root_values = {chess.Move.from_uci(m): float(v) for m, v in guard_input["values"]}
    root_strategy = {chess.Move.from_uci(m): float(p) for m, p in guard_input["strategy"]}
    # Use the exact live prune input, after search extraction and all preceding guards.
    chosen = chess.Move.from_uci(guard_input["move"])
    emitted = chess.Move.from_uci(trace["engine_final_moves"][-1])
    fen = trace["catastrophe_prune_risk"][-1]["sample"][0]
    color = chess.WHITE

    with tempfile.TemporaryDirectory(prefix="astra-prune-probe-") as tmp:
        with zipfile.ZipFile(args.archive) as zf:
            zf.extractall(tmp)
        sys.path.insert(0, str(Path(tmp) / "lib"))
        from fow_chess.engine_profile import PROFILES
        from fow_chess.engine_v2 import EngineV2

        profile = PROFILES["v1.6"]
        profile.apply_process_flags()

        class EngineStub:
            _catastrophe_prune = EngineV2._catastrophe_prune

            def __init__(self, boards):
                self.enumerator = OneWorldEnumerator(fen)
                self.perspective = color
                self.rng = random.Random(1)
                self._hv_prune_adaptive = profile.hv_prune_adaptive
                self._hv_prune_tau = profile.hv_prune_tau
                self._hv_prune_pref = profile.hv_prune_pref
                self._hv_prune_pmax = profile.hv_prune_pmax
                self._hv_prune_king_floor = profile.hv_prune_king_floor or None

        engine = EngineStub([chess.Board(fen)])
        prune_frac = float(os.environ.get("FOW_HV_PRUNE_FRAC", "0"))
        old = engine._catastrophe_prune(chosen, root_values, prune_frac, root_strategy)

        king_risks = {m: king_risk(fen, m, color) for m in root_values}
        best_risk = min(king_risks.values())
        royal_safe_values = {m: v for m, v in root_values.items()
                             if king_risks[m] <= best_risk + 1e-12}
        royal_safe_strategy = {m: p for m, p in root_strategy.items()
                               if m in royal_safe_values}
        if not royal_safe_values:
            raise AssertionError("no royal-safe candidates in one-world probe")
        corrected = engine._catastrophe_prune(
            chosen, royal_safe_values, prune_frac, royal_safe_strategy)

        result = {
            "classification": "single-position exact-world counterfactual",
            "game": trace["game"], "decision_frame": trace["decision_frame"],
            "profile": profile.name, "world_count": 1, "world_fen": fen,
            "search_move_before_prune": chosen.uci(),
            "old_prune_move": old.uci(),
            "actor_emitted_move": emitted.uci(),
            "captured_live_guard_input": True,
            "new_royal_first_move": corrected.uci(),
            "risk": {m.uci(): {"king_capture": king_risks[m],
                               "root_value": root_values[m]}
                     for m in (chosen, old, corrected)},
            "candidate_pool_size_before": len(root_values),
            "candidate_pool_size_after_royal_filter": len(royal_safe_values),
            "limits": ["One retrospective Duck position only; no Elo claim.",
                       "The royal-first wrapper is a candidate algorithm, not a release."]
        }
        print(json.dumps(result, indent=2))
        if king_risks[old] > best_risk and king_risks[corrected] <= best_risk + 1e-12:
            raise SystemExit(0)
        raise SystemExit("the probe did not reproduce both old failure and candidate correction")


if __name__ == "__main__":
    main()
