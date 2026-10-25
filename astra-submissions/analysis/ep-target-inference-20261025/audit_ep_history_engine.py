#!/usr/bin/env python3
"""Validate the compiled observation+history EP helper on full cached replays."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

from audit_replay_move_sets import ROOT, HERE, ARCHIVE, state_metadata


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, default=ARCHIVE)
    ap.add_argument("--events", type=Path, default=HERE / "top-opponent-ep-action-coverage.jsonl")
    ap.add_argument("--games", type=int, default=0)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    game_ids = sorted({json.loads(line)["game"] for line in args.events.read_text().splitlines() if line})
    if args.games:
        game_ids = game_ids[:args.games]
    records: list[tuple[str, int, int]] = []
    lines: list[str] = []
    skipped = 0
    for game_id in game_ids:
        path = ROOT / "data/raw/games" / game_id / "replay.json"
        try:
            frames = json.loads(path.read_text())["frames"]
            for ply, frame in enumerate(frames):
                board = frame["board"]
                if len(board) != 64 or any(c not in "PNBRQKpnbrqk-" for c in board):
                    continue
                side = "white" if ply % 2 == 0 else "black"
                view = frame[side]
                previous = frames[ply - 1][side] if ply else "!" * 64
                castle, ep = state_metadata(frames, ply)
                lines.append(f"{'w' if side == 'white' else 'b'} {castle:x} {ep} {board} {view} {previous}\n")
                records.append((game_id, ply, ep))
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            skipped += 1
    with tempfile.TemporaryDirectory(prefix="astra-ep-history-audit-") as td:
        work = Path(td)
        source = work / "source"
        source.mkdir()
        with zipfile.ZipFile(args.archive) as zf:
            for name in zf.namelist():
                zf.extract(name, source)
        subprocess.run(["python3", str(HERE / "apply_ep_history_candidate.py"),
                        "--source-root", str(source)], check=True, capture_output=True, text=True)
        binary = work / "history-probe"
        subprocess.run(["cc", "-O2", "-std=c11", "-D_POSIX_C_SOURCE=199309L", "-pthread",
                        "-I", str(source), str(HERE / "audit_history_moves.c"),
                        str(source / "src/board.c"), str(source / "src/belief.c"),
                        str(source / "src/movemodel.c"), str(source / "src/eval.c"),
                        "-lm", "-o", str(binary)], check=True)
        result = subprocess.run([str(binary)], input="".join(lines), text=True,
                                capture_output=True, check=True)
        output_rows = result.stdout.splitlines()
        if len(output_rows) != len(records):
            raise RuntimeError(f"probe rows {len(output_rows)} != replay positions {len(records)}")
    stats = {"false_candidates": 0, "false_ep_candidates": 0, "false_other_candidates": 0,
             "missed_true_moves": 0, "missed_ep_moves": 0, "missed_other_moves": 0,
             "positions_with_false": 0, "positions_with_missed": 0, "positions_with_ep_right": 0}
    with gzip.open(args.out, "wt") as out:
        for record, text in zip(records, output_rows):
            count, false_count, missed, fep, fother, mep, mother = map(int, text.split("\t"))
            stats["false_candidates"] += false_count
            stats["false_ep_candidates"] += fep
            stats["false_other_candidates"] += fother
            stats["missed_true_moves"] += missed
            stats["missed_ep_moves"] += mep
            stats["missed_other_moves"] += mother
            stats["positions_with_false"] += false_count > 0
            stats["positions_with_missed"] += missed > 0
            stats["positions_with_ep_right"] += record[2] >= 0
            out.write(json.dumps({"game": record[0], "ply": record[1], "ep_target": record[2],
                                  "candidate_count": count, "false_count": false_count,
                                  "missed_count": missed, "missed_ep_count": mep,
                                  "missed_other_count": mother}, separators=(",", ":")) + "\n")
    summary = {"archive": str(args.archive.relative_to(ROOT)) if args.archive.is_relative_to(ROOT) else str(args.archive),
               "games": len(game_ids), "games_skipped": skipped, "positions": len(records),
               "aggregate": stats,
               "candidate": "conservative current-observation EP inference plus one-ply own-view history proof",
               "meaning": "Compiled candidate move sets compared against true pseudo-legal moves on replay boards; not an Elo estimate.",
               "position_rows": str(args.out.relative_to(ROOT)) if args.out.is_relative_to(ROOT) else str(args.out)}
    summary_path = args.out.with_suffix("").with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
