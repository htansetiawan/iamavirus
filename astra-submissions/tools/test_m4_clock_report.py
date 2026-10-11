#!/usr/bin/env python3
"""Instrumentation checks; tiny fixtures are not chess-strength evidence."""
import copy
import json
from pathlib import Path
import tempfile

from m4_clock_run import inspect_game


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
    print('test_m4_clock_report: exact ply coverage, duplicates, option evidence and search/evaluator/clock faults passed')


if __name__=='__main__':main()
