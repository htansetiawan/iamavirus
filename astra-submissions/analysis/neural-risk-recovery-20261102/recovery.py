"""Recover exact legacy risk graphs and check current actor-history scoring.

Two old calibration TRAIN games, both colours. No fitting, tactical label
evaluation, GPU, playing-engine change or claim of predictive improvement.
"""
from collections import defaultdict
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tarfile
import time

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT))
import numpy as np
import onnxruntime as ort
from learning import features


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def actor_stream(replay,side,candidates):
    key=('white','black')[side]
    return dict(side=side,observations=[f[key] for f in replay['frames']],
                own_moves={i:replay['frames'][i+1]['move'] for i in range(side,len(replay['frames'])-1,2)},
                candidates=candidates)


def predict(actor,observe,score,permuted=False):
    side=actor['side'];tracker=features.FeatureTracker(side)
    hidden=np.zeros((1,256),dtype=np.float32);rows=[];hashes=[];reset_differences=[]
    for ply,view in enumerate(actor['observations']):
        phase=features.PHASE_INITIAL if ply==0 else (features.PHASE_AFTER_OWN if (ply-1)%2==side else features.PHASE_AFTER_OPPONENT)
        tracker.observe(view,phase,ply)
        planes,scalars=tracker.planes()[None],tracker.scalars()[None]
        hashes.append(hashlib.sha256(planes.tobytes()+scalars.tobytes()).hexdigest())
        hidden,spatial,belief,value=observe.run(None,dict(planes=planes,scalars=scalars,hidden=hidden))
        assert all(np.isfinite(x).all() for x in (hidden,spatial,belief,value))
        if ply in actor['candidates']:
            moves=actor['candidates'][ply]
            if permuted:moves=moves[::-1]
            _,src,dst,promo=features.candidate_arrays(moves,side)
            feed=dict(next_hidden=hidden,spatial=spatial,candidate_from=src[None],candidate_to=dst[None],promotion=promo[None])
            policy,danger=score.run(None,feed)
            assert policy.shape==danger.shape==(1,len(moves))
            assert np.isfinite(policy).all() and np.isfinite(danger).all()
            rows.append(dict(ply=ply,moves=moves,policy=policy[0].tolist(),danger=danger[0].tolist()))
            if ply>0 and not reset_differences:
                fresh=observe.run(None,dict(planes=planes,scalars=scalars,hidden=np.zeros((1,256),dtype=np.float32)))[0]
                reset_differences.append(float(np.max(np.abs(hidden-fresh))))
        if ply in actor['own_moves']:tracker.record_own_move(actor['own_moves'][ply])
    return rows,hashes,reset_differences


def main():
    os.sched_setaffinity(0,{6});started=time.monotonic()
    original=ROOT/'astra-submissions/analysis/neural-risk/run-20261011/state.json'
    old=json.loads(original.read_text())
    source=Path('/media/henrytan/seagate/git/iamavirus-data/astra-legacy/representations/capacity-v4-full3766-20261008/attention-small-export')
    cache=OUT/'cache';cache.mkdir(exist_ok=False);assets={}
    for name in ('model_manifest.json','observe.onnx','score.onnx'):
        wanted=next(h for p,h in old['inputs'].items() if p.endswith('/attention-small-export/'+name))
        payload=(source/name).read_bytes();assert hashlib.sha256(payload).hexdigest()==wanted,name
        (cache/name).write_bytes(payload)
        assets[name]=dict(source=str(source/name),sha256=wanted,bytes=len(payload))
    manifest=json.loads((cache/'model_manifest.json').read_text())
    assert manifest['feature_version']==features.FEATURE_VERSION=='features-v2'
    assert manifest['action_version']=='actions-v1' and manifest['parity']['failure_count']==0
    options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
    options.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
    observe=ort.InferenceSession(str(cache/'observe.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
    score=ort.InferenceSession(str(cache/'score.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
    assert observe.get_providers()==score.get_providers()==['CPUExecutionProvider']
    prior=ROOT/'astra-submissions/analysis/king-event-calibration-20261101'
    plan=json.loads((prior/'plan.json').read_text())
    selected=[next(c for c in plan['games'] if c['split']=='train' and c['side']==side) for side in ('white','black')]
    results=[]
    with tarfile.open(prior/'collected-games.tar.gz','r:gz') as archive:
        for case in selected:
            side=('white','black').index(case['side']);gid=case['game'];candidates=defaultdict(list)
            for line in archive.extractfile('games/'+gid+'.jsonl'):
                row=json.loads(line);assert row['split']=='train'
                candidates[row['ply']].append(row['move'])  # No risk or label enters the predictor.
            for moves in candidates.values():assert len(moves)==len(set(moves))
            path=Path(case['replay_path']);assert sha(path)==case['replay_sha256']
            replay=json.loads(path.read_text());actor=actor_stream(replay,side,dict(candidates))
            altered=copy.deepcopy(replay)
            for i,f in enumerate(altered['frames']):
                f['board']='X'*64;f[('black','white')[side]]='X'*64;f['clocks']=[-999,-999]
                if i and (i-1)%2!=side:f['move']='zzzz'
            altered.update(id='ignored',result='ignored',white='ignored',black='ignored')
            assert actor_stream(altered,side,dict(candidates))==actor
            rows,hashes,reset=predict(actor,observe,score)
            reversed_rows,hashes2,_=predict(actor,observe,score,permuted=True)
            assert hashes==hashes2
            error=0.0
            for a,b in zip(rows,reversed_rows):
                assert a['ply']==b['ply'] and a['moves']==b['moves'][::-1]
                for name in ('policy','danger'):
                    error=max(error,float(np.max(np.abs(np.array(a[name])-np.array(b[name][::-1])))))
            assert error<1e-5,error
            assert reset and reset[0]>1e-6,'Recurrent history should affect the hidden state'
            write(gid+'-predictions.json',dict(game=gid,side=side,rows=rows))
            results.append(dict(game=gid,side=side,split='train',replay_sha256=sha(path),
                observations=len(actor['observations']),decisions=len(rows),candidates=sum(len(r['moves']) for r in rows),
                feature_sequence_sha256=hashlib.sha256(''.join(hashes).encode()).hexdigest(),
                permutation_max_abs=error,history_reset_hidden_difference=reset[0],
                predictions_sha256=sha(OUT/(gid+'-predictions.json'))))
    write('receipt.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,assets=assets,games=results,
          elapsed_seconds=time.monotonic()-started,providers=observe.get_providers(),threads=1,
          source_sha256=sha(__file__),original_receipt_sha256=sha(original),
          data_plan_sha256=sha(prior/'plan.json'),data_archive_sha256=sha(prior/'collected-games.tar.gz'),
          feature_sources={n:sha(ROOT/'learning'/n) for n in ('features.py','action_codec.py','rules.py')},
          scope='Asset hash recovery, actor-input boundary, finite CPU inference, candidate permutation and recurrent-state sensitivity only. Two TRAIN games; no tactical-label evaluation, fitting, current-engine integration, GPU or strength claim.'))
    print(json.dumps(dict(passed=True,games=len(results),observations=sum(r['observations'] for r in results),
                         decisions=sum(r['decisions'] for r in results),candidates=sum(r['candidates'] for r in results),
                         elapsed_seconds=time.monotonic()-started)))


if __name__=='__main__':main()
