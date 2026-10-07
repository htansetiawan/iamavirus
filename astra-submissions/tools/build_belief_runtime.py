#!/usr/bin/env python3
"""Build an experimental belief gate on an immutable, newer release engine.

This creates a research staging tree, not a submission archive. Published
runtime bytes remain unchanged. The experimental belief currently supports
uniform and hand priors only; learned prior mode is explicitly rejected.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ASTRA = ROOT / "astra-submissions"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Expected exactly one pinned integration site: {old!r}")
    return text.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=ASTRA / "implementation")
    parser.add_argument("--ort", type=Path, default=Path.home() / "git/onnxruntime-sdk/onnxruntime-linux-x64-1.24.2")
    args = parser.parse_args()
    assert sha(args.release) == args.expected_sha256, "release archive changed"
    output = args.output.resolve()
    assert output.is_relative_to(ASTRA), "research tree must stay inside Astra"
    output.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(args.release) as archive:
        for name in archive.namelist():
            assert not Path(name).is_absolute() and ".." not in Path(name).parts
        archive.extractall(output)
    # Exact experimental replacements, independent of the live Fable worktree.
    overlays = ("belief.cc", "belief.h", "observation.cc", "observation.h")
    for name in overlays:
        (output / name).write_bytes((args.source / name).read_bytes())
    header = (output / "engine.h").read_text()
    header = replace_once(header, "  int opponent_prior = 1;", """  int opponent_prior = 1;
  bool preserve_capture_evidence = false;
  bool use_visibility_deductions = false;
  bool use_grouped_prediction = false;
  bool use_continuation_evidence = false;""")
    (output / "engine.h").write_text(header)
    engine = (output / "engine.cc").read_text()
    engine = replace_once(engine,
                          '  Override("FOW_EXPOSURE_STRIDE", &options.exposure_stride);',
                          '''  Override("FOW_EXPOSURE_STRIDE", &options.exposure_stride);
  OverrideFlag("FOW_CAPTURE_EVIDENCE", &options.preserve_capture_evidence);
  OverrideFlag("FOW_VISIBILITY_DEDUCTIONS", &options.use_visibility_deductions);
  OverrideFlag("FOW_GROUPED_PREDICTION", &options.use_grouped_prediction);
  OverrideFlag("FOW_CONTINUATION_EVIDENCE", &options.use_continuation_evidence);''')
    engine = replace_once(engine, "              options.opponent_prior),", """              options.opponent_prior == 1, options.preserve_capture_evidence,
              options.use_visibility_deductions, options.use_grouped_prediction,
              options.use_continuation_evidence),""")
    engine = replace_once(engine, "  (void)base_seconds;", """  (void)base_seconds;
  if (options.opponent_prior < 0 || options.opponent_prior > 1) {
    std::fprintf(stderr, "experimental belief gate supports only prior 0 or 1\\n");
    std::abort();
  }""")
    (output / "engine.cc").write_text(engine)
    harness = (args.source / "tools/benchmark_corpus.cc").read_text()
    # The standalone harness must include headers from this staging tree.
    harness = re.sub(r'#include "\.\./([^"\n]+)"', r'#include "\1"', harness)
    (output / "benchmark.cc").write_text(harness)
    sources = ["engine", "belief", "search", "evaluation", "observation", "transposition",
               "regret", "position", "move", "bitboard", "neural_observation", "neural_inference",
               "opponent_model"]
    command = ["g++", "-O2", "-std=c++20", "-Wall", "-Wextra", "-DNDEBUG", "-mpopcnt",
               "-DFOW_WITH_ONNX", "-I" + str(args.ort / "include"), "-I" + str(output),
               str(output / "benchmark.cc"), *[str(output / (s + ".cc")) for s in sources],
               "-L" + str(args.ort / "lib"), "-Wl,-rpath," + str(args.ort / "lib"),
               "-lonnxruntime", "-o", str(output / "benchmark")]
    with (output / "build.log").open("w") as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    files = {str(p.relative_to(output)): sha(p) for p in sorted(output.rglob("*"))
             if p.is_file() and p.suffix in (".cc", ".h", ".onnx")}
    manifest = dict(basis_archive=str(args.release), basis_archive_sha256=sha(args.release),
                    overlays={name: sha(args.source / name) for name in overlays},
                    files_sha256=files, binary_sha256=sha(output / "benchmark"),
                    compiler_command=command,
                    limitation="Research gate only; prior 0/1 supported; not a packaged release")
    (output / "integration-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"binary": str(output / "benchmark"), "sha256": manifest["binary_sha256"]}))


if __name__ == "__main__":
    main()
