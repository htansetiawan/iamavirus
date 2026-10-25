#!/usr/bin/env python3
"""Build a research v35 binary with only theta_full refitted; keep cheap prior frozen."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    ap.add_argument("fit_report", type=Path)
    ap.add_argument("output", type=Path, help="new directory; must not exist")
    a = ap.parse_args()
    src = a.source / "src/movemodel.c"
    if not src.is_file() or a.output.exists():
        raise SystemExit("invalid source or output already exists")
    weights = json.loads(a.fit_report.read_text())["models"]["full_refit"]["coefficients"]
    if len(weights) != 28:
        raise SystemExit("expected 28 fitted full-prior coefficients")
    shutil.copytree(a.source, a.output)
    model = a.output / "src/movemodel.c"
    text = model.read_text()
    pattern = r"(static const float theta_full\[MM_FEATURES\] = \{)([^}]+)(\};)"
    m = re.search(pattern, text)
    if not m:
        raise SystemExit("could not locate theta_full")
    if len(m.group(2).split(",")) != 28:
        raise SystemExit("source theta_full does not contain 28 entries")
    replacement = ", ".join(f"{float(x):.7f}f" for x in weights)
    text = text[:m.start()] + m.group(1) + replacement + m.group(3) + text[m.end():]
    model.write_text(text)
    proc = subprocess.run(["./build.sh"], cwd=a.output, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          check=False)
    if proc.returncode:
        raise SystemExit(proc.stdout)
    manifest = {
        "classification": "research-only v35 binary; chronological full prior refit, frozen cheap prior",
        "source_movemodel_sha256": sha(src),
        "candidate_movemodel_sha256": sha(model),
        "binary_sha256": sha(a.output / "mist"),
        "fit_report_sha256": sha(a.fit_report),
        "theta_full": weights,
        "cheap_prior": "unchanged from source archive",
    }
    (a.output / "full-refit-only-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({**manifest, "build": proc.stdout.strip(), "output": str(a.output)}, indent=2))


if __name__ == "__main__":
    main()
