"""Run the pinned, already-trained attention danger head on the frozen panel.

No fitting, selector changes, v35 risk fusion or privileged inputs. The legacy
probe's particle estimates are retained as raw diagnostics but are NOT v35 risk
and must not be used as a replacement for it. Only neural scores are assessed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
PANEL=ROOT/'astra-submissions/analysis/hidden-slider-zone-20261025/independent-audit-512/teacher-readiness-panel.json'
PROBE=ROOT/'astra-submissions/build/neural-risk-r1/probe'
MODEL=Path('/media/henrytan/seagate1/iamavirus/astra/representations/capacity-v4-full3766-20261008/attention-small-export')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def actor_stream(case,replay):
    side=0 if case['side']=='white' else 1
    lines=[f"START {case['game']} {side}"]
    for i,frame in enumerate(replay['frames'][:case['frame']+1]):
        assert frame['ply']==i
        phase=0 if i==0 else 1 if (i-1)%2==side else 2
        lines.append(f"OBS {i} {phase} {frame[case['side']]}")
        if i<case['frame'] and i%2==side:
            lines.append('MOVE '+replay['frames'][i+1]['move'])
    assert case['frame']%2==side
    lines += [f"SCORE {case['frame']}",'END']
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--model',type=Path,default=MODEL)
    p.add_argument('--panel',type=Path,default=PANEL)
    p.add_argument('--wall-cap',type=float,default=300)
    p.add_argument('--limit',type=int,default=0)
    a=p.parse_args()
    receipt=json.load(open(ROOT/'astra-submissions/analysis/neural-risk/run-20261011/state.json'))
    paths=[PROBE,ROOT/'astra-submissions/build/neural-risk-r1/probe-build.json',
           *(a.model/name for name in ['model_manifest.json','observe.onnx','score.onnx'])]
    verified={}
    for path in paths:
        old=str(path).replace('/media/henrytan/seagate1/','/media/henrytan/seagate/')
        expected=receipt['inputs'][old]
        actual=sha(path)
        if actual!=expected:raise RuntimeError('Pinned artifact changed: '+str(path))
        verified[str(path)]=actual
    panel=json.loads(a.panel.read_bytes())
    cases=panel['cases'][:a.limit] if a.limit else panel['cases']
    env={k:v for k,v in os.environ.items() if not k.startswith(('FOW_','ASTRA_'))}
    # NeuralTracker/model inputs do not depend on the Engine's particle count.
    # The one-particle legacy diagnostic is deliberately not used in analysis.
    settings={'FOW_MODE':'hybrid','FOW_PARTICLES':'1','FOW_OPPONENT_PRIOR':'1',
              'FOW_PREDICTION_MODE':'0','FOW_HISTORY_MODE':'0','FOW_FRONTIER_CAPACITY':'0',
              'FOW_ROOT_MODE':'0','FOW_CELL_THREADS':'1','FOW_BOOK_PLIES':'0',
              'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
    env.update(settings)
    rows=[]; failures=[]
    start=time.monotonic()
    for case in cases:
        remaining=a.wall_cap-(time.monotonic()-start)
        if remaining<=0 or len(failures)>=5:break
        path=ROOT/case['replay']
        if sha(path)!=case['replay_sha256']:raise RuntimeError('Panel replay changed')
        protocol=actor_stream(case,json.loads(path.read_bytes()))
        began=time.monotonic()
        try:
            proc=subprocess.run([str(PROBE),str(a.model)],input=protocol,
                                text=True,capture_output=True,env=env,
                                timeout=min(30,remaining))
            if proc.returncode:raise RuntimeError(proc.stderr[-1200:])
            outputs=[json.loads(line) for line in proc.stdout.splitlines()]
            assert len(outputs)==1
            row=outputs[0]
            assert row['game']==case['game'] and row['ply']==case['frame']
            assert row['side']==(0 if case['side']=='white' else 1)
            rows.append({'case':case,'actor_protocol':protocol,
                         'actor_protocol_sha256':hashlib.sha256(protocol.encode()).hexdigest(),
                         'native_prediction':row,'wall_seconds':time.monotonic()-began})
        except (AssertionError,RuntimeError,subprocess.TimeoutExpired) as error:
            failures.append({'game':case['game'],'frame':case['frame'],'error':str(error)})
        print(f'neural cases={len(rows)+len(failures)}/{len(cases)} failures={len(failures)}',
              file=sys.stderr,flush=True)
    print(json.dumps({'classification':'existing frozen model inference only; no training or choice change',
                      'panel_sha256':sha(a.panel),'collector_sha256':sha(Path(__file__)),
                      'verified_artifacts':verified,'settings':settings,
                      'legacy_particle_field_used':False,'gpu_used':False,
                      'wall_cap_seconds':a.wall_cap,'requested_cases':len(cases),
                      'wall_seconds':time.monotonic()-start,'failures':failures,'cases':rows},indent=2))


if __name__=='__main__':main()
