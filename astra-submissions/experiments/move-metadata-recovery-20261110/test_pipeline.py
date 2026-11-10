"""Offline fixtures only: no urllib/network calls are allowed."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlencode
import collect
import review
from learning.api_client import ApiError,FetchRecord

class OfflinePipeline(unittest.TestCase):
    def fixture(self,folder):
        out=folder/'out';out.mkdir();store=folder/'store';store.mkdir();snapshot=store/'source.sqlite'
        db=sqlite3.connect(snapshot);db.execute('create table moves(game_id text,moves_sha256 text,moves text)')
        moves='g1f3 b8c6';movehash=hashlib.sha256(moves.encode()).hexdigest()
        db.executemany('insert into moves values(?,?,?)',[(gid,movehash,moves) for gid in ('test0001','test0002','test0003')]);db.commit();db.close()
        self.row=lambda gid,at:dict(id=gid,createdAt=at,white='A',black='B',whitePlayerId='a',blackPlayerId='b',whiteVersion=1,blackVersion=2,result='1-0',reason='King capturable',plies=2)
        known=folder/'known.json';known.write_text(json.dumps(dict(games=[dict(game='test0001',created_at='2026-11-09T00:00:00Z',white='A',black='B',white_version=1,black_version=2,frames=3,sequence_sha256=movehash)])))
        plan=dict(dependencies={},store=str(store),snapshot=str(snapshot),target_rows=3,known_plan=str(known),request_cap=10,page_cap=10,response_bytes_cap=10000,max_bytes=1000000,since='2026-10-19T00:00:00Z',before='2026-11-10T19:15:00Z',wall_seconds=60)
        (out/'plan.json').write_text(json.dumps(plan));return out,store
    def fake(self,restart=False,wrong_plies=False):
        row=self.row
        class Client:
            def __init__(self,budget):self.requests_made=0;self.attempts=[];self.failed=False
            def get_bytes(self,path,params):
                self.requests_made+=1;self.attempts.append(dict(at='2026-11-10T20:00:00Z',monotonic=100+6*self.requests_made))
                url='https://6s890.lids.mit.edu'+path+'?'+urlencode(params)
                if restart and params.get('cursor') and not self.failed:
                    self.failed=True;raise ApiError(400,url,'expired cursor')
                games=[row('future00','2026-11-10T19:15:00Z'),row('test0001','2026-11-09T00:00:00Z')] if 'cursor' not in params else [row('test0002','2026-10-20T00:00:00Z'),row('older000','2026-10-18T00:00:00Z')]
                if wrong_plies:games[1]['plies']=3
                raw=json.dumps(dict(games=games,sort='played',order='desc',nextCursor='opaque')).encode()
                return raw,FetchRecord(url,'2026-11-10T20:00:00Z',hashlib.sha256(raw).hexdigest(),200,1)
        return Client
    def run_fixture(self,restart=False):
        with tempfile.TemporaryDirectory() as td:
            out,store=self.fixture(Path(td))
            with patch.object(collect,'OUT',out),patch.object(review,'OUT',out),patch.object(collect,'BoundedClient',self.fake(restart)):
                collect.main();review.main()
                result=json.loads((out/'result.json').read_text());audit=json.loads((out/'independent-review.json').read_text())
                self.assertEqual(result['matched'],2);self.assertEqual(result['unmatched'],1);self.assertFalse(result['training_ready']);self.assertTrue(audit['passed'])
                self.assertEqual(result['cursor_restarts'],int(restart));self.assertEqual(result['known_metadata_overlaps'],1)
                db=sqlite3.connect(store/'metadata.sqlite');db.execute("update metadata set json=replace(json,'King capturable','tampered')");db.commit();db.close()
                with self.assertRaises(AssertionError):review.main()
    def test_valid_window_and_independent_tamper_rejection(self):self.run_fixture()
    def test_one_cursor_restart_keeps_prior_metadata(self):self.run_fixture(True)
    def test_wrong_ply_stops_without_publishing_result(self):
        with tempfile.TemporaryDirectory() as td:
            out,store=self.fixture(Path(td))
            with patch.object(collect,'OUT',out),patch.object(collect,'BoundedClient',self.fake(wrong_plies=True)):
                with self.assertRaises(AssertionError):collect.main()
            self.assertEqual(json.loads((out/'execution.json').read_text())['status'],'failed');self.assertFalse((out/'result.json').exists())

if __name__=='__main__':unittest.main()
