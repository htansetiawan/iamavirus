#!/usr/bin/env python3
"""Paired sequential-belief metrics, checked against independent referee labels."""
import argparse
import gzip
import json
from pathlib import Path
import numpy as np
from m4_prior_fit import bootstrap


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--audits',type=Path,required=True);args=ap.parse_args()
    manifest=json.loads((args.run/'manifest.json').read_text())
    labels={r['id']:r for r in json.loads(gzip.open(args.audits,'rt').read())}
    decisions={(gid,d['ply']):d for gid,r in labels.items() for d in r['decisions']}
    rows={};checks={}
    for model in ['control26','visibility32']:
        status=json.loads((args.run/(model+'-status.json')).read_text());assert status['returncode']==0
        rows[model]=[json.loads(s) for s in (args.run/(model+'.jsonl')).read_text().splitlines()]
        expected={(g['id'],d['ply']) for g in manifest['games'] for d in labels[g['id']]['decisions']}
        found={(r['game'],r['ply']) for r in rows[model]};assert expected==found
        assert len(found)==len(rows[model])
        for r in rows[model]:
            d=decisions[r['game'],r['ply']]
            assert r['actual_fatal']==d['immediate_loss'] and r['actual_attack']==bool(d['attackers_before'])
            assert r['move']==d['move'] and r['inconsistent']==0 and r['cheap_calls']==0
            assert all(0<=r[k]<=1.000001 for k in ['truth_share','attack_probability','fatal_probability'])
        checks[model]=dict(decisions=len(found),all_independent_fatal_and_attack_labels_match=True,
                          all_belief_observations_match=True,only_full_model_used=True)
    a,b=rows['control26'],rows['visibility32']
    assert [(r['game'],r['ply']) for r in a]==[(r['game'],r['ply']) for r in b]
    cohorts={g['id']:g['cohort'] for g in manifest['games']};out=dict(checks=checks,cohorts={})
    primary=manifest.get('primary_cohort','random16')
    for label,select in [(primary,lambda r:cohorts[r['game']]==primary),
                          ('all_with_diagnostic',lambda r:True),
                          (primary+'_unchanged',lambda r:cohorts[r['game']]==primary and not decisions[r['game'],r['ply']]['opponent_move_changed_view'])]:
        indices=[i for i,r in enumerate(a) if select(r)];group=np.array([a[i]['game'] for i in indices]);rpt={}
        for model,rr in rows.items():
            selected=[rr[i] for i in indices];last={}
            for r in selected:last[r['game']]=r
            d=dict(games=len(last),decisions=len(selected),truth_present=sum(r['truth_present'] for r in selected),
                empty_belief=sum(r['worlds']==0 for r in selected),rebuilds=sum(r['rebuilds'] for r in last.values()),
                collapses=sum(r['collapses'] for r in last.values()),update_cpu_seconds=sum(r['update_cpu_seconds'] for r in last.values()))
            for metric in ['attack','fatal']:
                pred=np.array([r[metric+'_probability'] for r in selected]);y=np.array([r['actual_'+metric] for r in selected])
                d[metric]=dict(expected=float(pred.sum()),actual=int(y.sum()),brier=float(np.mean((pred-y)**2)))
            rpt[model]=d
        paired={}
        for metric in ['attack','fatal']:
            delta=np.array([(a[i][metric+'_probability']-a[i]['actual_'+metric])**2-
                           (b[i][metric+'_probability']-b[i]['actual_'+metric])**2 for i in indices])
            paired[metric+'_brier_reduction']=bootstrap(delta,group)
        paired['truth_support_gain']=bootstrap(np.array([b[i]['truth_present']-a[i]['truth_present'] for i in indices]),group)
        rpt['paired']=paired;out['cohorts'][label]=rpt
    out['diagnosed_traps']={gid:{model:[r for r in rr if r['game']==gid and r['actual_fatal']]
                                for model,rr in rows.items()} for gid in ['gjlnku86','c4ak2ldi']}
    out['limitations']=['Fixed historical policy and fixed 10k cap; no search or clock-driven thinning.',
        'Small game sample with few positives; bootstrap intervals are descriptive.',
        'Truth is confined to audit labels; played moves and observations drive belief updates.',
        'A better move-prior likelihood is not a demonstrated playing-strength gain.']
    (args.run/'report.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out['cohorts'][primary],indent=2))


if __name__=='__main__':main()
