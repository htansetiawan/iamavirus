"""A bounded reused-development complementarity check, never a strength gate."""
from collections import Counter, defaultdict
from datetime import datetime,timezone
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tarfile
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/recurrent-risk-complement-20261102'
OLD=ROOT/'astra-submissions/analysis/king-event-calibration-20261101'
RECOVERY=ROOT/'astra-submissions/analysis/neural-risk-recovery-20261102'
sys.path.insert(0,str(RECOVERY));sys.path.insert(0,str(ROOT/'astra-submissions/tools'))
import recovery
import analyze_neural_risk as calibration


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def prepare():
    assert json.loads((RECOVERY/'receipt.json').read_text())['passed']
    old=json.loads((OLD/'plan.json').read_text())
    games=sorted((dict(g) for g in old['games'] if g['split']=='train'),
                 key=lambda g:(datetime.fromisoformat(g['createdAt'].replace('Z','+00:00')),g['game']))
    assert len(games)==80 and len({g['sequence_sha256'] for g in games})==80
    for i,g in enumerate(games):g['role']='fit' if i<50 else 'development'
    deps=[Path(__file__),HERE/'README.md',RECOVERY/'recovery.py',RECOVERY/'receipt.json',
          *[RECOVERY/'cache'/n for n in ('model_manifest.json','observe.onnx','score.onnx')],
          Path(calibration.__file__),OLD/'plan.json',OLD/'collected-games.tar.gz',
          *[ROOT/'learning'/n for n in ('features.py','action_codec.py','rules.py')]]
    OUT.mkdir(exist_ok=True)
    plan=dict(at=datetime.now(timezone.utc).isoformat(),games=games,deps={str(p):sha(p) for p in deps},
              clip=calibration.CLIP,ridge=calibration.RIDGE,core=6,wall_seconds=600,
              source_scope='Original TRAIN games only, reused development; no independent confirmation claim.',
              gate='Positive neural coefficient; >=2% log-loss reduction, lower Brier, no worse played log loss, lower within-decision ranking error. Earns only a fresh v37 confirmation proposal.')
    write('plan.json',plan)
    print(json.dumps({'plan_sha256':sha(OUT/'plan.json'),'games':80,'fit':50,'development':30}))


def load():
    plan=json.loads((OUT/'plan.json').read_text())
    for p,h in plan['deps'].items():assert sha(p)==h,p
    for g in plan['games']:assert sha(g['replay_path'])==g['replay_sha256'],g['game']
    return plan


def ranking(decisions,probability):
    """Mean pairwise error per mixed decision, sorting rather than M squared."""
    total=0.0;mixed=0;unmixed=0;by_game=defaultdict(lambda:[0.0,0])
    for d in decisions:
        values=sorted((probability(d,c),c['y']) for c in d['candidates'])
        positives=sum(y for _,y in values);negatives=len(values)-positives
        if not positives or not negatives:unmixed+=1;continue
        seen_positive=0;error=0.0;i=0
        while i<len(values):
            j=i+1
            while j<len(values) and values[j][0]==values[i][0]:j+=1
            pos=sum(y for _,y in values[i:j]);neg=j-i-pos
            error+=neg*seen_positive+0.5*pos*neg
            seen_positive+=pos;i=j
        e=error/(positives*negatives);total+=e;mixed+=1
        by_game[d['game']][0]+=e;by_game[d['game']][1]+=1
    return dict(error=total/mixed if mixed else None,mixed_decisions=mixed,unmixed_decisions=unmixed,by_game=dict(by_game))


