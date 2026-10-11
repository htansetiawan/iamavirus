#!/usr/bin/env python3
"""Instrumentation checks; tiny fixtures are not chess-strength evidence."""
import copy
import json
from pathlib import Path
import tempfile

from m4_clock_run import inspect_game, summarize


def main():
    game={'result':'1-0','reason':'fixture','frames':[
        {'ply':0,'clocks':[180,180]}, {'ply':1,'clocks':[179,180]},
        {'ply':2,'clocks':[179,179]}], 'privateDiagnostics':{'white':
        'mist-m4: ok=1 ply=0 carry=7 snapshot=1 over=0\n'
        'm4-eval: ready=1 failed=0 scale=1\n'
        'm4-setup: ply=0 cheap_carried_roots=7\n'}}
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/'game.json'
        def check(g):
            path.write_text(json.dumps(g))
            return inspect_game(path,{'side':'white','scale':1},{'fast_roots':True})
        valid=check(game);assert valid['faults']==[] and valid['cheap_carried_roots']==7
        bad=copy.deepcopy(game);bad['privateDiagnostics']['white']=bad['privateDiagnostics']['white'].replace('m4-setup:', 'unrecognized:')
        assert 'missing_fast_root_diagnostics' in check(bad)['faults']
        bad=copy.deepcopy(game);bad['privateDiagnostics']['white']=bad['privateDiagnostics']['white'].replace('ply=0','ply=2',1)
        assert 'missing_m4_diagnostics' in check(bad)['faults']
        bad=copy.deepcopy(game);bad['privateDiagnostics']['white']+='mist-m4: ok=1 ply=0 carry=7 snapshot=1 over=0\n'
        assert 'missing_m4_diagnostics' in check(bad)['faults']
        bad=copy.deepcopy(game);bad['privateDiagnostics']['white']=bad['privateDiagnostics']['white'].replace('ok=1','ok=0').replace('over=0','over=1').replace('ready=1','ready=0')
        assert {'m4_snapshot_or_search_failure','m4_reported_overrun','stockfish_request_failure'}<=set(check(bad)['faults'])
        # Requested solver scheduling must be evidenced on every actual turn.
        path.write_text(json.dumps(game));job={'side':'white','scale':1,'settle_fraction':.2}
        assert 'missing_settling_diagnostics' in inspect_game(path,job)['faults']
        good=copy.deepcopy(game);good['privateDiagnostics']['white']+='m4-settle: ply=0 prefix=0 fraction=0.200000 iterations=20 nodes=100 expansions=3 seconds=0.060000\n'
        path.write_text(json.dumps(good));result=inspect_game(path,job)
        assert not result['faults'] and result['settled_decisions']==1 and result['settle_seconds']==.06
        bad=copy.deepcopy(good);bad['privateDiagnostics']['white']=bad['privateDiagnostics']['white'].replace('fraction=0.200000','fraction=0.100000')
        path.write_text(json.dumps(bad));assert 'wrong_settling_configuration' in inspect_game(path,job)['faults']
        # A configured policy intervention must actually execute on every ply.
        job={'side':'white','scale':1,'root_dominance':1}
        path.write_text(json.dumps(game))
        assert 'missing_dominance_diagnostics' in inspect_game(path,job)['faults']
        good=copy.deepcopy(game);good['privateDiagnostics']['white']+='m4-dominance: ply=0 complete=1 redirected=2 changed=1 skipped=0\n'
        path.write_text(json.dumps(good));result=inspect_game(path,job)
        assert not result['faults'] and result['dominance_profiled']==1 and result['dominance_changed']==1
        assert 'unexpected_dominance_diagnostics' in inspect_game(path,{'side':'white','scale':1})['faults']
        bad=copy.deepcopy(good);bad['privateDiagnostics']['white']=bad['privateDiagnostics']['white'].replace('redirected=2','redirected=0')
        path.write_text(json.dumps(bad));assert 'dominance_profile_failure' in inspect_game(path,job)['faults']
        good=copy.deepcopy(game);good['privateDiagnostics']['white']+='m4-dominance: ply=0 complete=0 redirected=0 changed=0 skipped=1\n'
        path.write_text(json.dumps(good));result=inspect_game(path,job)
        assert not result['faults'] and result['dominance_skipped']==1 and result['dominance_changed']==0
        # Same scale, different scheduling arms must never be pooled.
        root=Path(d);(root/'jobs').mkdir()
        for i,(arm,score) in enumerate([('scale1-settle0',0),('scale1-settle0.2',1)]):
            folder=root/'jobs'/str(i);folder.mkdir()
            (folder/'receipt.json').write_text(json.dumps({'scale':1,'arm':arm,'faults':[],'game':{'score':score}}))
        report=summarize(root,{'jobs':[{},{}],'classification':'fixture'})
        assert report['complete'] and len(report['totals'])==2
        assert report['totals']['scale1-settle0.2']['wins']==1
        assert report['totals']['scale1-settle0']['losses']==1
    print('test_m4_clock_report: exact ply coverage, duplicates, option evidence and search/evaluator/clock faults passed')


if __name__=='__main__':main()
