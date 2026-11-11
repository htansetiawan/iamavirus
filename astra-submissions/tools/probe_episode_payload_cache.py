"""Frozen small-scale episode-cache parity and reconstruction-cost probe."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import statistics
import sys
import time
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import audit_training_artifacts as shared
from learning import _native, histories, ingest

NAME = "episode-payload-cache-20261111"
OUT = ROOT / "astra-submissions/analysis" / NAME
PRIVATE = ROOT / "data/astra-spool" / NAME
CORE_SOURCE = ROOT / "astra-submissions/experiments" / NAME / "cache.py"
VALIDATOR = ROOT / "astra-submissions/experiments/last-only-pilot-20261110/build/native-validator.so"


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, obj):
    with path.open("x") as stream:
        stream.write(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def prepare():
    OUT.mkdir(exist_ok=False)
    PRIVATE.mkdir(exist_ok=False)
    previous = ROOT / "astra-submissions/analysis/daily-own-cohort-20261111/plan.json"
    prior = read(previous)
    cases = []
    for game in prior["game_ids"]:
        p = ROOT / "data/astra-spool/daily-own-cohort-20261111/games" / game / "replay.json"
        assert sha(p) == prior["dependencies"][str(p.relative_to(ROOT))]
        cases.append({"id": game, "path": str(p), "sha256": sha(p), "kind": "existing-all-thirty"})
    journal = ROOT / "data/astra-spool/training-artifact-readiness-20261111/journal.jsonl"
    technical = []
    with journal.open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("termination") not in (None, "normal") and row.get("plies", 0) >= 4:
                technical.append(row)
                if len(technical) == 2:
                    break
    assert [r["id"] for r in technical] == ["stoupr86", "tg8dgddl"]
    for row in technical:
        source = ROOT / "data/raw/games" / row["id"] / "replay.json"
        payload = source.read_bytes()
        p = PRIVATE / (row["id"] + ".json")
        p.write_bytes(payload)
        replay = json.loads(payload)
        assert replay["id"] == row["id"] and len(replay["frames"]) == row["plies"] + 1
        assert replay["reason"] == row["reason"] and replay["result"] == row["result"]
        cases.append({"id": row["id"], "path": str(p), "sha256": sha(p), "kind": row["termination"]})
    assert len(cases) == len({r["id"] for r in cases}) == 32
    paths = [ROOT / "learning" / (name + ".py") for name in
             ("dataset", "features", "histories", "ingest", "rules", "_native", "labels", "action_codec")]
    paths += [VALIDATOR, CORE_SOURCE]
    pipeline = {"schema": "EPC1", "python": sys.version, "zlib": zlib.ZLIB_VERSION,
                "files": {str(p.relative_to(ROOT)): sha(p) for p in paths}}
    fingerprint = hashlib.sha256(json.dumps(pipeline, sort_keys=True).encode()).hexdigest()
    dependencies = [Path(__file__), ROOT / "astra-submissions/specs/episode-payload-cache.md",
                    Path(shared.__file__), previous, journal, *paths]
    plan = {"at": now(), "core": 6, "wall_seconds": 300, "max_database_bytes": 128 * 1024**2,
            "cases": cases, "pipeline": pipeline, "pipeline_sha256": fingerprint,
            "source_sha256": {str(p): sha(p) for p in dependencies},
            "timing_order": [["baseline", "warm"] if i % 2 == 0 else ["warm", "baseline"] for i in range(6)],
            "gates": {"exact_output_and_error_checks": True, "warm_median_ratio_max": 0.5, "cold_ratio_max": 2.0},
            "antecedents": ["273 move cache and complete generation publication", "learning.feature_cache after episode export", "314 immutable episode/journal integrity", "336 packed replay cache", "394 fold-lineage limits", "395 actor-input checks"],
            "scope": "Isolated canonical-payload cache. Already pinned in-memory inputs; no mutable-raw freshness assertion, full gzip/publication cost, production integration, model fit, engine, game or strength claim."}
    save(OUT / "plan.json", plan)
    print(json.dumps({"plan_sha256": sha(OUT / "plan.json"), "cases": len(cases), "pipeline_sha256": fingerprint}), flush=True)


def run():
    plan = read(OUT / "plan.json")
    for path, digest in plan["source_sha256"].items():
        assert sha(Path(path)) == digest
    for case in plan["cases"]:
        assert sha(Path(case["path"])) == case["sha256"]
    spec = importlib.util.spec_from_file_location("episode_payload_cache_core", CORE_SOURCE)
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    assert _native._library is None
    _native.ensure_built = lambda verbose=True: VALIDATOR
    shared.NAME = NAME
    state = {"at": now(), "status": "running", "plan_sha256": sha(OUT / "plan.json")}
    save(OUT / "execution.json", state)
    def timeout(*_):
        raise TimeoutError("original 300-second payload-cache probe cap reached")
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(plan["wall_seconds"])
    started = time.monotonic()
    payloads = {r["id"]: Path(r["path"]).read_bytes() for r in plan["cases"]}
    pipeline = plan["pipeline_sha256"]
    calls, measurements, controls = Counter(), [], []
    cache = None

    def build(case, phase):
        calls[phase] += 1
        payload = payloads[case["id"]]
        assert hashlib.sha256(payload).hexdigest() == case["sha256"]
        replay = json.loads(payload)
        states, problems = ingest.validate_replay(replay)
        assert not problems, (case["id"], problems)
        return [histories.build_episode(replay, states, side, ingest.RULES_FINGERPRINT, case["sha256"]) for side in (0, 1)]

    def canonical(episodes, split):
        lines = []
        for ep in episodes:
            ep.metadata.split = split
            lines.append(json.dumps(ep.to_dict(), separators=(",", ":"), allow_nan=False).encode() + b"\n")
        return tuple(lines)

    def never():
        raise AssertionError("cache hit unexpectedly reconstructed an episode")

    def expect_error(name, error, action):
        try:
            action()
        except error:
            controls.append(name)
        else:
            raise AssertionError("control did not reject: " + name)

    def damage(name, update):
        cache.connection.execute("SAVEPOINT damage")
        try:
            update()
            first = plan["cases"][0]
            expect_error(name, core.CorruptEntry, lambda: cache.get(pipeline, first["sha256"]))
        finally:
            cache.connection.execute("ROLLBACK TO damage")
            cache.connection.execute("RELEASE damage")

    try:
        with shared.lease():
            expected = {}
            for case in plan["cases"]:
                episodes = build(case, "reference")
                if case["kind"] != "existing-all-thirty":
                    assert all(not any(ep.targets.value_valid) and not any(ep.targets.policy_valid) for ep in episodes)
                expected[case["id"]] = {s: canonical(episodes, s) for s in ("train", "validation", "test")}
            cache = core.Cache(PRIVATE / "cache.sqlite")
            cold_start = time.perf_counter()
            for case in plan["cases"]:
                lines, hit = cache.render(pipeline, case["sha256"], "train", lambda c=case: build(c, "cold"))
                assert not hit and lines == expected[case["id"]]["train"]
            cold_seconds = time.perf_counter() - cold_start
            for case in plan["cases"]:
                for split in ("train", "validation", "test"):
                    lines, hit = cache.render(pipeline, case["sha256"], split, never)
                    assert hit and lines == expected[case["id"]][split]
            for round_index, order in enumerate(plan["timing_order"]):
                for arm in order:
                    began = time.perf_counter()
                    digest = hashlib.sha256()
                    for case in plan["cases"]:
                        if arm == "baseline":
                            lines = canonical(build(case, "baseline"), "train")
                        else:
                            lines, hit = cache.render(pipeline, case["sha256"], "train", never)
                            assert hit
                        assert lines == expected[case["id"]]["train"]
                        for line in lines:
                            digest.update(line)
                    measurements.append({"round": round_index, "arm": arm, "seconds": time.perf_counter() - began,
                                         "output_sha256": digest.hexdigest()})
                    with (PRIVATE / "measurements.jsonl").open("a") as stream:
                        stream.write(json.dumps(measurements[-1]) + "\n")
                    print(json.dumps(measurements[-1]), flush=True)
            first = plan["cases"][0]
            source = first["sha256"]
            other = hashlib.sha256(b"changed-pipeline-or-source").hexdigest()
            assert cache.get(other, source) is None and cache.get(pipeline, other) is None
            controls.extend(("pipeline-version-miss", "source-content-miss"))
            expect_error("malformed-key", ValueError, lambda: cache.get("bad", source))
            expect_error("unknown-fold", ValueError, lambda: cache.render(pipeline, source, "other", never))
            expect_error("episode-source-mismatch", ValueError, lambda: core.pack(build(first, "control"), other))
            count = cache.connection.execute("SELECT count(*) FROM episodes").fetchone()[0]
            def interrupted():
                raise RuntimeError("injected builder interruption")
            expect_error("interrupted-builder", RuntimeError, lambda: cache.render(other, source, "train", interrupted))
            cache.connection.execute("PRAGMA query_only=ON")
            try:
                expect_error("failed-write", core.sqlite3.OperationalError,
                             lambda: cache.render(other, source, "train", lambda: build(first, "control")))
            finally:
                cache.connection.execute("PRAGMA query_only=OFF")
            assert cache.connection.execute("SELECT count(*) FROM episodes").fetchone()[0] == count == 32
            where = " WHERE pipeline_sha=? AND source_sha=?"
            damage("compressed-corruption", lambda: cache.connection.execute(
                "UPDATE episodes SET payload=?" + where, (b"bad", pipeline, source)))
            damage("raw-hash-corruption", lambda: cache.connection.execute(
                "UPDATE episodes SET raw_sha=?" + where, ("0" * 64, pipeline, source)))
            row = cache.connection.execute("SELECT payload FROM episodes" + where, (pipeline, source)).fetchone()
            original = zlib.decompress(row[0])
            def replace_payload(raw):
                blob = zlib.compress(raw, 1)
                cache.connection.execute("UPDATE episodes SET compressed_sha=?,raw_sha=?,payload=?" + where,
                    (hashlib.sha256(blob).hexdigest(), hashlib.sha256(raw).hexdigest(), blob, pipeline, source))
            damage("framing-corruption", lambda: replace_payload(b"NOPE" + original[4:]))
            damage("metadata-source-substitution", lambda: replace_payload(original.replace(source.encode(), other.encode())))
            damage("decompression-cap", lambda: replace_payload(b"0" * (core.MAX_RAW + 1)))
            assert len(controls) == 12
            for case in plan["cases"]:
                lines, hit = cache.render(pipeline, case["sha256"], "train", never)
                assert hit and lines == expected[case["id"]]["train"]
            cache.close()
            cache = None
        assert (PRIVATE / "cache.sqlite").stat().st_size <= plan["max_database_bytes"]
        for path, digest in plan["source_sha256"].items():
            assert sha(Path(path)) == digest
        for case in plan["cases"]:
            assert sha(Path(case["path"])) == case["sha256"]
        assert calls["reference"] == calls["cold"] == 32 and calls["baseline"] == 192
        assert len({r["output_sha256"] for r in measurements}) == 1
        save(PRIVATE / "measurements.json", measurements)
        baseline = statistics.median(r["seconds"] for r in measurements if r["arm"] == "baseline")
        warm = statistics.median(r["seconds"] for r in measurements if r["arm"] == "warm")
        gates = {"exact_output_and_error_checks": True, "warm_median_ratio_max": warm / baseline <= 0.5,
                 "cold_ratio_max": cold_seconds / baseline <= 2.0}
        result = {"at": now(), "status": "complete", "plan_sha256": sha(OUT / "plan.json"), "cases": 32,
                  "color_fold_line_comparisons": 32 * 2 * 3, "controls": controls, "builder_calls": dict(calls),
                  "cold_seconds": cold_seconds, "baseline_median_seconds": baseline, "warm_median_seconds": warm,
                  "warm_ratio": warm / baseline, "cold_ratio": cold_seconds / baseline, "gates": gates,
                  "all_gates_pass": all(gates.values()), "measurements_sha256": sha(PRIVATE / "measurements.json"),
                  "database_bytes": (PRIVATE / "cache.sqlite").stat().st_size, "scope": plan["scope"]}
        save(OUT / "result.json", result)
        state.update(status="complete", result_sha256=sha(OUT / "result.json"))
        print(json.dumps(result, indent=2), flush=True)
    except BaseException as exc:
        state.update(status="failed", error=repr(exc))
        raise
    finally:
        if cache is not None:
            cache.close()
        signal.alarm(0)
        state.update(ended_at=now(), seconds=time.monotonic() - started)
        shared.update(OUT / "execution.json", state)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("prepare", "run")
    globals()[sys.argv[1]]()
