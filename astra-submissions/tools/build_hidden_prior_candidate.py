#!/usr/bin/env python3
"""Build a research-only v35 binary with fitted unseen-threat coefficients."""
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
    ap.add_argument("source", type=Path, help="clean extracted v35 source directory")
    ap.add_argument("output", type=Path, help="new output directory; must not exist")
    ap.add_argument("--check-weight", type=float, default=1.4030842617900832)
    ap.add_argument("--threat-weight", type=float, default=0.44055880750935399)
    a = ap.parse_args()
    if not (a.source / "src/movemodel.c").is_file() or not (a.source / "build.sh").is_file():
        raise SystemExit("source must be an extracted v35 tree with src/movemodel.c and build.sh")
    if a.output.exists():
        raise SystemExit(f"output already exists: {a.output}")
    shutil.copytree(a.source, a.output)
    model = a.output / "src/movemodel.c"
    text = model.read_text()
    pattern = r"(static const float theta_full\[MM_FEATURES\] = \{)([^}]+)(\};)"
    match = re.search(pattern, text)
    if not match:
        raise SystemExit("could not locate theta_full array")
    values = [x.strip() for x in match.group(2).split(",")]
    if len(values) != 28 or values[-2:] != ["0.0000f", "0.0000f"]:
        raise SystemExit(f"expected the original 28-feature v35 array with two zero weights; found {len(values)} entries and tail {values[-2:]}")
    values[-2] = f"{a.check_weight:.7f}f"
    values[-1] = f"{a.threat_weight:.7f}f"
    updated = match.group(1) + ", ".join(values) + match.group(3)
    model.write_text(text[:match.start()] + updated + text[match.end():])
    proc = subprocess.run(["./build.sh"], cwd=a.output, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if proc.returncode:
        raise SystemExit(proc.stdout)
    binary = a.output / "mist"
    manifest = {"classification": "research-only v35 binary; two fitted theta_full coefficients changed",
                "source_movemodel_sha256": sha(a.source / "src/movemodel.c"),
                "candidate_movemodel_sha256": sha(model),
                "binary_sha256": sha(binary),
                "MM_CHECK_UNSEEN": a.check_weight,
                "MM_THREAT_UNSEEN": a.threat_weight,
                "theta_cheap_changed": False}
    (a.output / "hidden-prior-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({**manifest, "build": proc.stdout.strip(), "output": str(a.output)}, indent=2))


if __name__ == "__main__": main()
