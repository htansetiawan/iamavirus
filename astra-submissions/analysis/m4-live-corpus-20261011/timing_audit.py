#!/usr/bin/env python3
"""Identify unusually fast responses from replay clocks, without source guesses."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import statistics

ap=argparse.ArgumentParser();ap.add_argument('--replays',type=Path,required=True);args=ap.parse_args()
root=Path(__file__).resolve().parent
rows=json.loads(gzip.decompress((root/'audits.json.gz').read_bytes()))
sources={s['game']:s for s in json.loads((root/'summary.json').read_text())['sources']}
times=[];fast=[]
for row in rows:
    path=args.replays/(row['id']+'.json.gz')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sources[row['id']]['sha256']
    replay=json.loads(gzip.decompress(path.read_bytes()));index=0 if row['side']=='white' else 1
    for d in row['decisions']:
        ply=d['ply'];before=replay['frames'][ply]['clocks'][index]
        after=replay['frames'][ply+1]['clocks'][index]
        elapsed=before+replay['timeControl']['incrementSeconds']-after
        assert elapsed>=-.001
        times.append(elapsed)
        if elapsed<.05:
            fast.append({'game':row['id'],'side':row['side'],'ply':ply,'move':d['move'],
                'elapsed_seconds':elapsed,'clock_before':before,'clock_after':after,
                'fatal':d['immediate_loss'],'unchanged_view':not d['opponent_move_changed_view']})
report={'decisions':len(times),'median_seconds':statistics.median(times),'fast_threshold_seconds':.05,
        'fast_responses':fast,'fast_fatal':sum(r['fatal'] for r in fast),
        'limitation':'Clock-derived elapsed times; no inference about internal fast-return branches.'}
(root/'timing.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
