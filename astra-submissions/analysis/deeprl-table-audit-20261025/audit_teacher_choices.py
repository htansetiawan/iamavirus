"""Privileged offline teacher sanity labels, computed AFTER engine execution.

Run with fow-starter/.venv/bin/python. Ground truth is used only here, never
supplied to the actor/solver. The check is diagnostic, not a teacher override.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser()
    p.add_argument('result',type=Path)
    p.add_argument('--referee-dir',type=Path,required=True)
    a=p.parse_args()
    sys.path.insert(0,str(a.referee_dir))
    import chess
    from referee import FowBoard, position_key, outcome
    root=Path(__file__).resolve().parents[3]
    raw=a.result.read_bytes()
    data=json.loads(raw)
    rows=[]
    target_rows=[]
    for case in data['cases']:
        target_rows.append((case,case['target'],'base'))
        if 'paired_target' in case:
            target_rows.append((case,case['paired_target'],'teacher_4B'))
    for case,target,role in target_rows:
        replay_path=root/case['replay']
        assert hashlib.sha256(replay_path.read_bytes()).hexdigest()==case['replay_sha256']
        replay=json.loads(replay_path.read_bytes())
        board=FowBoard()
        repetitions=Counter({position_key(board):1})
        for frame in replay['frames'][1:case['frame']+1]:
            board.push(board.parse_uci(frame['move']))
            repetitions[position_key(board)]+=1
        truth=''.join(board.piece_at(sq).symbol() if board.piece_at(sq) else '-'
                      for sq in range(64))
        assert truth==replay['frames'][case['frame']]['board']
        assert outcome(board,repetitions) is None
        labels=[]
        for action in target['actions']:
            q=board.copy()
            try:
                q.push(q.parse_uci(action['uci']))
            except chess.IllegalMoveError:
                labels.append({**action,'true_legal':False,'true_king_fatal':None})
                continue
            our_king=q.king(board.turn)
            fatal=our_king is None or q.is_attacked_by(q.turn,our_king)
            labels.append({**action,'true_legal':True,'true_king_fatal':fatal})
        # Only the base move is sent through the actual front end. Teacher
        # labels evaluate its raw root selector, not an invented protocol move.
        chosen=next(v for v in labels if v['uci']==target['solver_move'])
        safe=[v for v in labels if v['true_legal'] and not v['true_king_fatal']]
        sampled=target['samples']
        attack_mass=0
        for sample in sampled:
            hypothesis=chess.Board(None)
            for sq,symbol in enumerate(sample['hypothesis_board']):
                if symbol!='-':
                    hypothesis.set_piece_at(sq,chess.Piece.from_symbol(symbol))
            king=hypothesis.king(board.turn)
            if king is None or hypothesis.is_attacked_by(not board.turn,king):
                attack_mass+=sample['weight']
        rows.append({'replay':case['replay'],'frame':case['frame'],'side':case['side'],
                     'slice':case.get('slice'),'role':role,
                     'frontend_move_checked':role=='base',
                     'budget_seconds':target['search_budget_seconds'],
                     'nodes':target['nodes'],'iterations':target['iterations'],
                     'candidate_count':len(labels),
                     'true_current_king_attacked':board.king(board.turn) is None or
                         board.is_attacked_by(not board.turn,board.king(board.turn)),
                     'sampled_worlds':len(sampled),
                     'sampled_current_king_attacked_mass':attack_mass,
                     'sampled_true_board_mass':sum(s['weight'] for s in sampled
                                                 if s['hypothesis_board']==truth),
                     'chosen':chosen,
                     'true_safe_actions':safe,
                     'true_fatal_action_count':sum(v['true_king_fatal'] is True for v in labels),
                     'true_illegal_action_count':sum(not v['true_legal'] for v in labels)})
    paired={}
    for row in rows:
        key=(row['replay'],row['frame'],row['slice'])
        paired.setdefault(key,{})[row['role']]=row
    by_slice={}
    for (replay,frame,slice_name),pair in paired.items():
        if len(pair)!=2:
            continue
        base,teacher=pair['base'],pair['teacher_4B']
        def bad(r):return not r['chosen']['true_legal'] or r['chosen']['true_king_fatal']
        for key in (slice_name,'all'):
            c=by_slice.setdefault(key,Counter())
            c['pairs']+=1
            c['base_unsafe']+=int(bad(base))
            c['teacher_unsafe']+=int(bad(teacher))
            c['rescued']+=int(bad(base) and not bad(teacher))
            c['regressed']+=int(not bad(base) and bad(teacher))
            c['both_unsafe']+=int(bad(base) and bad(teacher))
            c['both_safe']+=int(not bad(base) and not bad(teacher))
            c['no_safe_action_in_root']+=int(not base['true_safe_actions'])
            # This is attack-event coverage, not truth-board recall.
            c['attack_absent_from_sample']+=int(
                base['true_current_king_attacked'] and
                base['sampled_current_king_attacked_mass']==0)
    paired_summary={}
    for key,c in by_slice.items():
        discordant=c['rescued']+c['regressed']
        tail=min(c['rescued'],c['regressed'])
        pvalue=min(1,2*sum(math.comb(discordant,k) for k in range(tail+1))/2**discordant)
        paired_summary[key]={**dict(c),
                             'unsafe_rate_reduction':(c['rescued']-c['regressed'])/c['pairs'],
                             'exact_discordant_pair_p_two_sided':pvalue}
    print(json.dumps({'input_sha256':hashlib.sha256(raw).hexdigest(),
                      'referee_sha256':hashlib.sha256((a.referee_dir/'referee.py').read_bytes()).hexdigest(),
                      'classification':'privileged post-hoc labels; never actor input',
                      'paired_counts':paired_summary,
                      'cases':rows},indent=2))


if __name__=='__main__':
    main()
