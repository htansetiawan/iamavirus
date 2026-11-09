"""Frozen16-game full-clock pilot, isolated first attempts and failure stop."""
from datetime import datetime,timezone
import concurrent.futures as futures
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import zipfile

from prepare import HERE,ROOT,OUT,BUILD,PROTO,sha,write
sys.path.insert(0,str(ROOT))
from learning import compare_archives as ca, rules

PILOT=OUT/'full-games';PBUILD=HERE/'build/pilot'


def now():return datetime.now(timezone.utc).isoformat()


def prepare():
    review=json.loads((OUT/'review.json').read_text());assert review['gate_pass']
    PILOT.mkdir(exist_ok=False);PBUILD.mkdir(parents=True,exist_ok=False)
    parent=ROOT/'astra-submissions/iamavirus-v38-mist-c-allchildren.zip'
    candidate=PBUILD/'guard-either-research.zip'
    with zipfile.ZipFile(parent) as z:content={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    content['src/main.c']=(PROTO/'src/main.c').read_bytes();content['src/guard_envelope.h']=(PROTO/'src/guard_envelope.h').read_bytes()
    text=content['run.sh'].decode();assert text.count('exec ./mist')==1
    content['run.sh']=text.replace('exec ./mist','export ASTRA_GUARD_EITHER=1\nexec ./mist').encode()
    content['ASTRA-GUARD-EXPERIMENT.md']=b'Local unversioned research only. Parent arena v38; adds either-weighting guard action support. No playing-strength claim or arena release. Source in astra-submissions/experiments/guard-disagreement-20261109.\n'
    with zipfile.ZipFile(candidate,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,data in sorted(content.items()):
            info=zipfile.ZipInfo(name);info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o100755 if name.endswith('.sh') or name=='bin/stockfish' else 0o100644)<<16;z.writestr(info,data)
    builds=PBUILD/'extracted';builds.mkdir()
    original=ca.build(parent,builds);modified=ca.build(candidate,builds)
    jobs=[]
    for pair in range(8):
        for side in ('white','black'):jobs.append(dict(id=f'p{pair}-{side}',pair=pair,lane=pair%2,side=side,seed=2701200+2*pair))
    deps=[HERE/'pilot.py',ROOT/'learning/compare_archives.py',ROOT/'learning/rules.py',ROOT/'learning/_native.py',
          Path('/home/henrytan/git/fow-starter/referee.py'),parent,candidate]
    for root in (original,modified):deps +=[p for p in root.rglob('*') if p.is_file() and (p.name in ('mist','stockfish','history.bin','run.sh','build.sh') or p.suffix in ('.c','.h'))]
    write(PILOT/'plan.json',dict(at=now(),candidate=str(candidate),candidate_sha256=sha(candidate),parent=str(parent),parent_sha256=sha(parent),
          candidate_build=str(modified),parent_build=str(original),jobs=jobs,slots={'0':[0,1],'1':[2,3]},
          wall_seconds=10800,per_game_seconds=2450,base_seconds=180,increment_seconds=2,
          min_points=10,gate='16clean games,>=10points to earn further opponent test; no release',
          stop_on_any_technical=True,control_review_sha256=sha(OUT/'review.json'),dependencies={str(p):sha(p) for p in deps},
          scope='Small development duel against exactv38; not an arena-strength estimate. No failed attempt replaced.'))
    write(PILOT/'build.json',dict(parent_binary_sha256=sha(original/'mist'),candidate_binary_sha256=sha(modified/'mist'),
         candidate_archive_sha256=sha(candidate),changed_playing_files=['src/main.c','src/guard_envelope.h','run.sh']))
    print(json.dumps(dict(prepared=True,candidate_sha256=sha(candidate),plan_sha256=sha(PILOT/'plan.json'))),flush=True)


def main():
    plan=json.loads((PILOT/'plan.json').read_text())
    for name,digest in plan['dependencies'].items():assert sha(Path(name))==digest,name
    assert json.loads((OUT/'review.json').read_text())['gate_pass'] and sha(OUT/'review.json')==plan['control_review_sha256']
    # Preserve the reserved parent/candidate byte mapping; inherited experiment
    # variables must not silently turn the parent into a different engine.
    for key in list(os.environ):
        if key.startswith(('MIST_','ASTRA_','FOW_')):os.environ.pop(key)
    start=time.monotonic();stop=threading.Event();write(PILOT/'started.json',dict(at=now(),pid=os.getpid(),plan_sha256=sha(PILOT/'plan.json')))
    kit=Path('/home/henrytan/git/fow-starter');python=kit/'.venv/bin/python'
    def execute_lane(number):
        records=[];cores=','.join(map(str,plan['slots'][str(number)]))
        for job in [j for j in plan['jobs'] if j['lane']==number]:
            if stop.is_set():break
            if time.monotonic()-start+plan['per_game_seconds']>plan['wall_seconds']:stop.set();break
            folder=PILOT/'jobs'/job['id'];folder.mkdir(parents=True,exist_ok=False)
            write(folder/'started.json',dict(at=now(),job=job))
            white=plan['candidate_build'] if job['side']=='white' else plan['parent_build'];black=plan['parent_build'] if job['side']=='white' else plan['candidate_build']
            cmd=['taskset','-c',cores,str(python),str(kit/'referee.py'),'--trusted-local',
                 '--white',f"env FOW_SEED={job['seed']} bash {white}/run.sh",'--black',f"env FOW_SEED={job['seed']+1} bash {black}/run.sh",
                 '--white-name','candidate' if job['side']=='white' else 'v38','--black-name','v38' if job['side']=='white' else 'candidate',
                 '--base-time','180','--increment','2','--max-plies','1000','--output',str(folder/'replay.json')]
            failure=None;clock=time.monotonic()
            with (folder/'stdout.txt').open('x') as stdout,(folder/'stderr.txt').open('x') as stderr:
                proc=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,start_new_session=True)
                state=Path(f'/proc/{proc.pid}/stat').read_text().rsplit(')',1)[1].split();write(folder/'process.json',dict(pid=proc.pid,start_ticks=state[19]))
                try:proc.wait(timeout=plan['per_game_seconds'])
                except subprocess.TimeoutExpired:ca.kill_tree(proc.pid);proc.wait();failure='game_wall_timeout'
            if proc.returncode:failure=failure or f'referee_exit_{proc.returncode}'
            replay=json.loads((folder/'replay.json').read_text()) if (folder/'replay.json').exists() else None
            score=None;validated=0
            if replay:
                val=rules.GameState(max_plies=1000)
                for frame in replay['frames']:
                    if frame['move']:
                        assert frame['move'] in val.board.legal_moves();val.push(frame['move'])
                    assert val.board.board_string()==frame['board'] and val.board.observation(0)==frame['white'] and val.board.observation(1)==frame['black'];validated+=1
                normal=replay['reason'] in rules.NORMAL_REASONS
                if not normal:failure=failure or f"technical_{replay['reason']}"
                else:assert val.outcome()==(replay['result'],replay['reason'])
                raw={'1-0':1.,'0-1':0.,'1/2-1/2':.5}.get(replay['result'])
                if raw is not None:score=raw if job['side']=='white' else 1-raw
            else:failure=failure or 'missing_replay'
            record=dict(at=now(),job=job,result=replay.get('result') if replay else None,reason=replay.get('reason') if replay else None,
                        score=score,technical_failure=failure,elapsed=time.monotonic()-clock,validated_frames=validated,
                        plies=len(replay['frames'])-1 if replay else None,files={p.name:sha(p) for p in folder.iterdir() if p.is_file()})
            write(folder/'result.json',record);records.append(record);print(json.dumps({k:v for k,v in record.items() if k!='files'}),flush=True)
            if failure:stop.set();break
        write(PILOT/f'lane{number}-completion.json',dict(at=now(),records=len(records),stopped=stop.is_set()))
        return records
    def lane(number):
        try:return execute_lane(number)
        except BaseException as error:
            stop.set()
            write(PILOT/f'lane{number}-failure.json',dict(at=now(),error=repr(error)))
            raise
    try:
        with futures.ThreadPoolExecutor(max_workers=2) as pool:rows=sum(list(pool.map(lane,(0,1))),[])
        clean=[r for r in rows if not r['technical_failure']];points=sum(r['score'] for r in clean)
        write(PILOT/'completion.json',dict(at=now(),completed=len(rows),planned=16,clean=len(clean),points=points,
             gate_pass=len(rows)==len(clean)==16 and points>=10,elapsed=time.monotonic()-start,
             unstarted=[j['id'] for j in plan['jobs'] if not (PILOT/'jobs'/j['id']/'started.json').exists()]))
    except BaseException as error:
        stop.set();write(PILOT/'failure.json',dict(at=now(),error=repr(error)));raise


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='prepare':prepare()
    else:main()
