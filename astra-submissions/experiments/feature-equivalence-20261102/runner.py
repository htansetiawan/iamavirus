from collections import defaultdict
import gzip
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback
import numpy as np
from settings import HERE,ROOT,OUT,now,sha,unique
from extract_augmented import collect
from bound import audit,log_probabilities,uci,lse


def group_mean(rows,field):
    games=defaultdict(list)
    for row in rows:games[row['metadata']['game']].append(field(row))
    return float(np.mean([np.mean(v) for v in games.values()])) if games else None


def summary(records):
    result={}
    for name,pick in {'all':lambda r:True,'primary':lambda r:r['primary'],
                      'late':lambda r:r['primary'] and r['late'],'surprise':lambda r:r['primary'] and r['surprise']}.items():
        rows=[r for r in records if pick(r['metadata'])]
        result[name]=dict(cases=len(rows),games=len({r['metadata']['game'] for r in rows}),
            cases_with_feature_floor=sum(r['features']['nll_floor']>1e-9 for r in rows),
            games_with_feature_floor=len({r['metadata']['game'] for r in rows if r['features']['nll_floor']>1e-9}),
            feature_floor=group_mean(rows,lambda r:r['features']['nll_floor']),
            geometry_floor=group_mean(rows,lambda r:r['geometry']['nll_floor']),
            parent_local_floor=group_mean(rows,lambda r:r['parent_local']['nll_floor']),
            geometry_parent_local_floor=group_mean(rows,lambda r:r['geometry_parent_local']['nll_floor']),
            cases_with_parent_local_floor=sum(r['parent_local']['nll_floor']>1e-9 for r in rows),
            bound_reduction=group_mean(rows,lambda r:r['features']['nll_floor']-r['geometry']['nll_floor']),
            baseline_nll=group_mean(rows,lambda r:r['models']['baseline']),
            quadratic_posterior_nll=group_mean(rows,lambda r:r['models']['quadratic-posterior']))
    return result


def witness(row,record,index):
    bound,ids,groups=audit(row);edge=int(np.flatnonzero(row['actor_edge'])[0]);group=groups[ids[edge]]
    alternatives=group[~row['positive'][group]]
    if not len(alternatives):return None
    path=OUT/'witnesses'/f'{index:02d}-{row["meta"]["game"]}-{row["meta"]["ply"]}.npz'
    arrays={k:v for k,v in row.items() if k!='meta'}
    with path.open('xb') as f:np.savez_compressed(f,**arrays)
    candidates=[]
    for other in alternatives[:12]:
        candidates.append(dict(move=uci(row['moves'][other]),parent=int(row['a_parent'][other]),
            same_parent=int(row['a_parent'][other])==int(row['a_parent'][edge]),edge=int(other)))
    return dict(metadata=row['meta'],features=record['features'],geometry=record['geometry'],parent_local=record['parent_local'],
        true_move=uci(row['moves'][edge]),true_edge=edge,true_parent=int(row['a_parent'][edge]),
        alternatives=candidates,path=str(path.relative_to(ROOT)),sha256=sha(path))


