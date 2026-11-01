#!/usr/bin/env python3
"""Check the frozen four-arm screen and apply its recorded acceptance rule."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics

from run_replay_gate import ROOT, event, summarize


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('directory',type=Path)
    args=ap.parse_args();directory=args.directory
    pins=json.loads((directory/'pins.json').read_text())
    case_path=Path(pins['cases'])
    assert sha(case_path)==pins['cases_sha256']
    cases=json.loads(case_path.read_text())['cases']
    rows=[json.loads(s) for s in (directory/'results.jsonl').read_text().splitlines()]
    expected={(c['game'],c['ply']) for c in cases}
    observed=[(r['case']['game'],r['case']['ply']) for r in rows]
    assert len(rows)==len(cases)==len(set(observed)) and set(observed)==expected
    arms=pins['arms'];assert arms==['v35','off','mixture','residual']
    for r in rows:
        assert set(r['arms'])==set(arms)
        assert all('error' not in a and a['legal'] for a in r['arms'].values())
    report=summarize(rows,arms)
    stored=json.loads((directory/'summary.json').read_text());assert stored.pop('complete') is True
    assert report==stored
    decision={}
    for arm in ('mixture','residual'):
        candidate,baseline,off=(report['arms'][a] for a in (arm,'v35','off'))
        primary=(baseline['fatal_or_exchange']-candidate['fatal_or_exchange']>=3
                 and candidate['fatal']<baseline['fatal']
                 and candidate['exchange_loss']<=baseline['exchange_loss']
                 and candidate['queen_exchange_loss']<=baseline['queen_exchange_loss'])
        decision[arm]={'passes_preregistered_screen':primary,
                       'net_combined_fixes_vs_v35':baseline['fatal_or_exchange']-candidate['fatal_or_exchange'],
                       'net_combined_fixes_vs_off':off['fatal_or_exchange']-candidate['fatal_or_exchange'],
                       'median_paired_elapsed_ratio_vs_off':statistics.median(r['arms'][arm]['elapsed']/r['arms']['off']['elapsed'] for r in rows),
                       'median_paired_nodes_ratio_vs_off':statistics.median(r['arms'][arm]['nodes']/r['arms']['off']['nodes'] for r in rows if r['arms']['off'].get('nodes',0)>0)}
    changes=[]
    for r in rows:
        baseline=r['arms']['v35']
        for arm in ('off','mixture','residual'):
            v=r['arms'][arm]
            fields=['fatal','exchange_loss','queen_exchange_loss','forced_king_loss_after_capture','fatal_or_exchange']
            changed=[f for f in fields if event(baseline,f)!=event(v,f)]
            if changed:changes.append({'game':r['case']['game'],'ply':r['case']['ply'],'arm':arm,
                                       'changed_labels':changed,'v35':baseline,'candidate':v})
    audit={'cases':len(rows),'runs':len(rows)*len(arms),'decisions':decision,'changes':changes,
           'summary':report,'pins_sha256':sha(directory/'pins.json'),
           'results_sha256':sha(directory/'results.jsonl'),
           'scope':'Development screen, not held-out strength. No release follows a failed screen.'}
    (directory.parent/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({'cases':audit['cases'],'runs':audit['runs'],'decisions':decision},indent=2))


if __name__=='__main__':main()
