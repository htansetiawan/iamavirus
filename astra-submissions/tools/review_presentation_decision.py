"""Independently reconcile the fixed teaching trace; run no bot or scorer."""
from collections import Counter
from datetime import datetime, timezone
import difflib
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
NAME = 'presentation-real-decision-20261111'
OUT = ROOT / 'astra-submissions/analysis' / NAME
BUILD = ROOT / 'astra-submissions/experiments' / NAME
PRIVATE = ROOT / 'data/astra-spool' / NAME


def read(path): return json.loads(Path(path).read_text())
def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def close(a,b): assert math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-12),(a,b)
def save(path,value):
    with path.open('x') as stream: stream.write(json.dumps(value,indent=2,allow_nan=False)+'\n')


def main():
    plan=read(OUT/'plan.json');execution=read(OUT/'execution.json')
    assert execution['status']=='complete' and execution['completed']==2
    assert execution['plan_sha256']==sha(OUT/'plan.json')
    for path,digest in plan['dependencies'].items(): assert sha(path)==digest,path
    source_differences={}
    for name,digest in plan['source_members'].items():
        control,trace=(BUILD/arm/name for arm in ('control','trace'))
        assert sha(control)==digest
        a,b=control.read_text().splitlines(),trace.read_text().splitlines()
        opcodes=difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes()
        assert all(tag in ('equal','insert') for tag,*_ in opcodes),name
        added=[line for tag,i,j,k,l in opcodes if tag=='insert' for line in b[k:l]]
        if added:source_differences[Path(name).name]=len(added)
    assert sorted(source_differences)==plan['changed_trace_files']
    logs={};timings={};protocol={}
    for arm in plan['arms']:
        receipt=read(OUT/(arm+'-execution.json'))
        assert receipt['code']==0
        for ext in ('stdout','stderr'):assert sha(PRIVATE/(arm+'.'+ext))==receipt[ext+'_sha256']
        text=(PRIVATE/(arm+'.stderr')).read_text();logs[arm]=text
        protocol[arm]=(PRIVATE/(arm+'.stdout')).read_text().splitlines()
        assert protocol[arm][:3]==['ready','move d2d4','move c1f4'] and len(protocol[arm])==4
        assert 'mist: stockfish ready' in text and 'belief empty' not in text and 'thinned' not in text
        timings[arm]=[(m[0],int(m[1]),int(m[2])) for m in re.findall(r'mist: timing (own|opp) update [\d.]+ s \|P\| (\d+) -> (\d+)',text)]
    assert timings['control']==timings['trace']
    trace=[json.loads(line[7:]) for line in logs['trace'].splitlines() if line.startswith('@astra ')]
    groups={kind:[r for r in trace if r['kind']==kind] for kind in {r['kind'] for r in trace}}
    assert len(groups['belief'])==1
    belief=groups['belief'][0];worlds=groups['world'];samples=groups['sample']
    assert len(worlds)==belief['count']<=4096 and not belief['overflowed']
    assert [r['index'] for r in worlds]==list(range(len(worlds)))
    close(sum(r['weight'] for r in worlds),1)
    normalizer=sum(math.exp(r['logw']) for r in worlds)
    for row in worlds:close(row['weight'],math.exp(row['logw'])/normalizer)
    close(sum(r['chance_weight'] for r in samples),1)
    assert len(samples)==len(worlds)<=32
    for row in samples:
        assert row['requested']==32 and row['distinct']==len(samples)
        close(row['chance_weight'],worlds[row['index']]['weight'])
    spec=importlib.util.spec_from_file_location('presentation_course_referee',next(p for p in plan['dependencies'] if p.endswith('/fow-starter/referee.py')))
    referee=importlib.util.module_from_spec(spec);spec.loader.exec_module(referee)
    replay=read(next(p for p in plan['dependencies'] if p.endswith('/c8ozqj0m.json')))
    frames=replay['frames'];states=[referee.FowBoard()];counts=[1];opponent_candidates={}
    def board_string(board):return ''.join(p.symbol() if (p:=board.piece_at(i)) else '-' for i in range(64))
    def key(board):return (board_string(board),0 if board.turn else 1,int(board.castling_rights),board.ep_square if board.ep_square is not None else -1,board.halfmove_clock)
    for ply in range(1,5):
        following={};moves=set()
        for board in states:
            options=list(referee.fow_moves(board))
            if board.turn:options=[m for m in options if m.uci()==frames[ply]['move']]
            for move in options:
                child=board.copy(stack=False);child.push(move)
                king=child.king(not child.turn)
                if king is None or child.is_attacked_by(child.turn,king):continue
                if referee.observation(child,True)!=frames[ply]['white']:continue
                following[key(child)]=child;moves.add(move.uci())
        states=list(following.values());counts.append(len(states))
        if ply%2==0:opponent_candidates[str(ply)]=sorted(moves)
    reported_keys={(r['board'],r['side'],r['castle'],r['ep'],r['halfmove']) for r in worlds}
    assert reported_keys=={key(b) for b in states}
    assert [row[2] for row in timings['trace']]==counts[1:]
    assert all(row['view']==frames[4]['white'] for row in worlds)
    assert frames[4]['board'] in {row['board'] for row in worlds}
    roots=sorted(groups['root'],key=lambda r:r['action']);children=sorted(groups['initial_child'],key=lambda r:r['action'])
    assert len(worlds)==1 and len(children)==len(roots)==len(groups['guard'])==32
    assert all(row['root_infoset']==0 for row in roots)
    assert [row['move'] for row in children]==[row['move'] for row in roots]
    legal={move.uci() for move in referee.fow_moves(states[0])}
    assert {r['move'] for r in roots}==legal
    assert all(not r['excluded'] and r['combined']==r['combined_sharp']==0 for r in groups['guard'])
    assert all(r['frontier'] and r['sf_scored'] and r['matched_scores']==32 and not r['ranked_floor'] for r in children)
    for row in children:close(row['utility'],math.tanh(row['sf_cp']/400))
    values=[r['utility'] for r in children];previous=None;means=[]
    for iteration in (1,2):
        rows=sorted([r for r in groups['cfr_update'] if r['iteration']==iteration],key=lambda r:r['action'])
        assert [r['action'] for r in rows]==list(range(32))
        expected=[max(r['regret_before']+r['last_before'],0) for r in rows];total=sum(expected)
        expected=[r/total if total else 1/32 for r in expected]
        baseline=sum(p*v for p,v in zip(expected,values,strict=True));means.append(baseline)
        for i,row in enumerate(rows):
            close(row['strategy'],expected[i]);close(row['instantaneous'],values[i]-baseline)
            if previous is not None:
                close(row['regret_before'],max(previous[i]['regret_before']+previous[i]['instantaneous'],0))
                close(row['last_before'],previous[i]['instantaneous'])
        previous=rows
    predicted=[max(r['regret']+r['last'],0) for r in roots];total=sum(predicted)
    close(sum(r['probability'] for r in roots),1)
    for row,value in zip(roots,predicted,strict=True):close(row['probability'],value/total if total else 1/32)
    chosen=max(roots,key=lambda r:r['probability'])
    assert [r['move'] for r in roots if r['selected']]==[chosen['move']]
    assert protocol['trace'][-1]=='move '+chosen['move']
    assert not any(r['owner']=='astra-'+NAME for r in read(ROOT/'chatroom/cores.json')['allocation'])
    result=dict(at=datetime.now(timezone.utc).isoformat(),status='complete',scope=plan['scope'],plan_sha256=sha(OUT/'plan.json'),
        review_source_sha256=sha(Path(__file__)),annotation_inserted_lines=source_differences,
        observed_belief_counts=counts,opponent_moves_consistent_with_received_views=opponent_candidates,
        retained_world_count=len(worlds),search_world_count=len(samples),root_actions=len(roots),
        all_initial_children_scored=True,guard_exclusions=0,initial_strategy_value=means[0],second_strategy_value=means[1],
        initial_children=children,first_two_updates=groups['cfr_update'],final_root_strategy=roots,
        control_log=next(s for s in logs['control'].splitlines() if s.startswith('mist: n=')),
        trace_log=next(s for s in logs['trace'].splitlines() if s.startswith('mist: n=')),
        selected_move=chosen['move'],recorded_arena_move=frames[5]['move'],same_move_as_control=protocol['control'][-1]==protocol['trace'][-1],
        checks=['All frozen dependencies and raw protocol/log hashes match.',
                'All control source members match v38; trace has insertions only in the three declared files.',
                'Independent course enumeration matches all four belief-count transitions and final complete states.',
                'All world views and chance weights reconcile; truth joined only after execution.',
                'All 32 initial child utilities match returned centipawn conversion.',
                'First two root updates match independent expected values, instantaneous regrets and clipped previous update.',
                'Final strategy matches normalized positive regret plus prediction; selected move is its argmax.',
                'All reported root actions legal; core lease released.'],
        limitations=plan['limitations']+['One-world prefix illustrates inference and search, not a nontrivial 32-draw distribution.',
                                       'One retained true world does not establish common knowledge or a complete Obscuro subgame.'])
    save(OUT/'result.json',result)
    print(json.dumps({k:result[k] for k in ('status','observed_belief_counts','opponent_moves_consistent_with_received_views','root_actions','initial_strategy_value','second_strategy_value','selected_move','recorded_arena_move')},indent=2))


if __name__=='__main__':main()
