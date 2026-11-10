"""Select a separate panel with established large-population coverage."""
from importlib.util import module_from_spec, spec_from_file_location
from itertools import permutations
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ANALYSIS = ROOT/'astra-submissions/analysis'
STORE = ROOT/'data/astra-spool'
OUT = ANALYSIS/HERE.name
PRIVATE = STORE/HERE.name
FIRST = 'exact-updater-speed-20261110'
OLD = ANALYSIS/'quiet-prior-sequential-20261110'
spec = spec_from_file_location('exact_speed_runner', HERE.parent/FIRST/'run.py')
speed = module_from_spec(spec)
spec.loader.exec_module(speed)
ARMS = speed.ARMS
read, save, sha = speed.read, speed.save, speed.sha


def select():
    source = read(OLD/'plan.json')
    audited = read(OLD/'independent-review.json')
    assert audited['passed'] and audited['calls_sha256']==sha(OLD/'calls.json')
    calls = {row['name']:row for row in read(OLD/'calls.json')}
    bins = {team:[] for team in source['teams']}
    examined = []
    for game in source['games']:
        label = game['game']+'-s0-original'
        output = OLD/(label+'.stdout')
        assert calls[label]['code']==0 and sha(output)==calls[label]['stdout_sha256']
        records = [json.loads(line) for line in output.read_text().splitlines()]
        assert len(records)==game['rows']
        large = sum(r['decision'] and r['parents']>10000 for r in records)
        full = sum(r['decision'] and r['full_update'] for r in records)
        bins[game['team']].append(dict(**game, own_observer=game['our_name']=='IAmAVirus', historical_large=large, historical_full=full))
        examined.append(output)
    for games in bins.values():
        games.sort(key=lambda game:(-game['historical_large'],game['game']))
    panel = [games[i] for i in range(4) for games in bins.values()]
    assert len(panel)==len({g['game'] for g in panel})==24
    earlier = read(STORE/FIRST/'plan.json')
    assert {g['game'] for g in panel}.isdisjoint(g['game'] for g in earlier['panel'])
    assert source['seeds'][0]==earlier['seed']
    assert sum(g['historical_large'] for g in panel)>=earlier['cutoff_updates_min']
    for g in panel:
        assert sha(g['trace'])==source['dependencies'][g['trace']]
    return panel, examined, earlier


def prepare():
    closed = read(ANALYSIS/FIRST/'terminal-verification.json')
    assert closed['failed_conditions']==['coverage']
    panel, examined, earlier = select()
    OUT.mkdir(exist_ok=False); PRIVATE.mkdir(exist_ok=False)
    for arm in ARMS:
        binary = STORE/FIRST/arm
        assert sha(binary)==earlier['dependencies'][str(binary)]
        (PRIVATE/arm).symlink_to(binary)
    orders = list(permutations(ARMS))
    jobs = [dict(game=g['game'],arm=arm) for i,g in enumerate(panel) for arm in orders[i%len(orders)]]
    keys = ('seed','cores','child_timeout','total_timeout','update_min','cutoff_updates_min',
            'total_cost_max','game_median_max','tail_ratio_max')
    plan = {key:earlier[key] for key in keys}
    pins = [Path(__file__), HERE.parent/FIRST/'run.py', OLD/'plan.json', OLD/'independent-review.json', OLD/'calls.json',
            ANALYSIS/FIRST/'terminal-verification.json', STORE/FIRST/'plan.json', *examined,
            *(PRIVATE/arm for arm in ARMS), *(Path(g['trace']) for g in panel)]
    plan.update(at=speed.now(),panel=panel,jobs=jobs,dependencies={str(p):sha(p) for p in sorted(set(pins))})
    save(PRIVATE/'plan.json',plan)
    save(OUT/'plan-summary.json',dict(**{key:plan[key] for key in keys},
        at=plan['at'],plan_sha256=sha(PRIVATE/'plan.json'), parent_plan_sha256=sha(STORE/FIRST/'plan.json'),
        games=len(panel), jobs=len(jobs), pins=len(pins), historical_frames=sum(g['rows'] for g in panel),
        historical_full=sum(g['historical_full'] for g in panel), historical_large=sum(g['historical_large'] for g in panel),
        binaries={arm:sha(PRIVATE/arm) for arm in ARMS},
        scope='Different panel from 345. Four games per old 323 opponent stratum by highest historical v38 large-update count. Same three binaries and all thresholds. Selection never reads candidate, truth-share or timing fields. Enriched stress panel rather than arena sampling.'))
    print((OUT/'plan-summary.json').read_text(),flush=True)


def run():
    speed.HERE, speed.OUT, speed.PRIVATE = HERE, OUT, PRIVATE
    speed.run()


if __name__=='__main__':
    {'prepare':prepare,'run':run}[sys.argv[1]]()
