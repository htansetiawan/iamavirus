"""Same-belief paired replay; truth enters labels only after actor exit."""
from datetime import datetime,timezone
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from prepare import HERE,ROOT,OUT,BUILD,sha,write
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import rules
from fresh_taxonomy_gate import exchange_probe


def now():return datetime.now(timezone.utc).isoformat()


def protocol(replay,ply,side):
    key=('white','black')[side];tc=replay.get('timeControl',{})
    lines=['fow',f"{'w' if side==0 else 'b'} {tc.get('baseSeconds',180)} {tc.get('incrementSeconds',2)}"];forced=[]
    for p in range(ply+1):
        lines.append(replay['frames'][p][key])
        if p%2==side:
            lines.append(str(replay['frames'][p]['clocks'][side]))
            if p<ply:forced.append(replay['frames'][p+1]['move'])
    return '\n'.join(lines)+'\n',forced


def state_at(replay,ply):
    state=rules.GameState(max_plies=1000)
    for i,frame in enumerate(replay['frames'][:ply+1]):
        if i:
            assert frame['move'] in state.board.legal_moves();state.push(frame['move'])
        assert state.board.board_string()==frame['board']
        assert state.board.observation(0)==frame['white'] and state.board.observation(1)==frame['black']
    return state


def target_check(t):
    assert t['own_reach_consistent'] and abs(sum(w['weight'] for w in t['samples'])-1)<1e-9
    assert abs(sum(a['probability'] for a in t['actions'])-1)<1e-9
    assert abs(sum(a['q']*a['probability'] for a in t['actions'])-t['root_value'])<1e-9
    assert abs(t['solver_value']-t['root_value'])<1e-9
    assert max(t['actions'],key=lambda a:a['probability'])['uci']==t['solver_move']
    assert set(t['avoid_moves']).isdisjoint(a['uci'] for a in t['actions'])


