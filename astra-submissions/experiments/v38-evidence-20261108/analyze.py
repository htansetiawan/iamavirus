"""Explain completed candidate evidence without changing a playing parameter."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / 'astra-submissions/analysis/sf-allchildren-20261102'
OUT = ROOT / 'astra-submissions/analysis/v38-evidence-20261108'
REF = ROOT / 'astra-submissions/experiments/sf-allchildren-20261102/build/referee.py'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    os.sched_setaffinity(0, {4, 5})
    pilot = json.loads((OLD/'full-games/independent-review.json').read_text())
    plan = json.loads((OLD/'full-games/plan.json').read_text())
    audit = json.loads((OLD/'search/independent-review.json').read_text())
    summary = json.loads((OLD/'search/paired-summary.json').read_text())
    assert audit['labels_match'] and audit['summary_sha256'] == sha(OLD/'search/paired-summary.json')
    assert summary['results_sha256'] == sha(OLD/'search/paired-results.jsonl')
    assert pilot['plan_sha256'] == sha(OLD/'full-games/plan.json')
    assert pilot['referee_sha256'] == sha(REF)
    rows = [json.loads(line) for line in (OLD/'search/paired-results.jsonl').read_text().splitlines()]
    assert len(rows) == 51 and all(r['exercised'] for r in rows)
    cases = []
    for r in rows:
        a, b = r['arms']['off'], r['arms']['on']
        cases.append(dict(game=r['case']['game'], ply=r['case']['ply'], base=a['move'], candidate=b['move'],
                          changed=a['move'] != b['move'], nodes_ratio=b['nodes']/a['nodes'],
                          iterations_ratio=b['iterations']/a['iterations'],
                          elapsed_ratio=b['search_elapsed']/a['search_elapsed'],
                          base_fatal=a['fatal'], candidate_fatal=b['fatal'],
                          base_material=None if a['exchange_loss'] is None else a['exchange_loss'] >= 2,
                          candidate_material=None if b['exchange_loss'] is None else b['exchange_loss'] >= 2))
    paired = dict(cases=len(cases), changed_moves=sum(c['changed'] for c in cases),
                  median_nodes_ratio=statistics.median(c['nodes_ratio'] for c in cases),
                  median_iterations_ratio=statistics.median(c['iterations_ratio'] for c in cases),
                  median_elapsed_ratio=statistics.median(c['elapsed_ratio'] for c in cases))
    for metric in ('fatal','material'):
        comparable = [c for c in cases if c['base_'+metric] is not None and c['candidate_'+metric] is not None]
        paired[metric] = dict(
            comparable=len(comparable), unassessed=len(cases)-len(comparable),
            fixed=[c for c in comparable if c['base_'+metric] and not c['candidate_'+metric]],
            broken=[c for c in comparable if not c['base_'+metric] and c['candidate_'+metric]],
            both=sum(c['base_'+metric] and c['candidate_'+metric] for c in comparable),
            neither=sum(not c['base_'+metric] and not c['candidate_'+metric] for c in comparable))
    spec = importlib.util.spec_from_file_location('v38_terminal_referee', REF)
    ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
    terminals = []
    counts = {'candidate':Counter(), 'base':Counter()}
    input_hashes = {}
    for job in plan['jobs']:
        row = next(r for r in pilot['rows'] if r['job'] == job)
        path = OLD/'full-games/jobs'/job['id']/'replay.json'
        assert sha(path) == row['artifacts']['replay.json']
        input_hashes[str(path.relative_to(ROOT))] = sha(path)
        game = json.loads(path.read_text())
        if game['result'] == '1/2-1/2':
            terminals.append(dict(job=job['id'], category='draw', reason=game['reason']))
            continue
        assert game['reason'] == 'King capturable'
        winner = game['result'] == '1-0'; loser = not winner
        board = ref.FowBoard()
        for frame in game['frames'][1:-1]: board.push_uci(frame['move'])
        assert board.turn == loser
        last = game['frames'][-1]['move']; move = ref.chess.Move.from_uci(last)
        piece = board.piece_at(move.from_square)
        was_attacked = bool(board.attackers(winner, board.king(loser)))
        capture = board.is_capture(move)
        castle = board.is_castling(move)
        view = game['frames'][-2]['white' if loser else 'black']
        assert view == ref.observation(board,loser)
        safe_replies = []
        for reply in ref.fow_moves(board):
            board.push(reply)
            own_king = board.king(loser)
            if own_king is not None and not board.is_attacked_by(winner,own_king):
                safe_replies.append(reply.uci())
            board.pop()
        board.push(move)
        king = board.king(loser); assert king is not None
        attackers = list(board.attackers(winner, king)); assert attackers
        category = ('king_capture_into_attack' if capture else 'king_move_into_attack') if piece.piece_type == ref.chess.KING else ('ignored_existing_attack' if was_attacked else 'uncovered_own_king')
        won_by = 'candidate' if (job['side']=='white') == winner else 'base'
        counts[won_by][category] += 1
        hidden = [sq for sq in attackers if view[sq] == '?']
        counts[won_by]['some_attacker_hidden'] += bool(hidden)
        counts[won_by]['all_attackers_hidden'] += len(hidden) == len(attackers)
        terminals.append(dict(job=job['id'], won_by=won_by, category=category,
            final_ply=game['frames'][-1]['ply'], final_move=last, capture=capture, castle=castle,
            truth_safe_replies=sorted(safe_replies), no_truth_safe_reply=not safe_replies,
            king_already_attacked=was_attacked, king_square=ref.chess.square_name(king),
            attackers=[dict(square=ref.chess.square_name(sq),piece=board.piece_at(sq).symbol(),hidden_before_losing_move=view[sq]=='?') for sq in attackers],
            tail=[f['move'] for f in game['frames'][-9:] if f['move']]))
    assert sum(t.get('won_by')=='candidate' for t in terminals) == 11
    assert sum(t.get('won_by')=='base' for t in terminals) == 4
    result = dict(at=datetime.now(timezone.utc).isoformat(), analysis_version=2, script_sha256=sha(__file__), paired=paired, cases=cases,
                  terminals=terminals, wins_by_terminal_category={a:dict(c) for a,c in counts.items()},
                  inputs=input_hashes, referee_sha256=sha(REF),
                  paired_results_sha256=sha(OLD/'search/paired-results.jsonl'),
                  limitations=['Post-hoc description of completed development evidence, not another gate.',
                    'No causal attribution of wins to extra nodes: evaluator outputs also change.',
                    'Hidden attacker classification uses the loser view immediately before its final move.',
                    'Truth-safe replies use the completed true board, not information available to the bot.',
                    'No current Misty result or candidate parameter is changed.'])
    with (OUT/'evidence.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(dict(paired={k:v for k,v in paired.items() if k not in ('fatal','material')},
               fatal={k:len(v) if isinstance(v,list) else v for k,v in paired['fatal'].items()},
               material={k:len(v) if isinstance(v,list) else v for k,v in paired['material'].items()},
               wins_by_terminal_category=result['wins_by_terminal_category'],candidate_losses=[t for t in terminals if t.get('won_by')=='base'])),flush=True)

if __name__=='__main__':main()
