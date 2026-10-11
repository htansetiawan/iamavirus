#!/usr/bin/env python3
"""Independently verify same-tree action traces and decompose their values.

All truth matching happens here, after the bot has exited. Values describe its
finite saved continuation policy, not solved game values or calibrated odds.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

import chess
from m4_tree_audit import encoded, state, record_state


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(row, referee):
    board=referee.FowBoard(None)
    for sq,piece in enumerate(row['board']):
        if piece!='-':board.set_piece_at(sq,chess.Piece.from_symbol(piece))
    board.turn=row['side']==0;board.castling_rights=int(row['castle'],16)
    board.ep_square=row['ep'] if row['ep']>=0 else None
    board.halfmove_clock=row['halfmove']
    return board


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();run=args.run
    manifest=json.loads((run/'manifest.json').read_text())
    for name,record in manifest['files'].items():assert sha(run/name)==record['sha256'],name
    spec=importlib.util.spec_from_file_location('comparison_referee',run/'kit/referee.py')
    referee=importlib.util.module_from_spec(spec);spec.loader.exec_module(referee)
    receipt=json.loads((run/'receipt.json').read_text());assert receipt['returncode']==0
    replay=json.loads((run/'game.json').read_text())
    probe=json.loads((run/'probe/results.json').read_text());assert len(probe['rows'])==1
    row=probe['rows'][0]
    assert row['returncode']==0 and row['prefix_exact'] and row['outputs']==row['decision']
    assert all(m['ok']==1 and m['snapshot']==1 for m in row['metrics'])
    board=referee.FowBoard();counts=Counter({referee.position_key(board):1})
    for frame in replay['frames'][1:row['ply']+1]:
        assert referee.outcome(board,counts) is None
        move=chess.Move.from_uci(frame['move']);assert move in referee.fow_moves(board)
        board.push(move);counts[referee.position_key(board)]+=1
        assert encoded(board)==frame['board']
        assert all(referee.observation(board,c)==frame[k] for c,k in [(True,'white'),(False,'black')])
    own=board.turn;data={};root_reference=None;checked=0;trace_hashes={}
    for move,record in row['alternative_traces'].items():
        path=Path(record['path']);assert sha(path)==record['sha256'];trace_hashes[move]=record['sha256']
        records=[json.loads(s) for s in path.read_text().splitlines()]
        assert records[-1]['kind']=='end' and records[-1]['complete'] and records[-1]['records']==len(records)-1
        meta={r['root']:r for r in records if r['kind']=='root'};nodes={}
        for r in records:
            if r['kind']=='node':
                group=nodes.setdefault(r['root'],{});assert r['path'] not in group;group[r['path']]=r
        assert set(meta)==set(nodes) and len(nodes)==records[-1]['roots']
        roots={k:v[''] for k,v in nodes.items()}
        if root_reference is None:root_reference=roots
        else:assert roots==root_reference,'Root states/values/reaches differ between exports'
        for root,paths in nodes.items():
            initial=decode(paths[''],referee)
            for prefix,recorded in paths.items():
                b=initial.copy(stack=False)
                for uci in prefix.split('/') if prefix else []:
                    action=chess.Move.from_uci(uci);assert action in referee.fow_moves(b),(root,prefix)
                    b.push(action)
                assert state(b)==record_state(recorded),(root,prefix)
                checked+=1
        mass=sum(r['cf']*r['opp'] for r in meta.values());assert mass>0
        expected=fatal=0.;true=[];worlds=[]
        for root,paths in nodes.items():
            weight=meta[root]['cf']*meta[root]['opp']/mass
            after=paths[move];b=decode(after,referee)
            immediate=bool(b.king(not own) is not None and (b.king(own) is None or b.is_attacked_by(not own,b.king(own))))
            expected+=weight*after['raw'];fatal+=weight*immediate
            matches=state(board)==record_state(paths[''])
            worlds.append({'root':root,'weight':weight,'raw':after['raw'],'weighted_value':weight*after['raw'],
                           'immediate_king_loss':immediate,'true_state':matches,'board':paths['']['board']})
            if matches:
                replies=sorted((n for key,n in paths.items() if '/' in key),key=lambda n:n['probability'],reverse=True)
                true.append({'root':meta[root],'selected_action':after,'top_replies':replies[:5]})
        profile=next(p for p in row['action_profiles'] if p['move']==move)
        assert abs(expected-profile['raw'])<2e-8,(move,expected,profile)
        assert abs(fatal-profile['fatal'])<2e-8,(move,fatal,profile)
        data[move]={'raw_value':expected,'immediate_king_loss_share':fatal,'policy_probability':profile['policy'],
                    'execution_probability':profile['played'],'roots':len(meta),'mass':mass,'true_roots':true,'worlds':worlds}
    differences=[]
    actions=list(data)
    for i,left in enumerate(actions):
        for right in actions[i+1:]:
            rhs={w['root']:w for w in data[right]['worlds']}
            deltas=[]
            for w in data[left]['worlds']:
                other=rhs[w['root']];assert w['weight']==other['weight']
                deltas.append({'root':w['root'],'weight':w['weight'],'true_state':w['true_state'],
                    'left_value':w['raw'],'right_value':other['raw'],'weighted_difference':w['weight']*(w['raw']-other['raw']),
                    'board':w['board']})
            deltas.sort(key=lambda w:w['weighted_difference'],reverse=True)
            differences.append({'left':left,'right':right,'aggregate_difference':sum(w['weighted_difference'] for w in deltas),
                'largest_favors_left':deltas[:5],'largest_favors_right':list(reversed(deltas[-5:]))})
    result={'classification':'retrospective same-tree comparison, not a strength test','actual_selected_move':row['chosen'],
            'ply':row['ply'],'side':row['side'],'source':str(run.resolve()),'manifest_sha256':sha(run/'manifest.json'),
            'tool_sha256':sha(Path(__file__)),'probe_sha256':sha(run/'probe/results.json'),'trace_sha256':trace_hashes,
            'hypothetical_node_states_checked':checked,'alternatives':data,'pairwise_value_decomposition':differences}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'selected':row['chosen'],'checked_states':checked,'alternatives':{k:{n:v[n] for n in
        ['raw_value','immediate_king_loss_share','policy_probability','execution_probability']} for k,v in data.items()}},indent=2))


if __name__=='__main__':main()
