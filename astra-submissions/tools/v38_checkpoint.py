"""Audit saved public listing pages and describe schedule-matched v38 results."""
from collections import defaultdict
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import sys

TEAM = 'a2c35173659545c99752376a70418438'
REFERENCE = .543


def load(directory, pattern, version):
    pages = [json.loads(p.read_text()) for p in sorted(directory.glob(pattern))]
    assert pages
    games = [g for page in pages for g in page['games']]
    assert len(games) == len({g['id'] for g in games}) == pages[0]['summary']['total']
    assert pages[-1]['nextCursor'] is None
    for g in games:
        side = 'white' if g['whitePlayerId'] == TEAM else 'black'
        other = 'black' if side == 'white' else 'white'
        assert g[side+'PlayerId'] == TEAM and g[side+'Version'] == version
        assert g['result'] in ('1-0', '0-1', '1/2-1/2')
        g['side'] = side
        g['score'] = .5 if g['result'] == '1/2-1/2' else float(g['result'] == ('1-0' if side == 'white' else '0-1'))
        g['opponent'] = g[other]
        g['stratum'] = (g[other+'PlayerId'], g[other+'Version'], side)
    result = stats(games)
    assert all(result[k] == pages[0]['summary']['team1'][k] for k in ('wins', 'draws', 'losses'))
    return sorted(games, key=lambda g: (datetime.fromisoformat(g['createdAt']), g['id']))


def stats(games):
    scores = [g['score'] for g in games]
    return dict(games=len(scores), wins=scores.count(1), draws=scores.count(.5),
                losses=scores.count(0), points=sum(scores),
                score=sum(scores)/len(scores) if scores else None)


def matched(candidate, baseline):
    c, b = defaultdict(list), defaultdict(list)
    for g in candidate: c[g['stratum']].append(g)
    for g in baseline: b[g['stratum']].append(g)
    rows = []
    for key, games in sorted(c.items()):
        if key not in b: continue
        cs, bs = stats(games), stats(b[key])
        rows.append(dict(opponent=games[0]['opponent'], opponent_id=key[0], opponent_version=key[1],
                         our_side=key[2], candidate=cs, baseline=bs,
                         expected_points=cs['games']*bs['score']))
    count = sum(r['candidate']['games'] for r in rows)
    actual = sum(r['candidate']['points'] for r in rows)
    expected = sum(r['expected_points'] for r in rows)
    return dict(matched_games=count, unmatched_games=len(candidate)-count,
                candidate_score=actual/count if count else None,
                baseline_expected_score=expected/count if count else None,
                difference=(actual-expected)/count if count else None, rows=rows,
                limitation='Historical opponent-version/color standardization; sparse cells, opponent drift and time confounding remain. No causal or significance claim.')


def main():
    directory = Path(sys.argv[1])
    candidate = load(directory, 'games-*.json', 38)
    baseline = load(directory, 'baseline-v37-*.json', 37)
    checks = {}
    for n in (48, 300):
        if len(candidate) < n: continue
        s = stats(candidate[:n]); s['z_vs_fixed_reference'] = (s['points']-REFERENCE*n)/math.sqrt(.25*n)
        s['last_completed_at'] = candidate[n-1]['createdAt']
        s['retain_under_declared_rule'] = s['z_vs_fixed_reference'] > -2 if n == 48 else s['score'] >= REFERENCE
        checks[str(n)] = s
    unusual = [g for g in candidate if g['reason'] not in ('King capturable', 'Threefold repetition', 'Fifty-move rule', '50-move rule', 'Move limit reached', 'No legal moves', 'Stalemate', 'Insufficient material')]
    opponents = defaultdict(list)
    for g in candidate: opponents[(g['opponent'],g['stratum'][1])].append(g)
    result = dict(candidate=stats(candidate), baseline=stats(baseline), fixed_reference=REFERENCE,
                  checkpoints=checks, color={s:stats([g for g in candidate if g['side']==s]) for s in ('white','black')},
                  opponents=[dict(opponent=k[0], version=k[1], **stats(v)) for k,v in sorted(opponents.items())],
                  unusual_endings=[{k:g[k] for k in ('id','side','opponent','reason','score','createdAt')} for g in unusual],
                  matched=matched(candidate,baseline),
                  first_300_matched=matched(candidate[:300],baseline),
                  sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.glob('*.json')
                           if p.name != 'checkpoint.json'},
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with (directory/'checkpoint.json').open('x') as f:
        json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('sources','opponents','matched','first_300_matched')}))
    for name in ('matched','first_300_matched'):
        print(name,json.dumps({k:v for k,v in result[name].items() if k!='rows'}))


if __name__ == '__main__':
    main()
