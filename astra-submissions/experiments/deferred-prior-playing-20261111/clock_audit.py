"""Read referee clocks and native search counters from completed local games."""
from argparse import ArgumentParser
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from statistics import median

ROOT = Path(__file__).resolve().parents[3]
SEARCH = re.compile(r'^mist: n=(?P<decision>\d+) \|P\|=(?P<worlds>\d+)(?P<capped>\(capped\))? '
                    r'samples=\d+ moves=\d+ infosets=\d+ nodes=(?P<nodes>\d+) iters=\d+ .*? sf=(?P<calls>\d+)/[0-9.]+s ',
                    re.MULTILINE)
COLORS = ('white','black')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def audit_game(game, job):
    frames = game['frames']
    tc = game['timeControl']
    assert tc==dict(baseSeconds=180,incrementSeconds=2) and frames[0]['clocks']==[180,180]
    assert [(r['side'],r['status']) for r in game['localNativeStockfishReadiness']]==[('white','ready'),('black','ready')]
    elapsed = [[],[]]
    for ply,(before,after) in enumerate(zip(frames,frames[1:]),1):
        mover = (ply-1)%2
        old,new = before['clocks'],after['clocks']
        assert after['ply']==ply and all(math.isfinite(x) and x>=0 for x in new)
        assert old[1-mover]==new[1-mover]
        seconds = old[mover]+tc['incrementSeconds']-new[mover]
        assert -1e-6<=seconds<=old[mover]+1e-6
        elapsed[mover].append(max(0.,seconds))
    seat = {}
    for i,color in enumerate(COLORS):
        text = game['privateDiagnostics'][color]
        parsed = list(SEARCH.finditer(text))
        assert len(parsed)<=len(elapsed[i]) and elapsed[i]
        assert [int(row['decision']) for row in parsed]==list(range(1,len(parsed)+1))
        calls = [int(row['calls']) for row in parsed]
        assert calls==sorted(calls)
        total = math.fsum(elapsed[i])
        seat[color] = dict(moves=len(elapsed[i]), seconds=total, median_move_seconds=median(elapsed[i]),
                           first_move_seconds=elapsed[i][0], remaining_seconds=frames[-1]['clocks'][i],
                           reported_searches=len(parsed), total_nodes=sum(int(row['nodes']) for row in parsed),
                           total_stockfish_calls=calls[-1] if calls else 0,
                           capped_searches=sum(bool(row['capped']) for row in parsed),
                           median_belief_worlds=median(int(row['worlds']) for row in parsed) if parsed else None)
    return dict(game=job['id'],pair=job['pair'],candidate_color=job['side'],by_color=seat)


def summarize(out):
    plan = read(out/'plan.json')
    result = read(out/'result.json')
    assert sha(out/'plan.json')==result['plan_sha256']
    pairs = defaultdict(dict)
    verified = []
    for job in plan['jobs']:
        game_dir = Path(plan['store'])/'jobs'/job['id']
        record = game_dir/'result.json'
        if not record.exists():
            continue
        record = read(record)
        if record['faults'] or record['score'] is None:
            continue
        replay = game_dir/'replay.json'
        assert record['replay_sha256']==sha(replay) and record['job']==job
        checked = audit_game(read(replay),job)
        pairs[job['pair']][job['side']] = checked
        verified.append(checked)
    assert len(verified)==result['games']
    paired = [[],[]]
    for legs in pairs.values():
        if set(legs)!=set(COLORS):
            continue
        for i,color in enumerate(COLORS):
            candidate = legs[color]['by_color'][color]
            reference = legs[COLORS[1-i]]['by_color'][color]
            paired[i].append(dict(first_move_difference=candidate['first_move_seconds']-reference['first_move_seconds'],
                                  total_seconds_difference=candidate['seconds']-reference['seconds'],
                                  nodes_difference=candidate['total_nodes']-reference['total_nodes']))
    clocks = {color:{key:median(row[key] for row in paired[i]) for key in paired[i][0]} if paired[i] else {}
              for i,color in enumerate(COLORS)}
    aggregate = {}
    for name in ('candidate','reference'):
        seats = [g['by_color'][g['candidate_color'] if name=='candidate' else COLORS[1-COLORS.index(g['candidate_color'])]] for g in verified]
        aggregate[name] = {key:sum(s[key] for s in seats) for key in
                           ('moves','reported_searches','total_nodes','total_stockfish_calls','capped_searches')}
    return dict(at=datetime.now(timezone.utc).isoformat(),games=len(verified),complete_pairs=len(paired[0]),
                result_sha256=sha(out/'result.json'),aggregate=aggregate,paired_median_differences=clocks,
                scope='Descriptive elapsed clocks and native diagnostics on actual game paths. Different positions, legal moves and seeds affect workload. The playing gate uses the independent game result only.')


def main():
    parser = ArgumentParser()
    parser.add_argument('--trial',choices=('last-only-fresh-pilot-20261110','deferred-prior-playing-20261111'),
                        default='deferred-prior-playing-20261111')
    parser.add_argument('--write',action='store_true')
    args = parser.parse_args()
    out = ROOT/'astra-submissions/analysis'/args.trial
    summary = json.dumps(summarize(out),indent=2,allow_nan=False)+'\n'
    if args.write:
        with (out/'clock-audit.json').open('x') as stream:
            stream.write(summary)
    print(summary,end='',flush=True)


if __name__=='__main__':
    main()
