"""Read-only journal evidence and cached no-op check under the new writer lock.

Does not compact, append, replace or download any replay/journal bytes. Creating
the advisory .writer.lock is the only write to the raw store. Receipts go here.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from learning.ingest import RawStore, ingest_replay, validate_replay


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    begin = time.monotonic()
    raw = ROOT / "data/raw"
    store = RawStore(raw)
    with store.writer():
        known = store.accepted_ids()
        counts = Counter()
        sha = hashlib.sha256()
        byte_count = 0
        last = None
        with store.accepted.open("rb") as handle:
            for line in handle:
                sha.update(line)
                byte_count += len(line)
                assert line.endswith(b"\n"), "preserve incomplete tail; no production test"
                if line.strip():
                    row = json.loads(line)
                    counts[row["id"]] += 1
                    last = row["id"]
        assert set(counts) == known
        assert store._index_offset == byte_count
        initial_hash = sha.hexdigest()
        directory = store.games / last
        paths = [directory / name for name in ("replay.json", "listing.json", "fetch_metadata.json")]
        assert all(path.is_file() for path in paths)
        sources = {p.name: digest(p) for p in paths}
        replay = json.loads(paths[0].read_text())
        states, problems = validate_replay(replay)
        assert not problems, problems
        result = ingest_replay(store, replay, json.loads(paths[1].read_text()),
                               json.loads(paths[2].read_text()), None)
        assert result.cached and not result
        assert sources == {p.name: digest(p) for p in paths}
        assert store.accepted.stat().st_size == byte_count
    # The owner may append after unlocking; certify the original prefix, not
    # the moving whole-file size. Never rewrite it to make a hash agree.
    remaining = byte_count
    sha = hashlib.sha256()
    with store.accepted.open("rb") as handle:
        while remaining:
            chunk = handle.read(min(1024 * 1024, remaining))
            assert chunk, "journal unexpectedly shortened"
            sha.update(chunk)
            remaining -= len(chunk)
    assert sha.hexdigest() == initial_hash
    receipt = {
        "at": datetime.now(timezone.utc).isoformat(), "raw": str(raw.resolve()),
        "journal_prefix_bytes": byte_count, "journal_prefix_sha256": initial_hash,
        "rows": sum(counts.values()), "unique_ids": len(counts),
        "duplicate_extra_rows": sum(n - 1 for n in counts.values()),
        "duplicated_ids": {k: n for k, n in counts.items() if n > 1},
        "prefix_unchanged": True, "journal_compacted": False,
        "cached_noop": {"id": last, "frames_verified": len(states),
                        "source_sha256_unchanged": sources},
        "wall_seconds": time.monotonic() - begin,
        "limitations": ["Existing duplicate rows deliberately retained.",
                        "One cached no-op is not a new live ingestion or strength test.",
                        "fcntl advisory locks require all future writers to use the convention.",
                        "The game transaction is serialized, not a crash-atomic multi-file filesystem transaction."]}
    output = Path(__file__).with_name("live-audit.json")
    output.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: v for k, v in receipt.items() if k != "duplicated_ids"}, indent=2))


if __name__ == "__main__":
    main()
