"""Frozen-cohort and scoring rules; no model fitting or arena interaction."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/prospective-quiet-teacher-20261110'
OLD = HERE.parent / 'capture-fixed-prior-20261110'
OLD_OUT = ROOT / 'astra-submissions/analysis/capture-fixed-prior-20261110'
TEAMS = {
    'f394d843d970454f868c38c7f6963cc9': 'Greek Gift',
    'knight-vision': 'Knight Vision',
    '0729dbf4b76c841d7582c2dddea32faa': 'Farsight',
    '46f21742c86746bb8fe897d62b81318d': 'In Pawn Sight',
    'strongly-invisible': 'Strongly Invisible',
    'db107815c3b14827a79ec9e3d12f4726': 'Decent Chess Bot',
    '31f523b6aaac47adbfb957d0b0123408': 'Crimson Fog',
    'instructors': 'Instructors',
    'd0335ee36a454199b847210e1e94d5ee': 'Mist Opportunities',
    '8d775e234808489c815a4a9f6bbabfe4': 'duck',
    'e2f593ca1fea4710b07a8120dd6b3477': 'HYPOTHERMIA',
}
OWN = 'a2c35173659545c99752376a70418438'
PRIORITY = ['instructors', '8d775e234808489c815a4a9f6bbabfe4', 'e2f593ca1fea4710b07a8120dd6b3477']


def now():
    return datetime.now(timezone.utc).isoformat()


def instant(text):
    value = datetime.fromisoformat(text.replace('Z', '+00:00'))
    if value.tzinfo is None:
        raise ValueError('timestamp must carry timezone')
    return value.astimezone(timezone.utc)


def stamp_ns(text):
    """Exact RFC3339 order, including fractions datetime would truncate."""
    m = re.fullmatch(r'(\d{4}-\d\d-\d\d[Tt]\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?([Zz]|[+-]\d\d:\d\d)', text)
    if not m:
        raise ValueError('unsupported timestamp: '+repr(text))
    prefix, fraction, offset = m.groups()
    base = datetime.fromisoformat(prefix.upper()+('+00:00' if offset.upper()=='Z' else offset))
    delta = base.astimezone(timezone.utc)-datetime(1970,1,1,tzinfo=timezone.utc)
    return (delta.days*86400+delta.seconds)*10**9+int((fraction or '').ljust(9,'0'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data, *, exclusive=False):
    text = json.dumps(data, indent=2, allow_nan=False) + '\n'
    if exclusive:
        with Path(path).open('x') as handle:
            handle.write(text)
    else:
        # Small receipts are atomic, not a shared accepted-data journal.
        import sys
        sys.path.insert(0, str(ROOT))
        from learning.api_client import atomic_write
        atomic_write(Path(path), text.encode())


def check_pins(plan):
    for name, expected in plan['dependencies'].items():
        assert sha(name) == expected, f'changed dependency: {name}'


def relevant(row):
    return any(row.get(side + 'PlayerId') in TEAMS for side in ('white', 'black'))


def own_game(row):
    return any(row.get(side + 'PlayerId') == OWN for side in ('white', 'black'))


def validate_listing(row):
    assert re.fullmatch('[a-z0-9]{8}', row['id'])
    assert row['result'] in ('1-0', '0-1', '1/2-1/2')
    assert isinstance(row['plies'], int) and row['plies'] >= 0
    instant(row['createdAt'])


def ordered_candidates(listings, cutoff):
    return sorted((row for row in listings if relevant(row) and stamp_ns(row['createdAt']) >= stamp_ns(cutoff)),
                  key=lambda row: (stamp_ns(row['createdAt']), row['id']))


def cohort_game(row, replay, source_sha, denied):
    """Declared metadata/rules/sequence exclusions only, never performance."""
    for key in ('id', 'createdAt', 'result', 'white', 'black', 'whitePlayerId',
                'blackPlayerId', 'whiteVersion', 'blackVersion'):
        assert replay.get(key) == row.get(key), f'listing/replay disagreement: {key}'
    frames = replay['frames']
    assert len(frames) == row['plies'] + 1
    if replay.get('rulesVersion') != 'fow-v1':
        return None, 'not fow-v1'
    if row['plies'] < 4:
        return None, 'fewer than four plies'
    sequence = [frame['move'] for frame in frames[1:]]
    signature = hashlib.sha256(' '.join(sequence).encode()).hexdigest()
    if signature in denied:
        return None, 'whole-sequence duplicate'
    selected = [ply for ply in range(row['plies'])
                if replay.get(('white', 'black')[ply % 2] + 'PlayerId') in TEAMS]
    assert selected
    return dict(game=row['id'], split='future', created_at=row['createdAt'],
                white=replay['white'], black=replay['black'],
                white_id=replay.get('whitePlayerId'), black_id=replay.get('blackPlayerId'),
                white_version=replay.get('whiteVersion'), black_version=replay.get('blackVersion'),
                selected_plies=selected, moves=sequence, sequence_sha256=signature,
                replay_sha256=source_sha, frames=len(frames)), None



def bootstrap(meta,delta,seed,draws):
    import numpy as np
    groups={}
    for row,value in zip(meta,delta):
        item=groups.setdefault(row['game'],[0.,0]);item[0]+=float(value);item[1]+=1
    values=np.array([groups[k] for k in sorted(groups)]);rng=np.random.default_rng(seed);estimates=[]
    for _ in range(draws):
        sample=values[rng.integers(len(values),size=len(values))]
        estimates.append(float(sample[:,0].sum()/sample[:,1].sum()))
    return np.quantile(estimates,[.025,.975]).tolist()


def summarize(plan,rows):
    import numpy as np
    primary=np.array([r['primary'] for r in rows]);capture=np.array([r['capture'] for r in rows])
    prediction={k:np.array([r['logp'][k] for r in rows]) for k in plan['models']}
    names={'gain':'base','matched_quadratic_gain':'quadratic','production_quadratic_gain':'production'}
    metrics=dict(primary=int(primary.sum()),decisions=len(rows),capture_targets=int(capture.sum()),
        surprise_captures=sum(r['primary'] and r['surprise'] for r in rows),
        nll={k:float(-v[primary].mean()) for k,v in prediction.items()},priority={},by_team_version=[])
    selected=[r for r in rows if r['primary']]
    for index,(name,control) in enumerate(names.items()):
        delta=prediction['teacher']-prediction[control];metrics[name]=float(delta[primary].mean())
        metrics[name+'_interval95']=bootstrap(selected,delta[primary],plan['seed']+index,plan['bootstrap_draws'])
    gain=prediction['teacher']-prediction['base'];metrics['all_move_gain']=float(gain.mean())
    metrics['capture_target_error']=float(abs(gain[capture]).max(initial=0))
    for team in PRIORITY:
        mask=primary&np.array([r['team_id']==team for r in rows])
        metrics['priority'][team]=dict(games=len({r['game'] for r,ok in zip(rows,mask) if ok}),decisions=int(mask.sum()),gain=float(gain[mask].mean()) if mask.any() else 0.)
    for team,version in sorted({(r['team_id'],r['version']) for r in selected},key=lambda k:(k[0],-1 if k[1] is None else k[1])):
        mask=primary&np.array([r['team_id']==team and r['version']==version for r in rows])
        metrics['by_team_version'].append(dict(team_id=team,name=TEAMS[team],version=version,games=len({r['game'] for r,ok in zip(rows,mask) if ok}),decisions=int(mask.sum()),gain=float(gain[mask].mean())))
    return metrics


def gate_result(plan,m,checks):
    g=plan['gate']
    return dict(primary=m['primary']>=g['primary_min'],native_gain=m['gain']>=g['native_gain'],
        matched_quadratic=m['matched_quadratic_gain']>=g['quadratic_gain'],
        production_quadratic=m['production_quadratic_gain']>=g['quadratic_gain'],
        native_confidence=m['gain_interval95'][0]>0,production_confidence=m['production_quadratic_gain_interval95'][0]>0,
        all_moves=m['all_move_gain']>=0,capture_identity=m['capture_target_error']==0 and checks['capture_action_error']==0,
        capture_coverage=m['surprise_captures']>=g['surprise_min'],native_control_parity=checks['native_control_max_error']<g['numeric_tolerance'],
        priority_coverage=all(m['priority'][t]['games']>=g['priority_games_min'] for t in PRIORITY),
        priority_nonregression=all(m['priority'][t]['gain']>=0 for t in PRIORITY))
