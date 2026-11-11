"""Stream-check one daily archive without extracting it to the filesystem."""
from collections import Counter
import gzip
import hashlib
from pathlib import Path, PurePosixPath
import tarfile

from audit_training_artifacts import Reader


def check_archive(spec, expected, receipt_stream=None):
    path = Path(spec["path"])
    before = path.stat()
    assert before.st_size == spec["bytes"]
    compressed_budget, decoded_budget = [0], [0]
    replay_counts, snapshots = Counter(), set()
    journal_members = journal_bytes = journal_lines = members = 0
    journal_hash = hashlib.sha256()
    journal_remaining = spec["journal_prefix_bytes"]
    with path.open("rb") as source:
        compressed = Reader(source, compressed_budget, spec["max_compressed_bytes"])
        with gzip.GzipFile(fileobj=compressed, mode="rb") as zipped:
            decoded = Reader(zipped, decoded_budget, spec["max_decoded_bytes"])
            with tarfile.open(fileobj=decoded, mode="r|") as archive:
                for member in archive:
                    members += 1
                    name = PurePosixPath(member.name)
                    assert not name.is_absolute() and ".." not in name.parts, member.name
                    parts = name.parts
                    if parts and parts[0] == "snapshots" and len(parts) >= 2:
                        snapshots.add(parts[1])
                    if parts and parts[0] == "games" and len(parts) >= 2:
                        assert parts[1] in expected, ("unexpected game", parts[1])
                    if len(parts) == 3 and parts[0] == "games" and parts[2] == "replay.json":
                        game = parts[1]
                        assert member.isfile() and member.size <= spec["max_replay_bytes"]
                        digest, size = hashlib.sha256(), 0
                        stream = archive.extractfile(member)
                        assert stream is not None
                        while True:
                            chunk = stream.read(1024**2)
                            if not chunk:
                                break
                            digest.update(chunk); size += len(chunk)
                        assert size == member.size
                        assert digest.hexdigest() == expected[game]["sha256"], game
                        replay_counts[game] += 1
                        if receipt_stream is not None:
                            import json
                            receipt_stream.write(json.dumps({"id": game, "bytes": size, "sha256": digest.hexdigest()}, separators=(",", ":")) + "\n")
                    elif parts == ("accepted.jsonl",):
                        journal_members += 1
                        assert journal_members == 1 and member.isfile()
                        assert member.size >= spec["journal_prefix_bytes"]
                        stream = archive.extractfile(member)
                        assert stream is not None
                        while True:
                            chunk = stream.read(1024**2)
                            if not chunk:
                                break
                            take = min(journal_remaining, len(chunk))
                            journal_hash.update(chunk[:take]); journal_remaining -= take
                            journal_bytes += len(chunk); journal_lines += chunk.count(b"\n")
            # Tar EOF can precede gzip EOF. Drain the latter so its trailer/CRC
            # is checked and every compressed byte enters the recorded hash.
            while decoded.read(1024**2):
                pass
        assert compressed.bytes == before.st_size
    after = path.stat()
    assert (before.st_dev, before.st_ino, before.st_size) == (after.st_dev, after.st_ino, after.st_size)
    assert replay_counts == Counter({game: row["count"] for game, row in expected.items()})
    assert journal_members == 1 and journal_remaining == 0
    assert journal_hash.hexdigest() == spec["journal_prefix_sha256"]
    assert journal_lines >= spec["journal_lines"]
    assert max([spec["before_last_snapshot"], *snapshots]) == spec["after_last_snapshot"]
    return {"archive_sha256": compressed.digest.hexdigest(), "compressed_bytes": compressed.bytes,
            "decoded_tar_bytes": decoded.bytes, "tar_members": members,
            "replay_members": sum(replay_counts.values()), "unique_replays": len(replay_counts),
            "duplicate_replay_members": sum(replay_counts.values()) - len(replay_counts),
            "archived_journal_bytes": journal_bytes, "archived_journal_lines": journal_lines,
            "verified_journal_prefix_bytes": spec["journal_prefix_bytes"],
            "verified_journal_prefix_sha256": journal_hash.hexdigest(),
            "journal_lines_beyond_cursor": journal_lines - spec["journal_lines"],
            "snapshot_entries": len(snapshots), "last_snapshot": spec["after_last_snapshot"],
            "archive_inode_and_size_unchanged": True, "all_expected_replay_occurrences_match": True}
