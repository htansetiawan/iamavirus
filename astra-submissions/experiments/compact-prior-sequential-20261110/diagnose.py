"""Decompose the closed compact-prior result into support and weight effects."""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'astra-submissions/analysis/compact-prior-sequential-20261110'
RAW = ROOT/'data/astra-spool'/OUT.name
FLOOR = 1e-12
ARMS = ('original','learned')
SUPPORT = ('both_present','lost','gained','both_absent')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def load():
    plan = read(RAW/'plan.json')
    result = read(OUT/'result.json')
    reviewed = read(OUT/'independent-review.json')
    assert reviewed['passed'] and reviewed['result_sha256']==sha(OUT/'result.json')
    assert reviewed['source_plan_sha256']==sha(RAW/'plan.json')
    assert read(RAW/'execution.json')['status']=='complete'
    assert result['decision']=='close_frozen_full_head_sequential'
    assert [name for name,value in result['conditions'].items() if not value]==['priority_nonregression']
    assert result['calls_sha256']==sha(RAW/'calls.json')
    calls = {call['name']:call for call in read(RAW/'calls.json')}
    games = []
    for game in plan['games']:
        records = []
        for seed in range(len(plan['seeds'])):
            peers = []
            for arm in ARMS:
                name = f"{game['game']}-s{seed}-{arm}"
                output = RAW/(name+'.stdout')
                assert calls[name]['code']==0 and calls[name]['stdout_sha256']==sha(output)
                rows = [json.loads(line) for line in output.read_text().splitlines()]
                assert len(rows)==game['rows']
                peers.append(rows)
            for native,learned in zip(*peers):
                assert native['decision']==learned['decision'] and native['ply']==learned['ply']
                if not native['decision'] or native['ply']<16:
                    continue
                presence = (bool(native['matches']),bool(learned['matches']))
                kind = {(True,True):'both_present',(True,False):'lost',(False,True):'gained',(False,False):'both_absent'}[presence]
                delta = math.log(max(learned['truth_share'],FLOOR))-math.log(max(native['truth_share'],FLOOR))
                records.append(dict(delta=delta,support=kind,capped=native['ever_capped'] or learned['ever_capped']))
        games.append(dict(team=game['team'],own_observer=game['own_observer'],records=records))
    return games, result


def summarize(games):
    games = [game for game in games if game['records']]
    rows = [r for game in games for r in game['records']]
    assert rows
    sums = [math.fsum(r['delta'] for r in game['records']) for game in games]
    counts = [len(game['records']) for game in games]
    total = math.fsum(sums)
    cells = {}
    for key in SUPPORT:
        values = [r['delta'] for r in rows if r['support']==key]
        cells[key] = dict(rows=len(values), contribution_to_mean=math.fsum(values)/len(rows),
                          mean_on_rows=math.fsum(values)/len(values) if values else None)
    cap = {}
    for key in (False,True):
        values = [r['delta'] for r in rows if r['capped']==key]
        cap[str(key).lower()] = dict(rows=len(values), mean=math.fsum(values)/len(values) if values else None)
    rng = np.random.default_rng(3521111)
    choices = rng.integers(len(games),size=(4000,len(games)))
    bootstrap = np.array(sums)[choices].sum(1)/np.array(counts)[choices].sum(1)
    loo = [(total-value)/(len(rows)-count) for value,count in zip(sums,counts) if count<len(rows)]
    return dict(games=len(games),decisions=len(rows),gain=total/len(rows), support=cells, by_capped=cap,
                descriptive_game_interval95=np.quantile(bootstrap,[.025,.975]).tolist(),
                negative_games=sum(value<0 for value in sums),leave_one_game_out_range=[min(loo),max(loo)])


def main():
    games,result = load()
    teams = defaultdict(list)
    for game in games:
        teams[game['team']].append(game)
    priority = {name:summarize(teams[name]) for name in ('Instructors','duck','HYPOTHERMIA')}
    for name,value in priority.items():
        assert abs(value['gain']-result['by_team'][name]['gain'])<1e-12
    combined = summarize(games)
    assert abs(combined['gain']-result['gain'])<1e-12 and combined['decisions']==result['primary']
    report = dict(at=datetime.now(timezone.utc).isoformat(),result_sha256=sha(OUT/'result.json'),combined=combined,priority=priority,
                  own_observer=summarize([g for g in games if g['own_observer']]),
                  scope='Descriptive decomposition on the already scored 343 development panel. Support changes and weights are observational. Bootstrap resamples whole games within each displayed subgroup.')
    with (OUT/'support-decomposition.json').open('x') as stream:
        json.dump(report,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(combined=combined['support'],instructors=priority['Instructors']),indent=2),flush=True)


if __name__=='__main__':
    main()
