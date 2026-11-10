"""Validate every oracle-mined path with complete-prefix repetition history."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from prepare import ROOT,OUT,sha,write,position,text
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref


def push(board,counts,uci):
    move=ref.chess.Move.from_uci(uci);assert move in ref.fow_moves(board),uci
    board.push(move);counts[ref.position_key(board)]+=1
    return ref.outcome(board,counts)


def safe(board,uci):
    p=board.copy(stack=False);mover=p.turn;p.push(ref.chess.Move.from_uci(uci))
    return p.king(not mover) is None or (p.king(mover) is not None and not p.is_attacked_by(not mover,p.king(mover)))


def main():
    started=time.monotonic();plan=json.loads((OUT/'plan.json').read_text());done=json.loads((OUT/'completion.json').read_text())
    assert done['exit_code']==0 and not done['timed_out']
    for path,digest in plan['dependencies'].items():assert sha(path)==digest,path
    raw=Path(done['raw_path']);assert sha(raw)==done['raw_sha256'] and raw.stat().st_size==done['raw_bytes']
    bases={};frame_checks=0;games={}
    for case in plan['cases']:
        if case['game'] not in games:games[case['game']]=json.loads(Path(case['replay_path']).read_text())
        replay=games[case['game']];board=ref.FowBoard();counts=Counter({ref.position_key(board):1})
        for ply,frame in enumerate(replay['frames'][:case['ply']-1]):
            if ply:assert push(board,counts,frame['move']) is None
            assert text(board)==frame['board'] and ref.observation(board,True)==frame['white'] and ref.observation(board,False)==frame['black']
            frame_checks+=1
        assert position(board)==case['ancestor'];bases[case['context']]=(board,counts)
    valid=0;excluded=Counter();raw_count=Counter();valid_contexts=Counter();valid_games=Counter();families=Counter();actual_hits=0;conflicts=0;different_currents=0;individually=0;eligible_games=set()
    summaries={};examples=[]
    validated=raw.parent/'validated.jsonl'
    with raw.open() as source,validated.open('x') as target:
        for number,line in enumerate(source,1):
            row=json.loads(line);ci=row['context'];case=plan['cases'][ci]
            if row['kind']=='summary':
                assert ci not in summaries;summaries[ci]=row;continue
            assert row['kind']=='witness';raw_count[ci]+=1
            assert row['actual_previous']==case['actual_previous'] and row['same_opponent_move']==case['same_opponent_move']
            assert row['alternative_previous']!=row['actual_previous'] and row['reach_weights'] is None
            base,base_counts=bases[ci];p=base.copy(stack=True);q=base.copy(stack=True)
            pc=base_counts.copy();qc=base_counts.copy();us=p.turn;them=not us
            assert position(base)==row['ancestor']
            assert push(p,pc,row['actual_previous']) is None
            q_end=push(q,qc,row['alternative_previous'])
            if q_end is not None:excluded['alternative_past_terminal']+=1;continue
            previous_view=ref.observation(p,them);assert previous_view==ref.observation(q,them)
            assert push(p,pc,row['same_opponent_move']) is None
            q_end=push(q,qc,row['same_opponent_move'])
            if q_end is not None:excluded['alternative_reply_terminal']+=1;continue
            current_view=ref.observation(p,them);assert current_view==ref.observation(q,them)
            assert position(p)==row['actual_root'] and position(q)==row['alternative_root'] and text(p)!=text(q)
            p_end=push(p,pc,row['actual_current_move']);q_end=push(q,qc,row['alternative_current_move'])
            if p_end is not None or q_end is not None:excluded['current_move_terminal']+=1;continue
            assert ref.observation(p,them)==ref.observation(q,them)==row['shared_opponent_view']
            dp=int(p.is_attacked_by(us,p.king(them)));dq=int(q.is_attacked_by(us,q.king(them)))
            assert dp==row['actual_danger'] and dq==row['alternative_danger']
            legal_p={m.uci() for m in ref.fow_moves(p)};legal_q={m.uci() for m in ref.fow_moves(q)}
            assert legal_p==legal_q=={r['uci'] for r in row['replies']}
            np_=nq=intersect=different=0
            for reply in row['replies']:
                sp=int(safe(p,reply['uci']));sq=int(safe(q,reply['uci']))
                assert sp==reply['actual_safe'] and sq==reply['alternative_safe']
                np_+=sp;nq+=sq;intersect+=sp and sq;different+=sp!=sq
            assert [np_,nq]==row['safe_counts'] and intersect==row['safe_intersection'] and different>0
            actual_hits+=row['actual_current_move']==case['recorded_current'];conflicts+=np_>0 and nq>0 and intersect==0
            different_currents+=row['actual_current_move']!=row['alternative_current_move']
            if np_>0 and nq>0:individually+=1;eligible_games.add(case['game'])
            alt=ref.chess.Move.from_uci(row['alternative_previous']);c=ref.chess.Move.from_uci(row['actual_current_move'])
            family=f"past-{base.piece_at(alt.from_square).symbol().lower()}_now-{ref.chess.Piece.from_symbol(row['actual_root']['board'][c.from_square]).symbol().lower()}_danger-{dp}-{dq}"
            families[family]+=1;valid+=1;valid_contexts[ci]+=1;valid_games[case['game']]+=1
            record=dict(game=case['game'],ply=case['ply'],raw_line=number,pattern_family=family,
                        recorded_current_hit=row['actual_current_move']==case['recorded_current'],
                        matching_opponent_views=[previous_view,current_view,row['shared_opponent_view']],**row)
            target.write(json.dumps(record)+'\n')
            key=hashlib.sha256(f"288-example-{case['game']}-{case['ply']}-{row['alternative_previous']}-{row['actual_current_move']}".encode()).hexdigest()
            examples.append((key,record));examples=sorted(examples,key=lambda pair:pair[0])[:12]
    assert len(summaries)==len(plan['cases'])==32
    for ci,s in summaries.items():assert s['witnesses']==raw_count[ci]
    write(OUT/'examples.json',dict(selection='Twelve smallest salted witness hashes, not selected by outcome or safety score.',rows=[r for _,r in examples]))
    followup=individually>=12 and len(eligible_games)>=4
    write(OUT/'audit.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,contexts=len(summaries),games=len(games),
          source_frame_checks=frame_checks,raw_candidates=sum(raw_count.values()),validated_witnesses=valid,
          excluded_terminal_paths=dict(excluded),games_with_witnesses=dict(valid_games),contexts_with_witnesses=dict(valid_contexts),
          actual_current_move_hits=actual_hits,different_current_action_witnesses=different_currents,
          individually_escapable_witnesses=individually,individually_escapable_games=len(eligible_games),nontrivial_two_world_royal_conflicts=conflicts,pattern_families=dict(families),
          private_input_design_worth_review=followup,validated_path=str(validated),validated_sha256=sha(validated),
          validated_bytes=validated.stat().st_size,raw_sha256=done['raw_sha256'],
          elapsed_seconds=time.monotonic()-started,auditor_sha256=sha(Path(__file__)),
          scope='Oracle feasibility only. Actual true ancestor and hidden reply were offline miner inputs. '
                'All accepted alternative histories are legal from the same real prefix and give the opponent identical views. '
                'Current action strings may differ; children are canonical representatives of immediate royal-consequence classes. Counterfactual reach weights are unspecified; no runtime generator, CFR strategy or strength estimate.'))
    print(json.dumps(dict(validated_witnesses=valid,games=len(valid_games),actual_current_hits=actual_hits,
                         private_input_design_worth_review=followup)),flush=True)


if __name__=='__main__':main()
