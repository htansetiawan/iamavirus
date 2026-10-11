#!/usr/bin/env python3
"""Freeze Fable's risk-selected 24-death/24-survival gate with referee labels.

Inputs are local completed matches, not public arena games. Selection reproduces
kappa_check.py before looking at any new candidate. Large inputs live on the
external disk; the compact manifest is suitable for the repository.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import sys

from m4_replay_probe import inputs


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def immutable(path, value):
    data = (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Refusing to replace different input: {path}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--calibration', type=Path, required=True)
    ap.add_argument('--selection-script', type=Path, required=True)
    ap.add_argument('--games-root', type=Path, required=True)
    ap.add_argument('--cache', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--kit', type=Path, default=Path.home()/'git/fow-starter')
    args = ap.parse_args()
    sys.path.insert(0, str(args.kit))
    import chess
    import referee
    if args.out.exists():
        raise ValueError('Gate manifest already exists; verify/reuse it instead of reselection')
    raw = json.loads(args.calibration.read_text())
    dead = [r for r in raw if r['died'] and r['risk'] > r['least']+.01]
    eligible = [r for r in raw if not r['died'] and r['risk'] > r['least']+.01]
    survived = random.Random(1).sample(eligible, min(len(eligible), 24))
    assert len(dead) == len(survived) == 24, 'Changed calibration: review the gate before proceeding'
    allowed = {'id','white','black','result','reason','timeControl','rulesVersion','createdAt','frames','protocol'}
    cases, receipt, seen, seen_seats = [], {}, {}, set()
    for cohort, rows in [('death', dead), ('survival', survived)]:
        for index, row in enumerate(rows, 1):
            source = args.games_root/row['game']
            if source not in seen:
                game = json.loads(source.read_text())
                clean = {k:v for k,v in game.items() if k in allowed}
                assert clean.get('protocol') and not clean['protocol'].get('truncated')
                target = args.cache/source.name
                immutable(target, clean)
                receipt[source.name] = {'source': str(source.resolve()), 'source_sha256':sha(source),
                                        'cache':str(target.resolve()), 'cache_sha256':sha(target),
                                        'removed_fields': sorted(set(game)-allowed),
                                        'source_kind':'local completed referee match; not public API'}
                seen[source] = clean
            game = seen[source]
            colors = [s for s in ('white','black') if game[s] == row['us']]
            assert len(colors) == 1, f'Ambiguous side for {row}'
            side, decision, played, _ = inputs(game, row['k'], colors[0])
            assert played[decision-1] == row['move']
            ply = 2*(decision-1)+(side == 'black')
            board = referee.FowBoard()
            reps = Counter({referee.position_key(board):1})
            for frame in game['frames'][1:ply+1]:
                move = chess.Move.from_uci(frame['move'])
                assert move in referee.fow_moves(board)
                board.push(move); reps[referee.position_key(board)] += 1
            actual = ''.join(board.piece_at(i).symbol() if board.piece_at(i) else '-' for i in range(64))
            assert actual == game['frames'][ply]['board']
            assert board.turn == (side == 'white') and referee.outcome(board, reps) is None
            assert game['frames'][ply+1]['move'] == row['move']
            loss = '0-1' if side == 'white' else '1-0'
            legal = list(referee.fow_moves(board))
            safe, outcomes = [], {}
            for move in legal:
                child = board.copy(); child.push(move)
                counts = reps.copy(); counts[referee.position_key(child)] += 1
                outcome = referee.outcome(child, counts); outcomes[move.uci()] = outcome
                if not outcome or outcome[0] != loss:
                    safe.append(move.uci())
            actual_result = outcomes[row['move']]
            actual_died = bool(actual_result and actual_result[0] == loss)
            assert actual_died == bool(row['died']), f'Historical label disagrees with referee: {row}'
            key = (game['id'], side, decision)
            assert key not in seen_seats; seen_seats.add(key)
            cases.append({'case':f'{cohort[0]}{index:02}', 'cohort':cohort, 'game':game['id'],
                          'source_file':source.name, 'cache':receipt[source.name]['cache'],
                          'cache_sha256':receipt[source.name]['cache_sha256'], 'side':side,
                          'decision':decision, 'ply':ply, 'played':row['move'], 'us':row['us'],
                          'opponent':row['opp'], 'selection_row':row,
                          'legal_moves':sorted(outcomes), 'safe_moves':sorted(safe),
                          'unavoidable_immediate_loss':not safe, 'played_outcome':actual_result,
                          'truth_board':actual, 'truth_fen':board.fen(),
                          'played_promotion':len(row['move'])==5})
    manifest = {'created_at':datetime.now(timezone.utc).isoformat(),
                'classification':'selected local replay gate; not an arena-strength estimate',
                'calibration':str(args.calibration), 'calibration_sha256':sha(args.calibration),
                'selection_script_sha256':sha(args.selection_script),
                'selection':'all died with risk>least+.01; random.Random(1).sample(eligible survivals,24)',
                'eligible_survivals':len(eligible), 'referee_sha256':sha(args.kit/'referee.py'),
                'python':sys.version, 'inputs':receipt, 'cases':cases}
    immutable(args.out, manifest)
    print(json.dumps({'cases':len(cases), 'games':len(receipt),
                      'unavoidable':[r['case'] for r in cases if r['unavoidable_immediate_loss']],
                      'opponents':dict(Counter(r['opponent'] for r in cases)),
                      'manifest_sha256':sha(args.out)}))


if __name__ == '__main__':
    main()
