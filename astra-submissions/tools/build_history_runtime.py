#!/usr/bin/env python3
"""Build an isolated history-v2 research runtime from an immutable arena ZIP.

The two belief files are the only engine algorithm overlays. Search, neural
weights and rule sources come from the supplied archive. No archive is emitted.
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


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError(f"integration site changed: {before!r}")
    return text.replace(before, after, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=ASTRA / "candidates/history-v2")
    parser.add_argument("--control", action="store_true", help="Keep the archive belief unchanged")
    parser.add_argument("--ort", type=Path, default=Path.home() / "git/onnxruntime-sdk/onnxruntime-linux-x64-1.24.2")
    args = parser.parse_args()
    if sha(args.release) != args.expected_sha256:
        parser.error("archive SHA256 mismatch")
    output = args.output.resolve()
    if not output.is_relative_to(ASTRA):
        parser.error("research build must remain under astra-submissions")
    output.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(args.release) as archive:
        for info in archive.infolist():
            p = Path(info.filename)
            if p.is_absolute() or ".." in p.parts or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("unsafe archive member")
        archive.extractall(output)
    overlays = {}
    if not args.control:
        basis = json.loads((args.source / "basis.json").read_text())
        for name in ("belief.cc", "belief.h"):
            if sha(output / name) != basis["basis_files"][name]:
                raise ValueError(f"belief basis changed: {name}")
            (output / name).write_bytes((args.source / name).read_bytes())
            overlays[name] = sha(args.source / name)
        header = (output / "engine.h").read_text()
        header = replace_once(header, "  bool visibility_deductions = true;",
                              "  bool visibility_deductions = true;\n  int history_mode = 0;")
        (output / "engine.h").write_text(header)
        engine = (output / "engine.cc").read_text()
        engine = replace_once(engine,
            '  OverrideFlag("FOW_VISIBILITY_DEDUCTIONS", &options.visibility_deductions);',
            '  OverrideFlag("FOW_VISIBILITY_DEDUCTIONS", &options.visibility_deductions);\n'
            '  Override("FOW_HISTORY_MODE", &options.history_mode);')
        engine = replace_once(engine,
            "  belief_.set_visibility_deductions(options_.visibility_deductions);",
            "  belief_.set_visibility_deductions(options_.visibility_deductions);\n"
            "  if (options_.history_mode < 0 || options_.history_mode > 2) std::abort();\n"
            "  belief_.set_history_mode(options_.history_mode);")
        (output / "engine.cc").write_text(engine)
        (output / "history_test.cc").write_bytes((args.source / "history_test.cc").read_bytes())
    benchmark = ASTRA / "implementation/tools/benchmark_corpus.cc"
    text = re.sub(r'#include "\.\./([^"\n]+)"', r'#include "\1"', benchmark.read_text())
    (output / "benchmark.cc").write_text(text)
    probe = ASTRA / "tools/probe_belief.cc"
    (output / "probe.cc").write_bytes(probe.read_bytes())
    sources = ["engine", "belief", "search", "evaluation", "observation", "transposition",
               "regret", "position", "move", "bitboard", "neural_observation", "neural_inference",
               "opponent_model"]
    commands = []
    common = ["g++", "-O2", "-std=c++20", "-Wall", "-Wextra", "-Werror", "-pthread", "-mpopcnt",
              "-I" + str(output)]
    tasks = [("benchmark", ["benchmark", *sources], True),
             ("probe", ["probe", "belief", "opponent_model", "observation", "position", "move", "bitboard"], False)]
    if not args.control:
        tasks.append(("history_test", ["history_test", "belief", "opponent_model", "observation",
                                       "position", "move", "bitboard"], False))
    with (output / "build.log").open("w") as log:
        for name, files, neural in tasks:
            command = [*common]
            if neural:
                command += ["-DFOW_WITH_ONNX", "-I" + str(args.ort / "include")]
            command += [str(output / (s + ".cc")) for s in files]
            if neural:
                command += ["-L" + str(args.ort / "lib"), "-Wl,-rpath," + str(args.ort / "lib"), "-lonnxruntime"]
            command += ["-o", str(output / name)]
            commands.append(command)
            subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    manifest = {
        "basis_archive": str(args.release.resolve()), "basis_archive_sha256": sha(args.release),
        "control": args.control, "overlays": overlays,
        "benchmark_source_sha256": sha(benchmark), "probe_source_sha256": sha(probe),
        "files_sha256": {str(p.relative_to(output)): sha(p) for p in sorted(output.rglob("*"))
                          if p.is_file() and p.suffix in (".cc", ".h", ".onnx")},
        "binaries": {name: sha(output / name) for name, _, _ in tasks}, "commands": commands,
        "status": "research runtime only; not a submission archive",
        "modes": {"0": "control with own-move memory alignment repair",
                  "1": "exact observation and previous-mover survival",
                  "2": "mode 1 plus bounded history recovery"}}
    (output / "integration-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"output": str(output), "binaries": manifest["binaries"]}), flush=True)


if __name__ == "__main__":
    main()
