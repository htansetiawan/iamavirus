"""Read-only cache/receipt review; never repeats a timed reconstruction."""
import hashlib
import json
from pathlib import Path
import sqlite3
import struct
import zlib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "astra-submissions/analysis/episode-payload-cache-20261111"
PRIVATE = ROOT / "data/astra-spool/episode-payload-cache-20261111"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    plan, result, execution = (read(OUT / name) for name in ("plan.json", "result.json", "execution.json"))
    assert result["status"] == execution["status"] == "complete"
    assert execution["result_sha256"] == sha(OUT / "result.json")
    assert result["plan_sha256"] == execution["plan_sha256"] == sha(OUT / "plan.json")
    assert execution["seconds"] <= plan["wall_seconds"]
    for path, expected in plan["source_sha256"].items():
        assert sha(Path(path)) == expected
    for case in plan["cases"]:
        assert sha(Path(case["path"])) == case["sha256"]
    measurements = read(PRIVATE / "measurements.json")
    assert sha(PRIVATE / "measurements.json") == result["measurements_sha256"]
    assert measurements == [json.loads(line) for line in (PRIVATE / "measurements.jsonl").open()]
    assert [(r["round"], r["arm"]) for r in measurements] == [(i, arm) for i, arms in enumerate(plan["timing_order"]) for arm in arms]
    medians = {}
    for arm in ("baseline", "warm"):
        times = sorted(r["seconds"] for r in measurements if r["arm"] == arm)
        assert len(times) == 6 and all(t > 0 for t in times)
        medians[arm] = (times[2] + times[3]) / 2
    assert medians["baseline"] == result["baseline_median_seconds"]
    assert medians["warm"] == result["warm_median_seconds"]
    warm_ratio = medians["warm"] / medians["baseline"]
    cold_ratio = result["cold_seconds"] / medians["baseline"]
    assert warm_ratio == result["warm_ratio"] and cold_ratio == result["cold_ratio"]
    expected_gates = {"exact_output_and_error_checks": True,
                      "warm_median_ratio_max": warm_ratio <= plan["gates"]["warm_median_ratio_max"],
                      "cold_ratio_max": cold_ratio <= plan["gates"]["cold_ratio_max"]}
    assert result["gates"] == expected_gates and result["all_gates_pass"] == all(expected_gates.values())
    assert len(result["controls"]) == len(set(result["controls"])) == 12
    database = PRIVATE / "cache.sqlite"
    before = sha(database)
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
    assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    stored = {r[0]: r[1:] for r in connection.execute(
        "SELECT source_sha,compressed_sha,raw_sha,payload FROM episodes WHERE pipeline_sha=?", (plan["pipeline_sha256"],))}
    assert len(stored) == connection.execute("SELECT count(*) FROM episodes").fetchone()[0] == len(plan["cases"]) == 32
    digest = hashlib.sha256()
    episodes = decisions = 0
    for case in plan["cases"]:
        compressed_sha, raw_sha, blob = stored[case["sha256"]]
        assert hashlib.sha256(blob).hexdigest() == compressed_sha
        raw = zlib.decompress(blob)
        assert len(raw) <= 32 * 1024**2 and hashlib.sha256(raw).hexdigest() == raw_sha
        magic, *sizes = struct.unpack_from(">4sIIII", raw)
        assert magic == b"EPC1" and sum(sizes) + 20 == len(raw)
        offset, pieces = 20, []
        for size in sizes:
            pieces.append(raw[offset:offset + size]); offset += size
        replay = read(Path(case["path"]))
        for side in (0, 1):
            prefix, metadata_bytes = pieces[2 * side:2 * side + 2]
            metadata = json.loads(metadata_bytes)
            assert metadata["game_id"] == case["id"] and metadata["source_hash"] == case["sha256"] and metadata["split"] == ""
            metadata["split"] = "train"
            line = prefix + json.dumps(metadata, separators=(",", ":"), allow_nan=False).encode() + b"}\n"
            digest.update(line)
            obj = json.loads(line)
            actor, target = obj["actor"], obj["targets"]
            assert actor["side"] == side
            delivered = replay["frames"][:-1] if case["kind"] == "existing-all-thirty" else replay["frames"]
            assert actor["observations"] == [f["white" if side == 0 else "black"] for f in delivered]
            for i, event in enumerate(actor["decision_event_indices"]):
                assert actor["own_actions"][i] == replay["frames"][event + 1]["move"]
                assert target["boards"][i] == replay["frames"][event]["board"]
            if case["kind"] != "existing-all-thirty":
                assert not any(target["value_valid"]) and not any(target["policy_valid"])
            episodes += 1
            decisions += len(actor["decision_event_indices"])
    connection.close()
    assert sha(database) == before
    assert {r["output_sha256"] for r in measurements} == {digest.hexdigest()}
    assert not any(r["owner"] == "astra-episode-payload-cache-20261111" for r in read(ROOT / "chatroom/cores.json")["allocation"])
    # Conditional cost model, not a changed gate or full-pipeline projection.
    break_even = (cold_ratio - 1) / (cold_ratio - warm_ratio)
    review = {"at": datetime.now(timezone.utc).isoformat(), "status": "complete_review",
              "result_sha256": sha(OUT / "result.json"), "review_source_sha256": sha(Path(__file__)),
              "database_sha256": before, "database_read_only_unchanged": True,
              "records": len(stored), "episodes": episodes, "decisions": decisions,
              "all_twelve_output_digests_reproduced": True, "gate_verdict_preserved": expected_gates,
              "all_gates_pass": all(expected_gates.values()),
              "conditional_cost_model": {"formula": "h * warm_ratio + (1-h) * cold_ratio", "break_even_hit_fraction": break_even,
                  "limitations": "Assumes these small-probe per-case costs mix linearly; excludes raw-identity discovery, gzip/publication, disk scale, first-deployment economics and production scheduling. Does not change the failed cold gate or qualify integration."},
              "scope": "Read-only SQLite decoding/source alignment and original-measurement/gate arithmetic. No timed rerun, native rule replay, retraining, export or new candidate."}
    with (OUT / "review.json").open("x") as stream:
        stream.write(json.dumps(review, indent=2) + "\n")
    print(json.dumps(review, indent=2))


if __name__ == "__main__":
    main()
