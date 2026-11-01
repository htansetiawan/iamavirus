#!/usr/bin/env python3
"""Recompute the frozen predictive gate from per-decision score artifacts."""
import argparse,gzip,hashlib,json
from pathlib import Path
import numpy as np

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);a=ap.parse_args();p=a.directory
    manifest=json.loads((p/'data-v2/manifest.json').read_text());fits=json.loads((p/'fit/frozen-models.json').read_text())
    assert fits['manifest_sha256']==sha(p/'data-v2/manifest.json')
    prior=json.loads(Path(manifest['exclusion_plan']).read_text())
    assert not ({x['id'] for x in manifest['games']}&{x['game'] for x in prior['games']})
    assert len({x['sequence_sha256'] for x in manifest['games']})==2100
    models={}
    for name in ['static','temporal']:
        q=p/'fit'/(name+'.json');assert sha(q)==fits['models'][name]['sha256'];r=json.loads(q.read_text())
        assert len(r['coefficients'])==859 and all(np.isfinite(r['coefficients']))
        # Strong convexity supplies a conservative objective optimization-gap bound.
        models[name]={'parameters':859,'gradient_inf':r['fit']['max_gradient'],
                      'objective_gap_upper_bound':859*r['fit']['max_gradient']**2/(2*1e-4)}
    report={'models':models,'splits':{}}
    for split in ['validation','test']:
        with gzip.open(p/'fit'/(split+'-scores.jsonl.gz'),'rt') as f:rows=[json.loads(line) for line in f]
        expected={x['index'] for x in manifest['games'] if x['split']==split}
        assert {r['game_index'] for r in rows}==expected
        assert len({(r['game_index'],r['ply']) for r in rows})==len(rows)
        for r in rows:
            assert r['side']==r['ply']%2 and r['legal_moves']>0
            for name in ['static','temporal']:
                s=r[name];assert np.isfinite(s['logp']) and s['logp']<=1e-12
                if r['ambiguous']:
                    assert abs(s['conditional_logp']+s['observation_logp']-s['logp'])<1e-10
        amb=[r for r in rows if r['ambiguous']]
        delta=np.array([r['temporal']['conditional_logp']-r['static']['conditional_logp'] for r in amb])
        nll_delta=-np.mean([r['temporal']['logp']-r['static']['logp'] for r in rows])
        old=json.loads((p/'fit'/(split+'.json')).read_text())
        assert abs(float(delta.mean())-old['ambiguous_gain'])<1e-12
        assert abs(float(nll_delta)-old['all_move_nll_change'])<1e-12
        stats={'positions':len(rows),'ambiguous':len(amb),'games':len(expected),'ambiguous_gain':float(delta.mean()),'all_move_nll_change':float(nll_delta)}
        if split=='test':
            sums={i:0.0 for i in expected};counts={i:0 for i in expected}
            for r,d in zip(amb,delta):sums[r['game_index']]+=d;counts[r['game_index']]+=1
            ids=sorted(i for i in expected if counts[i]);s=np.array([sums[i] for i in ids]);n=np.array([counts[i] for i in ids])
            rng=np.random.default_rng(11012026);est=[]
            for _ in range(40):
                take=rng.integers(0,len(ids),(100,len(ids)));est.extend((s[take].sum(1)/n[take].sum(1)).tolist())
            interval=np.quantile(est,[.025,.975]);assert np.allclose(interval,old['ambiguous_gain_uncertainty']['whole_game_bootstrap_95'],atol=1e-12)
            stats['bootstrap_95']=interval.tolist()
            refs={manifest['teams'].index(x) for x in ['Instructors','duck','HYPOTHERMIA']}
            rg=np.mean([d for r,d in zip(amb,delta) if r['team_id'] in refs])
            stats['reference_ambiguous_gain']=float(rg)
            stats['passes']=bool(interval[0]>0 and nll_delta<=.005 and rg>=-.01)
            assert stats['passes']==old['passes_test']
        else:
            stats['passes']=bool(delta.mean()>=.02 and nll_delta<=.005)
            assert stats['passes']==old['passes_validation']
        report['splits'][split]=stats
    report['earns_belief_integration']=all(x['passes'] for x in report['splits'].values())
    report['scope']='Predictive fit plus native parity only; no capped belief, guard, search, or strength claim.'
    (p/'predictive-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
