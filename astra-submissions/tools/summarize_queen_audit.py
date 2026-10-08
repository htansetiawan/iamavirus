#!/usr/bin/env python3
"""Summarize paired selected-queen-capture diagnostics, not playing strength."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import statistics


def key(row):
    t = row['target']; return t['game'], t['side'], t['ply']


def probability(row, name='exact_capturer_occupancy'):
    return row['final']['queen'][name] / row['final']['particles']


def aggregate(rows):
    low = [r for r in rows if probability(r) < .05]
    metrics = ['exact_capturer_occupancy', 'true_attacker_union_occupancy',
               'own_move_allowed', 'own_move_loses_king', 'geometric_threat',
               'queen_capture_allowed', 'queen_capture_survives',
               'actual_capture_allowed', 'actual_capture_survives']
    return {'events':len(rows), 'mean_population_mass':
            {m:statistics.mean(probability(r,m) for r in rows) for m in metrics} if rows else {},
            'exact_mass_bands':dict(Counter('below_0.05' if probability(r)<.05 else
                '0.05_to_below_0.3' if probability(r)<.3 else 'at_least_0.3' for r in rows)),
            'true_capture_loses_opponent_king':sum(not r['final']['queen']['actual_capturing_side_survived'] for r in rows),
            'low_mass_diagnosis':{
                'events':len(low), 'never_seen':sum(r['last_seen_ply']<0 for r in low),
                'any_collapse':sum(bool(r['collapses']) for r in low),
                'zero_mass':sum(r['final']['tracked_held']==0 for r in low),
                'seen_then_collapsed':sum(r['last_seen_ply']>=0 and bool(r['collapses_after_last_seen']) for r in low),
                'capturer_never_moved':sum(r['last_capturer_move_ply']==0 for r in low),
                'capturer_stationary_at_least_10_plies':sum(r['target']['ply']-r['last_capturer_move_ply']>=10 for r in low),
                'last_low_crossing_was_collapse':sum(bool(r['last_low_crossing']) and r['last_low_crossing']['collapsed'] for r in low),
                'last_low_crossing_after_own_move':sum(bool(r['last_low_crossing']) and r['last_low_crossing']['after_own_move'] for r in low),
                'capturer_types':dict(Counter(r['target']['capturer_piece'].upper() for r in low))}}


def paired(control, candidate, seed=20261008):
    if set(control)!=set(candidate):
        raise ValueError('comparison must have identical game seats')
    ids = sorted(control)
    if len({k[0] for k in ids}) != len(ids):
        raise ValueError('this bootstrap expects one seat per game')
    metrics = {m:(lambda r, m=m:probability(r,m)) for m in
               ['exact_capturer_occupancy','true_attacker_union_occupancy','queen_capture_survives']}
    metrics['mass_below_0.05'] = lambda r:float(probability(r)<.05)
    result = {}
    for m, value in metrics.items():
        differences = [value(candidate[k])-value(control[k]) for k in ids]
        rng = random.Random(seed)
        samples = sorted(statistics.mean(rng.choices(differences,k=len(ids))) for _ in range(10000))
        result[m] = {'candidate_minus_control':statistics.mean(differences),
                     'paired_game_bootstrap_95':[samples[249],samples[9749]]}
    return {'games':len(ids),'metrics':result}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control-run',type=Path,required=True)
    parser.add_argument('--candidate-run',type=Path)
    parser.add_argument('--control-prediction',type=int,default=0)
    parser.add_argument('--candidate-prediction',type=int,default=1)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    states=[];arms=[];provenance=[]
    for path,mode in [(args.control_run,args.control_prediction),
                      (args.candidate_run or args.control_run,args.candidate_prediction)]:
        state=json.loads((path/'state.json').read_text())
        if state['state']!='complete' or state['failed_runs'] or not state['inputs_unchanged']:
            raise ValueError('incomplete or changed run')
        rows=[json.loads(s) for s in (path/'runs.jsonl').read_text().splitlines()]
        rows=[r for r in rows if r['prediction']==mode and r['complete']]
        if len(rows)!=state['seats']:
            raise ValueError('missing arm rows')
        states.append(state);arms.append({key(r):r for r in rows})
        provenance.append({'run':str(path),'prediction':mode,'state':state,
                           'runs_sha256':hashlib.sha256((path/'runs.jsonl').read_bytes()).hexdigest()})
    for field in ['probe_sha256','targets_sha256','seats','particles','seed','limit']:
        if states[0][field]!=states[1][field]:raise ValueError('unmatched '+field)
    groups={}
    for label,select in [('all_selected',lambda r:True),
                         ('opponent_survives_actual_capture',lambda r:r['final']['queen']['actual_capturing_side_survived']),
                         ('arena_v13',lambda r:r['target']['arena_version']==13)]:
        selected=[{k:r for k,r in arm.items() if select(r)} for arm in arms]
        groups[label]={'control':aggregate(list(selected[0].values())),
                       'candidate':aggregate(list(selected[1].values())),
                       'paired':paired(*selected)}
    result={'provenance':provenance,'groups':groups,
            'denominators':'All mean masses divide raw counts by the full equal-weight particle population. Own-move support and immediate king loss are reported separately. No conditional denominator is silently substituted.',
            'limitations':['Selected/inspected queen-capture events; not natural-frequency calibration, move selection, or Elo.',
                           'Primary comparison retains every event selected for this run; surviving-opponent and arena-v13 breakdowns are diagnostic.',
                           'One belief seed. Bootstrap intervals reflect sampled games, not particle-seed variation.',
                           'A geometric or allowed capture may lose the capturing king. Surviving captures exclude worlds already terminal after our move.',
                           'After-own-move low support combines ApplyOurMove and subsequent observation conditioning; this audit does not separate them.']}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'output':str(args.output),'paired':groups['all_selected']['paired']}))


if __name__=='__main__':main()
