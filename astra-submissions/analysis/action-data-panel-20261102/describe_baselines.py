"""Development-only selectors using proposal scores, never rollout labels.

Started after examining the first four branch results. This is descriptive
analysis, not a preregistered promotion gate or a fitted model.
"""
from collections import defaultdict
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    dataset=json.loads((OUT/'dataset.json').read_text())
    for n,h in dataset['artifacts'].items():assert sha(OUT/n)==h,n
    plan=json.loads((OUT/'plan.json').read_text())
    targets=[json.loads(line) for line in (OUT/'root-targets.jsonl').read_text().splitlines()]
    groups=defaultdict(dict)
    for r in targets:
        key=(r['source_group'],r['repeat']);assert r['arm'] not in groups[key]
        groups[key][r['arm']]=r
    selectors={name:[] for name in ('current_choice','higher_root_value','higher_root_probability')}
    choices={name:{} for name in selectors}
    fixed={r['source']:r for r in json.loads((OUT/'baseline-choices.json').read_text())['rows']}
    for case in plan['cases']:
        index=int(case['id'][1:]);proposal=json.loads((OUT/f'proposal-{index}/proposal.json').read_text())
        if not proposal['supported']:continue
        rows={r['move']:r for r in proposal['rows']}
        a,b=rows[proposal['chosen']],rows[proposal['alternative']]
        # Tie retains the current action. These choices cannot see any outcomes.
        choices['current_choice'][case['game']]=0
        choices['higher_root_value'][case['game']]=int(b['value']>a['value'])
        choices['higher_root_probability'][case['game']]=int(b['probability']>a['probability'])
        assert choices['higher_root_value'][case['game']]==fixed[case['game']]['higher_value_arm']
        assert choices['higher_root_probability'][case['game']]==fixed[case['game']]['higher_probability_arm']
    for (source,repeat),arms in sorted(groups.items()):
        assert set(arms)=={0,1}
        assert arms[0]['seed']==arms[1]['seed'] and arms[0]['root_post_clocks']==arms[1]['root_post_clocks']
        for name,rows in selectors.items():
            arm=choices[name][source];selected=arms[arm];control=arms[0]
            lo,hi=selected['terminal_return_interval'];clo,chi=control['terminal_return_interval']
            delta=[0,0] if arm==0 else [lo-chi,hi-clo]
            rows.append(dict(source=source,repeat=repeat,arm=arm,
                             selected_return=selected['terminal_return'],
                             selected_return_bounds=[lo,hi],difference_bounds=delta,
                             difference=delta[0] if delta[0]==delta[1] else None))
    results={}
    for name,rows in selectors.items():
        n=len(rows);assert n
        results[name]=dict(source_count=len(choices[name]),
                           alternative_source_count=sum(choices[name].values()),
                           selected_censored=sum(r['selected_return'] is None for r in rows),
                           return_mean_bounds=[sum(r['selected_return_bounds'][k] for r in rows)/n for k in (0,1)],
                           difference_mean_bounds=[sum(r['difference_bounds'][k] for r in rows)/n for k in (0,1)],
                           unresolved_differences=sum(r['difference'] is None for r in rows),rows=rows)
    result=dict(results=results,dataset_sha256=sha(OUT/'dataset.json'),source_sha256=sha(Path(__file__)),
                selectors_sha256=sha(OUT/'baseline-choices.json'),
                scope='Development description after the fixed panel. Bounds reflect missing returns, not sampling confidence. Sources, not branches, are independent groups. No trained model, selector promotion or Elo claim.')
    with (OUT/'baseline-descriptions.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({name:{k:v for k,v in r.items() if k!='rows'} for name,r in results.items()}))


if __name__=='__main__':main()
