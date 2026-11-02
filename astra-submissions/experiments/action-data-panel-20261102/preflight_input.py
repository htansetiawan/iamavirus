"""Validate the proposed student interface against the already-audited 243 data."""
import copy
import hashlib
import json
from pathlib import Path

from input_contract import critic_input,digest,VERSION

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/action-data-panel-20261102'
OLD=ROOT/'astra-submissions/analysis/action-continuation-20261102'


def main():
    old=json.loads((OLD/'plan.json').read_text());checks=0;rows=[]
    for i,c in enumerate(old['cases']):
        p=json.loads((ROOT/c['prefix']).read_text());proposal=json.loads((OLD/f'proposal-{i}/proposal.json').read_text())
        side=p['branch_ply']%2;other=('black','white')[side]
        for action in (proposal['chosen'],proposal['alternative']):
            wanted=critic_input(p,action,proposal)
            changed=copy.deepcopy(p)
            for j,f in enumerate(changed['frames']):
                f['board']='X'*64;f[other]='X'*64;f['clocks'][1-side]=-999
                if j and (j-1)%2!=side:f['move']='zzzz'
            changed.update(id='unused identity',result='unused outcome',opponent='unused name')
            changed['timeControl']['untrusted_extra']='ignored'
            altered_proposal=copy.deepcopy(proposal);altered_proposal.update(result='unused outcome',seed=-1)
            assert critic_input(changed,action,altered_proposal)==wanted;checks+=1
            own=copy.deepcopy(p);key=('white','black')[side]
            own['frames'][0][key]='?'*64
            assert digest(critic_input(own,action,proposal))!=digest(wanted);checks+=1
            score=copy.deepcopy(proposal);row=next(r for r in score['rows'] if r['move']==action);row['value']+=.01
            assert digest(critic_input(p,action,score))!=digest(wanted);checks+=1
            future=copy.deepcopy(p);future['frames'].append(copy.deepcopy(future['frames'][-1]))
            try:critic_input(future,action,proposal)
            except AssertionError:checks+=1
            else:raise AssertionError('future frame accepted in prefix')
            rows.append(dict(case=i,action=action,actor_input_sha256=digest(wanted)))
        assert rows[-1]['actor_input_sha256']!=rows[-2]['actor_input_sha256']
    result=dict(passed=True,schema=VERSION,checks=checks,rows=rows,
                source_sha256=hashlib.sha256((HERE/'input_contract.py').read_bytes()).hexdigest(),
                scope='Whitelisted actor input, forbidden-field invariance, allowed-input sensitivity and future-frame rejection. No model fit.')
    with (OUT/'input-preflight.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'passed':True,'checks':checks,'schema':VERSION}))


if __name__=='__main__':main()
