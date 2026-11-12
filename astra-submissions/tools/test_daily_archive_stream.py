"""Functional archive checks, including actual mirror output and gzip EOF."""
from copy import deepcopy
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

from check_daily_archive_stream import check_archive

ROOT = Path(__file__).resolve().parents[2]


class ArchiveChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.raw, self.store = self.base / "raw", self.base / "store"
        (self.raw / "snapshots").mkdir(parents=True)
        self.lines = []
        def add(game):
            p = self.raw / "games" / game
            p.mkdir(parents=True, exist_ok=True)
            (p / "replay.json").write_text(json.dumps({"id": game}))
            self.lines.append(json.dumps({"id": game}) + "\n")
        add("a0000001"); add("a0000002")
        self.journal = self.raw / "accepted.jsonl"
        self.journal.write_text("".join(self.lines))
        command = [sys.executable, str(ROOT / "tools/mirror_raw.py"), "--raw", str(self.raw), "--store", str(self.store)]
        subprocess.run(command, check=True, capture_output=True)
        add("a0000003"); self.lines.append(self.lines[-1])
        self.journal.write_text("".join(self.lines))
        subprocess.run(command, check=True, capture_output=True)
        state = json.loads((self.store / "mirror-state.json").read_text())
        self.path = self.store / state["last_archive"]
        payload = (self.raw / "games/a0000003/replay.json").read_bytes()
        self.expected = {"a0000003": {"sha256": hashlib.sha256(payload).hexdigest(), "count": 2}}
        self.spec = {"path": str(self.path), "bytes": self.path.stat().st_size,
                     "max_compressed_bytes": 1024**2, "max_decoded_bytes": 1024**2,
                     "max_replay_bytes": 1024**2, "journal_prefix_bytes": self.journal.stat().st_size,
                     "journal_prefix_sha256": hashlib.sha256(self.journal.read_bytes()).hexdigest(),
                     "journal_lines": 4, "before_last_snapshot": "", "after_last_snapshot": ""}

    def test_actual_mirror_duplicate_occurrences(self):
        result = check_archive(self.spec, self.expected)
        self.assertEqual((result["replay_members"], result["unique_replays"], result["duplicate_replay_members"]), (2, 1, 1))
        self.assertEqual(result["journal_lines_beyond_cursor"], 0)

    def test_truncated_gzip_trailer_is_rejected_after_tar_eof(self):
        p = self.base / "truncated.gz"
        p.write_bytes(self.path.read_bytes()[:-8])
        spec = dict(self.spec, path=str(p), bytes=p.stat().st_size)
        with self.assertRaises((EOFError, gzip.BadGzipFile)):
            check_archive(spec, self.expected)

    def test_wrong_replay_content_hash(self):
        expected = deepcopy(self.expected); expected["a0000003"]["sha256"] = "0" * 64
        with self.assertRaises(AssertionError):
            check_archive(self.spec, expected)

    def test_missing_or_extra_replay_occurrences(self):
        for count in (1, 3):
            with self.subTest(count=count), self.assertRaises(AssertionError):
                check_archive(self.spec, {"a0000003": dict(self.expected["a0000003"], count=count)})

    def test_wrong_journal_prefix(self):
        with self.assertRaises(AssertionError):
            check_archive(dict(self.spec, journal_prefix_sha256="0" * 64), self.expected)

    def test_wrong_snapshot_frontier(self):
        with self.assertRaises(AssertionError):
            check_archive(dict(self.spec, after_last_snapshot="unrecorded"), self.expected)

    def test_compressed_budget(self):
        with self.assertRaises(AssertionError):
            check_archive(dict(self.spec, max_compressed_bytes=1), self.expected)

    def test_unsafe_member_path(self):
        p = self.base / "unsafe.gz"
        with tarfile.open(p, "w:gz") as archive:
            member = tarfile.TarInfo("../escape"); member.size = 1
            archive.addfile(member, io.BytesIO(b"x"))
        with self.assertRaises(AssertionError):
            check_archive(dict(self.spec, path=str(p), bytes=p.stat().st_size), self.expected)


if __name__ == "__main__":
    unittest.main()
