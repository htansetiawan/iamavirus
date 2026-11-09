"""Bounded serial replay of the frozen diagnosis; no network or GPU work."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from prepare import HERE,ROOT,OUT,BUILD,sha,write
sys.path[:0] = [str(ROOT/'astra-submissions/tools'),str(ROOT),'/home/henrytan/git/fow-starter']
from fresh_taxonomy_gate import protocol
import referee as ref


def now(): return datetime.now(timezone.utc).isoformat()


def call(case, seed, destination, preflight=False, control=False):
    destination.mkdir(parents=True,exist_ok=False)
    replay = json.loads(Path(case['replay_path']).read_text())
    assert sha(Path(case['replay_path'])) == case['replay_sha256']
    side = 0 if case['side'] == 'white' else 1
    feed,forced = protocol(replay,case['ply'],side)
    (destination/'input.txt').write_text(feed)
    env = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_'))}
    env.update(MIST_STOCKFISH=str(BUILD/'bin/stockfish'),MIST_HISTORY_TABLE=str(BUILD/'data/history.bin'),
               MIST_FORCE_MOVES=','.join(forced),FOW_SEED=str(seed),ASTRA_SF_ALLCHILDREN='1',
               OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    if not control:
        env.update(MIST_TEACHER_OUT=str(destination/'tree.jsonl'),ASTRA_POST_READOUT='1',
                   ASTRA_POST_TRUTH=replay['frames'][case['ply']]['board'])
    if preflight: env['MIST_MAX_SECONDS']='0.3'
    binary = BUILD/('mist-control' if control else 'mist-diagnostic')
    write(destination/'started.json',dict(at=now(),case=case,seed=seed,binary_sha256=sha(binary),
          preflight=preflight,control=control,expected_moves=len(forced)+1))
    started=time.monotonic()
    proc=subprocess.Popen([str(binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          text=True,env=env,start_new_session=True)
    stat=Path(f'/proc/{proc.pid}/stat').read_text().rsplit(')',1)[1].split()
    write(destination/'process.json',dict(pid=proc.pid,pgid=proc.pid,start_ticks=stat[19]))
    fault=None
    try: stdout,stderr=proc.communicate(feed,timeout=120)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid,signal.SIGKILL);stdout,stderr=proc.communicate();fault='case_timeout'
    (destination/'stdout.txt').write_text(stdout);(destination/'stderr.txt').write_text(stderr)
    moves=[line[5:].strip() for line in stdout.splitlines() if line.startswith('move ')]
    if proc.returncode != 0: fault=fault or f'exit_{proc.returncode}'
    if moves[:-1] != forced or len(moves) != len(forced)+1: fault=fault or 'forced_prefix_or_move_count'
    board=ref.FowBoard()
    for frame in replay['frames'][1:case['ply']+1]:board.push_uci(frame['move'])
    assert ref.observation(board,side==0) == replay['frames'][case['ply']][case['side']]
    safe=[]
    for move in ref.fow_moves(board):
        board.push(move);king=board.king(side==0)
        if king is not None and not board.is_attacked_by(side!=0,king):safe.append(move.uci())
        board.pop()
    chosen=moves[-1] if moves else None;fatal=None
    if chosen:
        move=ref.chess.Move.from_uci(chosen)
        if move not in ref.fow_moves(board):fault=fault or 'illegal_choice'
        else:
            board.push(move);king=board.king(side==0)
            fatal=king is None or board.is_attacked_by(side!=0,king)
    trees=[]
    if (destination/'tree.jsonl').exists():trees=[json.loads(line) for line in (destination/'tree.jsonl').read_text().splitlines()]
    if len(trees)>1:fault=fault or 'multiple_target_exports'
    if not control and not any(line.startswith('astra: placement ') for line in stderr.splitlines()):fault=fault or 'missing_post_readout'
    members=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            st=(p/'stat').read_text().rsplit(')',1)[1].split()
            if int(st[2])==proc.pid and st[0] not in ('Z','X'):members.append(int(p.name))
        except (FileNotFoundError,PermissionError):pass
    if members:
        os.killpg(proc.pid,signal.SIGKILL);fault=fault or 'live_owned_children_after_exit'
    result=dict(at=now(),elapsed=time.monotonic()-started,exit_code=proc.returncode,fault=fault,
                move=chosen,forced_moves=len(forced),truth_safe_moves=safe,fatal=fatal,
                tree_exported=bool(trees),live_members=members,
                files={p.name:sha(p) for p in destination.iterdir() if p.is_file()})
    write(destination/'result.json',result)
    return result


def preflight():
    os.sched_setaffinity(0,{0,1});plan=json.loads((OUT/'plan.json').read_text());records=[]
    for side in ('white','black'):
        case=dict(next(c for c in plan['cases'] if c['side']==side));case['ply']=0 if side=='white' else 1
        for control in (True,False):
            r=call(case,2691109,OUT/f'preflight-{side}-{control}',True,control)
            assert not r['fault'],r
            if not control:assert r['tree_exported']
            records.append(dict(side=side,control=control,**r))
    write(OUT/'preflight.json',dict(passed=True,records=records))
    print('Both-color control and post-decision diagnostic preflight passed.',flush=True)


def main():
    os.sched_setaffinity(0,{0,1});plan=json.loads((OUT/'plan.json').read_text())
    assert json.loads((OUT/'preflight.json').read_text())['passed']
    for name,digest in plan['dependencies'].items():assert sha(Path(name))==digest,name
    started=time.monotonic();write(OUT/'started.json',dict(at=now(),pid=os.getpid(),plan_sha256=sha(OUT/'plan.json')))
    completed=[];stop='completed'
    for seed in plan['seeds']:
        for case in plan['cases']:
            if time.monotonic()-started+plan['case_seconds']>plan['wall_seconds']:
                stop='global_wall_bound';break
            dest=OUT/'jobs'/f"{case['id']}-s{seed}"
            r=call(case,seed,dest);completed.append(dict(case=case['id'],seed=seed,result=r))
            print(json.dumps(dict(case=case['id'],seed=seed,elapsed=round(r['elapsed'],2),move=r['move'],fatal=r['fatal'],fault=r['fault'])),flush=True)
            if r['fault']:stop='technical_failure';break
        if stop!='completed':break
    write(OUT/'completion.json',dict(at=now(),stop=stop,completed=len(completed),planned=len(plan['cases'])*len(plan['seeds']),
          elapsed=time.monotonic()-started,rows=completed))
    return 0 if stop=='completed' else 1


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='preflight':preflight()
    else:sys.exit(main())
