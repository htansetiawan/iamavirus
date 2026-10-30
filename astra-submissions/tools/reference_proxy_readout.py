#!/usr/bin/env python3
"""Audit proxy replays and compare descriptively with frozen real references.

Material/exposure measures diagnose behaviour; they are not calibrated Elo.
No historical continuation after a candidate deviation is used for these game
metrics. Proxy games here were actually played to completion on the referee.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning import ingest, rules  # noqa: E402

VALUES = dict(P=1, N=3, B=3, R=5, Q=9, K=0)


def material(board, side):
    white = sum(VALUES.get(p.upper(), 0) * (1 if p.isupper() else -1) for p in board)
    return white if side == 0 else -white


def exposure(state, move, side):
    """True-board post-move attack from a source hidden before the decision."""
    before = state.board.board_string()
    source, target = rules.square_index(move[:2]), rules.square_index(move[2:4])
    value = VALUES[before[source].upper()]
    child = state.copy(); child.push(move)
    view = state.board.observation(side)
    attackers = {reply[:2] for reply in child.board.legal_moves()
                 if reply[2:4] == move[2:4] and view[rules.square_index(reply[:2])] == '?'}
    return {'piece_value': value, 'hidden_attackers': sorted(attackers),
            'hidden_attacked_piece_move': value >= 3 and bool(attackers),
            'captured_visible_material': VALUES.get(before[target].upper(), 0)}


def game_metrics(replay, side):
    states, problems = ingest.validate_replay(replay)
    if problems:
        raise ValueError(problems)
    frames = replay['frames']; early = []
    for ply in range(side, min(30, len(frames)-1), 2):
        move = frames[ply+1]['move']
        tag = exposure(states[ply], move, side)
        tag['ply'] = ply+1
        tag['captured_next_reply'] = bool(ply+2 < len(frames) and frames[ply+2]['move'][2:4] == move[2:4])
        tag['net_material_over_reply'] = (material(frames[ply+2]['board'], side) - material(frames[ply]['board'], side)
                                          if ply+2 < len(frames) else None)
        tag['net_material_after_our_next_turn'] = (material(frames[ply+3]['board'], side) - material(frames[ply]['board'], side)
                                                  if ply+3 < len(frames) else None)
        early.append(tag)
    risk = [t for t in early if t['hidden_attacked_piece_move']]
    at30 = material(frames[30]['board'], side) if len(frames) > 30 else None
    return {'plies': len(frames)-1, 'piece_moves_first30': sum(t['piece_value'] >= 3 for t in early),
            'hidden_attacked_piece_moves_first30': len(risk),
            'risky_piece_captured_next_reply': sum(t['captured_next_reply'] for t in risk),
            'risky_piece_captured_with_net_loss': sum(t['captured_next_reply'] and t['net_material_over_reply'] < 0 for t in risk),
            'risky_move_net_loss_at_least2': sum(t['net_material_over_reply'] is not None and t['net_material_over_reply'] <= -2 for t in risk),
            'risky_move_net_loss2_after_our_next_turn': sum(t['net_material_after_our_next_turn'] is not None and t['net_material_after_our_next_turn'] <= -2 for t in risk),
            'material_at_ply30': at30,
            'down3_at_ply30': at30 <= -3 if at30 is not None else None,
            'early_terminal': len(frames) <= 30,
            'early_events': risk}


def aggregate(rows):
    events = Counter()
    for r in rows:
        for key in ('piece_moves_first30', 'hidden_attacked_piece_moves_first30',
                    'risky_piece_captured_next_reply', 'risky_piece_captured_with_net_loss', 'risky_move_net_loss_at_least2',
                    'risky_move_net_loss2_after_our_next_turn'):
            events[key] += r['metrics'][key]
    reached30 = [r for r in rows if r['metrics']['material_at_ply30'] is not None]
    return {'games': len(rows), 'wins': sum(r['score'] == 1 for r in rows),
            'draws': sum(r['score'] == .5 for r in rows), 'score': sum(r['score'] for r in rows),
            'score_rate': sum(r['score'] for r in rows) / len(rows) if rows else None,
            'early_material_events': dict(events), 'games_reaching_ply30': len(reached30),
            'down3_at_ply30': sum(r['metrics']['down3_at_ply30'] for r in reached30),
            'mean_material_at_ply30': sum(r['metrics']['material_at_ply30'] for r in reached30) / len(reached30) if reached30 else None,
            'early_terminal_games': sum(r['metrics']['early_terminal'] for r in rows)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base', type=Path, required=True)
    ap.add_argument('--mode', choices=('hybrid', 'neural'), default='hybrid')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(); base = args.base
    manifest = json.loads((base/'manifest.json').read_text())
    rows = []
    for g in manifest['games']:
        side = next((s for s in ('white', 'black') if g[s] == 'IAmAVirus' and g[s+'Version'] == 35), None)
        if side is None:
            continue
        opponent = g['black' if side == 'white' else 'white'].lower()
        if opponent not in ('instructors', 'duck'):
            continue
        raw = Path(g['replay_path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == g['replay_sha256']
        rp = json.loads(raw)
        score = .5 if rp['result'] == '1/2-1/2' else float(rp['result'] == ('1-0' if side == 'white' else '0-1'))
        rows.append({'id': g['id'], 'source': 'real arena', 'team': opponent, 'v35_colour': side,
                     'score': score, 'metrics': game_metrics(rp, int(side == 'black'))})
    calibration = base / ('calibration-' + args.mode)
    errors = []
    for path in sorted(calibration.glob('*-results.jsonl')):
        for line in path.read_text().splitlines():
            g = json.loads(line)
            if 'error' in g:
                errors.append(g); continue
            raw = Path(g['replay']).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == g['replay_sha256']
            replay = json.loads(raw)
            proxy_side = 'black' if g['v35_colour'] == 'white' else 'white'
            trace = replay.get('privateDiagnostics', {}).get(proxy_side, '')
            fallback = [line for line in trace.splitlines()
                        if any(s in line for s in ('model unavailable', 'inference failed', 'scoring failed'))]
            if fallback:
                errors.append({'game': g['replay'], 'error': 'proxy inference fallback', 'trace': fallback})
                continue
            choices = re.findall(r'cands=([a-h][1-8][a-h][1-8][qrbn]?):[^\n]* move=([a-h][1-8][a-h][1-8][qrbn]?)', trace)
            rows.append({'id': Path(g['replay']).stem, 'source': 'learned proxy', 'team': g['team'],
                         'v35_colour': g['v35_colour'], 'score': g['v35_score'],
                         'proxy_modes_in_retained_log': dict(Counter(re.findall(r'\bmode=(\w+)', trace))),
                         'proxy_policy_top_choice_agreement_retained': {'decisions': len(choices), 'matches': sum(a == b for a, b in choices)},
                         'trace_caveat': 'retained stderr can be bounded; separate startup logs prove model load',
                         'metrics': game_metrics(replay, int(g['v35_colour'] == 'black'))})
    result = {'classification': 'descriptive calibration, not a candidate Elo estimate',
              'definitions': {'hidden_attack': 'opponent legal capture of moved piece after our move; attacker source was hidden before our move',
                              'piece': 'knight, bishop, rook or queen; pawn=1, minors=3, rook=5, queen=9',
                              'down3': 'net material <= -3 at ply30, only games reaching that ply; early endings separately counted',
                              'reply_loss': 'capture on moved-piece destination with negative net material change across our move and the reply',
                              'reply_loss2': 'net material falls at least 2 across our fog-exposed piece move and the reply, regardless of which piece was captured',
                              'reply_loss2_after_our_next_turn': 'same net loss measured after our next move, allowing one recapture; longer combinations can still change it',
                              'causality': 'attacked moves can be sound sacrifices or exchanges; lower exposure alone is not stronger play'},
              'groups': {}, 'errors': errors, 'games': rows}
    for source in ('real arena', 'learned proxy'):
        result['groups'][source] = {}
        for team in ('instructors', 'duck'):
            selected = [r for r in rows if r['source'] == source and r['team'] == team]
            result['groups'][source][team] = {'all': aggregate(selected), **{
                colour: aggregate([r for r in selected if r['v35_colour'] == colour]) for colour in ('white', 'black')}}
    paired = []
    for line in (base/'replay-gate/results.jsonl').read_text().splitlines():
        case = json.loads(line); desc = case['case']
        rp = json.loads(Path(desc['replay_path']).read_text())
        states, problems = ingest.validate_replay(rp)
        assert not problems, problems
        state = states[desc['ply']]; side = int(desc['side'] == 'black')
        tags = {'recorded': exposure(state, case['played'], side)}
        for name, choice in case['variants'].items():
            if 'move' in choice:
                tags[name] = exposure(state, choice['move'], side)
        paired.append({'game': desc['game'], 'ply': desc['ply'], 'choices': tags})
    result['paired_decision_exposure'] = {
        name: {'cases': sum(name in c['choices'] for c in paired),
               'hidden_attacked_piece_moves': sum(c['choices'].get(name, {}).get('hidden_attacked_piece_move', False) for c in paired)}
        for name in ('recorded', 'v35', 'r4', 'v23', 'v35-repeat')}
    result['paired_decisions'] = paired
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'groups': result['groups'], 'errors': errors}, indent=2))


if __name__ == '__main__':
    main()
