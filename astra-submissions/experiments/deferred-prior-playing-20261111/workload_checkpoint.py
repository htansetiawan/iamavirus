"""Describe search work in already verified games without changing the gate."""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import json
import re
from statistics import median

from clock_audit import COLORS, SEARCH, audit_game, read, sha

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'astra-submissions/analysis/deferred-prior-playing-20261111'
MOVE = re.compile(r' move=([a-h][1-8][a-h][1-8][qrbn]?)$')
THINNING = re.compile(r'^mist: clock [0-9.]+ s: P thinned from (\d+) to (\d+) before the update$',re.MULTILINE)
REBUILT = re.compile(r'^mist: belief empty, rebuilt \d+ positions from the view \(rebuild \d+\)$',re.MULTILINE)


def decision_rows(replay):
    frames = replay['frames']
    elapsed = [[],[]]
    for ply,(old,new) in enumerate(zip(frames,frames[1:]),1):
        side = (ply-1)%2
        seconds = old['clocks'][side]+2-new['clocks'][side]
        elapsed[side].append(dict(seconds=max(0.,seconds),move=new['move'],ply=ply))
    for side,color in enumerate(COLORS):
        trace = replay['privateDiagnostics'][color].splitlines()
        searches = [(SEARCH.match(line),MOVE.search(line)) for line in trace if line.startswith('mist: n=')]
        assert len(searches)==len(elapsed[side])
        for i,((stat,move),item) in enumerate(zip(searches,elapsed[side]),1):
            assert stat and move and int(stat['decision'])==i and move[1]==item['move']
            item.update(nodes=int(stat['nodes']),worlds=int(stat['worlds']),capped=bool(stat['capped']))
    return elapsed


def update_counts(replay, color):
    text = replay['privateDiagnostics'][color]
    thinned = [(int(before),int(after)) for before,after in THINNING.findall(text)]
    assert all(before>after for before,after in thinned)
    return dict(clock_thinnings=len(thinned),parents_before=sum(before for before,_ in thinned),
                parents_retained=sum(after for _,after in thinned),rebuilds=len(REBUILT.findall(text)))


def describe(rows):
    assert rows
    return dict(decisions=len(rows),median_seconds=median(row['seconds'] for row in rows),
                median_nodes=median(row['nodes'] for row in rows),median_worlds=median(row['worlds'] for row in rows),
                capped_decisions=sum(row['capped'] for row in rows),total_nodes=sum(row['nodes'] for row in rows),
                total_seconds=sum(row['seconds'] for row in rows))


def main():
    verified = read(OUT/'first-four-verification.json')
    plan = read(OUT/'plan.json')
    assert verified['plan_sha256']==sha(OUT/'plan.json')
    jobs = {job['id']:job for job in plan['jobs']}
    pool = {name:[] for name in ('candidate','reference')}
    updates = {name:defaultdict(int) for name in pool}
    paired = defaultdict(dict)
    for receipt in verified['games']:
        job = jobs[receipt['game']]
        path = Path(plan['store'])/'jobs'/job['id']/'replay.json'
        assert sha(path)==receipt['replay_sha256']
        replay = read(path)
        audit_game(replay,job)
        rows = decision_rows(replay)
        own = COLORS.index(job['side'])
        pool['candidate'].extend(rows[own])
        pool['reference'].extend(rows[1-own])
        for name,color in (('candidate',COLORS[own]),('reference',COLORS[1-own])):
            for key,value in update_counts(replay,color).items():
                updates[name][key] += value
        paired[job['pair']][job['side']] = (replay,rows)
    shared = {'candidate':[],'reference':[]}
    pair_sizes = []
    for pair,legs in sorted(paired.items()):
        assert set(legs)==set(COLORS)
        w,wrows = legs['white']
        b,brows = legs['black']
        matched = 0
        for ply,(white,black) in enumerate(zip(w['frames'],b['frames'])):
            if ply==min(len(w['frames']),len(b['frames']))-1:
                break
            assert all(white[key]==black[key] for key in ('board','white','black'))
            side = ply%2
            candidate,reference = (wrows,brows) if side==0 else (brows,wrows)
            shared['candidate'].append(candidate[side][ply//2])
            shared['reference'].append(reference[side][ply//2])
            matched += 1
            if w['frames'][ply+1]['move']!=b['frames'][ply+1]['move']:
                break
        pair_sizes.append(dict(pair=pair,common_prefix_decisions=matched))
    report = dict(at=datetime.now(timezone.utc).isoformat(),verified_games=len(verified['games']),
                  first_four_receipt_sha256=sha(OUT/'first-four-verification.json'),
                  all_moves={key:dict(**describe(value),**updates[key]) for key,value in pool.items()},
                  shared_prefix={key:describe(value) for key,value in shared.items()},
                  common_by_pair=pair_sizes,
                  scope='Descriptive early checkpoint. Shared prefixes match observed and true board history. Seeds and elapsed clocks may differ. Divergent game paths and the small sample limit attribution. This diagnostic does not affect the playing gate.')
    with (OUT/'first-four-workload.json').open('x') as stream:
        json.dump(report,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
