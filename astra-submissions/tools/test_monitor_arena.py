"""No network: regression checks for cache reuse and interrupted writes."""
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import monitor_arena as monitor


class CacheTests(unittest.TestCase):
    def test_reuses_shared_cache_without_network(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cache = root / 'cache'
            (cache / 'abcd1234').mkdir(parents=True)
            replay = {'id': 'abcd1234', 'frames': [{'ply': 0}]}
            (cache / 'abcd1234' / 'replay.json').write_text(json.dumps(replay))
            client = unittest.mock.Mock()
            destination = root / 'out' / 'abcd1234.json.gz'
            metadata = []
            monitor.cache_replay(client, replay['id'], destination, cache, metadata)
            client.get.assert_not_called()
            with gzip.open(destination, 'rt') as handle:
                self.assertEqual(json.load(handle), replay)
            self.assertEqual(metadata[0]['cache'], str(cache / 'abcd1234' / 'replay.json'))
            self.assertFalse(destination.with_name(destination.name + '.tmp').exists())

    def test_interruption_does_not_publish_partial_gzip(self):
        with tempfile.TemporaryDirectory() as d:
            destination = Path(d) / 'abcd1234.json.gz'
            client = unittest.mock.Mock()
            client.get.return_value = ({'id': 'abcd1234'}, {'url': 'test'})
            with patch.object(monitor.json, 'dump', side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    monitor.cache_replay(client, 'abcd1234', destination, None, [])
            self.assertFalse(destination.exists())
            self.assertFalse(destination.with_name(destination.name + '.tmp').exists())

    def test_wrong_cache_path_fails_before_output_or_network(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            result = subprocess.run([sys.executable, monitor.__file__, '--output', str(root/'out'),
                '--cache', str(root/'missing')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('--cache must be an existing directory', result.stderr)
            self.assertFalse((root/'out').exists())


if __name__ == '__main__':
    unittest.main()
