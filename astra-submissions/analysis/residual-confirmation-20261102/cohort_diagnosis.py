"""Post-result composition diagnosis; no fitting, selection or gate changes."""
from collections import Counter,defaultdict
import gzip
import hashlib
import json
from pathlib import Path
from datetime import datetime,timezone
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
DATA=ROOT/'astra-submissions/experiments/residual-confirmation-20261102/work'


def main():
    assert json.loads((OUT/'review.json').read_text())['passed']
    with np.load(DATA/'holdout/data.npz') as a:d={k:a[k] for k in a.files}
    with np.load(DATA/'predictions.npz') as a:p={k:a[k] for k in a.files}
    games=json.loads((OUT/'games.json').read_text());y=d['y'].astype(np.float64)
    def loss(prob):
        prob=np.clip(prob,1e-6,1-1e-6);return -(y*np.log(prob)+(1-y)*np.log1p(-prob))
    delta=loss(p['flat'])-loss(p['calibrated_sf'])
    pieces=d['x'][:,:,0];values=np.array([0,1,3,3,5,9,0,1,3,3,5,9,0])
    total=values[pieces].sum(1)
    own=(values[pieces]*(pieces<7)).sum(1);enemy=(values[pieces]*(pieces>=7)).sum(1);balance=own-enemy
    sf=p['calibrated_sf']
    axes={
        'material_phase':np.where(total>=60,'60+ material',np.where(total>=30,'30–59 material','under30 material')),
        'material_balance':np.where(balance>=3,'ahead3+',np.where(balance<=-3,'behind3+','within2')),
        'sf_probability':np.select([sf<.1,sf<.3,sf<.7,sf<.9],['under.1','.1–.3','.3–.7','.7–.9'],default='.9+')}
    weights=np.zeros(len(y));reports={}
    for group,name in [(0,'older_unused'),(1,'new_date')]:
        mask=d['group']==group;_,inv,n=np.unique(d['game'][mask],return_inverse=True,return_counts=True)
        weights[mask]=1/n[inv]/len(n)
        item=dict(games=len(n),positions=int(mask.sum()),mean_logloss_difference=float((weights[mask]*delta[mask]).sum()),axes={})
        for axis,labels in axes.items():
            rows=[]
            for label in sorted(set(labels.tolist())):
                take=mask&(labels==label);mass=float(weights[take].sum());contribution=float((weights[take]*delta[take]).sum())
                rows.append(dict(bin=label,positions=int(take.sum()),game_weight_mass=mass,
                    conditional_difference=contribution/mass if mass else None,contribution=contribution))
            assert abs(sum(v['contribution'] for v in rows)-item['mean_logloss_difference'])<1e-12
            item['axes'][axis]=rows
        reports[name]=item
    # Freeze-source metadata joins: game-level diagnostics, never model inputs.
    pair_stats=defaultdict(list);versions=Counter();individual=[]
    for gi in np.unique(d['game'][d['group']==1]):
        g=games[int(gi)];row=g['row'];mask=d['game']==gi;diff=float(delta[mask].mean())
        pair=tuple(sorted([row['white'],row['black']]))
        pair_stats[pair].append(diff)
        for side in ('white','black'):versions[(row[side],row.get(side+'Version'))]+=1
        individual.append(dict(game=row['id'],white=row['white'],black=row['black'],white_version=row.get('whiteVersion'),
            black_version=row.get('blackVersion'),logloss_difference=diff))
    pairs=[dict(teams=list(pair),games=len(v),mean_difference=float(np.mean(v)),
        contribution_to_new_date=float(sum(v)/reports['new_date']['games'])) for pair,v in pair_stats.items()]
    pairs.sort(key=lambda r:-r['contribution_to_new_date'])
    standardized={}
    for axis in axes:
        old={r['bin']:r for r in reports['older_unused']['axes'][axis]}
        new=reports['new_date']['axes'][axis]
        standardized[axis]=sum(r['game_weight_mass']*old[r['bin']]['conditional_difference'] for r in new if old[r['bin']]['conditional_difference'] is not None)
    result=dict(at=datetime.now(timezone.utc).isoformat(),post_hoc=True,cohorts=reports,
        older_bin_differences_reweighted_to_new_mix=standardized,pairs=pairs,
        new_date_versions=[dict(team=t,version=v,games=n) for (t,v),n in sorted(versions.items(),key=lambda r:str(r[0]))],
        individual_games=sorted(individual,key=lambda r:-r['logloss_difference']),
        scope='Descriptive after the fixed gate failed. Axes decompose equal-game loss differences; one-axis standardization is not causal attribution. No refit, gate relaxation or arm selection.',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with (OUT/'cohort-diagnosis.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    text=['# Post-result cohort diagnosis','','The newer-game safeguard failed. This diagnostic does not change that decision.','',
        '| Axis | Older difference reweighted to newer composition | Actual newer difference |','|---|---:|---:|']
    for axis,value in standardized.items():text.append(f"| {axis} | {value:+.5f} | {reports['new_date']['mean_logloss_difference']:+.5f} |")
    text+=['','Each axis is a separate descriptive comparison. It does not identify a causal distribution shift.','']
    for name,item in reports.items():
        text += [f'## {name}','','| Axis / bin | Weight share | Conditional difference | Contribution |','|---|---:|---:|---:|']
        for axis,rows in item['axes'].items():
            for r in rows:text.append(f"| {axis} / {r['bin']} | {r['game_weight_mass']:.1%} | {r['conditional_difference']:+.5f} | {r['contribution']:+.5f} |")
        text.append('')
    text+=['## Newer pair contributions','','These names join public replay metadata; they are not runtime features. Small groups are noisy.','',
        '| Pair | Games | Mean difference | Contribution |','|---|---:|---:|---:|']
    for r in pairs[:12]:text.append(f"| {' / '.join(r['teams'])} | {r['games']} | {r['mean_difference']:+.5f} | {r['contribution_to_new_date']:+.5f} |")
    (OUT/'cohort-diagnosis.md').write_text('\n'.join(text)+'\n')
    print(json.dumps({'standardized':standardized,'newer_difference':reports['new_date']['mean_logloss_difference'],'top_pairs':pairs[:5]}),flush=True)


if __name__=='__main__':main()
