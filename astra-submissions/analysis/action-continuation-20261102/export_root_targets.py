"""Export action-conditional returns and paired differences after the frozen pilot.

The input is the actor's permitted prefix plus an action. Terminal returns are
labels, never actor inputs. Same-source branches must remain in one data split.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
PROJECTION=OUT.parent/'budget-continuation-20261102/export_labels.py'
spec=importlib.util.spec_from_file_location('private_projection',PROJECTION)
projection=importlib.util.module_from_spec(spec);spec.loader.exec_module(projection)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def packed(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def main():
    review=json.loads((OUT/'review.json').read_text())
    assert review['passed'] and review['summary_sha256']==sha(OUT/'summary.json')
    plan=json.loads((OUT/'plan.json').read_text())
    frozen=json.loads((OUT/'branches.json').read_text())
    receipts={r['job']['id']:r for r in review['rows']}
    rows=[];pairs={};source_input={};checks=0
    for job in frozen['jobs']:
        case=plan['cases'][job['case']];r=receipts[job['id']]
        path=OUT/job['id']/'replay.json';assert sha(path)==r['replay_sha256']
        game=json.loads(path.read_text());ply=case['branch_ply'];side=ply%2
        actor=projection.actor_input(game,ply);digest=hashlib.sha256(packed(actor)).hexdigest()
        # All interventions and replicate seeds for a source share one input.
        assert source_input.setdefault(case['game'],digest)==digest
        assert actor['own_moves']==[game['frames'][p+1]['move'] for p in range(side,ply,2)]
        assert game['frames'][ply+1]['move']==job['action']
        events=[e for e in game['protocol']['events'] if e['direction']=='input'
                and e['side']==actor['side'] and e['ply']<=ply]
        assert [e['text'] for e in events if len(e['text'])==64]==actor['observations']
        # Mutating truth, the opponent's private inputs, and every future frame
        # must leave the student's pre-action input byte-identical.
        altered=copy.deepcopy(game);other=('black','white')[side]
        for i,frame in enumerate(altered['frames']):
            frame['board']='X'*64;frame[other]='X'*64;frame['clocks'][1-side]=-999
            if i and (i-1)%2!=side:frame['move']='zzzz'
            if i>ply:frame[actor['side']]='X'*64;frame['clocks'][side]=-999;frame['move']='zzzz'
        altered['result']='ignored';altered['privateDiagnostics']={};altered['protocol']={}
        assert packed(projection.actor_input(altered,ply))==packed(actor);checks+=1
        altered['frames']=altered['frames'][:ply+1]
        assert packed(projection.actor_input(altered,ply))==packed(actor);checks+=1
        expected=None if game['censored'] else (0 if game['result']=='1/2-1/2'
                 else (1 if (game['result']=='1-0')==(side==0) else -1))
        assert r['actor_return']==expected
        proposal=json.loads((OUT/f'proposal-{job["case"]}/proposal.json').read_text())
        teacher=next(x for x in proposal['rows'] if x['move']==job['action'])
        row=dict(id=job['id'],source_group=case['game'],branch_ply=ply,side=actor['side'],
                 action=job['action'],arm=job['arm'],repeat=job['repeat'],seed=job['seed'],
                 actor_input_ref=dict(replay=job['id']+'/replay.json',through_ply=ply,
                                      side=actor['side'],projection_sha256=digest),
                 terminal_return=expected,censored=game['censored'],common_clock_charge=job['common_charge'],
                 terminal_return_interval=[-1,1] if expected is None else [expected,expected],
                 root_post_clocks=r['root_post_clocks'],replay_sha256=sha(path),
                 proposal_probability=teacher['probability'],proposal_tree_value=teacher['value'],
                 target='Q of this forced action followed by reconstructed v37/v37, actor perspective')
        rows.append(row);pairs.setdefault((case['game'],job['repeat']),{})[job['arm']]=row
    pair_rows=[]
    for (source,repeat),arms in sorted(pairs.items()):
        assert arms[0]['root_post_clocks']==arms[1]['root_post_clocks']
        assert arms[0]['seed']==arms[1]['seed']
        a,b=arms[0]['terminal_return'],arms[1]['terminal_return']
        lo_a,hi_a=arms[0]['terminal_return_interval'];lo_b,hi_b=arms[1]['terminal_return_interval']
        pair_rows.append(dict(source_group=source,repeat=repeat,baseline=arms[0]['id'],alternative=arms[1]['id'],
                              complete=a is not None and b is not None,
                              return_difference=None if a is None or b is None else b-a,
                              return_difference_interval=[lo_b-hi_a,hi_b-lo_a]))
    for name,data in [('root-targets.jsonl',rows),('paired-targets.jsonl',pair_rows)]:
        with (OUT/name).open('x') as f:
            for r in data:f.write(json.dumps(r,separators=(',',':'))+'\n')
    manifest=dict(source_groups=len(source_input),root_rows=len(rows),paired_rows=len(pair_rows),
                  terminal_root_labels=sum(r['terminal_return'] is not None for r in rows),
                  complete_pairs=sum(r['complete'] for r in pair_rows),privacy_checks=checks,
                  source_input_sha256=source_input,projection_code_sha256=sha(PROJECTION),
                  exporter_sha256=sha(Path(__file__)),review_sha256=sha(OUT/'review.json'),
                  artifacts={n:sha(OUT/n) for n in ('root-targets.jsonl','paired-targets.jsonl')},
                  split='Group by original source game across 241/242/243, every branch and seed.',
                  censoring='Cutoff can depend on action. Training only on completed branches can bias returns; nulls and bounded intervals preserve what is unknown. Intervals are outcome bounds, not confidence intervals.',
                  limit='Two reused development groups. A pair is one noisy comparison, not a validated action ranking. No fitting or strength claim.')
    with (OUT/'root-dataset.json').open('x') as f:json.dump(manifest,f,indent=2);f.write('\n')
    print(json.dumps({k:manifest[k] for k in ('source_groups','root_rows','paired_rows','terminal_root_labels','complete_pairs','privacy_checks')}))


if __name__=='__main__':main()