def one(case,index,folder,seconds=2.5,same=False):
    folder.mkdir(parents=True,exist_ok=False);replay=json.loads(Path(case['replay_path']).read_text())
    assert sha(Path(case['replay_path']))==case['replay_sha256']
    side=('white','black').index(case['side']);feed,forced=protocol(replay,case['ply'],side)
    (folder/'input.txt').write_text(feed)
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
    env.update(MIST_STOCKFISH=str(BUILD/'bin/stockfish'),MIST_HISTORY_TABLE=str(BUILD/'data/history.bin'),
               ASTRA_SF_ALLCHILDREN='1',MIST_TEACHER_OUT=str(folder/'targets.jsonl'),MIST_FORCE_MOVES=','.join(forced),
               FOW_SEED='2701109',MIST_MAX_SECONDS='10',ASTRA_GUARD_PAIR=str(index%2),ASTRA_PAIR_SECONDS=str(seconds),
               OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    if same:env['ASTRA_PAIR_SAME']='1'
    write(folder/'started.json',dict(at=now(),case=case,order=index%2,seconds=seconds,same=same,forced=forced))
    start=time.monotonic();proc=subprocess.Popen([str(BUILD/'mist')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,text=True,env=env,start_new_session=True)
    st=Path(f'/proc/{proc.pid}/stat').read_text().rsplit(')',1)[1].split()
    write(folder/'process.json',dict(pid=proc.pid,pgid=proc.pid,start_ticks=st[19]))
    try:stdout,stderr=proc.communicate(feed,timeout=150)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid,signal.SIGKILL);stdout,stderr=proc.communicate()
        (folder/'stdout.txt').write_text(stdout);(folder/'stderr.txt').write_text(stderr)
        write(folder/'failure.json',dict(reason='case_timeout',exit_code=proc.returncode));raise
    (folder/'stdout.txt').write_text(stdout);(folder/'stderr.txt').write_text(stderr)
    assert proc.returncode==0,(proc.returncode,stderr[-1000:])
    members=[]
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():continue
        try:
            item=(path/'stat').read_text().rsplit(')',1)[1].split()
            if int(item[2])==proc.pid and item[0] not in ('Z','X'):members.append(int(path.name))
        except (FileNotFoundError,PermissionError):pass
    if members:
        os.killpg(proc.pid,signal.SIGKILL)
        raise RuntimeError(f'owned process group survived parent exit: {members}')
    moves=[s[5:] for s in stdout.splitlines() if s.startswith('move ')]
    assert moves[:-1]==forced and len(moves)==len(forced)+1
    targets=[json.loads(s) for s in (folder/'targets.jsonl').read_text().splitlines()] if (folder/'targets.jsonl').exists() else []
    logs=re.findall(r'astra: pair arm=(\d+) ok=(\d+) elapsed=(\S+) belief=(\d+) unchanged=(\d+)',stderr)
    state=state_at(replay,case['ply']);arms={}
    if not targets:
        assert not logs
        for arm in ('base','candidate'):arms[arm]=dict(move=moves[-1],**exchange_probe(state,moves[-1]))
        exercised=False
    else:
        assert len(targets)==len(logs)==2
        for t,l in zip(targets,logs):
            target_check(t);assert l[1]=='1' and l[4]=='1'
            arm='candidate' if l[0]=='1' else 'base';probe=exchange_probe(state,t['solver_move'])
            assert probe['legal'],(case,t['solver_move'])
            arms[arm]=dict(move=t['solver_move'],elapsed=float(l[2]),belief_fingerprint=l[3],target=t,**probe)
        a,b=arms['base']['target'],arms['candidate']['target']
        for key in ('samples','belief_count','belief_overflowed','search_budget_seconds'):assert a[key]==b[key],key
        assert arms['base']['belief_fingerprint']==arms['candidate']['belief_fingerprint']
        assert set(b['avoid_moves'])<=set(a['avoid_moves'])
        assert {x['uci'] for x in a['actions']}<={x['uci'] for x in b['actions']}
        assert arms['base']['move']==moves[-1],'frontend changed baseline solver move'
        if same:assert a['avoid_moves']==b['avoid_moves']
        exercised=True
    assert all(a['legal'] for a in arms.values())
    row=dict(case=case,elapsed=time.monotonic()-start,exercised=exercised,arms=arms,live_owned_members=members,
             files={p.name:sha(p) for p in folder.iterdir() if p.is_file()})
    write(folder/'result.json',row);return row


def preflight():
    os.sched_setaffinity(0,{0,1});plan=json.loads((OUT/'plan.json').read_text());rows=[]
    for side in ('white','black'):
        case=dict(next(c for c in plan['cases'] if c['side']==side));case['ply']=0 if side=='white' else 1
        for same in (True,False):
            row=one(case,len(rows),OUT/f'preflight-{side}-{same}',.3,same);assert row['exercised'];rows.append(row)
    write(OUT/'preflight.json',dict(passed=True,rows=rows));print('4 paired preflights pass.',flush=True)


def main():
    os.sched_setaffinity(0,{0,1});plan=json.loads((OUT/'plan.json').read_text())
    assert json.loads((OUT/'preflight.json').read_text())['passed']
    for p,h in plan['dependencies'].items():assert sha(Path(p))==h,p
    start=time.monotonic();write(OUT/'execution.json',dict(at=now(),pid=os.getpid(),plan_sha256=sha(OUT/'plan.json')))
    rows=[]
    try:
        for i,case in enumerate(plan['cases']):
            assert time.monotonic()-start+plan['case_seconds']<plan['wall_seconds'],'global_wall_bound'
            row=one(case,i,OUT/'jobs'/case['id'],plan['per_search_seconds']);rows.append(row)
            print(json.dumps(dict(case=case['id'],exercised=row['exercised'],base=row['arms']['base']['move'],candidate=row['arms']['candidate']['move'],fatal=[row['arms'][a]['fatal'] for a in ('base','candidate')])),flush=True)
        write(OUT/'terminal.json',dict(at=now(),state='complete',completed=len(rows),elapsed=time.monotonic()-start))
    except BaseException as e:
        write(OUT/'terminal.json',dict(at=now(),state='failed',error=repr(e),completed=len(rows),elapsed=time.monotonic()-start));raise


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='preflight':preflight()
    else:main()
