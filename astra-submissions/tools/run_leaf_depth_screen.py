#!/usr/bin/env python3
"""Fixed, matched depth-1/depth-3 screen versus one immutable Misty wrapper.

Eight blocks, four games per block: both depths, both colours, same seeds.
This is a small candidate screen, not proof of an Elo improvement.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import zipfile
import shlex


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,indent=2)+'\n'); temp.replace(path)


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--engine',type=Path,required=True)
    ap.add_argument('--misty-archive',type=Path,required=True)
    ap.add_argument('--kit',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--cores',default='0,1')
    ap.add_argument('--blocks',type=int,default=8)
    ap.add_argument('--seed',type=int,default=2026102601)
    ap.add_argument('--seconds',type=int,default=10800)
    args=ap.parse_args()
    engine,kit,out=map(Path.resolve,(args.engine,args.kit,args.out))
    if out.exists(): raise SystemExit('Use a new output; never silently resume/rewrite a screen.')
    out.mkdir(parents=True)
    misty=out/'misty'; misty.mkdir()
    with zipfile.ZipFile(args.misty_archive) as z:z.extractall(misty)
    manifest={
        'classification':'fixed paired screen; not an Elo estimate or arena promotion',
        'state':'running','started_at':stamp(),'blocks_planned':args.blocks,
        'seed':args.seed,'wall_cap_seconds':args.seconds,'cores':args.cores,
        'time_control':{'base_seconds':180,'increment_seconds':2},
        'engine':str(engine),'engine_sha256':sha(engine/'mist'),
        'engine_build':json.loads((engine/'experiment.json').read_text()),
        'misty_archive_sha256':sha(args.misty_archive),
        'referee_sha256':sha(kit/'referee.py'),
        'pass_screen':'at least +3/16 points against Misty at depth3 versus depth1; no candidate protocol/time failure; then independent review, not automatic promotion',
        'games':[]}
    receipt=out/'manifest.json'; save(receipt,manifest)
    started=time.monotonic()
    for block in range(args.blocks):
        depths=(1,3) if block%2==0 else (3,1)
        for colour in ('white','black'):
            for depth in depths:
                remaining=args.seconds-(time.monotonic()-started)
                if remaining<1:
                    manifest['state']='wall_cap'; break
                engine_seed=args.seed+block*4+(colour=='black')*2
                misty_seed=engine_seed+1
                bot=shlex.join(['env',f'FOW_SEED={engine_seed}',f'MIST_SF_DEPTH={depth}',
                                 'bash',str(engine/'run.sh')])
                opp=shlex.join(['env',f'FOW_SEED={misty_seed}','bash',str(misty/'run.sh')])
                name=f'block{block:02d}-depth{depth}-{colour}'
                replay_path=out/(name+'.json')
                command=['taskset','-c',args.cores,str(kit/'.venv/bin/python'),str(kit/'referee.py'),
                    '--trusted-local','--white',bot if colour=='white' else opp,
                    '--black',opp if colour=='white' else bot,
                    '--white-name',f'v35-depth{depth}' if colour=='white' else 'Misty-v16',
                    '--black-name','Misty-v16' if colour=='white' else f'v35-depth{depth}',
                    '--base-time','180','--increment','2','--max-plies','1000',
                    '--output',str(replay_path)]
                before=time.monotonic()
                with (out/(name+'.log')).open('w') as log:
                    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                    try: code=process.wait(timeout=remaining)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid,signal.SIGTERM)
                        try:process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid,signal.SIGKILL);process.wait()
                        manifest['state']='wall_cap';break
                if code or not replay_path.exists():
                    manifest['state']='runner_failure';manifest['failed_game']=name;break
                replay=json.loads(replay_path.read_text())
                result=replay['result']
                score=.5 if result=='1/2-1/2' else float((result=='1-0')==(colour=='white'))
                row={'block':block,'depth':depth,'colour':colour,'engine_seed':engine_seed,
                     'misty_seed':misty_seed,'result':result,'score':score,'reason':replay['reason'],
                     'plies':len(replay['frames'])-1,'final_clocks':replay['frames'][-1]['clocks'],
                     'seconds':time.monotonic()-before,'replay':str(replay_path),'sha256':sha(replay_path)}
                manifest['games'].append(row);save(receipt,manifest)
                print(json.dumps(row),flush=True)
                if any(x in replay['reason'].lower() for x in ('time','illegal','crash','protocol','initializ')):
                    manifest['state']='reliability_review';manifest['failed_game']=name;break
            if manifest['state']!='running':break
        if manifest['state']!='running':break
    if manifest['state']=='running':manifest['state']='complete'
    manifest['finished_at']=stamp();manifest['elapsed_seconds']=time.monotonic()-started
    manifest['summary']={str(d):{'games':sum(g['depth']==d for g in manifest['games']),
                                 'points':sum(g['score'] for g in manifest['games'] if g['depth']==d)} for d in (1,3)}
    complete=[b for b in range(args.blocks) if sum(g['block']==b for g in manifest['games'])==4]
    manifest['complete_blocks']=complete
    manifest['matched_block_point_deltas']=[sum((1 if g['depth']==3 else -1)*g['score']
        for g in manifest['games'] if g['block']==b) for b in complete]
    save(receipt,manifest);print(json.dumps({k:manifest[k] for k in ('state','summary','complete_blocks')}),flush=True)


if __name__=='__main__':main()
