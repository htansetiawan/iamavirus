#!/usr/bin/env python3
"""Enumerate indistinguishable replies that require incompatible defenses.

This is an offline tactical labeler. It assumes one known current board; it is
not a general imperfect-information policy and never reads a live arena board.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys


def analyze(board,move,referee,chess):
    us=board.turn;theirs='0-1' if us else '1-0'
    assert move in referee.fow_moves(board)
    after=board.copy();after.push(move);end=referee.outcome(after,{referee.position_key(after):1})
    if end:return {'move':move.uci(),'immediate_outcome':end}
    groups=defaultdict(list);terminal=[];replies=list(referee.fow_moves(after))
    for reply in replies:
        child=after.copy();child.push(reply);end=referee.outcome(child,{referee.position_key(child):1})
        if end:terminal.append({'reply':reply.uci(),'outcome':end});continue
        groups[referee.observation(child,us)].append((reply.uci(),child))
    detail=[]
    for view,worlds in groups.items():
        action_sets=[set(m.uci() for m in referee.fow_moves(p)) for _,p in worlds]
        actions=sorted(set.union(*action_sets));fatal={};safe_sets=[]
        for i,(reply,p) in enumerate(worlds):
            safe=set()
            for text in actions:
                if text not in action_sets[i]:loses=True
                else:
                    child=p.copy();child.push_uci(text);end=referee.outcome(child,{referee.position_key(child):1})
                    loses=bool(end and end[0]==theirs)
                fatal.setdefault(text,[]).append(loses)
                if not loses:safe.add(text)
            safe_sets.append(safe)
        common=set.intersection(*safe_sets);minimum=min(sum(v) for v in fatal.values())
        incompatible=[(worlds[i][0],worlds[j][0]) for i in range(len(worlds)) for j in range(i)
                      if safe_sets[i] and safe_sets[j] and not safe_sets[i]&safe_sets[j]]
        item=dict(observation=view,replies=[r for r,_ in worlds],worlds=len(worlds),responses=len(actions),
             universal_survival=sorted(common),minimum_fatal_worlds=minimum,
             uniform_conditional_min_risk=minimum/len(worlds),incompatible_reply_pairs=incompatible)
        if minimum:
            item['safe_by_reply']={r:sorted(safe_sets[i]) for i,(r,_) in enumerate(worlds)}
            item['fatal_matrix']=fatal
            if incompatible:
                # Equal mixing over disjoint defense sets gives a 1/2 lower
                # bound. A matching response mixture proves the local value.
                defense=next(((a,b) for a in actions for b in actions
                    if max((x+y)/2 for x,y in zip(fatal[a],fatal[b]))<=.5),None)
                if defense:item['one_response_minimax_proof']={
                    'attacker_mix':dict.fromkeys(incompatible[0],.5),
                    'defender_mix':dict.fromkeys(defense,.5),'immediate_loss_value':.5,
                    'scope':'Only this finite immediate-response game, not full-chess value or observed opponent policy.'}
        detail.append(item)
    alive=sum(g['worlds'] for g in detail)
    return dict(move=move.uci(),opponent_legal_replies=len(replies),terminal_replies=terminal,
        continuing_replies=alive,observation_groups=len(detail),
        groups_with_no_universal_survival=sum(g['minimum_fatal_worlds']>0 for g in detail),
        uniform_reply_min_risk=sum(g['minimum_fatal_worlds'] for g in detail)/alive if alive else None,
        groups=detail)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--game',type=Path,required=True)
    ap.add_argument('--kit',type=Path,required=True);ap.add_argument('--ply',type=int,required=True)
    ap.add_argument('--moves',nargs='+',required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();sys.path.insert(0,str(args.kit));import referee,chess
    g=json.loads(args.game.read_text());b=referee.FowBoard()
    for frame in g['frames'][1:args.ply+1]:b.push_uci(frame['move'])
    assert ''.join(b.piece_at(s).symbol() if b.piece_at(s) else '-' for s in range(64))==g['frames'][args.ply]['board']
    reports=[analyze(b,chess.Move.from_uci(m),referee,chess) for m in args.moves]
    out=dict(game=g['id'],ply=args.ply,fen=b.fen(),moves=reports,
        game_sha256=hashlib.sha256(args.game.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        assumption='Single known current board; verify singleton belief before interpreting as an online decision rule.',
        limitations=['Uniform surviving-opponent-reply calculation is a diagnostic, not a fitted opponent policy.',
                    'Only immediate failure at our next response is labeled; no longer-term material or win probability.',
                    'Counterfactual repetition history is not modeled; used here only in the early opening.'])
    args.out.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in r.items() if k!='groups'} for r in reports],indent=2))


if __name__=='__main__':main()
