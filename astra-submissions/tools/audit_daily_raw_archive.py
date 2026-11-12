"""Pin and verify the completed daily archive after the episode-index audit."""
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import signal
import sys
import time

import audit_training_artifacts as shared
from check_daily_archive_stream import check_archive

ROOT = Path(__file__).resolve().parents[2]
NAME = "daily-raw-archive-20261111"
OUT = ROOT / "astra-submissions/analysis" / NAME
PRIVATE = ROOT / "data/astra-spool" / NAME
EPISODES = ROOT / "astra-submissions/analysis/daily-episode-generation-20261111"
EPPRIVATE = ROOT / "data/astra-spool/daily-episode-generation-20261111"
BEFORE = ROOT / "data/astra-spool/daily-refresh-observation-20261111/archive-before.json"


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
    if not (EPISODES / "review.json").exists():
        print(json.dumps({"status": "waiting_for_episode_index_review"}))
        return 75
    ep_result, ep_review = read(EPISODES / "result.json"), read(EPISODES / "review.json")
    assert ep_result["status"] == "complete" and ep_review["status"] == "complete_index_review"
    assert ep_review["result_sha256"] == sha(EPISODES / "result.json")
    assert sha(EPPRIVATE / "episode-index.jsonl") == ep_result["index_sha256"]
    before = read(BEFORE)
    assert sha(ROOT / "tools/mirror_raw.py") == before["source_script_sha256"]
    functional = ROOT / "astra-submissions/analysis/daily-refresh-observation-20261111/archive-stream-functional-checks.json"
    tested = read(functional)
    assert tested["status"] == "passed" and tested["tests"] == 8
    for path, digest in tested["source_sha256"].items():
        assert sha(ROOT / path) == digest
    state_path = Path(before["archive_state_path"])
    after_bytes = state_path.read_bytes()
    after = json.loads(after_bytes)
    if after == before["state"]:
        print(json.dumps({"status": "waiting_for_archive_publication"}))
        return 75
    assert after["lines"] >= before["state"]["lines"]
    assert Path(after["last_archive"]).name == after["last_archive"]
    assert after["last_archive"].endswith(".tar.gz")
    path = state_path.parent / after["last_archive"]
    assert path.is_file() and not path.is_symlink()
    OUT.mkdir(exist_ok=False)
    PRIVATE.mkdir(exist_ok=False)
    (PRIVATE / "after-state.json").write_bytes(after_bytes)
    references = {}
    for line in (EPPRIVATE / "episode-index.jsonl").open():
        row = json.loads(line)
        if row["side"] == 0:
            assert row["id"] not in references
            references[row["id"]] = row["source_hash"]
    count = Counter()
    prefix = PRIVATE / "journal-prefix.jsonl"
    raw = ROOT / "data/raw"
    with (raw / ".writer.lock").open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_SH)
        with (raw / "accepted.jsonl").open("rb") as source, prefix.open("xb") as target:
            for n in range(after["lines"]):
                line = source.readline()
                assert line.endswith(b"\n"), "archive cursor exceeds a complete raw-journal prefix"
                target.write(line)
                if n >= before["state"]["lines"]:
                    count[json.loads(line)["id"]] += 1
                assert target.tell() <= 512 * 1024**2
        expected, reference_counts = {}, Counter()
        for game, occurrences in count.items():
            assert Path(game).name == game and game not in (".", "..")
            if game in references:
                digest, kind = references[game], "verified_episode_index"
            else:
                digest, kind = sha(raw / "games" / game / "replay.json"), "separate_raw_capture"
            expected[game] = {"count": occurrences, "sha256": digest, "reference": kind}
            reference_counts[kind] += 1
    save(PRIVATE / "expected-replays.json", expected)
    stat = path.stat()
    spec = {"path": str(path), "bytes": stat.st_size, "device": stat.st_dev, "inode": stat.st_ino,
            "max_compressed_bytes": 4 * 1024**3, "max_decoded_bytes": 32 * 1024**3,
            "max_replay_bytes": 64 * 1024**2, "journal_prefix_bytes": prefix.stat().st_size,
            "journal_prefix_sha256": sha(prefix), "journal_lines": after["lines"],
            "before_last_snapshot": before["state"].get("last_snapshot", ""),
            "after_last_snapshot": after.get("last_snapshot", "")}
    assert spec["bytes"] <= spec["max_compressed_bytes"]
    sources = [Path(__file__), ROOT / "astra-submissions/tools/check_daily_archive_stream.py", Path(shared.__file__),
               ROOT / "tools/mirror_raw.py", BEFORE, functional, EPISODES / "result.json", EPISODES / "review.json",
               EPPRIVATE / "episode-index.jsonl", PRIVATE / "after-state.json", prefix, PRIVATE / "expected-replays.json"]
    plan = {"at": now(), "core": 6, "wall_seconds": 900, "archive": spec,
            "before_cursor": before["state"]["lines"], "after_cursor": after["lines"],
            "suffix_journal_rows": sum(count.values()), "unique_expected_replays": len(expected),
            "replay_reference_counts": dict(reference_counts),
            "source_sha256": {str(p): sha(p) for p in sources},
            "scope": "One new daily archive: full gzip EOF/CRC, all compressed bytes, indexed journal prefix, exact replay multiplicities/hashes and snapshot frontier. No filesystem extraction, all-auxiliary-file comparison, old archive-chain certification, device-health, training or strength claim."}
    save(OUT / "plan.json", plan)
    print(json.dumps({"status": "prepared", "plan_sha256": sha(OUT / "plan.json"),
                      "suffix_rows": plan["suffix_journal_rows"], "unique_replays": len(expected),
                      "archive_bytes": spec["bytes"]}), flush=True)
    return 0


def run():
    plan = read(OUT / "plan.json")
    for path, expected in plan["source_sha256"].items():
        assert sha(Path(path)) == expected
    expected = read(PRIVATE / "expected-replays.json")
    state = {"at": now(), "status": "running", "plan_sha256": sha(OUT / "plan.json")}
    save(OUT / "execution.json", state)
    shared.NAME = NAME
    def timeout(*_):
        raise TimeoutError("original 900-second daily archive audit cap reached")
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(plan["wall_seconds"])
    started = time.monotonic()
    try:
        with shared.lease(), (PRIVATE / "replay-receipts.jsonl").open("x") as stream:
            checks = check_archive(plan["archive"], expected, stream)
        for path, digest in plan["source_sha256"].items():
            assert sha(Path(path)) == digest
        result = {"at": now(), "status": "complete", "plan_sha256": sha(OUT / "plan.json"), **checks,
                  "before_cursor": plan["before_cursor"], "after_cursor": plan["after_cursor"],
                  "replay_reference_counts": plan["replay_reference_counts"],
                  "receipt_sha256": sha(PRIVATE / "replay-receipts.jsonl"), "scope": plan["scope"]}
        save(OUT / "result.json", result)
        state.update(status="complete", result_sha256=sha(OUT / "result.json"))
        print(json.dumps(result, indent=2), flush=True)
    except BaseException as exc:
        state.update(status="failed", error=repr(exc))
        raise
    finally:
        signal.alarm(0)
        state.update(ended_at=now(), seconds=time.monotonic() - started)
        shared.update(OUT / "execution.json", state)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("prepare", "run")
    sys.exit(globals()[sys.argv[1]]())
