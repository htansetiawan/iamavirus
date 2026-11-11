import json
import datetime as dt
import hashlib
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from learning.daily_report import previous_report, version_taxonomy
from learning import daily_report
from daily_intel_status import reference_archive, rolling_losses
import daily_intel_status as intel

ROOT = Path(__file__).resolve().parents[2]


class IntelRefreshTests(unittest.TestCase):
    def test_previous_report_excludes_scorecard_current_rerun_and_future(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            for name, value in {
                '2026-10-29.json': {'generated': '29', 'taxonomy': {'x': {}}},
                '2026-10-30.json': {'generated': '30', 'taxonomy': {'x': {}}},
                '2026-10-31.json': {'generated': 'current', 'taxonomy': {}},
                '2026-11-01.json': {'generated': 'future', 'taxonomy': {}},
                'scorecard-2026-10-31.json': {'games': []},
                'intel-latest.json': {'generated': 'intel'},
            }.items():
                (path/name).write_text(json.dumps(value))
            self.assertEqual(previous_report(directory, '2026-10-31')['generated'], '30')
            (path/'2026-10-30.json').write_text('{broken')
            self.assertEqual(previous_report(directory, '2026-10-31')['generated'], '29')

    def test_version_and_colour_do_not_mix_and_rates_are_move_weighted(self):
        def game(version, moves, capture):
            return {'white': 'A', 'black': 'A', 'whiteVersion': version, 'blackVersion': 4,
                    'counts': {'white': {'moves': moves, 'capture': capture}, 'black': {'moves': 5, 'capture': 1}}}
        rows = version_taxonomy([game(4, 10, 2), game(4, 90, 9), game(5, 20, 10)])
        by_key = {(r['version'], r['side']): r for r in rows}
        self.assertEqual(by_key[4, 'white']['rates']['capture'], 11.)
        self.assertEqual(by_key[5, 'white']['rates']['capture'], 50.)
        self.assertEqual(by_key[4, 'black']['moves'], 15)
        self.assertEqual(by_key[4, 'black']['opponents'], {'A v4': 2, 'A v5': 1})

    def test_fixed_report_clock_rejects_future_leaderboard(self):
        with patch.object(daily_report, 'accepted_rows', return_value=[]), \
             patch.object(daily_report, 'latest_leaderboard', return_value=('2026-11-01T00:00:00+00:00', [])):
            with self.assertRaises(SystemExit) as error:
                daily_report.main(['--as-of', '2026-10-31T00:00:00+00:00'])
            self.assertEqual(error.exception.code, 2)

    def test_loss_index_is_bounded_by_version_and_colour_and_excludes_wins(self):
        rows = [dict(id=str(i), createdAt=f'2026-10-31T12:00:0{i}Z', white='IAmAVirus',
                     black='duck', whiteVersion=35, blackVersion=6, result='0-1') for i in range(5)]
        rows.append(dict(rows[-1], id='new-version', blackVersion=7))
        rows.append(dict(rows[-1], id='win', result='1-0'))
        rows.append(dict(rows[-1], id='old', createdAt='2026-10-01', result='0-1'))
        rows.append(dict(rows[-1], id='undated', createdAt=None))
        selected = rolling_losses(rows, '2026-10-25', per_group=2)
        self.assertEqual({r['id'] for r in selected}, {'3', '4', 'new-version'})

    def test_history_header_is_checked_instead_of_guessing_record_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'bot.zip'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('src/movemodel.c', 'parameters')
                archive.writestr('data/history.bin', struct.pack('<8sII', b'MISTHIST', 1, 2) + bytes(32))
            self.assertEqual(reference_archive(path, 35)['history']['records'], 2)
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('src/movemodel.c', 'parameters')
                archive.writestr('data/history.bin', struct.pack('<8sII', b'MISTHIST', 1, 2))
            self.assertIn('error', reference_archive(path, 35))

    def test_active_archive_uses_arena_mapping_and_checks_packaged_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root/'old-local-v12.zip'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('src/movemodel.c', 'parameters')
                archive.writestr('data/history.bin', struct.pack('<8sII', b'MISTHIST', 1, 2) + bytes(32))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            registry = root/'README.md'
            registry.write_text(f'| **37** | date | `{path.name}` (was `another-name.zip`) | `{digest[:12]}` |\n')
            with patch.object(intel, 'ROOT', root):
                result = intel.mapped_active_archive(registry, 37)
            self.assertTrue(result['mapping_verified'])
            self.assertEqual(result['arena_version'], 37)
            self.assertEqual(result['history']['records'], 2)
            self.assertEqual(result['sha256'], digest)

    def test_active_archive_refuses_unknown_duplicate_changed_or_external_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root/'bot.zip'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('src/movemodel.c', 'parameters')
                archive.writestr('data/history.bin', struct.pack('<8sII', b'MISTHIST', 1, 0))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            row = f'| 37 | date | `bot.zip` | `{digest[:12]}` |\n'
            registry = root/'README.md'
            with patch.object(intel, 'ROOT', root):
                for content, version, error in [
                    (row, None, 'unavailable'), (row, 38, 'found 0'),
                    (row + row, 37, 'found 2'),
                    (row.replace(digest[:12], '0' * 12), 37, 'does not match'),
                    (row.replace('bot.zip', '../outside.zip'), 37, 'outside the project'),
                ]:
                    with self.subTest(version=version, error=error):
                        registry.write_text(content)
                        result = intel.mapped_active_archive(registry, version)
                        self.assertFalse(result['mapping_verified'])
                        self.assertIn(error, result['error'])

    def test_active_archive_follows_canonical_markdown_link_before_upload_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root/'fable-submissions/README.md'
            registry.parent.mkdir()
            canonical = root/'astra-submissions/iamavirus-v38-canonical.zip'
            canonical.parent.mkdir()
            for path, count in ((canonical, 2), (registry.parent/'v38-review.zip', 0)):
                with zipfile.ZipFile(path, 'w') as archive:
                    archive.writestr('src/movemodel.c', 'parameters')
                    archive.writestr('data/history.bin', struct.pack('<8sII', b'MISTHIST', 1, count) + bytes(16 * count))
            digest = hashlib.sha256(canonical.read_bytes()).hexdigest()
            # Same cell shape as the real arena-v38 registry row. The alias
            # exists too, so existence-based fallback cannot hide the bug.
            for label in (canonical.name, f'`{canonical.name}`'):
                registry.write_text(f'| **38** | date | Astra [{label}](../astra-submissions/{canonical.name}), uploaded alias `v38-review.zip` | `{digest[:12]}` |\n')
                with self.subTest(label=label), patch.object(intel, 'ROOT', root):
                    result = intel.mapped_active_archive(registry, 38)
                    self.assertTrue(result['mapping_verified'], result.get('error'))
                    self.assertEqual(result['path'], str(canonical))
                    self.assertEqual(result['sha256'], digest)
                    self.assertEqual(result['history']['records'], 2)

    def test_active_archive_does_not_replace_a_bad_canonical_link_with_an_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root/'fable-submissions/README.md'
            registry.parent.mkdir()
            alias = registry.parent/'alias.zip'
            with zipfile.ZipFile(alias, 'w') as archive:
                archive.writestr('src/movemodel.c', 'parameters')
                archive.writestr('data/history.bin', struct.pack('<8sII', b'MISTHIST', 1, 0))
            digest = hashlib.sha256(alias.read_bytes()).hexdigest()
            for target, expected in (('../astra-submissions/missing.zip', 'No such file'),
                                     ('../../outside.zip', 'outside the project')):
                registry.write_text(f'| 38 | date | [canonical]({target}), uploaded alias `alias.zip` | `{digest[:12]}` |\n')
                with self.subTest(target=target), patch.object(intel, 'ROOT', root):
                    result = intel.mapped_active_archive(registry, 38)
                    self.assertFalse(result['mapping_verified'])
                    self.assertIn(expected, result['error'])

    def test_daily_publish_commits_available_reports_without_other_staged_work(self):
        # Exercise the actual scheduled publication block: optional steps may
        # fail, and another agent may have staged unrelated work concurrently.
        source = (ROOT/'tools/daily_refresh.sh').read_text()
        publication = 'REPORT=' + source.split('\nREPORT=', 1)[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root/'data/reports/daily'; out.mkdir(parents=True)
            day = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')
            (out/f'{day}.md').write_text('daily report\n')
            (out/'latest.md').write_text('daily report\n')
            (root/'unrelated.txt').write_text('another agent\n')
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, text=True, stderr=subprocess.STDOUT)
            git('init', '-q'); git('config', 'user.email', 'test@example.invalid')
            git('config', 'user.name', 'Test'); git('add', 'unrelated.txt')
            subprocess.run(['bash', '-c', 'set -u\nLOG=run.log\nPUSH=0\nstep() { :; }\n' + publication],
                           cwd=root, check=True, capture_output=True, text=True)
            committed = set(git('show', '--pretty=', '--name-only', 'HEAD').splitlines())
            self.assertEqual(committed, {f'data/reports/daily/{day}.md', 'data/reports/daily/latest.md'})
            self.assertEqual(git('diff', '--cached', '--name-only').strip(), 'unrelated.txt')


if __name__ == '__main__':
    unittest.main()
