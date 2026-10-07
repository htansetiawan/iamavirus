#!/usr/bin/env python3
"""Bounded CPU queue, build, off-parity and paired gates for bait admission.

Waits for the agreed CPU pair's real-clock matches. Node-limited jobs may share
the pair afterwards; their wall times are not treated as speed measurements.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from resume_experience_index import match_drivers

ASTRA = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--cores", default="2,3")
    args = parser.parse_args()
    cores = {int(n) for n in args.cores.split(",")}
    assert cores == {2, 3}, "only the agreed Astra CPU pair is supported"
    args.output.mkdir(parents=True, exist_ok=False)
    state_path = args.output / "state.json"
    state = dict(started_at=datetime.now(timezone.utc).isoformat(), pid=os.getpid(),
                 cores=sorted(cores), corpus_sha256=sha(args.corpus),
                 status="waiting_for_timed_matches")

    def update(status, **fields):
        state.update(status=status, at=datetime.now(timezone.utc).isoformat(), **fields)
        temporary = state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, indent=2) + "\n")
        temporary.replace(state_path)
        print(json.dumps(state), flush=True)

    def run(command, log):
        with log.open("w") as handle:
            subprocess.run(command, check=True, stdout=handle, stderr=subprocess.STDOUT)

    def compare(name, baseline, candidate, corpus, baseline_settings, candidate_settings):
        output = args.output / name
        command = [sys.executable, str(ASTRA / "tools/compare_replays.py"),
                   "--baseline", str(baseline), "--candidate", str(candidate),
                   "--corpus", str(corpus), "--model", str(ASTRA / "candidates/v12/model"),
                   "--output", str(output), "--workers", "2", "--nodes", "400000"]
        for setting in baseline_settings:
            command += ["--baseline-set", setting]
        for setting in candidate_settings:
            command += ["--candidate-set", setting]
        run(command, args.output / (name + ".log"))
        return json.loads((output / "summary.json").read_text())

    try:
        deadline = time.monotonic() + 120 * 60
        previous = None
        while blockers := match_drivers(cores):
            if blockers != previous:
                update("waiting_for_timed_matches", blockers=blockers)
                previous = blockers
            if time.monotonic() > deadline:
                raise TimeoutError("CPU pair still assigned to real-clock matches")
            time.sleep(30)
        os.sched_setaffinity(0, cores)
        update("building", blockers=[])
        run([sys.executable, str(ASTRA / "tools/build_bait_runtime.py"),
             "--output", str(args.build), "--resume-build"], args.output / "build-driver.log")
        binary = args.build / "benchmark"
        frozen = ASTRA / "analysis/release-v12/build/benchmark-candidate"
        assert sha(frozen) == "a4bca9a03bd604a7120cc2215ec1c672040c2a480f1b318f444664ad2d2911f1"
        update("off_parity", binary_sha256=sha(binary))
        parity = compare("off-parity", frozen, binary,
                         ASTRA / "analysis/release-v12/prospective-seats.txt", [], ["FOW_BAIT_ROWS=0"])
        if parity["paired"]["changed_moves"]:
            raise RuntimeError("default-off runtime differs from the frozen release")
        update("latest_ten_gate", parity_decisions=parity["results"]["baseline"]["decisions"])
        current = compare("latest-ten", binary, binary, args.corpus,
                          ["FOW_BAIT_ROWS=0"], ["FOW_BAIT_ROWS=1", "FOW_BAIT_PARTICLES=32"])
        # A new immediate fatal decision is enough to withhold this first arm.
        # It remains a negative experiment, not a reason to silently tune data.
        if current["paired"]["newly_fatal"]:
            update("withheld_new_fatal_decisions", paired=current["paired"])
            return
        if not current["paired"]["changed_moves"]:
            update("no_action_effect_latest_ten", paired=current["paired"])
            return
        update("historical_target_gate", paired=current["paired"])
        historic = compare("historical-targets", binary, binary,
                           ASTRA / "analysis/release-v12/historical-seats.txt",
                           ["FOW_BAIT_ROWS=0"], ["FOW_BAIT_ROWS=1", "FOW_BAIT_PARTICLES=32"])
        update("offline_gates_complete", latest_ten_paired=current["paired"],
               historical_paired=historic["paired"], release_ready=False,
               limitation="Offline forced histories only. No timing/strength claim; no arena upload.")
    except Exception as error:
        update("failed", error=f"{type(error).__name__}: {error}")
        raise


if __name__ == "__main__":
    main()
