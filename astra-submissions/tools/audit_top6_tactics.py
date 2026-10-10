"""Exact-referee tactical opportunities in a frozen current-version corpus sample.

Counts offers in wins/draws/losses; separates forced death from avoidable bait.
These are observational rates, not causal win probabilities for a new policy.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
import statistics
import time

import chess
from analyze_mist import board_string, safe_moves, material
from mine_top6_exploits import read, pace


def load_referee(path):
    spec = importlib.util.spec_from_file_location('top6_referee', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit(replay, team, referee):
    side = 'white' if replay['white'] == team else 'black'
    color = side == 'white'
    frames = replay['frames']
    b = referee.FowBoard()
    repetitions = Counter({referee.position_key(b): 1})
    score = .5 if replay['result'] == '1/2-1/2' else float((replay['result'] == '1-0') == color)
    row = {'id': replay['id'], 'side': side, 'score': score,
           'opponent': replay['black' if color else 'white'],
           'plies': len(frames) - 1, 'reason': replay['reason'],
           'final_clock': frames[-1]['clocks'][0 if color else 1],
           'offers': [], 'checks': [], 'heavy_moves': 0, 'heavy_exposures': [],
           'terminal': None, 'castles': [], 'first_heavy_loss': None}
    material_margin = []
    for ply, after in enumerate(frames[1:], 1):
        before = frames[ply - 1]
        assert board_string(b) == before['board'], (replay['id'], ply, 'board')
        move = b.parse_uci(after['move'])
        mover = b.turn
        pc = b.piece_at(move.from_square)
        prior = b.copy(stack=False)
        if mover == color:
            obs = before[side]
            king = b.king(color)
            attackers = list(b.attackers(not color, king))
            offers = []
            for km in b.generate_pseudo_legal_moves(from_mask=b.kings & b.occupied_co[color]):
                victim = b.piece_at(km.to_square)
                if victim is None or victim.piece_type == chess.KING or victim.color == color:
                    continue
                gives_check = king in b.attacks(km.to_square)
                trial = b.copy(stack=False)
                trial.push(km)
                cover = list(trial.attackers(not color, km.to_square))
                if cover and all(obs[s] == '?' for s in cover):
                    offers.append({'ply': ply, 'move': km.uci(), 'piece': victim.symbol().upper(),
                                   'check': gives_check, 'taken': km == move,
                                   'cover': [chess.square_name(s) for s in cover],
                                   'already_attacked': bool(attackers)})
            if attackers or offers:
                assert referee.observation(b, color) == obs, (replay['id'], ply, 'view')
                safe = safe_moves(b)
                for offer in offers:
                    offer['avoidable'] = bool(safe)
                    offer['safe_moves'] = safe
                    row['offers'].append(offer)
                if attackers:
                    trial = b.copy(stack=False)
                    trial.push(move)
                    row['checks'].append({'ply': ply, 'hidden': all(obs[s] == '?' for s in attackers),
                                          'avoidable': bool(safe),
                                          'failed': trial.is_attacked_by(not color, trial.king(color)),
                                          'attackers': [chess.square_name(s) for s in attackers]})
            if b.is_castling(move):
                row['castles'].append({'ply': ply, 'move': move.uci()})
            if pc.piece_type in (chess.QUEEN, chess.ROOK):
                row['heavy_moves'] += 1
        b.push(move)
        repetitions[referee.position_key(b)] += 1
        material_margin.append(material(b, color) - material(b, not color))
        if mover == color and pc.piece_type in (chess.QUEEN, chess.ROOK):
            cover = [s for s in b.attackers(not color, move.to_square) if before[side][s] == '?']
            if cover:
                next_move = chess.Move.from_uci(frames[ply + 1]['move']) if ply + 1 < len(frames) else None
                row['heavy_exposures'].append({'ply': ply, 'move': move.uci(),
                                               'piece': pc.symbol().upper(),
                                               'hidden_cover': [chess.square_name(s) for s in cover],
                                               'captured_next': next_move is not None and next_move.to_square == move.to_square})
        if ply == len(frames) - 1:
            assert board_string(b) == after['board'], (replay['id'], 'final board')
            for s in ['white', 'black']:
                assert referee.observation(b, s == 'white') == after[s], (replay['id'], 'final view')
            end = referee.outcome(b, repetitions)
            if replay['reason'] in ('King capturable', 'Threefold repetition', '50-move rule', 'No legal moves'):
                assert end == (replay['result'], replay['reason']), (replay['id'], end)
            if score == 0 and replay['reason'] == 'King capturable':
                assert mover == color
                obs = before[side]
                assert referee.observation(prior, color) == obs
                king = b.king(color)
                killers = [{'piece': b.piece_at(s).symbol(), 'square': chess.square_name(s),
                            'hidden': obs[s] == '?'} for s in b.attackers(not color, king)]
                was_attacked = prior.is_attacked_by(not color, prior.king(color))
                capture = prior.is_capture(move)
                kind = ('king_bait' if pc.piece_type == chess.KING and capture else
                        'king_walk' if pc.piece_type == chess.KING else
                        'ignored_check' if was_attacked else 'opened_king_line')
                row['terminal'] = {'ply': ply, 'move': move.uci(), 'kind': kind,
                                   'already_attacked': was_attacked, 'killers': killers,
                                   'safe_moves': safe_moves(prior), 'material_margin': material_margin[-1]}
    row['ever_down3_held4'] = any(max(material_margin[i:i+4]) <= -3 for i in range(len(material_margin) - 3))
    return row


def summary(rows):
    result = {'games': len(rows), 'wdl': dict(Counter('W' if r['score'] == 1 else 'D' if r['score'] == .5 else 'L' for r in rows)),
              'bait': {}, 'check': {}, 'clock': {}, 'terminal': {},
              'heavy_moves': sum(r['heavy_moves'] for r in rows),
              'heavy_exposures': sum(len(r['heavy_exposures']) for r in rows),
              'heavy_exposures_captured_next': sum(e['captured_next'] for r in rows for e in r['heavy_exposures']),
              'kingside_castles': sum(any(e['move'] in ('e1g1', 'e8g8') for e in r['castles']) for r in rows)}
    for kind in ['all', 'check', 'quiet']:
        for piece in ['all', 'Q', 'R', 'B', 'N', 'P']:
            offers = [(r, e) for r in rows for e in r['offers']
                      if (piece == 'all' or e['piece'] == piece)
                      and (kind == 'all' or e['check'] == (kind == 'check'))]
            if not offers:
                continue
            eligible = [(r, e) for r, e in offers if e['avoidable']]
            result['bait'][kind + '/' + piece] = {
                'offers': len(eligible), 'taken': sum(e['taken'] for r, e in eligible),
                'games': len({r['id'] for r, e in eligible}),
                'taken_games': len({r['id'] for r, e in eligible if e['taken']}),
                'unavoidable_offers': sum(not e['avoidable'] for r, e in offers),
                'unavoidable_taken': sum(e['taken'] for r, e in offers if not e['avoidable'])}
    for hidden in [True, False]:
        for avoidable in [True, False]:
            es = [(r, e) for r in rows for e in r['checks'] if e['hidden'] == hidden and e['avoidable'] == avoidable]
            result['check'][('hidden' if hidden else 'visible') + ('/avoidable' if avoidable else '/forced')] = {
                'offers': len(es), 'failed': sum(e['failed'] for r, e in es),
                'games': len({r['id'] for r, e in es})}
    for label, score in [('win', 1), ('draw', .5), ('loss', 0)]:
        group = [r for r in rows if r['score'] == score]
        result['clock'][label] = {'games': len(group), 'final_le15': sum(r['final_clock'] <= 15 for r in group),
                                  'median_plies': statistics.median(r['plies'] for r in group) if group else None,
                                  'reasons': dict(Counter(r['reason'] for r in group))}
    terminals = [r['terminal'] for r in rows if r['terminal']]
    result['terminal'] = {'kinds': dict(Counter(t['kind'] for t in terminals)),
                          'with_safe_reply': sum(bool(t['safe_moves']) for t in terminals),
                          'all_killers_hidden': sum(all(k['hidden'] for k in t['killers']) for t in terminals),
                          'killers': dict(Counter(k['piece'].upper() for t in terminals for k in t['killers']))}
    result['losses_down3_held4'] = sum(r['ever_down3_held4'] for r in rows if r['score'] == 0)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raw', type=Path, default=Path('data/raw'))
    ap.add_argument('--analysis', type=Path, required=True)
    ap.add_argument('--referee', type=Path, default=Path('/home/henrytan/git/fow-starter/referee.py'))
    ap.add_argument('--sample', type=int, default=200)
    ap.add_argument('--duty', type=float, default=.2)
    args = ap.parse_args()
    manifest = read(args.analysis / 'games-manifest.json')
    referee = load_referee(args.referee)
    report = {'sample': args.sample, 'sampling': 'latest completed games per current version, all outcomes', 'teams': {}}
    for team, ids in manifest.items():
        rows = []
        for index, gid in enumerate(ids[-args.sample:]):
            start = time.monotonic()
            rows.append(audit(read(args.raw / 'games' / gid / 'replay.json'), team, referee))
            pace(start, args.duty)
            if index % 50 == 49:
                print(f'{team}: {index + 1}/{min(len(ids), args.sample)}', flush=True)
        report['teams'][team] = summary(rows)
        slug = team.lower().replace(' ', '-')
        (args.analysis / (slug + '-tactics.json')).write_text(json.dumps(rows, indent=2) + '\n')
        (args.analysis / 'tactics-summary.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'team': team, **report['teams'][team]}), flush=True)


if __name__ == '__main__':
    main()
