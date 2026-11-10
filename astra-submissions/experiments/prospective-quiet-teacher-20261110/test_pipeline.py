"""Synthetic selection, private-input boundary and gate tests; no trained scores."""
from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import torch
from protocol import ROOT,TEAMS,ordered_candidates,cohort_game,gate_result,stamp_ns
from collect import snapshot,source
from features import Producer,batch
from score import WorldQuietTeacher,ScalarResidual,predictions

TEAM=next(iter(TEAMS))


def row(game,stamp='2026-11-10T19:15:01.000000001Z'):
    return dict(id=game,createdAt=stamp,result='1-0',plies=4,white='Ref',black='Other',whitePlayerId=TEAM,blackPlayerId='other',whiteVersion=1,blackVersion=1)

def replay(r):
    from learning.histories import replay_from_moves
    result=replay_from_moves(r['id'],['e2e4','e7e5','g1f3','b8c6'],'1-0','King capturable',r['white'],r['black'])
    result.update({k:v for k,v in r.items() if k!='plies'});result['rulesVersion']='fow-v1';return result

@dataclass
class Fetch:url:str='fixture:public'

class Pipeline(unittest.TestCase):
    def test_exact_order_and_complete_snapshot(self):
        a=row('aaaaaaa1');b=row('aaaaaaa2','2026-11-10T19:15:01.000000002Z');c=row('aaaaaaa3','2026-11-10T19:14:59Z')
        self.assertEqual([r['id'] for r in ordered_candidates([b,a,c],'2026-11-10T19:15:00Z')],['aaaaaaa1','aaaaaaa2'])
        self.assertEqual(stamp_ns(b['createdAt'])-stamp_ns(a['createdAt']),1)
        class Client:
            def games_page(self,params,cursor):return dict(games=[b,a],sort='played',order='desc',nextCursor='more'),Fetch()
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError,'incomplete coverage'):snapshot(Client(),'2026-11-10T19:15:00Z',Path(folder),0,1)

    def test_sequence_duplicate_and_schema_failure(self):
        r=row('aaaaaaa1');rp=replay(r);g,reason=cohort_game(r,rp,'sha',set());self.assertIsNone(reason)
        self.assertEqual(cohort_game(r,rp,'sha',{g['sequence_sha256']})[1],'whole-sequence duplicate')
        rp['result']='0-1'
        with self.assertRaises(AssertionError):cohort_game(r,rp,'sha',set())

    def test_public_copy_and_cached_source_are_immutable(self):
        r=row('aaaaaaa1');rp=replay(r);raw=json.dumps(rp).encode()
        class Client:
            calls=0
            def get_bytes(self,url):self.calls+=1;return raw,Fetch()
        client=Client()
        with tempfile.TemporaryDirectory() as folder:
            saved,receipt=source(r,client,dict(replay_bytes_cap=1000000),Path(folder));self.assertEqual(saved,rp)
            again,_=source(r,client,{},Path(folder));self.assertEqual(again,rp);self.assertEqual(client.calls,1)
            p=Path(folder)/'games'/r['id']/'replay.json';p.write_text('{}')
            with self.assertRaises(AssertionError):source(r,client,{},Path(folder))

    def test_current_action_is_not_a_network_input(self):
        producer=Producer(ROOT/'astra-submissions/experiments/observed-class-20261110/build/producer.so')
        values=[]
        for action in ['e2e4','d2d4']:
            g=dict(game='fixture0',moves=[action],frames=2,selected_plies=[0],white='Ref',black='Other')
            generator=producer.game(g);inputs,meta=next(generator);generator.close();values.append((inputs,meta))
        for key in ('x','base','counts','moves','history_n'):
            self.assertTrue(np.array_equal(values[0][0][key],values[1][0][key]),key)
        self.assertTrue(all(np.array_equal(a,b) for a,b in zip(values[0][0]['board'],values[1][0]['board'])))
        self.assertNotEqual(values[0][1]['target'],values[1][1]['target'])
        b=batch([values[0][0],values[1][0]])
        self.assertNotIn('target',b);self.assertNotIn('y',b)

    def test_model_namespace_and_synthetic_prediction_contract(self):
        torch.set_num_threads(2);torch.set_float32_matmul_precision('highest')
        teacher=WorldQuietTeacher(width=16,latents=2).eval()
        models=dict(teacher=teacher,linear=ScalarResidual('linear'),quadratic=ScalarResidual('quadratic'),production=ScalarResidual('quadratic'))
        producer=Producer(ROOT/'astra-submissions/experiments/observed-class-20261110/build/producer.so')
        g=dict(game='fixture0',moves=['e2e4'],frames=2,selected_plies=[0],white='Ref',black='Other')
        gen=producer.game(g);inputs,_=next(gen);gen.close();b=batch([inputs]);lp,_=predictions(models,b)
        self.assertTrue(all(torch.equal(v,lp['base']) for v in lp.values()))
        self.assertTrue(hasattr(teacher,'board_attention'))

    def test_gate_does_not_rescue_a_favorable_subset(self):
        from protocol import PRIORITY
        plan=dict(gate=dict(primary_min=5000,native_gain=.1,quadratic_gain=.03,surprise_min=100,priority_games_min=20,numeric_tolerance=1e-4))
        m=dict(primary=6000,gain=.11,matched_quadratic_gain=.04,production_quadratic_gain=.04,gain_interval95=[.01,.2],production_quadratic_gain_interval95=[.001,.08],all_move_gain=.1,capture_target_error=0,surprise_captures=200,priority={t:dict(games=25,gain=.1) for t in PRIORITY})
        checks=dict(capture_action_error=0,native_control_max_error=1e-6)
        self.assertTrue(all(gate_result(plan,m,checks).values()))
        m['production_quadratic_gain']=.029
        self.assertFalse(all(gate_result(plan,m,checks).values()))
        m['production_quadratic_gain']=.04;m['priority'][PRIORITY[0]]['gain']=-.001
        self.assertFalse(all(gate_result(plan,m,checks).values()))


if __name__=='__main__':unittest.main()
