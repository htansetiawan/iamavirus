"""Exploratory true-board check against one recorded reply; not policy search."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref
OUT=Path(__file__).resolve().parent

def mover_lost(board):
    king=board.king(not board.turn)
    return king is None or board.is_attacked_by(board.turn,king)

def main():
    plan=json.loads((OUT/'plan.json').read_text())
    replay=json.loads((Path(plan['archive'])/'0xe4vmwz.json').read_text())
    board=ref.FowBoard()
    for frame in replay['frames'][1:66]:
        move=ref.chess.Move.from_uci(frame['move']);assert move in ref.fow_moves(board);board.push(move)
    # Black to play66. White's actual next action is67.Qg8; Black dies on68.
    assert board.turn==ref.chess.BLACK
    assert replay['frames'][66]['move']=='a2a1r'
    assert replay['frames'][67]['move']=='f7g8'
    rows=[]
    for move in ref.fow_moves(board):
        b=board.copy();b.push(move)
        record=dict(move=move.uci())
        if mover_lost(b):
            record['case']='our_move_immediately_loses'
        elif ref.chess.Move.from_uci('f7g8') not in ref.fow_moves(b):
            record['case']='actual_reply_unavailable'
        else:
            b.push(ref.chess.Move.from_uci('f7g8'))
            if mover_lost(b):
                record['case']='actual_reply_would_lose_opponent_king'
            else:
                safe=[]
                for response in ref.fow_moves(b):
                    trial=b.copy();trial.push(response)
                    if not mover_lost(trial):safe.append(response.uci())
                record.update(case='actual_reply_leaves_a_safe_response' if safe else 'actual_reply_traps_all_responses',safe_responses=safe)
        rows.append(record)
    actual=next(x for x in rows if x['move']=='a2a1r')
    assert actual['case']=='actual_reply_traps_all_responses'
    result=dict(at=datetime.now(timezone.utc).isoformat(),game='0xe4vmwz',decision_ply=66,actual_move='a2a1r',recorded_reply='f7g8',
        counts=dict(Counter(x['case'] for x in rows)),moves=rows,
        scope='Post-selection oracle description on the already fixed pre-cutoff health game. Enumerate all our legal moves, then only the recorded opponent reply, then our one-ply king survival. No engine, fitted model, new data, promotion threshold or runtime recommendation.',
        limitations=['An alternative that survives this reply is not certified against other opponent replies.','The actual hidden positions are oracle inputs; belief membership, weights and live information remain unmeasured.','Does not include repetition/fifty-move outcomes of counterfactual histories; only king-capturability is tested.'],
        replay_sha256=hashlib.sha256((Path(plan['archive'])/'0xe4vmwz.json').read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),course_source_sha256=hashlib.sha256((ROOT.parent/'fow-starter/referee.py').read_bytes()).hexdigest())
    (OUT/'counterfactual.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(counts=result['counts'],actual=actual,alternatives=[x for x in rows if x['case'] not in ('our_move_immediately_loses','actual_reply_traps_all_responses')]),indent=2))
if __name__=='__main__':main()
