#!/usr/bin/env python3
"""Paired, observation-only decision replays of current reference matchups.

Ground truth is used by the scorer only. Recorded opponent replies are usable
only while their observation is unchanged; changed observations censor replay
continuation, rather than pretending the recording is a responsive opponent.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
import random
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from learning import ingest, rules  # noqa: E402
from learning.compare_archives import build, kill_tree  # noqa: E402


def make_cases(rows, per_color=2):
    buckets = {}
    for row in rows:
        if row['split'] != 'test': continue
        side = next((s for s in ('white','black') if row[s]=='IAmAVirus' and row.get(s+'Version')==35),None)
        if side is None: continue
        opponent=row['black' if side=='white' else 'white']
        if opponent not in ('Instructors','duck'):continue
        buckets.setdefault((opponent,side),[]).append(row)
    cases=[]
    for (opponent,side),group in sorted(buckets.items()):
        group.sort(key=lambda x:hashlib.sha256(('reference-gate-730:'+x['id']).encode()).hexdigest())
        for row in group[:per_color]:
            rp=json.loads(Path(row['replay_path']).read_text()); parity=0 if side=='white' else 1
            plies=list(range(parity,len(rp['frames'])-1,2))
            if not plies:continue
            for fraction in (.2,.5,.8):
                ply=plies[min(int(len(plies)*fraction),len(plies)-1)]
                if any(c['game']==row['id'] and c['ply']==ply for c in cases):continue
                cases.append({'game':row['id'],'opponent':opponent,'side':side,'ply':ply,
                              'phase_fraction':fraction,'replay_path':row['replay_path'],
                              'replay_sha256':row['replay_sha256'],'game_result':rp['result']})
    return cases


def score(state, move, side, replay, ply):
    if move not in state.board.legal_moves():return {'legal':False}
    child=state.copy();child.push(move);terminal=child.outcome()
    losing='0-1' if side==0 else '1-0'
    result={'legal':True,'terminal_after_choice':terminal,'fatal':bool(terminal and terminal[0]==losing),
            'recorded_reply_usable':False,'reply_censored_reason':None}
    if terminal:return result
    if ply+2>=len(replay['frames']):
        result['reply_censored_reason']='recording ended';return result
    opp=1-side;key='white' if opp==0 else 'black'
    if child.board.observation(opp)!=replay['frames'][ply+1][key]:
        result['reply_censored_reason']='opponent observation changed';return result
    reply=replay['frames'][ply+2]['move']
    if reply not in child.board.legal_moves():
        result['reply_censored_reason']='recorded action no longer legal';return result
    # Before the tested decision both players' complete histories were forced;
    # the identical new opponent view preserves that opponent's input history.
    result['recorded_reply_usable']=True;result['recorded_reply']=reply
    child.push(reply);result['terminal_after_recorded_reply']=child.outcome()
    return result


def run(case, binaries, cores):
    raw=Path(case['replay_path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==case['replay_sha256']
    rp=json.loads(raw);states,problems=ingest.validate_replay(rp);assert not problems,problems
    side=0 if case['side']=='white' else 1;ply=case['ply'];tc=rp.get('timeControl',{})
    feed=['fow',f"{'w' if side==0 else 'b'} {tc.get('baseSeconds',180)} {tc.get('incrementSeconds',2)}"]
    forced=[]
    for p in range(ply+1):
        feed.append(rp['frames'][p][case['side']])
        if p%2==side:
            feed.append(str(rp['frames'][p]['clocks'][side]))
            if p<ply:forced.append(rp['frames'][p+1]['move'])
    output={'case':case,'played':rp['frames'][ply+1]['move'],'variants':{}}
    for name,directory in binaries.items():
        env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_'))}
        env.update(FOW_SEED='730',MIST_FORCE_MOVES=','.join(forced))
        began=time.monotonic()
        try:
            proc=subprocess.Popen(['taskset','-c',cores,'bash',str(directory/'run.sh')],
                                  stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
            try:
                stdout,stderr=proc.communicate('\n'.join(feed)+'\n',timeout=120)
            except subprocess.TimeoutExpired:
                kill_tree(proc.pid);proc.wait()
                raise
            moves=[line[5:].strip() for line in stdout.splitlines() if line.startswith('move ')]
            if proc.returncode or len(moves)!=len(forced)+1:
                raise ValueError(f'protocol exit={proc.returncode} moves={len(moves)} expected={len(forced)+1}: {stderr[-200:]}')
            assert moves[:-1]==forced,'forced prefix not obeyed'
            move=moves[-1]
            output['variants'][name]={'move':move,'seconds':time.monotonic()-began,'repeat_recorded':move==output['played'],
                                      **score(states[ply],move,side,rp,ply)}
        except (subprocess.TimeoutExpired,ValueError,AssertionError) as e:
            output['variants'][name]={'error':str(e),'seconds':time.monotonic()-began}
    return output


def lane(cases, binaries, cores, checkpoint):
    # C++ rule-table initialization and ctypes state are process-local. Do not
    # validate independent games in Python threads sharing the native library.
    rows=[]
    with Path(checkpoint).open('w') as f:
        for case in cases:
            row=run(case,binaries,cores);rows.append(row)
            f.write(json.dumps(row)+'\n');f.flush()
            print('lane',cores,case['game'],case['ply'],{k:v.get('move',v.get('error')) for k,v in row['variants'].items()},flush=True)
    return rows


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dataset',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--per-color',type=int,default=2)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    archives={'v35':ROOT/'fable-submissions/iamavirus-v35-mist-c-v14.zip',
              'r4':ROOT/'data/candidates/iamavirus-v36-candidate-mist-c-v20-r4.zip',
              'v23':ROOT/'data/candidates/mist-c-v23-obs.zip'}
    pins={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in archives.items()}
    cases=make_cases(json.loads((args.dataset/'game-splits.json').read_text()),args.per_color)
    (args.out/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    (args.out/'pins.json').write_text(json.dumps(pins,indent=2)+'\n')
    binaries={k:build(p,args.out/'builds') for k,p in archives.items()}
    binaries['v35-repeat']=binaries['v35']
    rows=[]
    # One exclusive pair per lane; candidates share a case, seed and clock.
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(lane,cases[i::2],binaries,c,str(args.out/f'lane-{i}.jsonl')) for i,c in enumerate(('2,3','4,5'))]
        for future in concurrent.futures.as_completed(futures):
            for row in future.result():
                rows.append(row)
                with (args.out/'results.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
                print(row['case']['game'],row['case']['ply'],{k:v.get('move',v.get('error')) for k,v in row['variants'].items()},flush=True)
    summary={'cases':len(rows),'by_variant':{},'classification':'offline paired decision diagnostics; not game win rates'}
    for name in binaries:
        values=[r['variants'][name] for r in rows]
        summary['by_variant'][name]={'errors':sum('error'in v for v in values),'illegal':sum(v.get('legal') is False for v in values),
                                     'fatal':sum(v.get('fatal',False) for v in values),
                                     'repeat_recorded':sum(v.get('repeat_recorded',False) for v in values),
                                     'reply_usable':sum(v.get('recorded_reply_usable',False) for v in values),
                                     'reply_censored':dict(Counter(v['reply_censored_reason'] for v in values if v.get('reply_censored_reason')))}
    summary['v35_repeat_move_flips']=sum(r['variants']['v35'].get('move')!=r['variants']['v35-repeat'].get('move') for r in rows)
    (args.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
