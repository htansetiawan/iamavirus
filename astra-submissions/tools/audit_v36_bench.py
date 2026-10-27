#!/usr/bin/env python3
"""Pin and independently audit v36's fixed 40/32/32-game release screen.

Never runs a bot. A passing score is not an Elo claim, nor a pass of gates 1/2.
Incomplete jobs, duplicate jobs, changed artifacts and missing runtime evidence
cannot produce a passing gate. The live result ledger is always read-only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
ROLES = {"direct": (40, 200000), "candidate_misty": (32, 201000),
         "baseline_misty": (32, 201000)}
RESULTS = {"1-0": 1.0, "0-1": 0.0, "1/2-1/2": 0.5}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def instant(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamp must include a time zone")
    return dt.timestamp()


def write_json(path, value, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w") as out:
        json.dump(value, out, indent=2, allow_nan=False)
        out.write("\n")


def freeze(queue_path, role_ids, referee, opponent_environment):
    queue_path = Path(queue_path).resolve()
    queue = json.loads(queue_path.read_text())
    matches = {m["id"]: m for m in queue["matchups"]}
    if len(matches) != 3 or len(queue["matchups"]) != 3 or set(matches) != set(role_ids.values()):
        raise ValueError("exactly three distinct, named matchup roles are required")
    artifacts = {}
    for role, (count, seed) in ROLES.items():
        m = matches[role_ids[role]]
        if m["max_games"] != count or m["seed"] != seed:
            raise ValueError(f"{role}: games/seeds differ from the decision contract")
        if m.get("a_env", []) or m.get("b_env", []):
            raise ValueError(f"{role}: unexpected runtime overrides")
        sp = m.get("sprt", {})
        if not (0 < sp.get("alpha", 1) <= 1e-12 and 0 < sp.get("beta", 1) <= 1e-12):
            raise ValueError("this gate requires the frozen fixed-length screen settings")
        for side in ("a", "b"):
            p = Path(m[side]).resolve()
            artifacts[str(p)] = digest(p)
    d, c, b = [matches[role_ids[r]] for r in ROLES]
    if not (Path(d["a"]).resolve() == Path(c["a"]).resolve()
            and Path(d["b"]).resolve() == Path(b["a"]).resolve()
            and Path(c["b"]).resolve() == Path(b["b"]).resolve()):
        raise ValueError("candidate, baseline and Misty roles are not matched")
    if len(artifacts) != 3:
        raise ValueError("expected three distinct archives")
    return {
        "schema": 1, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "classification": "pre-run input pins; not a gate result",
        "queue_path": str(queue_path), "queue_sha256": digest(queue_path),
        "queue": queue, "roles": role_ids, "artifacts_sha256": artifacts,
        "referee": str(Path(referee).resolve()), "referee_sha256": digest(referee),
        "opponent_environment": str(Path(opponent_environment).resolve()),
        "opponent_environment_sha256": digest(opponent_environment),
        "wall_cap_seconds": 43200,
    }


def verify_inputs(pins):
    failures = []
    pairs = list(pins["artifacts_sha256"].items()) + [
        (pins["queue_path"], pins["queue_sha256"]),
        (pins["referee"], pins["referee_sha256"]),
        (pins["opponent_environment"], pins["opponent_environment_sha256"]),
    ]
    try:
        env = json.loads(Path(pins["opponent_environment"]).read_text())
        pairs += list(env["binaries"].items())
        pairs += [(env["interpreter"]["path"], env["interpreter"]["sha256"])]
        for pkg in env["packages"].values():
            pairs += [(str(Path(pkg["root"]) / rel), sha) for rel, sha in pkg["files_sha256"]]
    except (KeyError, OSError, ValueError) as exc:
        failures.append(f"opponent environment manifest unreadable: {exc}")
    for path, sha in pairs:
        try:
            if digest(path) != sha:
                failures.append(f"changed input: {path}")
        except OSError as exc:
            failures.append(f"missing input: {path}: {exc}")
    return failures


def replay_check(row, referee):
    """Internal referee consistency, not an independent rules implementation."""
    path = ROOT / row["replay"]
    replay = json.loads(path.read_text())
    if replay["result"] != row["result"] or replay["reason"] != row["reason"]:
        raise ValueError("result/reason differs from replay")
    frames = replay["frames"]
    if not frames or len(frames) - 1 != row["plies"]:
        raise ValueError("frame count differs from ledger")
    board = referee.FowBoard()
    repetitions = Counter({referee.position_key(board): 1})
    ended = None
    low_clocks = [math.inf, math.inf]
    for i, frame in enumerate(frames):
        clocks = frame["clocks"]
        if len(clocks) != 2 or not all(isinstance(t, (int, float)) and math.isfinite(t) for t in clocks):
            raise ValueError(f"invalid clocks at ply {i}")
        if i:
            if ended is not None:
                raise ValueError("recorded move after board termination")
            board.push(board.parse_uci(frame["move"]))
            repetitions[referee.position_key(board)] += 1
        expected = referee.make_frame(board, clocks, frame["move"])
        for key in ("ply", "board", "white", "black"):
            if expected[key] != frame[key]:
                raise ValueError(f"{key} mismatch at ply {i}")
        ended = referee.outcome(board, repetitions)
        low_clocks = [min(low_clocks[s], clocks[s]) for s in (0, 1)]
    if frames[-1]["clocks"] != row["clocks"]:
        raise ValueError("final clocks differ from ledger")
    # Any non-board termination needs an explicit reliability/failure review.
    normal = ended is not None and tuple(ended) == (row["result"], row["reason"])
    move_limit = (ended is None and len(frames) - 1 == 1000
                  and (row["result"], row["reason"]) == ("1/2-1/2", "Move limit reached"))
    return {"sha256": digest(path), "frames": len(frames),
            "normal_board_termination": normal, "valid_move_limit_draw": move_limit,
            "minimum_recorded_clocks": low_clocks}


def audit(pins, rows, receipt, *, referee=None, input_failures=()):
    errors, pending, rejected = list(input_failures), [], []
    matches = {m["id"]: m for m in pins["queue"]["matchups"]}
    expected = {(pins["roles"][r], p, color)
                for r, (n, _) in ROLES.items() for p in range(n // 2)
                for color in ("white", "black")}
    seen, valid, replay_audits = set(), {}, {}
    frozen_at = instant(pins["created_at"])
    for row in rows:
        if row.get("matchup") not in matches:
            continue
        key = (row.get("matchup"), row.get("pair"), row.get("a_colour"))
        label = ":".join(map(str, key))
        if key not in expected or key in seen:
            errors.append(f"unexpected or duplicate job: {label}")
            continue
        seen.add(key)
        m = matches[key[0]]
        try:
            if row["seed"] != m["seed"] + 2 * key[1]:
                raise ValueError("wrong seed")
            if instant(row["ts"]) < frozen_at:
                raise ValueError("result predates input freeze")
            for side in ("a", "b"):
                path = str(Path(m[side]).resolve())
                if str(Path(row[side]).resolve()) != path:
                    raise ValueError(f"wrong {side} archive path")
                if row[f"{side}_sha"] != pins["artifacts_sha256"][path][:12]:
                    raise ValueError(f"wrong {side} archive hash")
                if row.get(f"{side}_env", []) != m.get(f"{side}_env", []):
                    raise ValueError(f"wrong {side} environment")
            if row["result"] not in RESULTS:
                pending.append(f"unresolved failed/unknown job: {label}: {row.get('reason')}")
                continue
            score = RESULTS[row["result"]]
            if key[2] == "black":
                score = 1 - score
            if score != row["a_score"]:
                raise ValueError("score disagrees with result/color")
            if len(row["clocks"]) != 2 or not all(math.isfinite(x) for x in row["clocks"]):
                raise ValueError("invalid end clocks")
            if referee is not None:
                check = replay_check(row, referee)
                replay_audits[label] = check
                if not (check["normal_board_termination"] or check.get("valid_move_limit_draw")):
                    rejected.append(f"non-board termination requires failure review: {label}: {row['reason']}")
            valid[key] = row
        except (KeyError, TypeError, ValueError, OSError) as exc:
            errors.append(f"{label}: {exc}")
    missing = sorted(expected - seen)
    if missing:
        pending.append(f"{len(missing)} expected jobs missing")
    if len(valid) != 104:
        pending.append(f"{len(valid)}/104 valid scored jobs")
    if referee is None:
        pending.append("replay integrity not checked")
    if not receipt:
        pending.append("run receipt absent")
    else:
        try:
            if receipt["queue_sha256"] != pins["queue_sha256"]:
                errors.append("run receipt belongs to a different queue")
            if receipt.get("state") != "complete":
                pending.append(f"run is {receipt.get('state', 'unknown')}")
            if instant(receipt["started_at"]) < frozen_at:
                errors.append("run started before inputs were frozen")
            if receipt.get("finished_at"):
                elapsed = instant(receipt["finished_at"]) - instant(receipt["started_at"])
                if elapsed < 0 or elapsed > pins["wall_cap_seconds"]:
                    errors.append("run exceeded its 12h wall cap or has invalid times")
                if any(not (instant(receipt["started_at"]) <= instant(row["ts"])
                            <= instant(receipt["finished_at"])) for row in valid.values()):
                    errors.append("result timestamp outside this run's interval")
            else:
                pending.append("run finish timestamp absent")
            attempts = receipt["attempted_jobs"]
            if not isinstance(attempts, int) or attempts < len(seen):
                errors.append("attempt count is invalid or below recorded result rows")
            elif attempts > len(seen):
                if receipt.get("state") in ("running", "wall_cap", "failed"):
                    pending.append(f"{attempts - len(seen)} started jobs have no final row yet")
                else:
                    errors.append("attempt count disagrees with result rows; reconcile missing attempts")
            if receipt["failed_jobs"]:
                pending.append("runner reported failed jobs; attribution/rejection required")
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"invalid run receipt: {exc}")
    summaries = {}
    for role in ROLES:
        role_rows = [v for k, v in valid.items() if k[0] == pins["roles"][role]]
        summaries[role] = {
            "games": len(role_rows), "points": sum(r["a_score"] for r in role_rows),
            "color_points": {c: sum(r["a_score"] for r in role_rows if r["a_colour"] == c)
                             for c in ("white", "black")},
            "wdl": {str(s): sum(r["a_score"] == s for r in role_rows) for s in (1, .5, 0)},
        }
    metrics = {}
    if len(valid) == 104:
        d, c, b = [summaries[r] for r in ROLES]
        direction = .5 * ((d["points"] / 40 - .5) + (c["points"] - b["points"]) / 32)
        metrics["combined_direction_D"] = direction
        for passed, message in [
            (d["points"] >= 18, "head-to-head score below 18/40"),
            (min(d["color_points"].values()) >= 7, "head-to-head color score below 7/20"),
            (c["points"] - b["points"] >= -4, "matched Misty difference below -4 points"),
            (direction > 0, "combined score direction is not positive"),
        ]:
            if not passed:
                rejected.append(message)
        clocks = {}
        for role in ROLES:
            rr = [v for k, v in valid.items() if k[0] == pins["roles"][role]]
            clocks[role] = [r["clocks"][0 if r["a_colour"] == "white" else 1] for r in rr]
        direct_b = [r["clocks"][1 if r["a_colour"] == "white" else 0]
                    for k, r in valid.items() if k[0] == pins["roles"]["direct"]]
        metrics["end_clock_medians"] = {r: statistics.median(v) for r, v in clocks.items()}
        metrics["direct_baseline_end_clock_median"] = statistics.median(direct_b)
        metrics["candidate_minimum_end_clock"] = min(clocks["direct"] + clocks["candidate_misty"])
        if metrics["candidate_minimum_end_clock"] < 10:
            rejected.append("candidate end clock below 10s")
        if statistics.median(clocks["direct"]) < statistics.median(direct_b) - 10:
            rejected.append("candidate median direct-game clock worsened by over 10s")
        if statistics.median(clocks["candidate_misty"]) < statistics.median(clocks["baseline_misty"]) - 10:
            rejected.append("candidate median Misty clock worsened by over 10s")
        # Each sample keeps both colors; Misty blocks keep both engines' games.
        direct_pairs = [sum(valid[(pins['roles']['direct'], p, col)]['a_score']
                            for col in ('white', 'black')) / 2 for p in range(20)]
        misty_pairs = [sum(valid[(pins['roles']['candidate_misty'], p, col)]['a_score']
                          - valid[(pins['roles']['baseline_misty'], p, col)]['a_score']
                          for col in ('white', 'black')) / 2 for p in range(16)]
        rng = random.Random(20261027036)
        boot = sorted(.5 * (statistics.mean(rng.choices(direct_pairs, k=20)) - .5
                           + statistics.mean(rng.choices(misty_pairs, k=16))) for _ in range(2000))
        metrics['direction_pair_bootstrap_95'] = [boot[49], boot[1949]]
    status = "invalid" if errors else "rejected" if rejected else "incomplete" if pending else "passed_screen"
    return {"status": status, "classification": "local v36 screen only; gates 1/2 and arena strength separate",
            "errors": errors, "rejections": rejected, "pending": pending,
            "expected_jobs": 104, "seen_jobs": len(seen), "valid_jobs": len(valid),
            "missing_jobs": missing, "matchups": summaries, "metrics": metrics,
            "replay_audits": replay_audits,
            "limits": "Replay checks reuse the referee; bootstrap assumes representative independent seed blocks. No arena Elo inference."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    pin = sub.add_parser("freeze")
    pin.add_argument("--queue", type=Path, required=True)
    for role in ROLES:
        pin.add_argument("--" + role.replace("_", "-"), required=True)
    pin.add_argument("--referee", type=Path, default=Path.home()/"git/fow-starter/referee.py")
    pin.add_argument("--opponent-environment", type=Path, default=ROOT/"astra-submissions/analysis/v36-plan-20261026/opponent-environment.json")
    pin.add_argument("--out", type=Path, required=True)
    run = sub.add_parser("audit")
    run.add_argument("--pins", type=Path, required=True)
    run.add_argument("--ledger", type=Path, default=ROOT/"data/arena_local/games.jsonl")
    run.add_argument("--run-receipt", type=Path)
    run.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "freeze":
        value = freeze(args.queue, {r: getattr(args, r) for r in ROLES}, args.referee, args.opponent_environment)
        failures = verify_inputs(value)
        if failures:
            raise SystemExit("\n".join(failures))
        write_json(args.out, value, exclusive=True)
        print(f"Frozen inputs: {args.out}; sha256={digest(args.out)}")
    else:
        pins = json.loads(args.pins.read_text())
        rows = [json.loads(s) for s in args.ledger.read_text().splitlines() if s.strip()]
        receipt = json.loads(args.run_receipt.read_text()) if args.run_receipt else None
        sys.path.insert(0, str(Path(pins["referee"]).parent))
        import referee
        report = audit(pins, rows, receipt, referee=referee, input_failures=verify_inputs(pins))
        report.update(audited_at=datetime.now(timezone.utc).isoformat(),
                      pins_sha256=digest(args.pins), auditor_sha256=digest(__file__))
        write_json(args.out, report)
        print(json.dumps({k: report[k] for k in ('status', 'seen_jobs', 'valid_jobs', 'errors', 'rejections', 'pending', 'metrics')}, indent=2))
        return 0 if report["status"] == "passed_screen" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
