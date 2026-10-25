#!/usr/bin/env python3
"""Replay one recorded decision through baseline and guard binaries with risk diagnostics."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

MOVE_RE = re.compile(r"^move ([a-h][1-8][a-h][1-8][qrbn]?)$")
RISK_RE = re.compile(r"^mist: risk ([a-h][1-8][a-h][1-8][qrbn]?) ([0-9.]+) qrisk ([^/ ]+)/([^ ]+) mrisk ([^ ]+)(?: \(chosen\))?$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(binary_dir: Path, frames: list[dict], target_frame: int, side: int,
           seed: int, max_seconds: float, timeout: float) -> dict:
    key = "white" if side == 0 else "black"
    selected = frames[:target_frame + 1]
    protocol = ["fow", f"{key} 180 2"]
    for t, frame in enumerate(selected):
        protocol.append(frame[key])
        if t % 2 == side:
            protocol.append(f"{frame['clocks'][side]:.3f}")
    forced = [frames[i]["move"] for i in range(1, target_frame + 1)
              if i % 2 == 1 - side]
    env = os.environ.copy()
    env.update({
        "FOW_SEED": str(seed),
        "MIST_CAP": "200000",
        "MIST_MAX_SECONDS": str(max_seconds),
        "MIST_FORCE_MOVES": ",".join(forced),
        "MIST_TRUTH_SEQ": ",".join(f["board"] for f in selected),
        "MIST_RISK": "1",
        "MIST_TIMING": "1",
        "MIST_STOCKFISH": str((binary_dir / "bin/stockfish").resolve()),
        "MIST_HISTORY_TABLE": str((binary_dir / "data/history.bin").resolve()),
    })
    proc = subprocess.run([str((binary_dir / "mist").resolve())],
                          input="\n".join(protocol) + "\n", text=True,
                          capture_output=True, cwd=binary_dir, env=env,
                          timeout=timeout, check=False)
    moves = [m.group(1) for line in proc.stdout.splitlines()
             if (m := MOVE_RE.match(line))]
    risk = {}
    for line in proc.stderr.splitlines():
        m = RISK_RE.match(line)
        if m:
            risk[m.group(1)] = {
                "king_risk": float(m.group(2)),
                "queen_risk": float(m.group(3)),
                "queen_risk_sharp": float(m.group(4)),
                "material_risk": float(m.group(5)),
                "chosen": "(chosen)" in line,
            }
    truth = [line for line in proc.stderr.splitlines()
             if line.startswith(f"mist: truth v={target_frame} ")]
    guards = [line for line in proc.stderr.splitlines()
              if line.startswith(("mist: king guard", "mist: queen guard"))]
    summaries = [line for line in proc.stderr.splitlines()
                 if line.startswith("mist: n=")]
    return {
        "binary": str((binary_dir / "mist").resolve()),
        "binary_sha256": sha256(binary_dir / "mist"),
        "returncode": proc.returncode,
        "chosen": moves[-1] if moves else None,
        "risk_by_move": risk,
        "truth_at_target": truth[-1] if truth else None,
        "guard_messages": guards,
        "decision_summary": summaries[-1] if summaries else None,
        "stderr_tail": proc.stderr.splitlines()[-16:],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--replay", type=Path, required=True)
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--target-frame", type=int, required=True,
                    help="observation frame immediately before the recorded decision")
    ap.add_argument("--side", choices=("white", "black"), required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--max-seconds", type=float, default=10.0)
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    replay_data = json.loads(a.replay.read_text())
    side = 0 if a.side == "white" else 1
    recorded = replay_data["frames"][a.target_frame + 1]["move"]
    result = {
        "classification": "same-history diagnostic replay; not a strength test",
        "game": replay_data.get("id"),
        "target_frame": a.target_frame,
        "side": a.side,
        "recorded_move": recorded,
        "true_observation": replay_data["frames"][a.target_frame][a.side],
        "baseline": replay(a.baseline.resolve(), replay_data["frames"],
                           a.target_frame, side, a.seed, a.max_seconds, a.timeout),
        "candidate": replay(a.candidate.resolve(), replay_data["frames"],
                            a.target_frame, side, a.seed, a.max_seconds, a.timeout),
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("game", "target_frame", "side", "recorded_move")}, indent=2))
    print("baseline:", json.dumps({k: result["baseline"][k] for k in
                                  ("chosen", "truth_at_target", "guard_messages", "decision_summary")}))
    print("candidate:", json.dumps({k: result["candidate"][k] for k in
                                    ("chosen", "truth_at_target", "guard_messages", "decision_summary")}))
    print("saved:", a.out)


if __name__ == "__main__":
    main()
