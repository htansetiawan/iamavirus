"""Drive-loss behavior and cleanup tests; fake public responses only."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import collect
from protocol import OWN,ordered_candidates,stamp_ns
from test_protocol import row,replay,Fetch


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.archive=self.root/'ssd';self.archive.mkdir()
        self.plan=dict(shared_raw=str(self.root/'shared'),games=1,replay_bytes_cap=1024*1024,owner_fallback_on_store_loss=True)
        self.own=row('future00');self.own['blackPlayerId']=OWN

    def fake_client(self,r):
        payload=json.dumps(replay(r)).encode()
        class Fake:
            calls=0
            def get_bytes(inner,path):
                inner.calls+=1
                assert path=='/api/games/'+r['id']
                return payload,Fetch(url='https://6s890.lids.mit.edu'+path)
        return Fake()

    def healthy(self):
        (self.root/'shared/games').mkdir(parents=True)
        (self.root/'shared/accepted.jsonl').write_text('{}\n')

    def test_healthy_owner_miss_still_defers(self):
        self.healthy();client=self.fake_client(self.own)
        g,decisions,pending=collect.seal_candidates([self.own,row('future01',18)],client,self.plan,self.archive,set())
        self.assertFalse(g or decisions);self.assertEqual(pending['game'],'future00');self.assertEqual(client.calls,0)

    def test_dangling_shared_store_fetches_once_to_ssd(self):
        (self.root/'shared').symlink_to(self.root/'unmounted')
        client=self.fake_client(self.own)
        games,_,pending=collect.seal_candidates([self.own],client,self.plan,self.archive,set())
        self.assertEqual(len(games),1);self.assertIsNone(pending);self.assertEqual(client.calls,1)
        saved=self.archive/'games/future00/replay.json';record=json.loads(saved.with_name('fetch.json').read_text())
        self.assertEqual(record['owner_fallback'],'shared store unavailable')
        self.assertEqual(record['sha256'],hashlib.sha256(saved.read_bytes()).hexdigest())
        self.assertFalse((self.root/'unmounted').exists())
        collect.source(self.own,client,self.plan,self.archive);self.assertEqual(client.calls,1)

    def test_cached_io_failure_can_use_private_source(self):
        self.healthy();cached=self.root/'shared/games/future00/replay.json';cached.parent.mkdir();cached.write_text('unreadable')
        original=Path.read_bytes;client=self.fake_client(self.own)
        def fail_target(path):
            if path==cached:raise OSError('fixture device offline')
            return original(path)
        with patch.object(Path,'read_bytes',fail_target):
            value,receipt=collect.source(self.own,client,self.plan,self.archive)
        self.assertEqual(value['id'],'future00');self.assertIn('device offline',receipt['cache_error']);self.assertEqual(client.calls,1)

    def test_readable_but_malformed_cache_is_not_overridden(self):
        self.healthy();cached=self.root/'shared/games/future00/replay.json';cached.parent.mkdir();cached.write_text('not JSON')
        client=self.fake_client(self.own)
        with self.assertRaises(json.JSONDecodeError):collect.source(self.own,client,self.plan,self.archive)
        self.assertEqual(client.calls,0)

    def test_secondary_receipt_error_preserves_primary_failure(self):
        local=self.root/'receipts';local.mkdir();state=dict(status='failed',error='original failure')
        original=collect.write
        def fail_archive(path,data,**kw):
            if path==self.archive/'execution.json':raise FileNotFoundError('archive missing')
            return original(path,data,**kw)
        with patch.object(collect,'OUT',local),patch.object(collect,'write',fail_archive):collect.record_terminal(state,self.archive)
        receipt=json.loads((local/'execution.json').read_text())
        self.assertEqual(receipt['error'],'original failure');self.assertIn('archive missing',receipt['archive_terminal_receipt_error'])

    def test_completion_without_archive_receipt_is_failed(self):
        local=self.root/'receipts';local.mkdir();state=dict(status='complete',phase='sealed')
        original=collect.write
        def fail_archive(path,data,**kw):
            if path==self.archive/'execution.json':raise FileNotFoundError('archive missing')
            return original(path,data,**kw)
        with patch.object(collect,'OUT',local),patch.object(collect,'write',fail_archive):
            with self.assertRaises(FileNotFoundError):collect.record_terminal(state,self.archive)
        self.assertEqual(json.loads((local/'execution.json').read_text())['status'],'failed')

    def test_nanosecond_order_and_cutoff(self):
        early,late,before=row('future01'),row('future00'),row('old00000')
        early['createdAt']='2026-11-10T12:00:00.000000001Z'
        late['createdAt']='2026-11-10T12:00:00.000000999Z'
        before['createdAt']='2026-11-10T11:59:59.999999999Z'
        self.assertEqual([r['id'] for r in ordered_candidates([late,before,early],'2026-11-10T12:00:00Z')],['future01','future00'])
        self.assertEqual(stamp_ns(late['createdAt'])-stamp_ns(early['createdAt']),998)


if __name__=='__main__':unittest.main()
