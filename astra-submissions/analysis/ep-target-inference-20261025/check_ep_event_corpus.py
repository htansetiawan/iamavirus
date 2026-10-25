#!/usr/bin/env python3
"""Run archived and patched v35 view_moves on a JSONL EP-event corpus."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ARCHIVE = ROOT / "fable-submissions/iamavirus-v35-mist-c-v14.zip"
TOP = {"Greek Gift", "Instructors", "Knight Vision", "Decent Chess Bot",
       "Strongly Invisible", "duck", "TA Baseline A", "TA Baseline S", "TA Baseline P"}


def compile_probe(source: Path, archive_dir: Path, output: Path) -> None:
    cmd = ["cc", "-O2", "-std=c11", "-D_POSIX_C_SOURCE=199309L", "-pthread",
           "-I", str(archive_dir), str(source), str(archive_dir / "src/board.c"),
           str(archive_dir / "src/belief.c"), str(archive_dir / "src/movemodel.c"),
           str(archive_dir / "src/eval.c"), "-lm", "-o", str(output)]
    subprocess.run(cmd, check=True)


def mover(event: dict) -> str:
    return event[event["side"]]


def won(event: dict) -> bool | None:
    if event["result"] == "1/2-1/2": return None
    return (event["result"] == "1-0") == (event["side"] == "white")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", type=Path, required=True)
    ap.add_argument("--archive", type=Path, default=ARCHIVE)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--top-team-games", type=int, default=0)
    ap.add_argument("--diagonal-prefilter-games", type=int, default=0)
    args = ap.parse_args()
    events = [json.loads(line) for line in args.events.read_text().splitlines() if line]
    with tempfile.TemporaryDirectory(prefix="astra-ep-corpus-check-") as td:
        work = Path(td)
        base, patched = work / "v35", work / "patched"
        base.mkdir()
        with zipfile.ZipFile(args.archive) as zf:
            for name in zf.namelist():
                if name.startswith("src/"):
                    zf.extract(name, base)
        shutil.copytree(base, patched)
        patch_root = work / "patch-root"
        (patch_root / "src").mkdir(parents=True)
        (patch_root / "src/belief.c").write_bytes((base / "src/belief.c").read_bytes())
        subprocess.run(["patch", "-p1", "-i", str(HERE / "belief-ep-observation.patch")],
                       cwd=patch_root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (patched / "src/belief.c").write_bytes((patch_root / "src/belief.c").read_bytes())
        base_bin, patch_bin = work / "base-probe", work / "patch-probe"
        compile_probe(HERE / "view_moves_batch.c", base, base_bin)
        compile_probe(HERE / "view_moves_batch.c", patched, patch_bin)
        input_text = "".join(f"{'b' if e['side']=='black' else 'w'} {e['castle_rooks']:x} {e['move']} {e['view']}\n" for e in events)
        base_out = subprocess.run([str(base_bin)], input=input_text, text=True, capture_output=True, check=True).stdout.splitlines()
        patch_out = subprocess.run([str(patch_bin)], input=input_text, text=True, capture_output=True, check=True).stdout.splitlines()
        if len(base_out) != len(events) or len(patch_out) != len(events):
            raise RuntimeError(f"probe line mismatch: events={len(events)}, baseline={len(base_out)}, patched={len(patch_out)}")
    rows = []
    by_team: dict[str, dict] = {}
    by_outcome: dict[str, dict] = {}
    for event, b, p in zip(events, base_out, patch_out):
        if b not in ("0", "1") or p not in ("0", "1"):
            raise RuntimeError(f"invalid probe response for {event['game']} ply {event['ply']}: {b!r}, {p!r}")
        event["baseline_available"], event["patched_available"] = b == "1", p == "1"
        event["recovered"] = b == "0" and p == "1"
        rows.append(event)
        name = mover(event)
        teams = by_team.setdefault(name, {"events": 0, "baseline_omitted": 0, "patched_omitted": 0, "recovered": 0})
        teams["events"] += 1
        teams["baseline_omitted"] += b == "0"
        teams["patched_omitted"] += p == "0"
        teams["recovered"] += event["recovered"]
        outcome = won(event)
        label = "draw" if outcome is None else "won" if outcome else "lost"
        group = by_outcome.setdefault(label, {"events": 0, "baseline_omitted": 0, "patched_omitted": 0, "recovered": 0})
        group["events"] += 1
        group["baseline_omitted"] += b == "0"
        group["patched_omitted"] += p == "0"
        group["recovered"] += event["recovered"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as f:
        for row in rows: f.write(json.dumps(row, separators=(",", ":")) + "\n")
    summary = {
        "archive_sha256": subprocess.run(["sha256sum", str(args.archive)], text=True, capture_output=True, check=True).stdout.split()[0],
        "top_team_games_scanned": args.top_team_games or None,
        "games_with_diagonal_pawn_prefilter": args.diagonal_prefilter_games or None,
        "unique_games_with_actual_ep": len({r["game"] for r in rows}),
        "actual_ep_actions": len(rows),
        "baseline_omitted": sum(not r["baseline_available"] for r in rows),
        "patched_omitted": sum(not r["patched_available"] for r in rows),
        "recovered": sum(r["recovered"] for r in rows),
        "by_top_bot_moving": {k: v for k, v in sorted(by_team.items()) if k in TOP},
        "by_replay_side_outcome": by_outcome,
        "event_rows": str(args.out),
        "scope_note": "Actual EP actions observed in prefiltered public games; no causal strength inference.",
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
