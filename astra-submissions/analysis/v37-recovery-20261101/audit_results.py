#!/usr/bin/env python3
"""Preserve the first result per scheduled cell and audit the completed recovery."""
import collections
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'astra-submissions/tools')]
from learning import arena_local, ingest
from resume_match_cells import first_cells, missing_cells


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    queue = ROOT/'data/arena_local/queue-v37.json'
    match = json.loads(queue.read_text())['matchups'][0]
    run = HERE/'reconciliation/run'
    status = json.loads((run/'status.json').read_text())
    assert status['state'] == 'complete' and not status['failed_cells']
    plan = json.loads((run/'plan.json').read_text())
    assert sha(queue) == plan['queue_sha256']
    hashes = {s:sha(ROOT/match[s]) for s in ('a','b')}
    assert hashes == plan['archives']
    rows, duplicates = first_cells(match, arena_local.ledger_games(match['id']), hashes)
    assert not missing_cells(match, rows, hashes)
    assert len(rows) == 100 and len(duplicates) == 3
    assert all(r['a_score'] in (0,.5,1) for r in rows)
    pair = collections.defaultdict(list)
    for r in rows: pair[r['pair']].append(r['a_score'])
    assert len(pair) == 50 and all(len(s)==2 for s in pair.values())
    means = np.array([sum(pair[p])/2 for p in sorted(pair)])
    rng = np.random.default_rng(11012026)
    bootstrap = means[rng.integers(0,50,size=(20000,50))].mean(axis=1)
    interval = np.quantile(bootstrap,[.025,.975]).tolist()
    score = float(means.mean())
    elo = lambda p: 400*math.log10(p/(1-p)) if 0<p<1 else None
    audit = []
    for r in rows:
        cell = r['pair'],r['a_colour']
        # Interrupted scheduler overwrote these paths; never attribute the
        # later duplicate's replay to the earlier retained result.
        if cell in ((39,'white'),(39,'black')):
            audit.append({'cell':cell,'status':'original replay unavailable after overwrite'})
            continue
        path = ROOT/r['replay']
        if cell == (36,'white'):
            path = HERE/'pair36-white-before-resumed-completion.json'
        payload = json.loads(path.read_bytes())
        states,errors = ingest.validate_replay(payload)
        if payload['result'] != r['result']: errors.append('result differs from first retained ledger row')
        if len(payload['frames'])-1 != r['plies']: errors.append('plies differ from first retained ledger row')
        audit.append({'cell':cell,'path':str(path.relative_to(ROOT)),'sha256':sha(path),
                      'frames':len(states),'errors':errors,'status':'verified' if not errors else 'failed'})
        if errors: raise ValueError(audit[-1])
    counts = collections.Counter(r['a_score'] for r in rows)
    by_colour = {}
    for c in ('white','black'):
        seats=[r['a_score'] for r in rows if r['a_colour']==c]
        n=collections.Counter(seats)
        by_colour[c]={'games':len(seats),'wins':n[1],'draws':n[.5],'losses':n[0],'score':sum(seats)/len(seats)}
    report={'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'matchup':match,
            'queue_sha256':sha(queue),'archive_sha256':hashes,
            'canonical_rule':'first recorded result per pair and colour, never the best result',
            'games':len(rows),'pairs':len(pair),'wins':counts[1],'draws':counts[.5],'losses':counts[0],
            'score':score,'score_95_pair_bootstrap':interval,'bootstrap_replicates':20000,'bootstrap_seed':11012026,
            'elo_point_estimate':elo(score),'elo_95_pair_bootstrap':[elo(p) for p in interval],
            'by_colour':by_colour,'termination':dict(collections.Counter(r['reason'] for r in rows)),
            'duplicates_excluded':duplicates,'recovery_status':status,'replay_audit':audit,
            'scope':'Local v37-v35 comparison only; not an arena Elo prediction or evidence against top opponents. Original replay provenance missing for two retained cells.'}
    (HERE/'canonical-games.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    report['canonical_games_sha256']=sha(HERE/'canonical-games.jsonl')
    (HERE/'final-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('replay_audit','duplicates_excluded','recovery_status')},indent=2))


if __name__=='__main__': main()
