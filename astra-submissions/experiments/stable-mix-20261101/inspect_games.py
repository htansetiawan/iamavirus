#!/usr/bin/env python3
"""Attribute executed mixed choices in completed games; no argmax counterfactual.

The runtime logs action indices, not the unplayed argmax UCI. We can identify
whether the played move differed, but cannot claim the unplayed action would
have saved the game. No changes to a running candidate are made.
"""
import json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest
from fresh_taxonomy_gate import exchange_probe,material_horizons
OUT=ROOT/'astra-submissions/analysis/stable-mix-20261101'
reports=[]
for path in sorted((OUT/'jobs').glob('*/result.json')):
    result=json.loads(path.read_text());job=result['job']
    if result['faults'] or job['arm']!='candidate':continue
    replay=json.loads((path.parent/'replay.json').read_text());states,errors=ingest.validate_replay(replay);assert not errors
    pending=None;choices=[]
    for line in replay['privateDiagnostics'][job['side']].splitlines():
        if line.startswith('astra-mix: mode='):
            pending=dict(re.findall(r'(\w+)=([^ ]+)',line))
        elif line.startswith('mist: n='):
            info=dict(re.findall(r'(\w+)=([^ ]+)',line))
            choices.append({'number':int(info['n']),'move':info['move'],'mix':pending})
            pending=None
    side=('white','black').index(job['side']);own=list(range(side,len(states)-1,2))
    assert len(choices)==len(own),(job['id'],len(choices),len(own))
    decisions=[]
    for choice,ply in zip(choices,own):
        assert choice['move']==replay['frames'][ply+1]['move']
        diff=bool(choice['mix'] and choice['mix']['selected']!=choice['mix']['argmax'])
        fatal=states[ply].board.move_loses_king(choice['move'])
        label={'ply':ply,**choice,'non_argmax':diff,'fatal':fatal,
               'recorded_material_loss':material_horizons(replay['frames'],ply,side)}
        if diff or fatal:label['probe']=exchange_probe(states[ply],choice['move'])
        decisions.append(label)
    reports.append({'job':job['id'],'score':result['score'],'decisions':len(decisions),
                    'non_argmax_choices':[d for d in decisions if d['non_argmax']],
                    'fatal_choices':[d for d in decisions if d['fatal']],
                    'first_net_loss_ge3':next((d for d in decisions if (d['recorded_material_loss']['3'] or 0)>=3),None)})
(OUT/'decision-audit.json').write_text(json.dumps({'scope':__doc__,'games':reports},indent=2)+'\n')
for r in reports:
    print(json.dumps({'job':r['job'],'score':r['score'],'mixed_choices':len(r['non_argmax_choices']),
                      'mixed_fatal':sum(d['fatal'] for d in r['non_argmax_choices']),
                      'mixed_material_events':sum((d['probe']['exchange_loss'] or 0)>=2 for d in r['non_argmax_choices']),
                      'fatal_choices':[(d['ply'],d['move'],d['non_argmax']) for d in r['fatal_choices']]}))
