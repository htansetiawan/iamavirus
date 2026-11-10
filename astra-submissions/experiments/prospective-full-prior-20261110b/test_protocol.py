"""Selection/failure/ownership tests using temporary stores and fake APIs."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from protocol import (TEAMS, OWN, PRIORITY, ordered_candidates, cohort_game, gate_result)
from collect import snapshot, source, seal_candidates, BudgetClient

TEAM = next(iter(TEAMS))
CUTOFF = '2026-11-10T07:15:00Z'


def row(game, minute=16, side=TEAM):
    return dict(id=game,createdAt=f'2026-11-10T07:{minute:02d}:00Z',result='1-0',plies=4,
                white='Reference',black='Other',whitePlayerId=side,blackPlayerId='other',
                whiteVersion=1,blackVersion=2)


def replay(r):
    from learning.histories import replay_from_moves
    result = replay_from_moves(r['id'],['e2e4','e7e5','g1f3','b8c6'],'1-0','Opponent crashed',r['white'],r['black'])
    result.update({k:v for k,v in r.items() if k != 'plies'})
    result['rulesVersion'] = 'fow-v1'
    return result


@dataclass
class Fetch:
    url: str = 'fixture:page'


class Pages:
    def __init__(self, pages):
        self.pages,self.calls = pages,[]

    def games_page(self, params, cursor):
        self.calls.append((dict(params),cursor))
        return self.pages[len(self.calls)-1], Fetch()


def page(rows, cursor=None):
    return dict(games=rows,nextCursor=cursor,sort='played',order='desc',playing=[])


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='astra-future-protocol-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_snapshot_cursors_fixed_filters_and_earliest_order(self):
        a,b,c = row('future00',18),row('future01',16),row('old00000',14)
        client = Pages([page([a],'opaque'),page([b,c],'unused')])
        result,n = snapshot(client,CUTOFF,self.root,0,5)
        self.assertEqual([r['id'] for r in result],['future01','future00'])
        self.assertEqual(n,2)
        self.assertEqual(client.calls[0][0],client.calls[1][0])
        self.assertEqual([x[1] for x in client.calls],[None,'opaque'])
        self.assertEqual(len(list(self.root.glob('page-*.json'))),2)

    def test_incomplete_snapshot_duplicate_and_order_fail_closed(self):
        with self.assertRaisesRegex(RuntimeError,'incomplete coverage'):
            snapshot(Pages([page([row('future00')],'more')]),CUTOFF,self.root,0,1)
        with self.assertRaisesRegex(AssertionError,'duplicate ID'):
            snapshot(Pages([page([row('future00'),row('future00')])]),CUTOFF,self.root,1,2)
        with self.assertRaisesRegex(AssertionError,'nonmonotone'):
            snapshot(Pages([page([row('future00',16),row('future01',17)])]),CUTOFF,self.root,2,2)

    def test_sequence_exclusions_are_whole_trajectory_not_outcome(self):
        r = row('future00')
        rp = replay(r)
        g,reason = cohort_game(r,rp,'source',set())
        self.assertIsNone(reason)
        self.assertEqual(g['selected_plies'],[0,2])
        self.assertEqual(g['split'],'future')
        self.assertEqual(g['sequence_sha256'],hashlib.sha256(' '.join(g['moves']).encode()).hexdigest())
        self.assertEqual(cohort_game(r,rp,'source',{g['sequence_sha256']})[1],'whole-sequence duplicate')
        # Opposite result and a different played version are still duplicates.
        r['result']=rp['result']='0-1'
        r['whiteVersion']=rp['whiteVersion']=17
        self.assertEqual(cohort_game(r,rp,'source',{g['sequence_sha256']})[1],'whole-sequence duplicate')

    def test_schema_mismatch_not_discarded_for_selection(self):
        r=row('future00');rp=replay(r);rp['result']='0-1'
        with self.assertRaisesRegex(AssertionError,'disagreement'):
            cohort_game(r,rp,'source',set())

    def test_own_replay_missing_defers_without_fetch_or_later_game(self):
        own=row('future00');own['blackPlayerId']=OWN
        class NoNetwork:
            def get_bytes(self,*args):
                raise AssertionError('must defer to owner')
        plan=dict(shared_raw=str(self.root/'shared'),games=1,replay_bytes_cap=1024*1024)
        games,decisions,pending=seal_candidates([own,row('future01',18)],NoNetwork(),plan,self.root,set())
        self.assertFalse(games or decisions)
        self.assertEqual(pending['game'],own['id'])

    def test_shared_cache_is_read_only_and_has_no_network_request(self):
        r=row('future00');rp=replay(r)
        path=self.root/'shared/games'/r['id']/'replay.json';path.parent.mkdir(parents=True)
        payload=json.dumps(rp).encode();path.write_bytes(payload)
        archive=self.root/'archive';archive.mkdir()
        plan=dict(shared_raw=str(self.root/'shared'),replay_bytes_cap=1024*1024,games=1)
        games,_,pending=seal_candidates([r],object(),plan,archive,set())
        self.assertEqual(len(games),1)
        self.assertIsNone(pending)
        self.assertEqual(path.read_bytes(),payload)
        again,receipt=source(r,object(),plan,archive)
        self.assertEqual(again,rp)
        self.assertEqual(receipt['sha256'],hashlib.sha256(payload).hexdigest())
        self.assertFalse((self.root/'shared/accepted.jsonl').exists())

    def test_model_gate_closes_on_each_missing_requirement(self):
        plan={'gate':dict(primary_min=5000,full_gain=.05,matched_linear_gain=.02,surprise_min=100,priority_games_min=20)}
        metric=dict(primary=5000,gain=.05,interval95=[.001,.1],matched_linear_gain=.02,
                    all_move_gain=0,capture_target_error=0,capture_action_error=0,surprise_captures=100,
                    priority={t:dict(games=20,gain=0) for t in PRIORITY})
        self.assertTrue(all(gate_result(plan,metric).values()))
        for key,value in [('primary',4999),('gain',.04999),('interval95',[0,.1]),
                          ('matched_linear_gain',.01999),('all_move_gain',-1e-9),
                          ('capture_action_error',1e-9),('surprise_captures',99)]:
            altered={**metric,key:value}
            self.assertFalse(all(gate_result(plan,altered).values()),key)
        altered=json.loads(json.dumps(metric));altered['priority'][PRIORITY[0]]['games']=19
        self.assertFalse(all(gate_result(plan,altered).values()))
        altered=json.loads(json.dumps(metric));altered['priority'][PRIORITY[0]]['gain']=-1e-9
        self.assertFalse(all(gate_result(plan,altered).values()))

    def test_request_budget_stops_before_another_request(self):
        client=BudgetClient(3);client.requests_made=3
        with self.assertRaisesRegex(RuntimeError,'budget exhausted'):
            client._pace()


if __name__=='__main__':
    unittest.main()
