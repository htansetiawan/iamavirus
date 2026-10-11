#!/usr/bin/env python3
"""Match post-decision M4 traces to an independent historical referee oracle.

Validate every exported hypothetical path's board transitions. Only afterward
match true roots and classify forcing replies. No truth is supplied to the bot.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(board):
    return ''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64))


def state(board):
    return (encoded(board), 0 if board.turn else 1, board.ep_square if board.ep_square is not None else -1,
            board.castling_rights, board.halfmove_clock)


def record_state(row):
    return row['board'], row['side'], row['ep'], int(row['castle'],16), row['halfmove']


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('runs',type=Path,nargs='+')
    ap.add_argument('--kit',type=Path,default=Path.home()/'git/fow-starter')
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();sys.path.insert(0,str(args.kit))
    import chess
    import referee
    checked=0;output=[];provenance=[]
    for run in args.runs:
        manifest=json.loads((run/'manifest.json').read_text())
        assert sha(args.kit/'referee.py')==manifest['referee_sha256']
        assert sha(run/'replay')==manifest['artifacts']['replay']['sha256']
        assert sha(run/'binary')==manifest['artifacts']['binary']['sha256']
        report=json.loads((run/'summary.json').read_text());assert report['complete']
        replay=json.loads((run/'replay').read_text())
        provenance.append({'run':str(run.resolve()),'manifest_sha256':sha(run/'manifest.json'),'summary_sha256':sha(run/'summary.json')})
        for row in report['rows']:
            result={k:row.get(k) for k in ['game','side','ply','mode','variant','seed','tactical_closure','leaf_scale','chosen','status']}
            if row['status']!='ok':
                result['classification']='probe_failed';output.append(result);continue
            board=referee.FowBoard();counts=Counter({referee.position_key(board):1})
            for i,frame in enumerate(replay['frames'][:row['ply']+1]):
                assert frame['ply']==i
                if i:
                    move=chess.Move.from_uci(frame['move'])
                    assert not referee.outcome(board,counts) and move in referee.fow_moves(board)
                    board.push(move);counts[referee.position_key(board)]+=1
                assert encoded(board)==frame['board']
                assert referee.observation(board,True)==frame['white']
                assert referee.observation(board,False)==frame['black']
            trace_path=Path(row['continuation_trace']['path'])
            assert sha(trace_path)==row['continuation_trace']['sha256']
            trace=[json.loads(line) for line in trace_path.read_text().splitlines()]
            assert trace[-1]['kind']=='end' and trace[-1]['complete'] and trace[-1]['records']==len(trace)-1
            metadata={};nodes=defaultdict(dict)
            for t in trace[:-1]:
                for value in t.values():
                    if isinstance(value,float):assert math.isfinite(value)
                if t['kind']=='root':
                    assert t['root'] not in metadata;metadata[t['root']]=t
                else:
                    assert t['kind']=='node' and t['path'] not in nodes[t['root']]
                    nodes[t['root']][t['path']]=t
            assert len(metadata)==len(nodes)==trace[-1]['roots']
            true_roots=[]
            for root,paths in nodes.items():
                origin=paths[''];hyp=referee.FowBoard(None)
                for square,piece in enumerate(origin['board']):
                    if piece!='-':hyp.set_piece_at(square,chess.Piece.from_symbol(piece))
                hyp.turn=origin['side']==0;hyp.castling_rights=int(origin['castle'],16)
                hyp.ep_square=origin['ep'] if origin['ep']>=0 else None;hyp.halfmove_clock=origin['halfmove']
                assert state(hyp)==record_state(origin)
                for path,t in paths.items():
                    child=hyp.copy()
                    for uci in path.split('/') if path else []:
                        move=chess.Move.from_uci(uci);assert move in referee.fow_moves(child),(root,path,uci)
                        child.push(move)
                    assert state(child)==record_state(t),(root,path,state(child),record_state(t))
                    checked+=1
                if state(board)==record_state(origin):true_roots.append(root)
            result['trace_sha256']=sha(trace_path);result['trace_roots']=len(nodes)
            result['true_roots']=len(true_roots);result['matches']=[]
            loss='0-1' if row['side']=='white' else '1-0'
            own=chess.Move.from_uci(row['chosen']);assert own in referee.fow_moves(board)
            child=board.copy();child.push(own);after=counts.copy();after[referee.position_key(child)]+=1
            ending=referee.outcome(child,after);forcing=[]
            if not ending:
                for reply in referee.fow_moves(child):
                    next_board=child.copy();next_board.push(reply);next_counts=after.copy();next_counts[referee.position_key(next_board)]+=1
                    terminal=referee.outcome(next_board,next_counts);safe=[]
                    if not terminal:
                        for escape in referee.fow_moves(next_board):
                            final=next_board.copy();final.push(escape);reps=next_counts.copy();reps[referee.position_key(final)]+=1
                            out=referee.outcome(final,reps)
                            if not out or out[0]!=loss:safe.append(escape.uci())
                    if (terminal and terminal[0]==loss) or (not terminal and not safe):
                        forcing.append({'reply':reply.uci(),'terminal':terminal,'safe_escapes':safe})
            result['oracle_forcing_replies']=forcing
            result['immediate_outcome']=ending
            result['classification']='true_root_missing' if not true_roots else 'no_forcing_reply' if not forcing else 'forcing_reply_present'
            for root in true_roots:
                paths=nodes[root];selected=paths[row['chosen']]
                match={'root':metadata[root],'selected':selected,'forcing':[]}
                for forced in forcing:
                    node=paths.get(row['chosen']+'/'+forced['reply'])
                    if not node:why='opponent_frontier_unexpanded' if selected['node_kind']=='frontier' else 'forcing_reply_not_in_action_set'
                    elif node['node_kind']=='frontier':why='own_response_frontier_unexpanded'
                    elif node['node_kind']=='terminal':why='terminal_loss_represented' if node['raw']<=-1+1e-9 else 'terminal_value_disagrees'
                    elif node['actions']>0 and node['loss_children']==node['actions']:
                        why='forced_loss_represented' if abs(node['raw']+1)<1e-9 else 'all_loss_children_value_disagrees'
                    else:why='responses_not_all_terminal_losses'
                    match['forcing'].append({'reply':forced['reply'],'classification':why,'node':node})
                result['matches'].append(match)
            output.append(result)
    result={'classification':'post-decision diagnostic; no strength inference','referee_sha256':sha(args.kit/'referee.py'),
            'source_sha256':sha(__file__),'provenance':provenance,'hypothetical_node_states_checked':checked,'rows':output}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,indent=2)+'\n')
    for r in output:
        print(json.dumps({k:r[k] for k in ['game','variant','seed','tactical_closure','chosen','true_roots','classification']}))
        for m in r['matches']:
            print(json.dumps({'root_reach':m['root']['cf']*m['root']['opp'],'alternate':m['root']['alternate'],'selected_raw':m['selected']['raw'],
                              'forcing':[(f['reply'],f['classification'],f['node']['probability'] if f['node'] else None) for f in m['forcing']]}))
    print('Checked hypothetical node states:',checked)


if __name__=='__main__':main()
