#!/usr/bin/env python3
"""Check six public replay EP actions against v35 and the proposed patch."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ARCHIVE = ROOT / "fable-submissions/iamavirus-v35-mist-c-v14.zip"
CASES = [
    ("0izeuvgd", 16, "d4e3"),
    ("6v4llaz2", 51, "g5h6"),
    ("8wef0oiw", 64, "g4h3"),
    ("7gylb8nl", 25, "g5f6"),
    ("jpo6pr7m", 24, "g4f3"),
    ("3cvzfvz5", 17, "c5d6"),
]
START_CASTLE = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)


def sq(text: str) -> int:
    return (ord(text[1]) - ord("1")) * 8 + ord(text[0]) - ord("a")


def castle_before(frames: list[dict], target_ply: int) -> int:
    rights = START_CASTLE
    for ply in range(1, target_ply):
        move = frames[ply]["move"]
        before = frames[ply - 1]["board"]
        if not move:
            raise ValueError(f"missing replay move at ply {ply}")
        src, dst = sq(move[:2]), sq(move[2:4])
        piece = before[src]
        if piece in "Kk":
            rights &= ~((1 << 0) | (1 << 7)) if piece == "K" else ~((1 << 56) | (1 << 63))
        if src in (0, 7, 56, 63):
            rights &= ~(1 << src)
        captured = before[dst]
        if captured in "Rr" and dst in (0, 7, 56, 63):
            rights &= ~(1 << dst)
    return rights


def compile_probe(source: Path, out: Path, archive_dir: Path) -> None:
    cmd = [
        "cc", "-O2", "-std=c11", "-D_POSIX_C_SOURCE=199309L", "-pthread",
        "-I", str(archive_dir), str(source),
        str(archive_dir / "src/board.c"), str(archive_dir / "src/belief.c"),
        str(archive_dir / "src/movemodel.c"), str(archive_dir / "src/eval.c"),
        "-lm", "-o", str(out),
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, default=ARCHIVE)
    ap.add_argument("--replay-root", type=Path, default=ROOT / "data/raw/games")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="astra-ep-replay-check-") as td:
        work = Path(td)
        with zipfile.ZipFile(args.archive) as zf:
            for name in zf.namelist():
                if name.startswith("src/"):
                    zf.extract(name, work)
        baseline = work / "view_moves_v35"
        compile_probe(HERE / "view_moves_probe.c", baseline, work)
        patch_root = work / "patch-root"
        (patch_root / "src").mkdir(parents=True)
        (patch_root / "src/belief.c").write_bytes((work / "src/belief.c").read_bytes())
        subprocess.run(
            ["patch", "-p1", "-i", str(HERE / "belief-ep-observation.patch")],
            cwd=patch_root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        (work / "src/belief.c").write_bytes((patch_root / "src/belief.c").read_bytes())
        patched = work / "view_moves_patched"
        compile_probe(HERE / "view_moves_probe.c", patched, work)

        rows = []
        for game, ply, expected in CASES:
            replay = json.loads((args.replay_root / game / "replay.json").read_text())
            frames = replay["frames"]
            if frames[ply]["move"] != expected:
                raise ValueError(f"{game}: expected frame {ply} move {expected}, got {frames[ply]['move']}")
            side = "white" if ply % 2 else "black"
            view = frames[ply - 1][side]
            castle = castle_before(frames, ply)
            args_probe = [view, side[0], hex(castle)]
            baseline_moves = subprocess.run([str(baseline), *args_probe], text=True, capture_output=True, check=True).stdout.splitlines()
            patched_moves = subprocess.run([str(patched), *args_probe], text=True, capture_output=True, check=True).stdout.splitlines()
            rows.append({
                "game": game, "ply": ply, "side": side, "move": expected,
                "baseline_available": expected in baseline_moves,
                "patched_available": expected in patched_moves,
                "castle_rooks": hex(castle),
            })
        result = {"cases": rows, "baseline_available": sum(r["baseline_available"] for r in rows),
                  "patched_available": sum(r["patched_available"] for r in rows)}
        print(json.dumps(result, indent=2))
        if result["patched_available"] != len(CASES):
            raise SystemExit("patch did not restore every recorded EP action")


if __name__ == "__main__":
    main()
