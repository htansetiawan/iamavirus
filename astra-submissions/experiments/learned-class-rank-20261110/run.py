"""One frozen learned-rank feasibility pass over reused training prefixes."""
import ctypes as C
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/learned-class-rank-20261110'
OLD=ROOT/'astra-submissions/analysis/capture-fixed-prior-20261110'
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def save(p,v,exclusive=True):
    with p.open('x' if exclusive else 'w') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def encode(s):
    sq=lambda t:ord(t[0])-97+8*(int(t[1])-1)
    return sq(s[:2])|(sq(s[2:4])<<6)|(('pnbrqk'.index(s[4]) if len(s)==5 else 6)<<12)
def board_text(b):return ''.join(b.piece_at(s).symbol() if b.piece_at(s) else '-' for s in range(64))


def main():
    start=time.monotonic();plan=json.loads((OUT/'plan.json').read_text())
    assert not (OUT/'execution.json').exists(),'one attempt only'
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    os.sched_setaffinity(0,set(plan['cores']))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('120-second bound')))
    signal.alarm(plan['max_seconds'])
    receipt=dict(started_at=now(),status='running',plan_sha256=sha(OUT/'plan.json'))
    save(OUT/'execution.json',receipt)
    rows=[]
    try:
        nd=lambda t:np.ctypeslib.ndpointer(dtype=t,flags='C_CONTIGUOUS')
        prior=C.CDLL(str(ROOT/'astra-submissions/experiments/capture-fixed-prior-20261110/build/bridge.so'),mode=C.RTLD_LOCAL)
        core=C.CDLL(str(ROOT/'astra-submissions/experiments/observed-class-20261110/build/producer.so'),mode=C.RTLD_LOCAL)
        native=C.CDLL(str(HERE/'build/native_math.so'),mode=C.RTLD_LOCAL)
        prior.prior_load.argtypes=[C.c_char_p];prior.prior_state.argtypes=[C.c_char_p]*3;prior.prior_step.argtypes=[C.c_uint16]
        prior.quiet_features.argtypes=[nd(np.uint16),nd(np.float32),nd(np.float32),nd(np.float32),nd(np.uint32),C.POINTER(C.c_uint),nd(np.uint8)]
        prior.quiet_logp.argtypes=[nd(np.float32),nd(np.float32),C.c_int,C.c_int,nd(np.float32),nd(np.float32),nd(np.float32)]
        native.astra_history_logp.argtypes=[C.c_int,nd(np.float32),nd(np.uint32),C.c_uint,nd(np.float32)]
        core.astra_test_set.argtypes=[C.c_char_p,C.c_int,C.c_uint64,C.c_int,C.c_int]
        core.astra_test_step.argtypes=[C.c_uint16]
        core.astra_test_state.argtypes=[C.c_char_p]*3+[C.POINTER(C.c_uint64),C.POINTER(C.c_int),C.POINTER(C.c_int)]
        core.astra_test_class.argtypes=[C.c_int,C.c_char_p,nd(np.uint16),nd(np.uint8),nd(np.uint8),nd(np.uint8),C.c_void_p]
        core.astra_rank_reassign.argtypes=[C.c_int,nd(np.uint32),nd(np.float64),nd(np.float64),nd(np.uint8),nd(np.float64)]
        history=next(p for p in plan['dependencies'] if p.endswith('/data/history.bin'))
        assert prior.prior_load(history.encode())
        models={kind:json.loads((OLD/f'22-{kind}-model.json').read_text()) for kind in ('linear','quadratic')}
        coefficients={k:(np.array(m['linear'],np.float32),np.array(m['quadratic'],np.float32)) for k,m in models.items()}
        zero=np.zeros(22,np.float32);zeroq=np.zeros((22,22),np.float32)
        moves=np.zeros(256,np.uint16);x=np.zeros((256,26),np.float32);full=np.zeros(256,np.float32);cheap=np.zeros(256,np.float32)
        counts=np.zeros(256,np.uint32);N=C.c_uint();surprise=np.zeros(256,np.uint8)
        cmoves=np.zeros(256,np.uint16);cap=np.zeros(256,np.uint8);consistent=np.zeros(256,np.uint8);eligible=np.zeros(256,np.uint8)
        pbuf=[C.create_string_buffer(65) for _ in range(3)];cbuf=[C.create_string_buffer(65) for _ in range(3)]
        checks=dict(parents=0,actions=0,capture_actions=0,masked_actions=0,powered_moments=0,capture_observations_identity=0,
                    state_frames=0,history_active=0,excluded_native_terminal=0)
        max_history_error=0.
        for g in plan['games']:
            board=ref.FowBoard();prior.prior_start()
            assert core.astra_test_set(board_text(board).encode(),0,int(board.clean_castling_rights()),-1,0)==0
            wanted=set(g['selected_plies'])
            for ply,text in enumerate(g['moves']):
                side=prior.prior_state(*pbuf)
                castle=C.c_uint64();ep=C.c_int();half=C.c_int()
                assert core.astra_test_state(*cbuf,C.byref(castle),C.byref(ep),C.byref(half))==side==ply%2
                assert tuple(b.value for b in pbuf)==tuple(b.value for b in cbuf)
                assert pbuf[0].value.decode()==board_text(board)
                assert pbuf[1].value.decode()==ref.observation(board,True) and pbuf[2].value.decode()==ref.observation(board,False)
                assert castle.value==int(board.clean_castling_rights()) and ep.value==(board.ep_square if board.ep_square is not None else -1) and half.value==board.halfmove_clock
                checks['state_frames']+=1
                n=prior.quiet_features(moves,x,full,cheap,counts,C.byref(N),surprise)
                target=np.flatnonzero(moves[:n]==encode(text));assert len(target)==1;target=int(target[0])
                action=ref.chess.Move.from_uci(text);assert action in ref.fow_moves(board)
                next_board=board.copy(stack=False);next_board.push(action)
                received=ref.observation(next_board,not board.turn)
                assert core.astra_test_class(side^1,received.encode(),cmoves,cap,consistent,eligible,None)==n
                assert np.array_equal(cmoves[:n],moves[:n]) and np.array_equal(cap[:n],x[:n,0]>0)
                assert all(bool(eligible[j])==(bool(consistent[j]) and not bool(cap[j])) for j in range(n))
                old=np.empty(n,np.float32);prior.quiet_logp(x,full,n,22,zero,zeroq,old)
                base=np.empty(n,np.float32);assert native.astra_history_logp(n,old,counts,N.value,base)==0
                if N.value>=3:
                    checks['history_active']+=1
                    for j in range(n):
                        expected=math.log((int(counts[j])+4*math.exp(float(old[j])))/(N.value+4))
                        error=abs(float(base[j])-expected);max_history_error=max(max_history_error,error)
                        assert error<4e-6,error
                else:assert base.tobytes()==old.tobytes()
                changed={};target_logs={};eligible_indices=np.flatnonzero(eligible[:n]);groups=np.zeros(n,np.uint32)
                for kind,(lin,q) in coefficients.items():
                    learned=np.empty(n,np.float32);prior.quiet_logp(x,full,n,22,lin,q,learned)
                    assert learned[cap[:n]>0].tobytes()==old[cap[:n]>0].tobytes()
                    ranking=np.empty(n,np.float32);assert native.astra_history_logp(n,learned,counts,N.value,ranking)==0
                    before=base.astype(np.float64);after=np.empty(n,np.float64);score=ranking.astype(np.float64)
                    assert core.astra_rank_reassign(n,groups,before,score,eligible,after)==0
                    reference=before.copy()
                    donors=sorted(eligible_indices,key=lambda j:(-before[j],j))
                    recipients=sorted(eligible_indices,key=lambda j:(-score[j],j))
                    for d,r in zip(donors,recipients):reference[r]=before[d]
                    assert after.tobytes()==reference.tobytes()
                    mask=eligible[:n]==0
                    assert after[mask].tobytes()==before[mask].tobytes()
                    assert np.sort(after[eligible_indices]).tobytes()==np.sort(before[eligible_indices]).tobytes()
                    for tau in (.5,1,2,3):
                        a=math.fsum(math.exp(tau*v) for v in before[eligible_indices])
                        b=math.fsum(math.exp(tau*v) for v in after[eligible_indices])
                        assert math.isclose(a,b,rel_tol=1e-14,abs_tol=1e-14)
                        checks['powered_moments']+=1
                    changed[kind]=int(np.count_nonzero(after!=before))
                    target_logs[kind]=float(after[target])
                    if cap[target]:assert not len(eligible_indices) and after.tobytes()==before.tobytes()
                assert math.isfinite(float(base[target])) and all(math.isfinite(v) for v in target_logs.values())
                primary=ply in wanted and ply//2>=8 and g[('white','black')[side]] in plan['teams'] and bool(consistent[target])
                rows.append(dict(game=g['game'],ply=ply,team=g[('white','black')[side]],selected_training_example=ply in wanted,
                    primary=primary,n=n,eligible=len(eligible_indices),capture=bool(cap[target]),surprise=bool(surprise[target]),
                    target_survives=bool(consistent[target]),history_n=N.value,changed=changed,
                    old=float(base[target]),ranked=target_logs,
                    oracle_ceiling_gain=2*(float(np.max(base[eligible_indices]))-float(base[target])) if eligible[target] else 0))
                checks['parents']+=1;checks['actions']+=n;checks['capture_actions']+=int(cap[:n].sum())
                checks['masked_actions']+=int((eligible[:n]==0).sum());checks['capture_observations_identity']+=int(cap[target]>0)
                checks['excluded_native_terminal']+=int(not consistent[target])
                assert prior.prior_step(encode(text))>=0 and core.astra_test_step(encode(text))>=0
                board=next_board
        def summary(selected):
            if not selected:return dict(decisions=0)
            gains={k:[2*(r['ranked'][k]-r['old']) for r in selected] for k in coefficients}
            return dict(decisions=len(selected),games=len({r['game'] for r in selected}),
                tempered_log_gain={k:math.fsum(v)/len(v) for k,v in gains.items()},
                quadratic_vs_linear=math.fsum(a-b for a,b in zip(gains['quadratic'],gains['linear']))/len(selected),
                changed={k:sum(r['changed'][k]>0 for r in selected) for k in coefficients},
                changed_games={k:len({r['game'] for r in selected if r['changed'][k]>0}) for k in coefficients},
                oracle_ceiling_gain=math.fsum(r['oracle_ceiling_gain'] for r in selected)/len(selected))
        primary=summary([r for r in rows if r['primary']]);assert primary['decisions']>0
        conditions=dict(changed=primary['changed']['quadratic']>=20,changed_games=primary['changed_games']['quadratic']>=4,
            positive_gain=primary['tempered_log_gain']['quadratic']>0,over_linear=primary['quadratic_vs_linear']>0,
            mask_capture_and_multiset_checks=True)
        save(OUT/'cases.json',rows)
        result=dict(at=now(),primary=primary,all_prefixes=summary(rows),
            ambiguous_primary=summary([r for r in rows if r['primary'] and r['eligible']>1]),
            checks=checks,max_history_scalar_error=max_history_error,conditions=conditions,
            decision='separate_untouched_cohort_design_only' if all(conditions.values()) else 'close_frozen_rank_scores_on_this_panel',
            scope=plan['scope'],cases_sha256=sha(OUT/'cases.json'),plan_sha256=sha(OUT/'plan.json'),
            models_fitted=False,future295_sources_opened=False)
        save(OUT/'result.json',result);print(json.dumps(result,indent=2),flush=True)
        receipt.update(status='complete',decision=result['decision'])
    except BaseException as exc:
        receipt.update(status='failed',error=repr(exc),completed_rows=len(rows))
        if rows and not (OUT/'partial-cases.json').exists():save(OUT/'partial-cases.json',rows)
        raise
    finally:
        signal.alarm(0);receipt.update(ended_at=now(),seconds=time.monotonic()-start)
        save(OUT/'execution.json',receipt,False)


if __name__=='__main__':main()
