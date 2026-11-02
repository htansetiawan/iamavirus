"""Recompute the frozen probe's joins, probability scores and gate from saved data."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import statistics

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    plan = json.loads((OUT/'plan.json').read_text())
    receipt = json.loads((OUT/'receipt.json').read_text())
    report = json.loads((OUT/'summary.json').read_text())
    assert receipt['state'] == 'completed' and not receipt['failures']
    assert digest(OUT/'plan.json') == receipt['plan_sha256']
    assert digest(OUT/'receipt.json') == report['receipt_sha256']
    assert len({c['sequence_sha256'] for c in plan['games']}) == 16
    assert Counter(c['side'] for c in plan['games']) == {0:8,1:8}
    names = ('sharp','flat','cnn','pool')
    computed = {}; total = thinnings = rebuilds = 0
    for phase in ('all_hidden','hidden_ply30plus','hidden_early','visible'):
        game_scores = {n:[] for n in names}; decisions = 0
        for case in plan['games']:
            gid = case['game']
            assert digest(case['replay_path']) == case['replay_sha256']
            replay = json.loads(Path(case['replay_path']).read_text())
            saved = json.loads((OUT/'games'/f'{gid}.json').read_text())
            assert saved['case'] == case and saved['process_returncode'] == 0
            stderr = (OUT/'games'/f'{gid}.stderr').read_text()
            assert digest(OUT/'games'/f'{gid}.stderr') == saved['stderr_sha256']
            assert digest(OUT/'games'/f'{gid}.stdout') == saved['stdout_sha256']
            native = [s.split() for s in stderr.splitlines() if s.startswith('astra-king-location ')]
            assert len(native) == len(saved['rows'])
            assert saved['thinnings'] == stderr.count('P thinned from')
            assert saved['rebuilds'] == stderr.count('belief empty, rebuilt')
            if phase == 'all_hidden':
                total += len(saved['rows']); thinnings += saved['thinnings']; rebuilds += saved['rebuilds']
            vals = {n:[] for n in names}
            for index, row in enumerate(saved['rows']):
                ply = case['side'] + 2*index
                assert row['ply'] == ply and row['decision'] == index
                assert row['worlds'] == int(native[index][2]) and row['missing'] == 0
                assert row['sharp'] == list(map(float,native[index][4:68]))
                assert row['flat'] == list(map(float,native[index][68:132]))
                frame = replay['frames'][ply]
                truth = frame['board'].index('k' if case['side']==0 else 'K')
                hidden = frame[('white','black')[case['side']]][truth] == '?'
                assert truth == row['truth'] and hidden == row['hidden']
                pooled = [math.sqrt(p*q) for p,q in zip(row['sharp'],row['cnn'])]
                norm = sum(pooled)
                assert norm > 0
                assert max(abs(p/norm-q) for p,q in zip(pooled,row['pool'])) < 1e-12
                assert all(p or not q for p,q in zip(row['sharp'],row['pool']))
                chosen = (hidden if phase=='all_hidden' else hidden and ply>=30 if phase=='hidden_ply30plus'
                          else hidden and ply<30 if phase=='hidden_early' else not hidden)
                if not chosen:
                    continue
                decisions += 1
                for name in names:
                    p = row[name]; t = p[truth]
                    assert len(p)==64 and all(math.isfinite(v) and v>=0 for v in p) and abs(sum(p)-1)<1e-6
                    vals[name].append((-math.log(max(t,1e-12)),sum((v-(j==truth))**2 for j,v in enumerate(p)),t,float(t>0)))
            for name in names:
                if vals[name]:
                    game_scores[name].append([statistics.mean(v[k] for v in vals[name]) for k in range(4)])
        metrics = {name:dict(zip(('nll','brier','truth_mass','nonzero_support'),
                   [statistics.mean(v[k] for v in values) for k in range(4)])) for name,values in game_scores.items() if values}
        assert decisions == report['phases'][phase]['decisions']
        assert len(game_scores['sharp']) == report['phases'][phase]['games']
        for name in metrics:
            for metric, value in metrics[name].items():
                assert abs(value-report['phases'][phase]['metrics'][name][metric]) < 1e-10
        computed[phase] = metrics
    primary, late = computed['all_hidden'],computed['hidden_ply30plus']
    gate = bool(late and all(primary[n]['nll']-primary['pool']['nll']>=.1
               and primary['pool']['brier']<=primary[n]['brier']
               and late['pool']['nll']<late[n]['nll'] for n in ('sharp','flat')))
    assert gate == report['confirmation_proposal_gate']
    assert (total,thinnings,rebuilds) == (report['total_decisions'],report['thinnings'],report['rebuilds'])
    result = dict(passed=True,games=16,decisions=total,thinnings=thinnings,rebuilds=rebuilds,
                  independently_recomputed_gate=gate,plan_sha256=digest(OUT/'plan.json'),
                  summary_sha256=digest(OUT/'summary.json'),audit_source_sha256=digest(__file__),
                  scope='Saved native marginal rows, truth joins, fixed geometric pool, equal-game metrics and gate. Does not validate king head calibration or playing strength.')
    with (OUT/'audit.json').open('x') as f:
        json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':main()
