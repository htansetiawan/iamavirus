#!/usr/bin/env python3
"""Reproduce the v35 view-move en-passant audit without editing the archive."""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[3]
REPORT = Path(__file__).resolve().parent
DEFAULT_ARCHIVE = ROOT / "fable-submissions/iamavirus-v35-mist-c-v14.zip"

PATCH = REPORT / "belief-ep-observation.patch"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    ap.add_argument("--games", type=int, default=500)
    ap.add_argument("--seed", type=int, default=1332956945)
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="astra-ep-audit-") as td:
        work = Path(td)
        with zipfile.ZipFile(args.archive) as zf:
            for name in zf.namelist():
                if name.startswith("src/"):
                    zf.extract(name, work)
        subprocess.run(["patch", "-p1", "-i", str(PATCH)], cwd=work, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        exe = work / "ep-audit"
        cmd = ["cc", "-O2", "-std=c11", "-Wall", "-Wextra", "-Wpedantic", "-D_POSIX_C_SOURCE=199309L", "-pthread",
               "-I", str(work), str(REPORT / "audit_ep_view_moves.c"),
               str(work / "src/board.c"), str(work / "src/belief.c"),
               str(work / "src/movemodel.c"), str(work / "src/eval.c"), "-lm", "-o", str(exe)]
        subprocess.run(cmd, check=True)
        subprocess.run([str(exe), str(args.games), str(args.seed)], check=True)


if __name__ == "__main__":
    main()
