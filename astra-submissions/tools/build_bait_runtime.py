#!/usr/bin/env python3
"""Stage/test a default-off hidden-bait admission variant of frozen Astra v12.

The experiment adds at most two root rows, never removes defensive rows, and
adds no payoff bonus. It does not assume the opponent will accept a sacrifice.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from build_belief_runtime import replace_once

ASTRA = Path(__file__).resolve().parents[1]
RELEASE_SHA = "a5f806d0039f514006f3af902767557ad35137d9d02e2779181d438eb5b47cf3"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


ADMISSION = r'''  ranked.resize(shortlist);
  for (const auto& row : ranked) trace->base_search_rows.push_back(row.move);
  if (options_.use_matrix_game && options_.bait_rows > 0) {
    double lowest_kept_risk = 1.0;
    for (const auto& row : ranked) {
      for (int i = 0; i < safe.size(); ++i) {
        if (row.move == safe[i]) lowest_kept_risk = std::min(lowest_kept_risk, safe_risk[i]);
      }
    }
    std::vector<astra::BaitCandidate> trials;
    for (int i = 0; i < safe.size(); ++i) {
      // An offensive admission cannot have higher estimated immediate king
      // risk than the safest move already retained. This is not an oracle.
      if (safe_risk[i] > lowest_kept_risk + 1e-12) continue;
      bool present = false;
      for (const auto& row : ranked) present |= row.move == safe[i];
      if (present) continue;
      auto bait = astra::DescribeBait(belief_.particles(), our_side_, en_passant,
                                     safe[i], options_.bait_particles);
      if (astra::HasBait(bait)) trials.push_back(bait);
    }
    const int admit = std::min<int>(options_.bait_rows, trials.size());
    std::partial_sort(trials.begin(), trials.begin() + admit, trials.end(), astra::BaitBefore);
    for (int i = 0; i < admit; ++i) {
      const Move move = trials[i].move;
      int score = 0;
      for (const auto& row : primary.root_values) if (row.move == move) score = row.score;
      ranked.push_back({move, score});
    }
    trace->bait_rows_added = admit;
    shortlist = static_cast<int>(ranked.size());
  }
  for (const auto& row : ranked) trace->search_rows.push_back(row.move);
  trace->shortlisted = shortlist;'''


AUDIT = r'''          if (verbose) {
            // Truth enters ONLY this diagnostic, after the actor has chosen.
            int available_bait = 0, base_covered = 0, final_covered = 0;
            const std::vector<Position> one_truth{truth};
            astra::BaitCandidate chosen_bait;
            for (Move alternative : true_legal) {
              const auto label = astra::DescribeBait(one_truth, seat.side,
                  truth.en_passant_square(), alternative, 1);
              if (alternative == choice) chosen_bait = label;
              if (!astra::HasBait(label)) continue;
              ++available_bait;
              for (Move row : trace.base_search_rows) base_covered += row == alternative;
              for (Move row : trace.search_rows) final_covered += row == alternative;
            }
            std::printf("BAIT_AUDIT {\"game\":\"%s\",\"side\":%d,\"ply\":%zu,"
                        "\"admitted_rows\":%d,\"true_bait_moves\":%d,\"base_covered\":%d,"
                        "\"final_covered\":%d,\"chosen_king_bait\":%.6f,"
                        "\"chosen_conditional_material_cp\":%.3f}\n",
                        seat.id.c_str(), seat.side, ply, trace.bait_rows_added,
                        available_bait, base_covered, final_covered,
                        chosen_bait.hidden_king_bait_fraction,
                        chosen_bait.mean_conditional_material_cp);
            // Public game IDs and UCI strings contain no JSON quoting characters.'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--resume-build", action="store_true")
    parser.add_argument("--ort", type=Path, default=Path.home() / "git/onnxruntime-sdk/onnxruntime-linux-x64-1.24.2")
    args = parser.parse_args()
    assert not (args.prepare_only and args.resume_build)
    output = args.output.resolve()
    assert output.is_relative_to(ASTRA)
    release = ASTRA / "iamavirus-v12-hybrid.zip"
    assert sha(release) == RELEASE_SHA
    manifest_path = output / "integration-manifest.json"
    if not args.resume_build:
        output.mkdir(parents=True, exist_ok=False)
        with zipfile.ZipFile(release) as archive:
            for name in archive.namelist():
                assert not Path(name).is_absolute() and ".." not in Path(name).parts
            archive.extractall(output)
        for name in ("tactical_labels.h", "bait_candidates.h", "test_tactical_labels.cc"):
            (output / name).write_bytes((ASTRA / "tools" / name).read_bytes())
        header = (output / "engine.h").read_text()
        header = replace_once(header, "  int exposure_stride = 4;", """  int exposure_stride = 4;
  int bait_rows = 0;  // Experimental/off: extra search rows, no payoff reward.
  int bait_particles = 32;""")
        header = replace_once(header, "  int shortlisted = 0;", """  int shortlisted = 0;
  int bait_rows_added = 0;
  std::vector<Move> base_search_rows;
  std::vector<Move> search_rows;""")
        (output / "engine.h").write_text(header)
        engine = (output / "engine.cc").read_text()
        engine = replace_once(engine, '#include "evaluation.h"', '#include "evaluation.h"\n#include "bait_candidates.h"')
        engine = replace_once(engine, '  Override("FOW_EXPOSURE_STRIDE", &options.exposure_stride);', '''  Override("FOW_EXPOSURE_STRIDE", &options.exposure_stride);
  Override("FOW_BAIT_ROWS", &options.bait_rows);
  Override("FOW_BAIT_PARTICLES", &options.bait_particles);
  options.bait_rows = std::clamp(options.bait_rows, 0, 2);
  options.bait_particles = std::clamp(options.bait_particles, 1, 128);''')
        engine = replace_once(engine, "  ranked.resize(shortlist);\n  trace->shortlisted = shortlist;", ADMISSION)
        (output / "engine.cc").write_text(engine)
        harness = (ASTRA / "analysis/release-v12/benchmark.cc").read_text()
        harness = replace_once(harness, '#include "engine.h"', '#include "engine.h"\n#include "bait_candidates.h"')
        harness = replace_once(harness, "          if (verbose) {\n            // Public game IDs and UCI strings contain no JSON quoting characters.", AUDIT)
        (output / "benchmark.cc").write_text(harness)
        manifest = dict(basis_archive_sha256=RELEASE_SHA, status="prepared",
                        builder_sha256=sha(Path(__file__)),
                        files_sha256={str(p.relative_to(output)): sha(p) for p in sorted(output.rglob("*"))
                                      if p.is_file() and p.suffix in (".cc", ".h", ".onnx")},
                        limitations=["Default off; research staging, not a numbered submission.",
                                     "Bait geometry is not a calibrated opponent capture probability.",
                                     "Immediate king risk uses the existing belief and may miss true attackers."])
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    else:
        manifest = json.loads(manifest_path.read_text())
        assert manifest["basis_archive_sha256"] == RELEASE_SHA
        assert manifest["status"] == "prepared"
        for name, digest in manifest["files_sha256"].items():
            assert sha(output / name) == digest, name
    if args.prepare_only:
        print(json.dumps(dict(status="prepared", path=str(output))))
        return
    common = ["g++", "-O2", "-std=c++20", "-Wall", "-Wextra", "-mpopcnt", "-I" + str(output)]
    rules = [str(output / (s + ".cc")) for s in ("position", "move", "bitboard", "observation")]
    with (output / "build.log").open("w") as log:
        subprocess.run(common + [str(output / "test_tactical_labels.cc"), *rules,
                                 "-o", str(output / "test_tactical_labels")], check=True, stdout=log, stderr=subprocess.STDOUT)
    tests = subprocess.run([str(output / "test_tactical_labels")], text=True, capture_output=True)
    (output / "test.log").write_text(tests.stdout + tests.stderr)
    tests.check_returncode()
    sources = ("engine", "belief", "search", "evaluation", "observation", "transposition", "regret",
               "position", "move", "bitboard", "neural_observation", "neural_inference", "opponent_model")
    command = common + ["-DNDEBUG", "-DFOW_WITH_ONNX", "-I" + str(args.ort / "include"),
                        str(output / "benchmark.cc"), *[str(output / (s + ".cc")) for s in sources],
                        "-L" + str(args.ort / "lib"), "-Wl,-rpath," + str(args.ort / "lib"),
                        "-lonnxruntime", "-o", str(output / "benchmark")]
    with (output / "build.log").open("a") as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    manifest.update(status="built", binary_sha256=sha(output / "benchmark"), compiler_command=command,
                    test_stdout=tests.stdout, test_binary_sha256=sha(output / "test_tactical_labels"))
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(dict(status="built", binary=str(output / "benchmark"), tests=tests.stdout)))


if __name__ == "__main__":
    main()