def execute():
    plan=load();os.sched_setaffinity(0,{plan['core']});started=time.monotonic()
    write('started.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),plan_sha256=sha(OUT/'plan.json')))
    ort=recovery.ort;options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
    options.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
    observe=ort.InferenceSession(str(RECOVERY/'cache/observe.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
    score=ort.InferenceSession(str(RECOVERY/'cache/score.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
    assert observe.get_providers()==score.get_providers()==['CPUExecutionProvider']
    groups={'fit':[],'development':[]};played={'fit':[],'development':[]};provenance=[]
    with tarfile.open(OLD/'collected-games.tar.gz','r:gz') as archive,(OUT/'joined.jsonl.gz').open('xb') as stream:
        with gzip.GzipFile(filename='',fileobj=stream,mode='wb',mtime=0) as zipped:
            for index,case in enumerate(plan['games']):
                gid=case['game'];side=('white','black').index(case['side'])
                original=[json.loads(line) for line in archive.extractfile('games/'+gid+'.jsonl')]
                candidates=defaultdict(list);labels={}
                for r in original:
                    assert r['split']=='train';key=(r['ply'],r['move']);assert key not in labels
                    candidates[r['ply']].append(r['move']);labels[key]=r
                replay=json.loads(Path(case['replay_path']).read_text())
                actor=recovery.actor_stream(replay,side,dict(candidates))
                predictions,hashes,_=recovery.predict(actor,observe,score)
                assert len(predictions)==len(candidates)
                for prediction in predictions:
                    ply=prediction['ply'];records=[];played_records=[]
                    for move,logit in zip(prediction['moves'],prediction['danger']):
                        original_row=labels[(ply,move)]
                        c=dict(particle_x=calibration.logit(original_row['sharp']),neural_x=logit,
                               y=original_row['fatal'],particle=original_row['sharp'],neural_logit=logit,
                               king_move=original_row['king_move'],ply=ply,move=move,played=original_row['played'])
                        records.append(c)
                        if c['played']:played_records.append(c)
                    d=dict(game=gid,side=side,ply=ply,event=ply,candidates=records)
                    groups[case['role']].append(d)
                    assert len(played_records)<=1
                    if played_records:played[case['role']].append(dict(d,candidates=played_records))
                    zipped.write((json.dumps(dict(role=case['role'],**d))+'\n').encode())
                provenance.append(dict(game=gid,role=case['role'],decisions=len(predictions),
                    candidates=len(original),replay_sha256=case['replay_sha256'],
                    feature_sequence_sha256=hashlib.sha256(''.join(hashes).encode()).hexdigest()))
                if (index+1)%10==0:print(json.dumps({'scored_games':index+1,'seconds':time.monotonic()-started}),flush=True)
    write('collection.json',dict(games=provenance,joined_sha256=sha(OUT/'joined.jsonl.gz'),seconds=time.monotonic()-started))
    means,scales=calibration.weighted_standardize(groups['fit'])
    data=calibration.rows(groups['fit'],means,scales)
    fitted={};metrics={};ranks={};played_metrics={}
    for name,active in (('particle',[1]),('fusion',[1,2])):
        fitted[name]=calibration.fit(data,active)
        beta=fitted[name]['beta']
        def predictor(d,c):
            return calibration.score(beta,[1.,(c['particle_x']-means[0])/scales[0],(c['neural_x']-means[1])/scales[1]])
        metrics[name]=calibration.weighted_metrics(groups['development'],predictor)
        played_metrics[name]=calibration.weighted_metrics(played['development'],predictor)
        ranks[name]=ranking(groups['development'],predictor)
        print(json.dumps({'fitted':name,'beta':beta,'seconds':time.monotonic()-started}),flush=True)
    a,b=metrics['particle'],metrics['fusion'];ra,rb=ranks['particle'],ranks['fusion']
    conditions=dict(neural_coefficient_positive=fitted['fusion']['beta'][2]>0,
        log_loss_gain_at_least_2pct=b['log_loss']<=.98*a['log_loss'],brier_lower=b['brier']<a['brier'],
        played_log_loss_no_worse=played_metrics['fusion']['log_loss']<=played_metrics['particle']['log_loss'],
        ranking_error_lower=ra['error'] is not None and rb['error'] is not None and rb['error']<ra['error'])
    report=dict(at=datetime.now(timezone.utc).isoformat(),status='complete',elapsed_seconds=time.monotonic()-started,
        fitted=fitted,means=means,scales=scales,development_metrics=metrics,played_metrics=played_metrics,ranking=ranks,
        paired_bootstrap=calibration.paired_bootstrap(a,b,seed=2451102),
        conditions=conditions,earns_fresh_confirmation_proposal=all(conditions.values()),
        plan_sha256=sha(OUT/'plan.json'),collection_sha256=sha(OUT/'collection.json'),source_sha256=sha(__file__),
        scope='Reused TRAIN pool split50/30, frozen old network and v35 risks. Development complementarity only; no current-engine integration, fresh confirmation, GPU, neural fitting or Elo result.')
    write('report.json',report)
    print(json.dumps({'conditions':conditions,'earns_fresh_confirmation_proposal':all(conditions.values()),'seconds':report['elapsed_seconds']}),flush=True)


if __name__=='__main__':
    assert sys.argv[1] in ('prepare','execute');globals()[sys.argv[1]]()
