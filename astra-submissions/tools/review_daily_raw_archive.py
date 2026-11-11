"""Independent count/source reductions of the archive replay receipts."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "astra-submissions/analysis/daily-raw-archive-20261111"
PRIVATE = ROOT / "data/astra-spool/daily-raw-archive-20261111"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    plan, result, execution = (read(OUT / name) for name in ("plan.json", "result.json", "execution.json"))
    assert result["status"] == execution["status"] == "complete"
    assert result["plan_sha256"] == execution["plan_sha256"] == sha(OUT / "plan.json")
    assert execution["result_sha256"] == sha(OUT / "result.json")
    assert execution["seconds"] <= plan["wall_seconds"]
    for path, expected in plan["source_sha256"].items():
        assert sha(Path(path)) == expected
    expected = read(PRIVATE / "expected-replays.json")
    assert sha(PRIVATE / "replay-receipts.jsonl") == result["receipt_sha256"]
    counts, references = Counter(), Counter()
    for line in (PRIVATE / "replay-receipts.jsonl").open():
        row = json.loads(line)
        assert row["id"] in expected and row["sha256"] == expected[row["id"]]["sha256"]
        assert row["bytes"] >= 0
        counts[row["id"]] += 1
    assert counts == Counter({game: row["count"] for game, row in expected.items()})
    for row in expected.values():
        references[row["reference"]] += 1
    assert dict(references) == plan["replay_reference_counts"] == result["replay_reference_counts"]
    assert sum(counts.values()) == result["replay_members"] == plan["suffix_journal_rows"]
    assert len(counts) == result["unique_replays"] == plan["unique_expected_replays"]
    assert sum(counts.values()) - len(counts) == result["duplicate_replay_members"]
    assert plan["after_cursor"] - plan["before_cursor"] == sum(counts.values())
    spec = plan["archive"]
    assert result["verified_journal_prefix_bytes"] == spec["journal_prefix_bytes"]
    assert result["verified_journal_prefix_sha256"] == sha(PRIVATE / "journal-prefix.jsonl") == spec["journal_prefix_sha256"]
    assert result["archived_journal_lines"] - result["journal_lines_beyond_cursor"] == plan["after_cursor"]
    assert result["last_snapshot"] == spec["after_last_snapshot"]
    stat = Path(spec["path"]).stat()
    assert (stat.st_dev, stat.st_ino, stat.st_size) == (spec["device"], spec["inode"], spec["bytes"])
    assert stat.st_size == result["compressed_bytes"]
    assert not any(r["owner"] == "astra-daily-raw-archive-20261111" for r in read(ROOT / "chatroom/cores.json")["allocation"])
    review = {"at": datetime.now(timezone.utc).isoformat(), "status": "complete_receipt_review",
              "result_sha256": sha(OUT / "result.json"), "review_source_sha256": sha(Path(__file__)),
              "replay_members": sum(counts.values()), "unique_replays": len(counts),
              "before_cursor": plan["before_cursor"], "after_cursor": plan["after_cursor"],
              "replay_reference_counts": dict(references), "journal_lines_beyond_cursor": result["journal_lines_beyond_cursor"],
              "scope": "Independent replay-receipt/source multiplicities, journal prefix, state arithmetic and inode/size reconciliation. Original stream pass checks gzip CRC and archive content; this is not a second tar scan, full historical chain/device certificate or strength claim."}
    with (OUT / "review.json").open("x") as stream:
        stream.write(json.dumps(review, indent=2) + "\n")
    print(json.dumps(review, indent=2))


if __name__ == "__main__":
    main()
