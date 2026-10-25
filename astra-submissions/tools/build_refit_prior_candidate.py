#!/usr/bin/env python3
"""Build v35 research binary with separately refitted full and cheap priors."""
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


def patch_array(text, name, weights, expected_len):
    pattern = rf"(static const float {name}\[MM_FEATURES\] = \{{)([^}}]+)(\}};)"
    m = re.search(pattern, text)
    if not m: raise ValueError(f"could not locate {name}")
    old = [x.strip() for x in m.group(2).split(",")]
    if len(old) != expected_len: raise ValueError(f"{name}: expected {expected_len} weights, got {len(old)}")
    if len(weights) > expected_len: raise ValueError(f"too many new weights for {name}")
    new = [f"{float(x):.7f}f" for x in weights]
    new.extend(["0.0000000f"] * (expected_len - len(new)))
    return text[:m.start()] + m.group(1) + ", ".join(new) + m.group(3) + text[m.end():]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    ap.add_argument("full_report", type=Path)
    ap.add_argument("cheap_report", type=Path)
    ap.add_argument("output", type=Path, help="new directory; must not exist")
    a = ap.parse_args()
    src = a.source / "src/movemodel.c"
    if not src.is_file() or a.output.exists(): raise SystemExit("invalid source or output already exists")
    full = json.loads(a.full_report.read_text())["models"]["full_refit"]["coefficients"]
    cheap = json.loads(a.cheap_report.read_text())["coefficients_18"]
    if len(full) != 28 or len(cheap) != 18: raise SystemExit("unexpected fitted coefficient dimensions")
    shutil.copytree(a.source, a.output)
    model = a.output / "src/movemodel.c"
    text = model.read_text()
    text = patch_array(text, "theta_full", full, 28)
    text = patch_array(text, "theta_cheap", cheap, 28)
    model.write_text(text)
    proc = subprocess.run(["./build.sh"], cwd=a.output, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if proc.returncode: raise SystemExit(proc.stdout)
    manifest = {"classification": "research-only v35 binary with separate chronological full and cheap prior refits",
                "source_movemodel_sha256": sha(src),
                "candidate_movemodel_sha256": sha(model),
                "binary_sha256": sha(a.output / "mist"),
                "full_report_sha256": sha(a.full_report),
                "cheap_report_sha256": sha(a.cheap_report),
                "theta_full": full, "theta_cheap_18": cheap,
                "cheap_tail": [0.0] * 10}
    (a.output / "refit-prior-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({**manifest, "build": proc.stdout.strip(), "output": str(a.output)}, indent=2))


if __name__ == "__main__": main()
