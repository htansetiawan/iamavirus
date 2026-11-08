"""Regression tests for the observed disconnected-archive publication bug."""
import contextlib
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from learning import daily_insights
spec = importlib.util.spec_from_file_location('raw_guard', ROOT/'astra-submissions/tools/check_raw_available.py')
guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
spec = importlib.util.spec_from_file_location('intel_status', ROOT/'astra-submissions/tools/daily_intel_status.py')
intel = importlib.util.module_from_spec(spec); spec.loader.exec_module(intel)
spec = importlib.util.spec_from_file_location('repair_backfill', Path(__file__).with_name('backfill.py'))
backfill = importlib.util.module_from_spec(spec); spec.loader.exec_module(backfill)


class ReportInputs(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = self.root/'raw'; self.out = self.root/'reports'
        self.out.mkdir()
        self.latest = self.out/'insights-latest.md'
        self.latest.write_text('last good report\n')

    def archive(self, recent=True):
        (self.raw/'games').mkdir(parents=True)
        (self.raw/'snapshots').mkdir()
        now = datetime.now(timezone.utc)
        row = dict(id='abcdefgh', white='Other A', black='Other B', result='1-0',
                   whiteVersion=1, blackVersion=1, plies=2,
                   createdAt=(now-timedelta(hours=1) if recent else now-timedelta(days=20)).isoformat())
        (self.raw/'accepted.jsonl').write_text(json.dumps(row)+'\n')
        snap = self.raw/'snapshots'/now.strftime('%Y-%m-%dT%H%M%S.%fZ0000')
        snap.mkdir()
        (snap/'leaderboard.json').write_text(json.dumps({'leaderboard':{'players':[
            {'name':'IAmAVirus','activeVersion':37,'rating':1900},
            {'name':'Other A','activeVersion':1,'rating':2000}]}}))

    def run_insights(self):
        with patch.object(sys, 'argv', ['daily_insights','--raw',str(self.raw),'--out',str(self.out)]), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            daily_insights.main()

    def assert_preserved(self):
        self.assertEqual(self.latest.read_text(), 'last good report\n')
        self.assertEqual([p.name for p in self.out.iterdir()], ['insights-latest.md'])

    def test_disconnected_raw_link_is_not_bootstrapped(self):
        self.raw.symlink_to(self.root/'unmounted/archive')
        with self.assertRaises(OSError): guard.check_raw_available(self.raw)
        with self.assertRaises(SystemExit) as e: self.run_insights()
        self.assertEqual(e.exception.code, 2); self.assert_preserved()

    def test_new_local_store_may_bootstrap_but_not_publish(self):
        guard.check_raw_available(self.raw)
        with self.assertRaises(OSError): guard.check_raw_available(self.raw, reports=True)
        with self.assertRaises(SystemExit): self.run_insights()
        self.assert_preserved()

    def test_missing_index_does_not_replace_report(self):
        self.archive(); (self.raw/'accepted.jsonl').unlink()
        with self.assertRaises(OSError): guard.check_raw_available(self.raw, reports=True)
        with self.assertRaises(SystemExit): self.run_insights()
        self.assert_preserved()

    def test_empty_or_unparseable_index_does_not_replace_report(self):
        self.archive()
        for content in ('', '{broken-json\n'):
            (self.raw/'accepted.jsonl').write_text(content)
            with self.assertRaises(SystemExit): self.run_insights()
            self.assert_preserved()

    def test_missing_snapshot_does_not_replace_report(self):
        self.archive()
        for p in (self.raw/'snapshots').glob('*/leaderboard.json'): p.unlink()
        with self.assertRaises(SystemExit): self.run_insights()
        self.assert_preserved()

    def test_index_supplies_games_without_random_listing_reads(self):
        self.archive()
        guard.check_raw_available(self.raw, reports=True)
        self.assertEqual(list((self.raw/'games').iterdir()), [])
        self.run_insights()
        text = self.latest.read_text()
        self.assertIn('Our active version: v37.', text)
        self.assertIn('Window: 7 days (1 games of all teams).', text)

    def test_zero_recent_games_is_valid_with_available_inputs(self):
        self.archive(recent=False); self.run_insights()
        text = self.latest.read_text()
        self.assertIn('Our active version: v37.', text)
        self.assertIn('Window: 7 days (0 games of all teams).', text)

    def test_archive_disappearing_before_write_preserves_report(self):
        self.archive()
        original = os.path.isdir; seen = {}
        targets = {str(self.raw/'games'), str(self.raw/'snapshots')}
        def available(path):
            if str(path) not in targets: return original(path)
            seen[str(path)] = seen.get(str(path),0)+1
            return seen[str(path)] == 1
        with patch.object(daily_insights.os.path, 'isdir', side_effect=available):
            with self.assertRaises(SystemExit): self.run_insights()
        self.assert_preserved()

    def test_recent_own_feed_does_not_hide_stale_other_feed(self):
        now = datetime.now(timezone.utc)
        rows = [dict(createdAt=now.isoformat(), white='IAmAVirus', black='Other'),
                dict(createdAt=(now-timedelta(days=2)).isoformat(), white='Other', black='Else')]
        c = intel.corpus_coverage(rows, now)
        self.assertTrue(c['other_feed_stale'])
        self.assertEqual(c['last_24h'], dict(ours=1, other_only=0))
        rows.append(dict(createdAt=(now-timedelta(hours=1)).isoformat(), white='Other', black='Else'))
        self.assertFalse(intel.corpus_coverage(rows, now)['other_feed_stale'])

    def test_backfill_excludes_watcher_and_known_games_and_stops_at_cutoff(self):
        row = dict(id='abcdefgh', createdAt='2026-11-08T00:00:00Z', white='Other', black='Else')
        self.assertEqual(backfill.selection(row, set()), 'fetch')
        self.assertEqual(backfill.selection(row, {'abcdefgh'}), 'known')
        self.assertEqual(backfill.selection(dict(row, white='IAmAVirus'), set()), 'our_watcher')
        self.assertEqual(backfill.selection(dict(row, black='IAmAVirus'), set()), 'our_watcher')
        self.assertEqual(backfill.selection(dict(row, createdAt='2026-11-05T23:00:00-08:00'), set()), 'before_cutoff')
        self.assertEqual(backfill.selection(dict(row, createdAt='2026-11-06T09:36:00Z'), set()), 'fetch')


if __name__ == '__main__':
    unittest.main()