def main():
    plan=json.loads((OUT/'plan.json').read_text());start=time.monotonic();os.sched_setaffinity(0,set(plan['cores']))
    for p,h in plan['dependencies'].items():assert sha(Path(p))==h,p
    def expired(*args):raise TimeoutError('Frozen20minute audit bound')
    signal.signal(signal.SIGALRM,expired);signal.alarm(plan['wall_seconds'])
    unique(OUT/'execution.json',dict(at=now(),pid=os.getpid(),pid_scope='exec sandbox',
        start_ticks=Path('/proc/self/stat').read_text().split()[21],plan_sha256=sha(OUT/'plan.json'),status='started'))
    try:
        cases=collect(plan,'validation')
        old=json.loads(Path(plan['previous_data']).read_text());new=json.loads((OUT/'validation-data.json').read_text())
        assert old['features_sha256']==new['features_sha256'] and old['games']==new['games']
        assert sum(v.nbytes for row in cases for v in row.values() if isinstance(v,np.ndarray))<=plan['max_feature_bytes']
        selected=json.loads(Path(plan['previous_selection']).read_text())
        models={k:(np.array(v['linear']),np.array(v['quadratic'])) for k,v in selected.items()}
        models['baseline']=(np.zeros(26),np.zeros((26,26)))
        previous=[json.loads(line) for line in gzip.open(plan['previous_scores'],'rt')];assert len(previous)==len(cases)
        records=[];extra=hashlib.sha256();checked=0;worst_violation=0.;group_variation=0.
        for index,(row,prior) in enumerate(zip(cases,previous)):
            assert row['meta']==prior['metadata'] and row['meta']['natural_support']
            for name in ('moves','successor_keys','parent_rows'):extra.update(row[name].tobytes())
            assert np.array_equal(row['parent_rows']['base'],row['u'])
            normal,_,groups=audit(row);geometry,_,_=audit(row,True)
            local,_,_=audit(row,parent_local=True);local_geometry,_,_=audit(row,geometry=True,parent_local=True)
            assert normal['supported'] and geometry['supported']
            assert geometry['nll_floor']<=normal['nll_floor']+1e-10
            assert local['nll_floor']<=normal['nll_floor']+1e-10
            assert local_geometry['nll_floor']==0
            nll={};x=row['x'].astype(float)
            for key,(linear,q) in models.items():
                logits=row['base'].astype(float)+x@linear+np.einsum('ni,ij,nj->n',x,q,x)
                logp,action_logs=log_probabilities(row,logits);nll[key]=-logp
                assert abs(max(logp,np.log(1e-12))-prior['predictions'][key]['posterior_logp'])<1e-8
                violation=logp+normal['nll_floor'];worst_violation=max(worst_violation,violation)
                assert violation<1e-9,(row['meta'],key,violation)
                for g in groups:
                    if len(g)<2:continue
                    variation=float(np.ptp(action_logs[g]));group_variation=max(group_variation,variation)
                    assert variation<1e-10
                checked+=1
            records.append(dict(metadata=row['meta'],features=normal,geometry=geometry,parent_local=local,geometry_parent_local=local_geometry,models=nll))
        with (OUT/'bounds.jsonl.gz').open('xb') as raw:
            with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as gz:
                for r in records:gz.write((json.dumps(r,allow_nan=False)+'\n').encode())
        # Fixed descriptive witness rule; this does not select a model or change a gate.
        ranking=sorted(range(len(records)),key=lambda i:(-(records[i]['features']['nll_floor']-records[i]['geometry']['nll_floor']),records[i]['metadata']['game'],records[i]['metadata']['ply']))
        (OUT/'witnesses').mkdir();witnesses=[];used=set()
        for surprise,limit in ((False,plan['witness_limit']),(True,plan['witness_surprise_limit'])):
            taken=0
            for i in ranking:
                r=records[i];meta=r['metadata']
                if meta['game'] in used or (surprise and not meta['surprise']):continue
                if r['features']['nll_floor']-r['geometry']['nll_floor']<=1e-9:continue
                w=witness(cases[i],r,len(witnesses))
                if w is None:continue
                witnesses.append(w);used.add(meta['game']);taken+=1
                if taken==limit:break
        unique(OUT/'witnesses.json',witnesses)
        result=dict(at=now(),elapsed=time.monotonic()-start,metrics=summary(records),
            model_case_checks=checked,maximum_bound_violation=worst_violation,maximum_group_logp_variation=group_variation,
            extra_export_sha256=extra.hexdigest(),unchanged_feature_sha256=new['features_sha256'],
            bounds_sha256=sha(OUT/'bounds.jsonl.gz'),witnesses=len(witnesses),plan_sha256=sha(OUT/'plan.json'),scope=plan['scope'])
        unique(OUT/'result.json',result);print(json.dumps(result),flush=True)
        unique(OUT/'terminal.json',dict(at=now(),status='complete',elapsed=time.monotonic()-start))
    except BaseException as exc:
        unique(OUT/'terminal.json',dict(at=now(),status='failed',error=repr(exc),traceback=traceback.format_exc()));raise
    finally:signal.alarm(0)


if __name__=='__main__':main()
