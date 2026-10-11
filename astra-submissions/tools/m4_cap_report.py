#!/usr/bin/env python3
"""Audit and summarize fixed-prior, paired cap-mode replay results."""
import argparse
import gzip
import json
from pathlib import Path
import numpy as np
from m4_prior_fit import bootstrap


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--early-audits',type=Path,required=True);ap.add_argument('--fresh-audits',type=Path,required=True)
    args=ap.parse_args();plan=json.loads((args.run/'manifest.json').read_text());modes=plan['modes']
    labels={};cohort={};rows={mode:[] for mode in modes};batch_reports={};parity={}
    for batch,path in [('sequential02',args.early_audits),('sequential-fresh26',args.fresh_audits)]:
        audits=json.loads(gzip.open(path,'rt').read());audits={g['id']:g for g in audits}
        selected=json.loads((args.run/batch/'input-manifest.json').read_text())['games'];expected=set()
        for g in selected:
            cohort[g['id']]=g['cohort']
            for d in audits[g['id']]['decisions']:
                key=(g['id'],d['ply']);assert key not in labels;labels[key]=d;expected.add(key)
        for mode in modes:
            status=json.loads((args.run/batch/f'mode{mode}-status.json').read_text());assert status['returncode']==0
            rr=[json.loads(s) for s in (args.run/batch/f'mode{mode}.jsonl').read_text().splitlines()]
            assert len(rr)==len(expected) and {(r['game'],r['ply']) for r in rr}==expected
            for r in rr:
                d=labels[r['game'],r['ply']]
                assert r['move']==d['move'] and r['actual_fatal']==d['immediate_loss']
                assert r['actual_attack']==bool(d['attackers_before']) and r['inconsistent']==r['cheap_calls']==0
                assert all(0<=r[k]<=1.000001 for k in ['truth_share','attack_probability','fatal_probability'])
            rows[mode].extend(rr)
        batch_reports[batch]=dict(games=len(selected),decisions=len(expected),all_independent_labels_match=True)
    control=0 if 0 in modes else 1
    a=rows[control];keys=[(r['game'],r['ply']) for r in a]
    for mode in modes:assert keys==[(r['game'],r['ply']) for r in rows[mode]]
    if 0 in modes and 1 in modes:
        def stripped(rr):return [{k:v for k,v in r.items() if k!='update_cpu_seconds'} for r in rr]
        assert stripped(rows[0])==stripped(rows[1]);parity['original_vs_heap_all_rows']=True
    selections={'primary42':np.array([cohort[r['game']]!='diagnostic' for r in a]),
                'all_including_extra_diagnostic':np.ones(len(a),bool),
                'fresh26':np.array([cohort[r['game']]=='fresh_all' for r in a]),
                'primary_unchanged_view':np.array([cohort[r['game']]!='diagnostic' and not labels[r['game'],r['ply']]['opponent_move_changed_view'] for r in a])}
    output=dict(seed=plan['seed'],cap=plan['cap'],classification='Offline belief, same historical moves; no Elo inference',
                parity=parity,batches=batch_reports,cohorts={})
    for name,sel in selections.items():
        ii=np.flatnonzero(sel);group=np.array([a[i]['game'] for i in ii]);report={}
        for mode,rr in rows.items():
            rsel=[rr[i] for i in ii];last={r['game']:r for r in rsel}
            item=dict(games=len(last),decisions=len(ii),truth_present=sum(r['truth_present'] for r in rsel),
                collapses=sum(r['collapses'] for r in last.values()),rebuilds=sum(r['rebuilds'] for r in last.values()),
                empty_belief=sum(r['worlds']==0 for r in rsel),
                update_cpu_seconds=sum(r['update_cpu_seconds'] for r in last.values()))
            for metric in ['attack','fatal']:
                p=np.array([r[metric+'_probability'] for r in rsel]);y=np.array([r['actual_'+metric] for r in rsel])
                item[metric]=dict(expected=float(p.sum()),actual=int(y.sum()),brier=float(np.mean((p-y)**2)))
            report['mode'+str(mode)]=item
        b=rows[2];paired={}
        for metric in ['attack','fatal']:
            delta=np.array([(a[i][metric+'_probability']-a[i]['actual_'+metric])**2-
                           (b[i][metric+'_probability']-b[i]['actual_'+metric])**2 for i in ii])
            paired[metric+'_brier_reduction']=bootstrap(delta,group)
        paired['truth_support_gain']=bootstrap(np.array([b[i]['truth_present']-a[i]['truth_present'] for i in ii]),group)
        report['paired']=paired;output['cohorts'][name]=report
    output['traps']={gid:{'mode'+str(mode):[r for r in rr if r['game']==gid and r['actual_fatal']]
                        for mode,rr in rows.items()} for gid in ['gjlnku86','c4ak2ldi','qkb2exm9']}
    (args.run/'report.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output['cohorts']['primary42'],indent=2))


if __name__=='__main__':main()
