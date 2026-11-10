"""Offline regressions for concurrent raw writers; no production data/network.

Run: .venv/bin/python astra-submissions/tests/test_ingest_concurrency.py -v
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning import api_client, ingest
from learning.histories import replay_from_moves

MOVES = ["e2e4", "e7e5", "g1f3", "b8c6"]


def replay(game):
    return replay_from_moves(game, MOVES, "1-0", "Opponent crashed", "White", "Black")


def fetch(game):
    return {"replay": {"url": f"fixture:{game}", "sha256": "original-network-bytes",
                       "fetched_at": "2026-11-10T00:00:00Z", "status": 200, "attempts": 1}}


def pipeline_worker(raw, kind, lane, barrier, first_saved, output):
    """Force stale snapshots in every caller, then enter the real writer API."""
    store = ingest.RawStore(Path(raw))
    store.accepted_ids()
    ids = ["same0000", f"{lane}only000", "same0001", f"{lane}only001", "same0000"]
    real_ingest = ingest.ingest_replay
    first = True

    def synchronized(*args, **kwargs):
        nonlocal first
        if first:
            barrier.wait(timeout=30)
            if kind == "api":
                # Guarantee the API's initial snapshot is stale by its first
                # append attempt, rather than relying on scheduler luck.
                assert first_saved.wait(timeout=30)
            first = False
        return real_ingest(*args, **kwargs)

    if kind == "api":
        class FakeClient:
            requests_made = 0

            def __init__(self, **kwargs):
                pass

            def leaderboard(self):
                return {"players": []}, api_client.FetchRecord("fixture:lb", "now", "hash", 200, 1)

            def iter_games(self, params, limit):
                for game in ids:
                    yield {"id": game, "result": "1-0", "plies": len(MOVES)}, None

            def replay(self, game):
                data = replay(game)
                record = api_client.FetchRecord(f"fixture:{game}", "now", "network", 200, 1)
                return data, record, False

        with patch.object(ingest.api_client, "ApiClient", FakeClient), \
                patch.object(ingest, "ingest_replay", synchronized):
            counts = ingest.ingest_from_api(Path(raw), None, None, None, None, False, 1.2)
    elif kind == "corpus":
        corpus = Path(raw) / "input.txt"
        corpus.write_text("".join(f"{game} w 1-0 Opponent_crashed Black {' '.join(MOVES)}\n" for game in ids))
        with patch.object(ingest, "ingest_replay", synchronized):
            counts = ingest.ingest_from_corpus(Path(raw), corpus)
    else:
        # Custom callers that save and append separately are safe too, even
        # with a stale caller-side known set. Their explicit transaction also
        # keeps the cross-file save/validate/append sequence together.
        barrier.wait(timeout=30)
        counts = {"accepted": 0}
        for game in ids:
            data = replay(game)
            with store.writer() if kind == "custom" else nullcontext():
                store.save_game(data, {"id": game}, fetch(game), None)
                assert not ingest.validate_replay(data)[1]
                counts["accepted"] += store.record_accepted(data)
            first_saved.set()
    output.put((kind, counts))


def atomic_worker(folder, lane, barrier):
    root = Path(folder)
    barrier.wait(timeout=30)
    for step in range(30):
        payload = json.dumps({"lane": lane, "step": step, "payload": str(lane) * 100000}).encode()
        api_client.atomic_write(root / "shared.json", payload)
        api_client.atomic_write(root / f"lane{lane}.json", payload)


class IngestConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="astra-ingest-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def run_processes(self, processes):
        for proc in processes:
            proc.start()
        try:
            deadline = time.monotonic() + 60
            for proc in processes:
                proc.join(max(0, deadline - time.monotonic()))
                self.assertEqual(proc.exitcode, 0, f"worker {proc.pid} failed or timed out")
        finally:
            for proc in processes:
                if proc.is_alive():
                    proc.terminate()
                    proc.join(5)

    def test_overlapping_api_corpus_and_custom_writers(self):
        context = mp.get_context("spawn")
        barrier, first_saved, output = context.Barrier(4), context.Event(), context.Queue()
        workers = [context.Process(target=pipeline_worker,
                   args=(str(self.root), kind, lane, barrier, first_saved, output))
                   for lane, kind in enumerate(("api", "corpus", "custom", "custom-bare"))]
        self.run_processes(workers)
        counts = dict(output.get(timeout=3) for _ in workers)
        rows = [json.loads(line) for line in (self.root / "accepted.jsonl").read_text().splitlines()]
        expected = {"same0000", "same0001"} | {f"{lane}only00{i}" for lane in range(4) for i in range(2)}
        self.assertEqual({row["id"] for row in rows}, expected)
        self.assertEqual(len(rows), len(expected))
        self.assertEqual(sum(c["accepted"] for c in counts.values()), len(expected))
        self.assertGreaterEqual(counts["api"]["already_accepted"], 1)
        store = ingest.RawStore(self.root)
        self.assertEqual({r["id"] for r in store.accepted_replays()}, expected)
        for game in expected:
            directory = store.games / game
            data = json.loads((directory / "replay.json").read_text())
            self.assertFalse(ingest.validate_replay(data)[1])
            metadata = json.loads((directory / "fetch_metadata.json").read_text())
            self.assertEqual(metadata["replay"]["sha256"],
                             hashlib.sha256((directory / "replay.json").read_bytes()).hexdigest())
            self.assertTrue((directory / "listing.json").exists() or game.startswith("1only"))
        self.assertFalse(list(self.root.rglob("*.tmp")))

    def test_api_reuses_hash_of_stored_bytes_and_preserves_source_digest(self):
        store = ingest.RawStore(self.root)
        data = replay("cache000")
        source = fetch(data["id"])
        ingest.ingest_replay(store, data, None, source, None)
        client = api_client.ApiClient(cache_dir=self.root)
        with patch.object(client, "get_bytes", side_effect=AssertionError("unexpected network request")):
            cached, record, hit = client.replay(data["id"])
        self.assertTrue(hit)
        self.assertEqual(cached, data)
        self.assertEqual(record.attempts, 0)
        metadata = json.loads((store.games / data["id"] / "fetch_metadata.json").read_text())
        self.assertEqual(metadata["replay"]["source_bytes_sha256"], "original-network-bytes")
        self.assertEqual(source["replay"]["sha256"], "original-network-bytes")

    def test_atomic_writers_same_and_disjoint_files(self):
        context = mp.get_context("spawn")
        barrier = context.Barrier(4)
        self.run_processes([context.Process(target=atomic_worker, args=(str(self.root), lane, barrier))
                            for lane in range(4)])
        for path in self.root.glob("*.json"):
            data = json.loads(path.read_text())
            self.assertEqual(data["payload"], str(data["lane"]) * 100000)
        self.assertEqual(len(list(self.root.glob("*.json"))), 5)
        self.assertFalse(list(self.root.glob("*.tmp")))

    def test_atomic_failure_keeps_previous_file_and_cleans_own_temp(self):
        path = self.root / "old.json"
        api_client.atomic_write(path, b'"original"')
        with patch.object(api_client.os, "replace", side_effect=OSError("injected rename failure")):
            with self.assertRaisesRegex(OSError, "injected"):
                api_client.atomic_write(path, b'"replacement"')
        self.assertEqual(path.read_bytes(), b'"original"')
        self.assertEqual(list(self.root.iterdir()), [path])

    def test_old_duplicates_remain_but_readers_and_writers_deduplicate(self):
        store = ingest.RawStore(self.root)
        data = replay("dupe0000")
        self.assertFalse(ingest.ingest_replay(store, data, None, fetch(data["id"]), None))
        original = store.accepted.read_bytes()
        store.accepted.write_bytes(original * 2)
        before = store.accepted.read_bytes()
        self.assertEqual(len(list(store.accepted_replays())), 1)
        self.assertFalse(store.record_accepted(data))
        self.assertTrue(ingest.ingest_replay(store, data, None, fetch(data["id"]), None).cached)
        self.assertEqual(store.accepted.read_bytes(), before)

    def test_missing_sources_recovered_without_new_accepted_row(self):
        store = ingest.RawStore(self.root)
        data = replay("recover0")
        listing = {"id": data["id"]}
        ingest.ingest_replay(store, data, listing, fetch(data["id"]), None)
        journal = store.accepted.read_bytes()
        directory = store.games / data["id"]
        original = {p.name: p.read_bytes() for p in directory.iterdir()}
        for filename in ("replay.json", "fetch_metadata.json", "listing.json"):
            (directory / filename).unlink()
            result = ingest.ingest_replay(store, data, listing, fetch(data["id"]), None)
            self.assertTrue(result.recovered)
            self.assertFalse(result)
            self.assertEqual(store.accepted.read_bytes(), journal)
            self.assertEqual({p.name: p.read_bytes() for p in directory.iterdir()}, original)
        # A later fetch cannot replace an already accepted source/provenance.
        other = replay(data["id"])
        other["white"] = "later response"
        self.assertTrue(ingest.ingest_replay(store, other, listing, {}, None).cached)
        self.assertEqual({p.name: p.read_bytes() for p in directory.iterdir()}, original)

    def test_partial_tail_preserved_and_append_refused_until_completed(self):
        store = ingest.RawStore(self.root)
        prefix = b'{"id":"old00000"}\n'
        partial = b'{"id":"partial0"'
        store.accepted.write_bytes(prefix + partial)
        self.assertEqual(store.accepted_ids(), {"old00000"})
        with self.assertRaisesRegex(ValueError, "incomplete journal tail"):
            store.record_accepted(replay("next0000"))
        self.assertEqual(store.accepted.read_bytes(), prefix + partial)
        with store.accepted.open("ab") as handle:
            handle.write(b'}\n')
        self.assertTrue(store.record_accepted(replay("next0000")))
        self.assertEqual(store.accepted_ids(), {"old00000", "partial0", "next0000"})

    def test_append_cost_is_incremental_and_replacement_invalidates_cache(self):
        store = ingest.RawStore(self.root)
        store.accepted.write_text("".join(json.dumps({"id": f"old{i:05d}"}) + "\n" for i in range(1000)))
        self.assertEqual(len(store.accepted_ids()), 1000)
        initial = store._index_bytes_read
        other = ingest.RawStore(self.root)
        for i in range(10):
            writer = store if i % 2 else other
            self.assertTrue(writer.record_accepted(replay(f"new{i:05d}")))
            # Same-process readers still see the other instance's new tail.
            self.assertEqual(len(store.accepted_ids()), 1001 + i)
        self.assertEqual(store._index_bytes_read, store.accepted.stat().st_size)
        self.assertLess(store._index_bytes_read - initial, initial)
        # Truncate to a smaller prefix, then replace the inode entirely.
        store.accepted.write_text('{"id":"truncate"}\n')
        self.assertEqual(store.accepted_ids(), {"truncate"})
        api_client.atomic_write(store.accepted, b'{"id":"replace0"}\n')
        self.assertEqual(store.accepted_ids(), {"replace0"})

    def test_same_store_thread_reentrancy_and_quarantine(self):
        store = ingest.RawStore(self.root)
        data = replay("thread00")
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: ingest.ingest_replay(store, data, None, {}, None), range(24)))
        self.assertEqual(sum(not r.cached for r in results), 1)
        bad = replay("invalid0")
        bad["frames"][1]["white"] = "?" * 64
        self.assertTrue(ingest.ingest_replay(store, bad, None, {}, None))
        self.assertEqual(store.accepted_ids(), {"thread00"})
        self.assertTrue((store.games / "invalid0" / "replay.json").exists())
        self.assertTrue((store.quarantine / "invalid0.json").exists())


if __name__ == "__main__":
    unittest.main()
