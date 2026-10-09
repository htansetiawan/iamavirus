"""CPU-only review of PPO cutoff targets and league exposure; never starts training.

Run from the repository root:
  .venv/bin/python astra-submissions/tools/audit_rl_review.py --output /tmp/rl-audit.json

Loads only the current gae() function through AST, avoiding trainer imports and
GPU/simulator initialization. Synthetic successor values test the mathematical
contract; they are not measurements of real trajectory values or playing strength.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml


def fingerprint(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest()}


def expected_gae(trans, values, bootstraps, gamma=1.0, lam=0.95):
    """Reference with explicit same-player successor values at unfinished tails."""
    sequences, pending = [], {}
    for k, row in enumerate(trans):
        pending.setdefault(row["game"], []).append(k)
        if row["done"]:
            sequences.append(pending.pop(row["game"]))
    sequences.extend(pending.values())
    advantage = np.zeros(len(trans))
    for seq in sequences:
        tail = trans[seq[-1]]
        next_value = 0.0 if tail["done"] else bootstraps[tail["game"]]
        running = 0.0
        for k in reversed(seq):
            delta = trans[k]["reward"] + gamma * next_value - values[k]
            running = delta + gamma * lam * running
            advantage[k] = running
            next_value = values[k]
    return advantage, advantage + values


def cutoff_cases(source: Path):
    tree = ast.parse(source.read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "gae")
    namespace = {"np": np}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), namespace)
    row = lambda g, done=False, reward=0.0: {"game": g, "done": done, "reward": reward}
    cases = [
        ("unfinished_single", [row(0)], [0.2], {0: 0.8}),
        ("unfinished_two_steps", [row(0), row(0)], [0.1, 0.2], {0: 0.8}),
        ("terminal_win_control", [row(0, True, 1.0)], [0.2], {}),
        ("terminal_loss_control", [row(0, True, -1.0)], [0.2], {}),
        ("interleaved_games", [row(0), row(1, True, 1.0), row(0)],
         [0.1, 0.2, 0.2], {0: 0.8}),
        ("reset_same_slot", [row(0, True, 1.0), row(0)], [0.2, 0.2], {0: 0.8}),
    ]
    results = []
    for name, trans, values, successor in cases:
        v = np.array(values)
        kwargs = {"bootstrap_values": successor} if any(
            arg.arg == "bootstrap_values" for arg in fn.args.args) else {}
        actual_a, actual_r = namespace["gae"](trans, v, 1.0, 0.95, **kwargs)
        expected_a, expected_r = expected_gae(trans, v, successor)
        results.append({"case": name, "transitions": trans, "pre_action_values": values,
                        "successor_values": successor,
                        "actual_advantage": actual_a.tolist(),
                        "expected_advantage": expected_a.tolist(),
                        "actual_return": actual_r.tolist(), "expected_return": expected_r.tolist(),
                        "matches_contract": bool(np.allclose(actual_a, expected_a) and
                                                 np.allclose(actual_r, expected_r))})
    return results


def exposure(path: Path):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    result = {"source": fingerprint(path), "windows": []}
    for label, window in (("first20", rows[:20]), ("last40", rows[-40:])):
        counts = {}
        for row in window:
            for name, (_, n) in row["score_vs"].items():
                counts[name] = counts.get(name, 0) + n
        total = sum(counts.values())
        result["windows"].append({"window": label,
            "iterations": [window[0]["iteration"], window[-1]["iteration"]],
            "completed_games": total, "by_member": counts,
            "duck_share": counts.get("duck", 0) / total,
            "instructors_games": counts.get("instructors", 0),
            "snapshot_share": sum(n for name, n in counts.items() if "snapshot" in name) / total})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = Path("learning/rl_train.py")
    configs = []
    for path in map(Path, ("learning/configs/rl_v18.yaml", "learning/configs/rl_v18_cont.yaml",
                           "learning/configs/rl_v20.yaml")):
        cfg = yaml.safe_load(path.read_text())["rl"]
        configs.append({"source": fingerprint(path), "league": cfg["league"],
                        "resume": cfg.get("resume"), "critic_init": cfg["critic_init"]})
    report = {"created_at": datetime.now(timezone.utc).isoformat(),
              "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "source": fingerprint(source), "cutoff_cases": cutoff_cases(source),
              "league_configs": configs,
              "exposure": [exposure(Path("checkpoints") / run / "rl_log.jsonl")
                           for run in ("rl-v18", "rl-v20")],
              "limits": ["Synthetic correctness evidence, not an Elo estimate.",
                         "Completed-game shares differ from assignment and decision shares.",
                         "No training, GPU work, root-source changes, or candidate build."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "cases": len(report["cutoff_cases"]),
                      "contract_mismatches": sum(not c["matches_contract"] for c in report["cutoff_cases"])}))


if __name__ == "__main__":
    main()
