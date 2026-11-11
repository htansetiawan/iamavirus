"""Two legal private-history witnesses for teaching; no agent/search is run."""
from collections import Counter
from contextlib import contextmanager
from datetime import datetime,timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from learning import _native
from learning.rules import Board

NAME='presentation-knowledge-20261111'
OUT=ROOT/'astra-submissions/analysis'/NAME
PRIVATE=ROOT/'data/astra-spool'/NAME
REPLAY=ROOT/'data/astra-spool/v38-mist-wins-20261111/c8ozqj0m.json'
REFEREE=Path('/home/henrytan/git/fow-starter/referee.py')
VALIDATOR=ROOT/'astra-submissions/experiments/last-only-pilot-20261110/build/native-validator.so'

def read(p):return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
def save(p,d):
    with p.open('x') as s:s.write(json.dumps(d,indent=2,allow_nan=False)+'\n')

@contextmanager
def lease():
    owner='astra-'+NAME;path=ROOT/'chatroom/cores.json'
    def change(take):
        with open('/tmp/iamavirus-cores-json.lock','a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);state=read(path)
            if take:
                assert not any(6 in r['cores'] for r in state['allocation'])
                state['allocation'].append(dict(owner=owner,cores=[6],pid=os.getpid(),purpose='two-history teaching rules check'))
            else:state['allocation']=[r for r in state['allocation'] if not(r['owner']==owner and r.get('pid')==os.getpid())]
            state['updated']=datetime.now(timezone.utc).isoformat();temp=path.with_suffix('.knowledge-tmp');temp.write_text(json.dumps(state,indent=2)+'\n');temp.replace(path)
    change(True)
    try:yield
    finally:change(False)

def main():
    assert sha(VALIDATOR)=='ae7a39913fe9d058b4b5392849ffc6a9260d2123a891d12454b016b4843665e3'
    old=read(ROOT/'astra-submissions/analysis/presentation-real-decision-20261111/plan.json')
    assert sha(REPLAY)==old['dependencies'][str(REPLAY)] and sha(REFEREE)==old['dependencies'][str(REFEREE)]
    OUT.mkdir(exist_ok=False);PRIVATE.mkdir(exist_ok=False)
    (PRIVATE/'previous-course-map.md').write_bytes((ROOT/'docs/course-map.md').read_bytes())
    lines=[['d2d4','c7c6','c1f4','d7d5','e2e3'],['d2d4','c7c6','b1c3','d7d5','e2e3']]
    dependencies=[Path(__file__),REPLAY,REFEREE,VALIDATOR,ROOT/'learning/_native.py',ROOT/'learning/rules.py',PRIVATE/'previous-course-map.md',ROOT/'astra-submissions/analysis/presentation-real-decision-20261111/plan.json']
    plan=dict(at=datetime.now(timezone.utc).isoformat(),lines=lines,core=6,wall_seconds=60,
        selection='Constructed teaching counterfactual: replace only White second move Bf4 by Nc3, then play e3 in both. Alternative e3 was also explored during a four-ply informal preflight; no predictive, independent-test or strength claim.',
        dependencies={str(p):sha(p) for p in dependencies},
        scope='Validate two five-ply histories and the actual four-ply information set. No policy, search, payoff, reach-weight, calibration, model, match, GPU or publication experiment.')
    save(OUT/'plan.json',plan)
    def timeout(*_):raise TimeoutError('teaching history check reached wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds'])
    spec=importlib.util.spec_from_file_location('knowledge_course_referee',REFEREE);ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    assert _native._library is None;_native.ensure_built=lambda verbose=True:VALIDATOR
    replay=read(REPLAY);assert [r['move'] for r in replay['frames'][1:6]]==lines[0]
    records=[]
    def string(board):return ''.join(p.symbol() if (p:=board.piece_at(sq)) else '-' for sq in range(64))
    for line in lines:
        board=ref.FowBoard();native=Board();frames=[];repetitions=Counter()
        for ply in range(6):
            if ply:
                move=line[ply-1]
                assert move in native.legal_moves() and ref.chess.Move.from_uci(move) in ref.fow_moves(board)
                native.push(move);board.push_uci(move);assert not native.mover_lost()
            repetitions[ref.position_key(board)]+=1
            assert ref.outcome(board,repetitions) is None
            assert native.board_string()==string(board)
            assert native.side==(0 if board.turn else 1)
            assert native.castling==int(board.castling_rights)
            assert native.en_passant==(board.ep_square if board.ep_square is not None else -1)
            assert native.halfmove_clock==board.halfmove_clock
            assert sorted(native.legal_moves())==sorted(m.uci() for m in ref.fow_moves(board))
            views={('white' if color==0 else 'black'):native.observation(color) for color in (0,1)}
            assert views['white']==ref.observation(board,True) and views['black']==ref.observation(board,False)
            frames.append(dict(ply=ply,board=string(board),**views,actions=sorted(native.legal_moves())))
        tokens={}
        for color,name in [(0,'white'),(1,'black')]:
            private=[['view',frames[0][name]]]
            for ply in range(1,6):
                if (ply-1)%2==color:private.append(['own_move',line[ply-1]])
                private.append(['view',frames[ply][name]])
            tokens[name]=private
        feed=['fow','b 180 2',frames[0]['black'],frames[1]['black'],str(replay['frames'][1]['clocks'][1])]
        for ply in (3,5):feed.extend([frames[ply-1]['black'],frames[ply]['black'],str(replay['frames'][ply]['clocks'][1])])
        records.append(dict(line=line,frames=frames,private_tokens=tokens,black_protocol='\n'.join(feed)+'\n'))
    a,b=records
    for ply in range(6):
        assert a['frames'][ply]['black']==b['frames'][ply]['black']
        for field in ('board','white','black'):assert a['frames'][ply][field]==replay['frames'][ply][field]
    assert a['private_tokens']['black']==b['private_tokens']['black'] and a['private_tokens']['white']!=b['private_tokens']['white']
    assert a['black_protocol']==b['black_protocol']
    assert a['frames'][5]['actions']==b['frames'][5]['actions']
    assert a['frames'][4]['white']!=b['frames'][4]['white']
    # Exhaust histories, not just deduplicated physical positions, for White's
    # four-ply actual private input. Fixed own actions; enumerate all Black moves.
    histories=[(ref.FowBoard(),[])];counts=[1]
    for ply in range(1,5):
        next_histories=[]
        for board,moves in histories:
            for move in ref.fow_moves(board):
                if board.turn and move.uci()!=lines[0][ply-1]:continue
                child=board.copy(stack=False);child.push(move)
                if ref.outcome(child,Counter()) is not None:continue
                if ref.observation(child,True)!=replay['frames'][ply]['white']:continue
                next_histories.append((child,moves+[move.uci()]))
        histories=next_histories;counts.append(len(histories))
    assert counts==[1,1,14,1,1] and histories[0][1]==lines[0][:4]
    save(PRIVATE/'records.json',records)
    for name,row in zip(('actual','alternative'),records,strict=True):
        with (PRIVATE/(name+'-black-input.txt')).open('x') as s:s.write(row['black_protocol'])
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    result=dict(at=datetime.now(timezone.utc).isoformat(),status='complete',plan_sha256=sha(OUT/'plan.json'),frames_checked=12,
        rules_sources=['Course referee Python','Pinned independent C++ rules library'],actual_white_history_counts=counts,
        black_views_equal_at_all_six_frames=True,black_own_actions_equal=True,black_protocol_with_held_clocks_identical=True,
        different_white_private_histories=True,black_final_legal_actions=len(a['frames'][5]['actions']),
        actual_four_ply_information_set_histories=1,minimum_black_compatible_histories=2,
        record_sha256=sha(PRIVATE/'records.json'),black_protocol_sha256=sha(PRIVATE/'actual-black-input.txt'),
        scope=plan['scope'],limitations=['Alternative Nc3 history is constructed, not an observed arena game.',
            'Clock messages are held equal by construction; no timing side-channel model.',
            'Membership by views and own actions does not establish positive policy reach or a posterior probability.',
            'This is not a full common-knowledge-set enumeration, KLUSS implementation, exploitability or playing-strength result.'])
    save(OUT/'result.json',result);signal.alarm(0);print(json.dumps(result,indent=2))

if __name__=='__main__':
    with lease():main()
