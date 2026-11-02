"""Independently check joined labels, model parity, metrics and ranking."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import tarfile

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
OLD=OUT.parent/'king-event-calibration-20261101'
RECOVERY=OUT.parent/'neural-risk-recovery-20261102'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    os.sched_setaffinity(0,{6})
    plan=json.loads((OUT/'plan.json').read_text());report=json.loads((OUT/'report.json').read_text())
    collection=json.loads((OUT/'collection.json').read_text())
    assert report['status']=='complete' and not report['earns_fresh_confirmation_proposal']
    for p,h in plan['deps'].items():assert sha(p)==h,p
    assert sha(OUT/'plan.json')==report['plan_sha256']
    assert sha(OUT/'collection.json')==report['collection_sha256']
    assert sha(OUT/'joined.jsonl.gz')==collection['joined_sha256']
    cases={g['game']:g for g in plan['games']};truth={}
    with tarfile.open(OLD/'collected-games.tar.gz','r:gz') as archive:
        for gid in cases:
            for line in archive.extractfile('games/'+gid+'.jsonl'):
                r=json.loads(line);assert r['split']=='train';k=(gid,r['ply'],r['move']);assert k not in truth
                truth[k]=r
    rows=[json.loads(line) for line in gzip.open(OUT/'joined.jsonl.gz','rt')]
    seen=set();seen_decisions=set();counts=Counter();preflight={}
    for p in RECOVERY.glob('*-predictions.json'):
        r=json.loads(p.read_text())
        for d in r['rows']:
            for move,value in zip(d['moves'],d['danger']):preflight[(r['game'],d['ply'],move)]=value
    parity=0;max_error=0.
    for d in rows:
        assert d['role']==cases[d['game']]['role'];counts[d['role']]+=1
        dk=(d['game'],d['ply']);assert dk not in seen_decisions;seen_decisions.add(dk)
        assert sum(c['played'] for c in d['candidates'])<=1
        for c in d['candidates']:
            k=(*dk,c['move']);assert k not in seen;seen.add(k);r=truth[k]
            assert c['y']==r['fatal'] and c['particle']==r['sharp'] and c['played']==r['played']
            assert c['king_move']==r['king_move'] and math.isfinite(c['neural_logit'])
            assert c['neural_x']==c['neural_logit']
            if k in preflight:
                parity+=1;max_error=max(max_error,abs(c['neural_logit']-preflight[k]))
    assert seen==set(truth) and parity==len(preflight) and max_error<1e-5
    metrics={}
    for name in ('particle','fusion'):
        beta=report['fitted'][name]['beta'];means,scales=report['means'],report['scales']
        loss=brier=played_loss=played_brier=rank_error=0.;n=pn=mixed=unmixed=0
        for d in rows:
            if d['role']!='development':continue
            n+=1;positive=[];negative=[]
            for c in d['candidates']:
                p=min(1-1e-4,max(1e-4,c['particle']))
                x=math.log(p)-math.log1p(-p)
                z=beta[0]+beta[1]*(x-means[0])/scales[0]+beta[2]*(c['neural_logit']-means[1])/scales[1]
                predicted=1/(1+math.exp(-z));predicted=min(1-1e-12,max(1e-12,predicted))
                y=c['y'];ll=-(y*math.log(predicted)+(1-y)*math.log1p(-predicted));bs=(predicted-y)**2
                loss+=ll/len(d['candidates']);brier+=bs/len(d['candidates'])
                (positive if y else negative).append(predicted)
                if c['played']:pn+=1;played_loss+=ll;played_brier+=bs
            if positive and negative:
                mixed+=1
                rank_error+=sum((a<b)+.5*(a==b) for a in positive for b in negative)/(len(positive)*len(negative))
            else:unmixed+=1
        values=dict(log_loss=loss/n,brier=brier/n,played_log_loss=played_loss/pn,
                    played_brier=played_brier/pn,ranking_error=rank_error/mixed)
        for k in ('log_loss','brier'):assert abs(values[k]-report['development_metrics'][name][k])<1e-12
        for k in ('log_loss','brier'):assert abs(values['played_'+k]-report['played_metrics'][name][k])<1e-12
        assert abs(values['ranking_error']-report['ranking'][name]['error'])<1e-12
        assert mixed==report['ranking'][name]['mixed_decisions'] and unmixed==report['ranking'][name]['unmixed_decisions']
        metrics[name]=values
    result=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,games=len(cases),decisions=dict(counts),
                candidates=len(seen),preflight_candidate_parity=parity,preflight_max_abs=max_error,
                independent_metrics=metrics,report_sha256=sha(OUT/'report.json'),source_sha256=sha(__file__),
                scope='All joined labels match original TRAIN data. Independent scalar metric and exhaustive real-decision pair ranking checks; not a generalization or playing-strength test.')
    with (OUT/'audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='independent_metrics'}))


if __name__=='__main__':main()
