#!/usr/bin/env python3
"""Apply Fable's known terminal-aware queen event to one fixed belief dump.

No new engine decision. Independently reproduce all old risks first, then
change only whether suicidal opponent captures count as queen losses.
"""
import gzip
import importlib.util
import json
import math
from pathlib import Path
from run import ROOT,OUT,sha

spec=importlib.util.spec_from_file_location('queen_reprice_oracle',ROOT/'astra-submissions/experiments/persistent-response-20261101/review.py')
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle);ref=oracle.ref
values={ref.chess.PAWN:1,ref.chess.KNIGHT:3,ref.chess.BISHOP:3,ref.chess.ROOK:5,ref.chess.QUEEN:9,ref.chess.KING:0}


def lost(board):
    king=board.king(not board.turn)
    return king is None or board.is_attacked_by(board.turn,king)


def event(board,uci):
    move=ref.chess.Move.from_uci(uci);target=board.piece_at(move.to_square)
    if target and target.piece_type==ref.chess.KING and target.color!=board.turn:return 0,0,0
    got=values[target.piece_type] if target and target.color!=board.turn else int(board.is_en_passant(move))
    child=board.copy(stack=False);child.push_uci(uci)
    if lost(child):return 1,0,0
    us=not child.turn;old=new=0
    for reply in ref.fow_moves(child):
        victim=child.piece_at(reply.to_square)
        if not victim or victim.color!=us or victim.piece_type!=ref.chess.QUEEN:continue
        q=child.copy(stack=False);q.push(reply);gain=9
        if q.is_attacked_by(us,reply.to_square):gain-=values[child.piece_at(reply.from_square).piece_type]
        old=max(old,gain)
        if not lost(q):new=max(new,gain)
    return 0,int(old-got>=4),int(new-got>=4)


if __name__=='__main__':
    case='23paw9tn-20';worlds=[];guards=[]
    with gzip.open(OUT/(case+'.stderr.gz'),'rt') as f:
        for line in f:
            a=line.split()
            if a and a[0]=='astra_world':
                b=ref.FowBoard(None);b.set_piece_map({i:ref.chess.Piece.from_symbol(c) for i,c in enumerate(a[1]) if c!='-'})
                b.turn=True;b.castling_rights=int(a[3]);b.ep_square=None if int(a[4])<0 else int(a[4]);b.halfmove_clock=int(a[5]);worlds.append((b,float(a[2])))
            elif a and a[0]=='astra_guard':guards.append(dict(move=a[1],king=[float(a[2]),float(a[3])],queen=[float(a[4]),float(a[5])],veto=bool(int(a[6]))))
    assert len(worlds)==54 and len(guards)==35
    weights=[[math.exp(lw/power) for b,lw in worlds] for power in (2,1)];totals=[sum(w) for w in weights];rows=[]
    for g in guards:
        events=[event(b,g['move']) for b,lw in worlds]
        risk=[[sum(w*e[k] for w,e in zip(ww,events))/total for ww,total in zip(weights,totals)] for k in range(3)]
        assert max(abs(a-b) for a,b in zip(risk[0],g['king']))<1e-10,(g,risk)
        assert max(abs(a-b) for a,b in zip(risk[1],g['queen']))<1e-10,(g,risk)
        rows.append(dict(move=g['move'],king=risk[0],old_queen=risk[1],corrected_queen=risk[2],old_veto=g['veto']))
    def retained(queen):
        risks=[[r['king'][k]+.9*r[queen][k] for k in (0,1)] for r in rows];least=[min(x[k] for x in risks) for k in (0,1)]
        for both in (True,False):
            kept=[r['move'] for r,x in zip(rows,risks) if not(x[1]>least[1]+.02 or (both and x[0]>least[0]+.02))]
            if kept:return kept
        raise AssertionError('no retained move')
    old=retained('old_queen');assert old==[g['move'] for g in guards if not g['veto']]
    result=dict(case=case,worlds=54,actions=35,old_risks_reproduced_tolerance=1e-10,old_retained=old,corrected_retained=retained('corrected_queen'),actions_detail=rows,
                known_fix_commit='dd89907',known_fix_note='chatroom/168-fable-terminal-aware-capture-events.md',
                script_sha256=sha(Path(__file__)),dump_sha256=sha(OUT/(case+'.stderr.gz')),referee_sha256=sha(oracle.REFPATH),
                scope='Same dumped worlds and weights. Only the known terminal-aware opponent-capture predicate changes. No new search, selected move, game, candidate modification or strength estimate.')
    with (OUT/'terminal-aware-reprice.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='actions_detail'}))
    print(json.dumps([r for r in rows if r['move'] in ('d2f4','c6e7')]))
