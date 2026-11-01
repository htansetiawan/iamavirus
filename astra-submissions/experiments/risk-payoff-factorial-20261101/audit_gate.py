#!/usr/bin/env python3
"""Audit all five arms and apply the pre-recorded integration gate."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics

from run_gate import summarize, event


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('directory',type=Path)
    args=ap.parse_args();d=args.directory
    pins=json.loads((d/'pins.json').read_text());case_path=Path(pins['cases'])
    assert sha(case_path)==pins['cases_sha256']
    expected=json.loads(case_path.read_text())['cases']
    rows=[json.loads(s) for s in (d/'results.jsonl').read_text().splitlines()]
    keys=[(r['case']['game'],r['case']['ply']) for r in rows]
    assert len(rows)==len(expected)==len(set(keys))
    assert set(keys)=={(r['game'],r['ply']) for r in expected}
    arms=pins['arms'];assert arms==['v35','raw2','cal2','raw1','cal1']
    for r in rows:
        assert set(r['arms'])==set(arms)
        assert all('error' not in x and x['legal'] for x in r['arms'].values())
    result=summarize(rows,arms);stored=json.loads((d/'summary.json').read_text())
    assert stored.pop('complete') is True and stored==result
    base,raw,cal=(result['arms'][a] for a in ('v35','raw1','cal1'))
    primary=(base['fatal_or_exchange']-cal['fatal_or_exchange']>=3 and cal['fatal']<base['fatal']
             and cal['exchange_loss']<=base['exchange_loss'] and cal['queen_exchange_loss']<=base['queen_exchange_loss'])
    calibration=(cal['fatal_or_exchange']<raw['fatal_or_exchange'] and cal['fatal']<=raw['fatal']
                 and cal['exchange_loss']<=raw['exchange_loss'] and cal['queen_exchange_loss']<=raw['queen_exchange_loss'])
    fields=['fatal','exchange_loss','queen_exchange_loss','forced_king_loss_after_capture','fatal_or_exchange']
    effects={}
    for f in fields:
        legacy=sum(int(event(r['arms']['cal2'],f))-int(event(r['arms']['raw2'],f)) for r in rows)
        ordinary=sum(int(event(r['arms']['cal1'],f))-int(event(r['arms']['raw1'],f)) for r in rows)
        effects[f]={'calibration_at_L_minus2':legacy,'calibration_at_L_minus1':ordinary,'interaction_difference':ordinary-legacy}
    ratios={}
    for arm in ('raw1','cal1','cal2'):
        control='raw1' if arm=='cal1' else 'raw2'
        ratios[arm]={'control':control,'median_paired_elapsed_ratio':statistics.median(r['arms'][arm]['elapsed']/r['arms'][control]['elapsed'] for r in rows),
                     'median_paired_node_ratio':statistics.median(r['arms'][arm]['nodes']/r['arms'][control]['nodes'] for r in rows if r['arms'][control].get('nodes',0)>0)}
    audit={'cases':len(rows),'runs':len(rows)*len(arms),'passes_vs_v35':primary,'passes_vs_raw1':calibration,
           'earns_independent_confirmation':primary and calibration,'factorial_effects':effects,'runtime':ratios,
           'summary':result,'pins_sha256':sha(d/'pins.json'),'results_sha256':sha(d/'results.jsonl'),
           'scope':'Inspected development set. Effect counts are descriptive, not an Elo estimate or a population effect.'}
    (d.parent/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k!='summary'},indent=2))


if __name__=='__main__':main()
