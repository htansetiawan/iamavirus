"""Describe the completed gate's losses and paired divergence; no parameter fit."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import importlib.util
import json
import sys

from run import OUT, ROOT, CANDIDATE, sha, write

spec = importlib.util.spec_from_file_location('misty_review_referee', CANDIDATE/'build/referee.py')
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)


def terminal(game):
    """Use the course move generator, including its distinct castling rules."""
    board = ref.FowBoard()
    for f in game['frames'][1:-1]:
        board.push_uci(f['move'])
    before = game['frames'][-2]
    assert board.turn == (before['ply'] % 2 == 0)
    if game['result'] == '1/2-1/2':
        return dict(category='draw', reason=game['reason'])
    assert game['reason'] == 'King capturable'
    winner = game['result'] == '1-0'
    loser = not winner
    assert board.turn == loser
    view = before['white' if loser else 'black']
    assert view == ref.observation(board, loser)
    king = board.king(loser)
    attacked = board.is_attacked_by(winner, king)
    move = ref.chess.Move.from_uci(game['frames'][-1]['move'])
    piece = board.piece_at(move.from_square)
    capture = board.is_capture(move)
    safe = []
    for reply in ref.fow_moves(board):
        board.push(reply)
        k = board.king(loser)
        if k is not None and not board.is_attacked_by(winner, k):
            safe.append(reply.uci())
        board.pop()
    board.push(move)
    attackers = list(board.attackers(winner, board.king(loser)))
    assert attackers
    kind = (('king_capture_into_attack' if capture else 'king_move_into_attack')
            if piece.piece_type == ref.chess.KING else
            ('ignored_existing_attack' if attacked else 'uncovered_own_king'))
    return dict(category=kind, final_ply=game['frames'][-1]['ply'], final_move=move.uci(),
                loser='white' if loser else 'black', already_attacked=bool(attacked),
                truth_safe_replies=sorted(safe), forced_before_last_move=not safe,
                attackers=[dict(square=ref.chess.square_name(a), piece=board.piece_at(a).symbol(),
                                hidden_before_move=view[a]=='?') for a in attackers])


def main(stopped=False):
    audit_path = OUT/('stopped-review.json' if stopped else 'independent-review.json')
    audit = json.loads(audit_path.read_text())
    assert not audit['live_owned_processes']
    if stopped:
        assert audit['decision'] == 'technical_failure_no_promotion' and not audit['gate_pass']
    else:
        assert audit['completed'] == 32
    games = {}
    rows = []
    groups = defaultdict(Counter)
    for entry in audit['rows']:
        job = entry['job']
        path = OUT/'jobs'/job['id']/'replay.json'
        assert sha(path) == entry['artifacts']['replay.json']
        game = json.loads(path.read_text())
        desc = (dict(category='technical', reason=game['reason'], failed_side=game['failedSide'])
                if entry.get('faults') else terminal(game))
        row = dict(job=job, score=entry['score'], terminal=desc,
                   plies=len(game['frames'])-1, final_clock=entry['final_clocks'][job['side']=='black'])
        rows.append(row)
        games[job['pair'], job['side'], job['arm']] = game
        if desc['category'] == 'technical':
            groups[job['arm']]['technical'] += 1
        elif desc['category'] == 'draw':
            groups[job['arm']]['draws'] += 1
        else:
            outcome = 'loss' if desc['loser'] == job['side'] else 'win'
            groups[job['arm']][outcome+'_'+desc['category']] += 1
            groups[job['arm']][outcome+'_forced_before_last_move'] += desc['forced_before_last_move']
            groups[job['arm']][outcome+'_all_attackers_hidden'] += all(a['hidden_before_move'] for a in desc['attackers'])
    divergence = []
    for pair in range(8):
        for side in ('white', 'black'):
            if not all((pair,side,arm) in games for arm in ('base','candidate')):
                divergence.append(dict(pair=pair,side=side,unpaired=True))
                continue
            a, b = [games[pair, side, arm] for arm in ('base', 'candidate')]
            first = next((i for i in range(1, min(len(a['frames']), len(b['frames'])))
                          if a['frames'][i]['move'] != b['frames'][i]['move']), None)
            owner = None if first is None else ('arm' if (first % 2 == 1) == (side == 'white') else 'Misty')
            divergence.append(dict(pair=pair, side=side, first_different_ply=first, first_different_actor=owner,
                base_move=None if first is None else a['frames'][first]['move'],
                candidate_move=None if first is None else b['frames'][first]['move']))
    result = dict(at=datetime.now(timezone.utc).isoformat(), audit_sha256=sha(audit_path),
                  script_sha256=sha(__file__), referee_sha256=sha(CANDIDATE/'build/referee.py'),
                  arms={k:dict(v) for k,v in groups.items()}, rows=rows, paired_first_divergence=divergence,
                  first_diverging_actors=dict(Counter(r['first_different_actor'] for r in divergence if not r.get('unpaired'))),
                  unmatched_pairs=sum(bool(r.get('unpaired')) for r in divergence),
                  gate_status=audit.get('decision', 'complete'),
                  limitations=['Post-hoc description of this complete development batch, not another advancement gate.',
                    'Truth-safe replies are offline labels; the actors were not given the true boards.',
                    'First divergence and last moves do not establish the causal decision that won or lost.',
                    'A matching seed is not deterministic control of wall-clock search or every opponent random source.'])
    prefix='stopped-explanation' if stopped else 'explanation'
    write(OUT/(prefix+'.json'), result)
    text = ['# What the Misty gate changed', '',
            'Post-hoc description; original advancement threshold and all results remain unchanged.', '',
            '| arm | clean losses | draws | clean wins | technical | lowest final clock |', '|---|---:|---:|---:|---:|---:|']
    for arm in ('base','candidate'):
        all_rows = [r for r in rows if r['job']['arm']==arm]
        r = [r for r in all_rows if r['terminal']['category']!='technical']
        text.append(f"| {arm} | {sum(x['score']==0 for x in r)} | {sum(x['score']==.5 for x in r)} | {sum(x['score']==1 for x in r)} | {len(all_rows)-len(r)} | {min(x['final_clock'] for x in all_rows):.1f}s |")
    text += ['', '## Loss patterns', '', '| arm / game | final move | pattern | truth-safe replies |', '|---|---|---|---:|']
    for r in rows:
        if r['score'] != 0 or r['terminal']['category']=='technical':
            continue
        t=r['terminal']; j=r['job']
        text.append(f"| {j['arm']} / block {j['pair']} {j['side']} | {t['final_move']} | {t['category']} | {len(t['truth_safe_replies'])} |")
    text += ['', 'Zero truth-safe replies means the final move was already forced on the true board. '
             'It must not be labelled a missed escape. A positive count does not establish that the actor could infer the danger.', '',
             '## Paired-game matching', '',
             f"First differing actor across {16-result['unmatched_pairs']} available paired histories: {result['first_diverging_actors']}. "
             f"{result['unmatched_pairs']} pairs have a missing game and are explicitly unassessed.", '',
             'A first difference in Misty before our actions diverge demonstrates residual opponent/search variability. '
             'It does not invalidate randomized comparisons, but same seed must not be described as an identical opponent response stream. '
             'The stopped audit makes no statistical comparison from outcome-dependent missing games.', '',
             f'Full attacker visibility, safe replies, replay hashes and divergences are in {prefix}.json. '
             'None is a deployed feature, fitted threshold or strength claim.']
    (OUT/(prefix+'.md')).write_text('\n'.join(text)+'\n')
    print(json.dumps(dict(arms=result['arms'], first_diverging_actors=result['first_diverging_actors'])), flush=True)


if __name__ == '__main__':
    assert sys.argv[1:] in ([], ['--stopped'])
    main(stopped=bool(sys.argv[1:]))
