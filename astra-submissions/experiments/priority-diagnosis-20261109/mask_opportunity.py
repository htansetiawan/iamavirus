"""Post-hoc action-support ceilings; no actor or search execution."""
from collections import Counter
import json

from prepare import OUT

review=json.loads((OUT/'review.json').read_text());counts=Counter();examples=[]
for row in review['rows']:
    if row['case']['kind']!='terminal' or not row['safe_legal_count']:continue
    safe=set(row['safe_in_view']);original=set(row['safe_kept'])
    risk={a['move']:(a['king']+.9*max(0,a['queen']),a['king_sharp']+.9*max(0,a['queen_sharp'])) for a in row['actions']}
    least=[min(v[i] for v in risk.values()) for i in (0,1)]
    union={m for m,v in risk.items() if v[0]<=least[0]+.02 or v[1]<=least[1]+.02}
    # Two-objective risk frontier in O(A log A), including identical optima.
    frontier=set();best=float('inf');ordered=sorted((v[0],v[1],m) for m,v in risk.items());i=0
    while i<len(ordered):
        j=i
        while j<len(ordered) and ordered[j][0]==ordered[i][0]:j+=1
        same=ordered[i:j];minimum=min(x[1] for x in same)
        if minimum<best:frontier.update(x[2] for x in same if x[1]==minimum)
        best=min(best,minimum);i=j
    counts['safe_available']+=1
    if not original:
        counts['all_safe_excluded']+=1
        counts['recovered_by_union']+=bool(union&safe)
        counts['recovered_by_adding_frontier']+=bool(frontier&safe)
        examples.append(dict(case=row['case']['id'],seed=row['seed'],union_safe=sorted(union&safe),pareto_safe=sorted(frontier&safe)))
result=dict(counts=dict(counts),examples=examples,scope='Post-hoc risk-mask opportunity check on the loss-conditioned fixed readouts. Current2% margin and0.9queen weight retained. Union and adding Pareto-risk actions are diagnostic masks only; no candidate search or strength claim.')
path=OUT/'mask-opportunity.json'
if path.exists():
    assert json.loads(path.read_text())==result
    print('Original mask opportunity receipt reproduced without overwrite.')
else:
    with path.open('x') as handle:json.dump(result,handle,indent=2);handle.write('\n')
    print(json.dumps(result['counts']))
