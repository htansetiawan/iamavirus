#!/usr/bin/env python3
"""Build an isolated v35 research candidate with one fitted hidden-zone feature."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile


def patch_header(text: str) -> str:
    old = "    MM_CHECK_UNSEEN, MM_THREAT_UNSEEN,\n    MM_FEATURES"
    new = ("    MM_CHECK_UNSEEN, MM_THREAT_UNSEEN,\n"
           "    /* Hidden slider attacks the enemy king's adjacent zone without checking. */\n"
           "    MM_HIDDEN_SLIDER_ZONE,\n    MM_FEATURES")
    if text.count(old) != 1:
        raise ValueError("unexpected movemodel.h feature enum")
    return text.replace(old, new)


def patch_model(text: str, full_weight: float, cheap_weight: float) -> str:
    # Each production prior gets its own coefficient, fitted against the
    # features that prior actually computes.
    for name in ("theta_full", "theta_cheap"):
        pattern = rf"(static const float {name}\[MM_FEATURES\] = \{{)([^}}]+)(\}};)"
        match = re.search(pattern, text)
        if not match:
            raise ValueError(f"missing {name}")
        values = [x.strip() for x in match.group(2).split(",")]
        if len(values) != 28:
            raise ValueError(f"expected 28 base weights in {name}, got {len(values)}")
        weight = full_weight if name == "theta_full" else cheap_weight
        values.append(f"{weight:.9g}f")
        text = text[:match.start()] + match.group(1) + ", ".join(values) + match.group(3) + text[match.end():]

    old = "    {\n        /* what the victim sees after the move: a check or a threat on a\n"
    new = "    int destination_hidden = 0;\n    {\n        /* what the victim sees after the move: a check or a threat on a\n"
    if text.count(old) != 1:
        raise ValueError("unexpected observation feature block")
    text = text.replace(old, new)
    old = "    if (!full) return;\n    const int other = mover ^ 1;"
    new = ("    const int other = mover ^ 1;\n"
           "    if (!full) {\n"
           "        if (type == BISHOP || type == ROOK || type == QUEEN) {\n"
           "            Position cheap_q = *p; Undo cheap_u; make_move(&cheap_q, m, &cheap_u);\n"
           "            const int cheap_king = king_square(&cheap_q, other);\n"
           "            if (cheap_king >= 0) {\n"
           "                char cheap_seen[65]; observation(&cheap_q, other, cheap_seen);\n"
           "                if (cheap_seen[to] == '?') {\n"
           "                    bb_t cheap_hits = attacks_from(&cheap_q, to);\n"
           "                    out[MM_HIDDEN_SLIDER_ZONE] = (float)__builtin_popcountll(cheap_hits & attacks_from(&cheap_q, cheap_king)) / 8.0f;\n"
           "                }\n"
           "            }\n"
           "        }\n"
           "        return;\n"
           "    }")
    if text.count(old) != 1:
        raise ValueError("unexpected cheap-model early return")
    text = text.replace(old, new)
    old = "        observation(&q, other, seen);\n        if (seen[to] == '?') {"
    new = "        observation(&q, other, seen);\n        destination_hidden = seen[to] == '?';\n        if (destination_hidden) {"
    if text.count(old) != 1:
        raise ValueError("unexpected hidden destination check")
    text = text.replace(old, new)
    old = ("    out[MM_KING_ZONE] = (float)__builtin_popcountll(hits & attacks_from(&q, their_king)) / 8.0f;\n"
           "    const int moved = promo != NO_PIECE ? promo : type;")
    new = ("    out[MM_KING_ZONE] = (float)__builtin_popcountll(hits & attacks_from(&q, their_king)) / 8.0f;\n"
           "    const int moved = promo != NO_PIECE ? promo : type;\n"
           "    if (destination_hidden && (moved == BISHOP || moved == ROOK || moved == QUEEN) && out[MM_KING_ZONE] > 0)\n"
           "        out[MM_HIDDEN_SLIDER_ZONE] = out[MM_KING_ZONE];")
    if text.count(old) != 1:
        raise ValueError("unexpected king-zone feature block")
    return text.replace(old, new)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source_zip", type=Path)
    ap.add_argument("--full-fit-report", type=Path, required=True)
    ap.add_argument("--cheap-fit-report", type=Path, required=True)
    ap.add_argument("--dataset-sha256", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit(f"output already exists: {args.output}")
    full_report = json.loads(args.full_fit_report.read_text())
    cheap_report = json.loads(args.cheap_fit_report.read_text())
    if full_report.get("base_prior") != "full" or cheap_report.get("base_prior") != "cheap":
        raise SystemExit("fit reports must cover both runtime priors")
    if full_report.get("dataset_sha256") != args.dataset_sha256 or cheap_report.get("dataset_sha256") != args.dataset_sha256:
        raise SystemExit("dataset hash does not match both fit reports")
    full_weight = float(full_report["fitted_weight"])
    cheap_weight = float(cheap_report["fitted_weight"])

    args.output.mkdir(parents=True)
    archive_sha = hashlib.sha256(args.source_zip.read_bytes()).hexdigest()
    with zipfile.ZipFile(args.source_zip) as archive:
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"unsafe path in archive: {info.filename}")
            target = args.output.joinpath(*path.parts)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            data = archive.read(info.filename)
            if info.filename == "src/movemodel.h":
                data = patch_header(data.decode()).encode()
            elif info.filename == "src/movemodel.c":
                data = patch_model(data.decode(), full_weight, cheap_weight).encode()
            target.write_bytes(data)
    proc = subprocess.run(["bash", "build.sh"], cwd=args.output, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.returncode:
        raise SystemExit(proc.stdout)

    model = args.output / "src/movemodel.c"
    header = args.output / "src/movemodel.h"
    binary = args.output / "mist"
    manifest = {
        "classification": "research candidate; no strength result or arena release",
        "base_archive": str(args.source_zip), "base_archive_sha256": archive_sha,
        "base_arena_version": 35,
        "feature_index": 28,
        "feature": "hidden bishop/rook/queen destination whose attack map reaches a square adjacent to the enemy king, but does not necessarily check",
        "full_weight": full_weight,
        "cheap_weight": cheap_weight,
        "full_fit_report": str(args.full_fit_report),
        "full_fit_report_sha256": hashlib.sha256(args.full_fit_report.read_bytes()).hexdigest(),
        "cheap_fit_report": str(args.cheap_fit_report),
        "cheap_fit_report_sha256": hashlib.sha256(args.cheap_fit_report.read_bytes()).hexdigest(),
        "training_dataset_sha256": args.dataset_sha256,
        "candidate_header_sha256": hashlib.sha256(header.read_bytes()).hexdigest(),
        "candidate_model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
        "candidate_binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "build": proc.stdout.strip(),
        "cheap_prior": "feature-specific coefficient fitted on the actual cheap-feature projection",
    }
    (args.output / "research-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({**manifest, "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
