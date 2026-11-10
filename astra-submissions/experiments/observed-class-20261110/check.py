"""Independent course-rules checks on existing training prefixes and fixtures."""
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/observed-class-20261110'
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def encode(s):
    sq=lambda v:ord(v[0])-97+8*(int(v[1])-1)
    return sq(s[:2])|(sq(s[2:4])<<6)|(('pnbrqk'.index(s[4]) if len(s)==5 else 6)<<12)
def decode(m):
    sq=lambda v:chr(97+v%8)+str(1+v//8)
    return sq(m&63)+sq((m>>6)&63)+('pnbrqk'[(m>>12)&7] if ((m>>12)&7)!=6 else '')
def board_text(b):return ''.join(b.piece_at(s).symbol() if b.piece_at(s) else '-' for s in range(64))


def main():
    started=time.monotonic();plan=json.loads((OUT/'plan.json').read_text())
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    lib=ctypes.CDLL(str(HERE/'build/producer.so'))
    U=ctypes.c_uint16;B=ctypes.c_uint8;D=ctypes.c_double;G=ctypes.c_uint32
    lib.astra_test_set.argtypes=[ctypes.c_char_p,ctypes.c_int,ctypes.c_uint64,ctypes.c_int,ctypes.c_int]
    lib.astra_test_step.argtypes=[U]
    lib.astra_test_state.argtypes=[ctypes.c_char_p]*3+[ctypes.POINTER(ctypes.c_uint64),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int)]
    lib.astra_test_class.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.POINTER(U),ctypes.POINTER(B),ctypes.POINTER(B),ctypes.POINTER(B),ctypes.c_void_p]
    lib.astra_rank_reassign.argtypes=[ctypes.c_int,ctypes.POINTER(G),ctypes.POINTER(D),ctypes.POINTER(D),ctypes.POINTER(B),ctypes.POINTER(D)]
    totals=dict(parents=0,children=0,ambiguous_quiet=0,synthetic_reordered=0,capture_observations_identity=0,
                en_passant=0,promotions=0,castles=0,king_captures=0,mover_king_pruned=0,empty_classes=0)
    rows=[]

    def load(board):
        assert lib.astra_test_set(board_text(board).encode(),0 if board.turn else 1,
               int(board.clean_castling_rights()),board.ep_square if board.ep_square is not None else -1,board.halfmove_clock)==0

    def snapshot(board):
        buffers=[ctypes.create_string_buffer(65) for _ in range(3)]
        castle=ctypes.c_uint64();ep=ctypes.c_int();half=ctypes.c_int()
        side=lib.astra_test_state(*buffers,ctypes.byref(castle),ctypes.byref(ep),ctypes.byref(half))
        assert side==(0 if board.turn else 1)
        assert buffers[0].value.decode()==board_text(board)
        assert buffers[1].value.decode()==ref.observation(board,True) and buffers[2].value.decode()==ref.observation(board,False)
        assert castle.value==int(board.clean_castling_rights()) and ep.value==(board.ep_square if board.ep_square is not None else -1)
        assert half.value==board.halfmove_clock
        return (side,tuple(b.value for b in buffers),castle.value,ep.value,half.value)

    def one(board,target,label,received=None):
        before=snapshot(board);victim=not board.turn;us=0 if victim else 1
        if target is not None:
            actual=board.copy(stack=False);action=ref.chess.Move.from_uci(target)
            assert action in ref.fow_moves(board);actual.push(action)
            observed=ref.observation(actual,victim)
            assert actual.king(victim) is not None,'use a delivered-view fixture, not a terminal king-capture view'
        else:
            assert received is not None
            observed=received
        arrays=[(U*256)(),(B*256)(),(B*256)(),(B*256)()];views=ctypes.create_string_buffer(256*65)
        n=lib.astra_test_class(us,observed.encode(),*arrays,views)
        assert n>0;move,cap,match,eligible=arrays
        expected={}
        for a in ref.fow_moves(board):
            capture=board.is_capture(a);next_board=board.copy(stack=False);next_board.push(a)
            view=ref.observation(next_board,victim)
            own_king=next_board.king(board.turn)
            survives=next_board.king(victim) is not None and own_king is not None and not next_board.is_attacked_by(victim,own_king)
            expected[a.uci()]=(capture,survives and view==observed,view)
            totals['en_passant']+=int(board.is_en_passant(a));totals['promotions']+=int(a.promotion is not None)
            totals['castles']+=int(board.is_castling(a));totals['king_captures']+=int(next_board.king(victim) is None)
            totals['mover_king_pruned']+=int(own_king is None or next_board.is_attacked_by(victim,own_king))
        assert n==len(expected) and len({int(move[i]) for i in range(n)})==n
        for i in range(n):
            text=decode(move[i]);a,b,v=expected[text]
            assert bool(cap[i])==a and bool(match[i])==b and bool(eligible[i])==(b and not a),(label,text,'mask')
            assert views.raw[65*i:65*i+64].decode()==v,(label,text,'view')
        other=[(U*256)(),(B*256)(),(B*256)(),(B*256)()]
        assert lib.astra_test_class(us,observed.encode(),*other,None)==n
        assert all(bytes(a)[:n*ctypes.sizeof(a._type_)]==bytes(b)[:n*ctypes.sizeof(b._type_)] for a,b in zip(arrays,other))
        assert snapshot(board)==before
        # Wrong side/invalid view are rejected without touching outputs.
        saved=[bytes(a) for a in arrays]
        assert lib.astra_test_class(us^1,observed.encode(),*arrays,views)==-1
        assert lib.astra_test_class(us,b'?'*64,*arrays,views)==-1
        assert all(bytes(a)==b for a,b in zip(arrays,saved))
        # Generic synthetic scores only: no fitted head or true-action ranking.
        raw=[-(1+int(move[i])%97)/17 for i in range(n)]
        top=max(raw);z=top+math.log(math.fsum(math.exp(x-top) for x in raw))
        old=[x-z for x in raw];score=[-x for x in old]
        g=(G*n)(*([0]*n));o=(D*n)(*old);s=(D*n)(*score);out=(D*n)()
        assert lib.astra_rank_reassign(n,g,o,s,eligible,out)==0
        idx=[i for i in range(n) if eligible[i]]
        assert sorted(o[i] for i in idx)==sorted(out[i] for i in idx)
        assert all(bytes(o)[8*i:8*i+8]==bytes(out)[8*i:8*i+8] for i in range(n) if not eligible[i])
        for tau in (.5,1,2,3):
            assert math.isclose(math.fsum(math.exp(tau*o[i]) for i in idx),math.fsum(math.exp(tau*out[i]) for i in idx),rel_tol=1e-14,abs_tol=1e-14)
        if target is None:
            assert not any(match[:n]) and bytes(o)==bytes(out)
            totals['empty_classes']+=1
        else:
            target_index=next(i for i in range(n) if int(move[i])==encode(target))
            assert match[target_index], (label, 'fixture target must be a continuing native transition')
            if cap[target_index]:
                assert not any(eligible[:n]) and bytes(o)==bytes(out)
                totals['capture_observations_identity']+=1
        totals['parents']+=1;totals['children']+=n
        totals['ambiguous_quiet']+=len(idx)>1
        changed=sum(o[i]!=out[i] for i in range(n));totals['synthetic_reordered']+=changed>0
        rows.append(dict(label=label,n=n,consistent=sum(match[:n]),eligible=len(idx),synthetic_changed=changed))

    for g in plan['games']:
        board=ref.FowBoard();load(board)
        for ply,target in enumerate(g['moves']):
            one(board,target,f"{g['game']}:{ply}")
            assert lib.astra_test_step(encode(target))>=0
            board.push(ref.chess.Move.from_uci(target));snapshot(board)
    for fixture in plan['fixtures']:
        board=ref.FowBoard(fixture['fen']);load(board)
        received=None
        if 'view_fen' in fixture:
            other=ref.FowBoard(fixture['view_fen']);assert other.turn==board.turn
            other.push(ref.chess.Move.from_uci(fixture['view_target']))
            received=ref.observation(other,not board.turn)
        one(board,fixture.get('target'),fixture['label'],received)
    assert totals['ambiguous_quiet']>=20 and totals['synthetic_reordered']>=20
    assert all(totals[k]>0 for k in ('en_passant','promotions','castles','king_captures','mover_king_pruned','capture_observations_identity'))
    assert totals['empty_classes']==2
    (OUT/'cases.json').write_text(json.dumps(rows,indent=2)+'\n')
    result=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,totals=totals,
                received_view_only_core=True,model_scores_used=False,future_295_sources_opened=False,
                native_filter_or_clock_changed=False,seconds=time.monotonic()-started,
                case_sha256=sha(OUT/'cases.json'),plan_sha256=sha(OUT/'plan.json'),
                scope='Native component and synthetic-weight parity on existing training traces/fixtures. No learned ranking, actual posterior, cost or playing-strength result. Native king pruning only; draw-history eligibility is not certified.')
    (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
