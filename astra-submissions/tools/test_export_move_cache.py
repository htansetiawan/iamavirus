"""Contract tests for move-cache parity, invalidation and safe publication."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import multiprocessing
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('move_cache', HERE/'export_move_cache.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


def records(path):
    result = {}
    with path.open() as handle:
        while header := handle.readline():
            _, gid, white, black = header.split()
            moves = handle.readline().strip()
            if gid in result:
                raise AssertionError(f'duplicate game {gid}')
            result[gid] = (white, black, moves)
    return result


class MoveCache(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = self.root/'raw'
        self.raw.mkdir()
        self.journal = self.raw/'accepted.jsonl'
        self.journal.touch()
        self.args = argparse.Namespace(raw=self.raw, out_prefix=self.root/'published/arena',
            cache=self.root/'cache/moves.sqlite', since='2026-10-19', games=1000000,
            test_share=.15, seed=7, seed_export=[], wall_seconds=30, legacy_files=True)

    def game(self, gid, moves='e2e4 e7e5 g1f3 b8c6', **changes):
        row = dict(id=gid, white='Knight Vision', black='IAmAVirus', createdAt='2026-11-09T00:00:00Z',
                   rulesVersion='fow-v1', plies=len(moves.split()),
                   moves_sha256=hashlib.sha256(moves.encode()).hexdigest())
        row.update(changes)
        folder = self.raw/'games'/gid
        folder.mkdir(parents=True, exist_ok=True)
        replay = dict(id=gid, rulesVersion=row['rulesVersion'],
                      frames=[dict(move=None)] + [dict(move=m) for m in moves.split()])
        (folder/'replay.json').write_text(json.dumps(replay))
        (folder/'listing.json').write_text(json.dumps(row))
        with self.journal.open('a') as handle:
            handle.write(json.dumps(row)+'\n')
        return row

    def run_export(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return exporter.export(self.args)

    def resolved(self):
        return exporter.resolve(self.args.out_prefix)

    def split_records(self):
        paths = self.resolved()
        return {name: records(Path(paths[name])) for name in ('train', 'test')}

    def test_reference_parity_and_warm_cache_needs_no_replays(self):
        for i in range(40):
            self.game(f'{i:08d}', black='baseline.py' if i % 3 == 0 else 'IAmAVirus')
        self.game('oldgame0', createdAt='2026-10-01T00:00:00Z')
        self.game('norules0', rulesVersion=None)
        self.game('random00', white='Uniform', black='Baseline')
        self.game('short000', moves='e2e4 e7e5')
        # Same selection/tag/split contract as the private reference exporter.
        expected = {'train': {}, 'test': {}}
        for i in range(40):
            gid = f'{i:08d}'
            split = 'test' if int(hashlib.sha1(gid.encode()).hexdigest(), 16) % 1000 < 150 else 'train'
            expected[split][gid] = ('Knight_Vision', '-' if i % 3 == 0 else 'IAmAVirus', 'e2e4 e7e5 g1f3 b8c6')
        first = self.run_export()
        self.assertEqual(first['replay_reads'], 40)
        self.assertEqual(self.split_records(), expected)
        # A warm cache uses no listing/replay files at all.
        for p in (self.raw/'games').glob('*/*.json'):
            p.unlink()
        second = self.run_export()
        self.assertEqual(second['replay_reads'], 0)
        self.assertEqual(second['cache_hits'], 40)
        self.assertEqual(self.split_records(), expected)
        self.assertNotEqual(first['generation'], second['generation'])
        self.assertTrue(Path(first['generation']).exists())

    def test_changed_hash_duplicate_row_and_partial_journal_tail(self):
        self.game('game0001')
        self.run_export()
        self.game('game0001', moves='d2d4 d7d5 c2c4 e7e6')
        with self.journal.open('a') as handle:
            handle.write('{"id":"unfinished')
        result = self.run_export()
        self.assertEqual(result['replay_reads'], 1)
        splits = self.split_records()
        self.assertEqual(sum(len(x) for x in splits.values()), 1)
        self.assertEqual(next(v['game0001'][2] for v in splits.values() if v), 'd2d4 d7d5 c2c4 e7e6')
        manifest = json.loads(Path(result['manifest']).read_text())
        self.assertEqual(manifest['journal']['duplicate_lines'], 1)
        self.assertGreater(manifest['journal']['ignored_incomplete_tail_bytes'], 0)

    def test_legacy_seed_verified_by_hash_and_truncated_tail_rejected(self):
        self.game('game0001')
        self.game('game0002')
        self.game('game0003')
        seed = self.root/'interrupted-train.txt'
        seed.write_text('game game0001 wrong_tags ignored\ne2e4 e7e5 g1f3 b8c6\n'
                        'game game0002 Knight_Vision IAmAVirus\nd2d4 d7d5 c2c4 e7e6\n'
                        'game game0003 Knight_Vision IAmAVirus\ne2e4 e7')
        self.args.seed_export = [seed]
        result = self.run_export()
        self.assertEqual(result['cache_hits'], 1)
        self.assertEqual(result['replay_reads'], 2)
        meta = json.loads(Path(result['manifest']).read_text())
        self.assertEqual(meta['seed_sources']['invalid'], 1)
        self.assertEqual(meta['seed_sources']['incomplete_tail'], 1)
        self.assertTrue(all(t[0] == 'Knight_Vision' for r in self.split_records().values() for t in r.values()))

    def test_bad_replay_preserves_last_good_generation_and_legacy_files(self):
        self.game('game0001')
        first = self.run_export()
        before = self.split_records()
        self.game('game0002')
        replay = self.raw/'games/game0002/replay.json'
        data = json.loads(replay.read_text())
        data['frames'][1]['move'] = 'd2d4'
        replay.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'move hash mismatch'):
            self.run_export()
        self.assertEqual(self.resolved()['generation'], first['generation'])
        self.assertEqual(self.split_records(), before)
        self.assertFalse(list(Path(str(self.args.out_prefix)+'-generations').glob('.tmp-*')))

    def test_empty_export_and_malformed_interior_do_not_publish(self):
        with self.assertRaisesRegex(ValueError, 'no eligible'):
            self.run_export()
        self.assertFalse(Path(str(self.args.out_prefix)+'-current').exists())
        self.assertFalse(Path(str(self.args.out_prefix)+'-current.json').exists())
        self.journal.write_text('{broken json}\n')
        with self.assertRaises(json.JSONDecodeError):
            self.run_export()

    def test_export_lock_blocks_concurrent_writer(self):
        self.game('game0001')
        with exporter.exclusive(Path(str(self.args.out_prefix)+'-export.lock')):
            with self.assertRaisesRegex(RuntimeError, 'another exporter'):
                self.run_export()

    def test_force_kill_during_generation_keeps_old_pointer(self):
        self.game('game0001')
        first = self.run_export()
        self.game('game0002')
        ready = self.root/'ready'
        def killed_export():
            original = exporter.durable_json
            def pause_before_manifest(path, data):
                ready.touch()
                signal.pause()
                return original(path, data)
            exporter.durable_json = pause_before_manifest
            self.run_export()
        process = multiprocessing.get_context('fork').Process(target=killed_export)
        process.start()
        self.addCleanup(lambda: process.is_alive() and process.kill())
        import time
        deadline = time.monotonic()+10
        while not ready.exists() and process.is_alive() and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertTrue(ready.exists())
        process.kill()
        process.join(5)
        self.assertEqual(process.exitcode, -signal.SIGKILL)
        self.assertEqual(self.resolved()['generation'], first['generation'])
        # SQLite recovers and a later export can finish; orphan temp directories
        # are never selected by the current pointer.
        completed = self.run_export()
        self.assertEqual(completed['train'] + completed['test'], 2)

    def test_pointer_swap_preserves_previously_resolved_pair(self):
        self.game('game0001')
        self.run_export()
        old = self.resolved()
        before = records(Path(old['train'])), records(Path(old['test']))
        self.game('game0002')
        self.run_export()
        self.assertEqual((records(Path(old['train'])), records(Path(old['test']))), before)
        self.assertEqual(sum(len(r) for r in self.split_records().values()), 2)

    def test_no_symlink_filesystem_and_publication_only_recovery(self):
        self.game('game0001')
        with mock.patch('os.symlink', side_effect=PermissionError('exFAT has no symlinks')):
            first = self.run_export()
            Path(str(self.args.out_prefix)+'-current.json').unlink()
            with mock.patch.object(exporter, 'journal_snapshot', side_effect=AssertionError('must not re-extract')):
                result = exporter.publish_generation(self.args.out_prefix, Path(first['generation']), True)
            self.assertEqual(result['generation'], first['generation'])
            self.assertEqual(self.resolved()['generation'], first['generation'])
            self.assertFalse(Path(str(self.args.out_prefix)+'-train.txt').is_symlink())

    def test_pointer_paths_relative_to_actual_mounted_directory(self):
        self.game('game0001')
        physical = self.root/'drive'
        physical.mkdir()
        logical = self.root/'long/nested/workspace/mounted'
        logical.parent.mkdir(parents=True)
        logical.symlink_to(physical, target_is_directory=True)
        self.args.out_prefix = logical/'arena'
        first = self.run_export()
        pointer = json.loads((physical/'arena-current.json').read_text())
        self.assertEqual(pointer['generation'], str(Path(first['generation']).relative_to(physical)))
        self.assertEqual(self.resolved()['generation'], first['generation'])


if __name__ == '__main__':
    unittest.main()
