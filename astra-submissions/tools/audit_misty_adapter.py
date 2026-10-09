"""Audit the local Misty adapter's visible-board move list without running Misty."""
import argparse
import ast
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from zipfile import ZipFile

import chess


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--adapter', type=Path, required=True)
    ap.add_argument('--referee', type=Path, required=True)
    ap.add_argument('--corpus', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    with ZipFile(args.adapter) as archive:
        source = archive.read('misty_bot.py').decode()
    # Only the view_board helper; imports/engine initialization are not executed.
    helper = [n for n in ast.parse(source).body
              if isinstance(n, ast.FunctionDef) and n.name == 'view_board']
    assert len(helper) == 1
    assert 'legal = list(board.pseudo_legal_moves)' in source, 'Adapter changed; review this audit'
    namespace = {'chess': chess}
    exec(compile(ast.Module(body=helper, type_ignores=[]), 'adapter_helper', 'exec'), namespace)
    spec = importlib.util.spec_from_file_location('ref', args.referee)
    ref = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ref)
    sys.path.insert(0, str(args.referee.parent))
    starter_spec = importlib.util.spec_from_file_location(
        'course_uniform', args.referee.parent / 'uniform_random.py')
    starter = importlib.util.module_from_spec(starter_spec)
    starter_spec.loader.exec_module(starter)
    stats, cases = Counter(), []
    for path in sorted((args.corpus / 'games').glob('*/replay.json')):
        data, board = json.loads(path.read_text()), ref.FowBoard()
        trackers = {side: starter.ObservationTracker(side) for side in (chess.WHITE, chess.BLACK)}
        for frame in data['frames'][:-1]:
            if frame['move']:
                move = board.parse_uci(frame['move'])
                trackers[board.turn].record_move(move)
                board.push(move)
            for side, key in [(chess.WHITE, 'white'), (chess.BLACK, 'black')]:
                trackers[side].observe(frame[key])
            color = board.turn
            side = 'white' if color else 'black'
            rights = {'K': board.has_kingside_castling_rights(color),
                      'Q': board.has_queenside_castling_rights(color)}
            visible = namespace['view_board'](frame[side], color, rights)
            expected = {m.uci() for m in ref.fow_moves(board)}
            actual = {m.uci() for m in visible.pseudo_legal_moves}
            stats['positions'] += 1
            repaired = {m.uci() for m in trackers[color].legal_moves()}
            stats['starter_tracker_mismatches'] += repaired != expected
            if actual != expected:
                stats['mismatched_positions'] += 1
                stats['positions_with_spurious_moves'] += bool(actual - expected)
                stats['positions_with_missing_moves'] += bool(expected - actual)
                if len(cases) < 20:
                    cases.append({'game': data['id'], 'ply': frame['ply'], 'side': side,
                                  'spurious': sorted(actual - expected),
                                  'missing': sorted(expected - actual)})
    result = {'adapter_zip': str(args.adapter),
              'adapter_sha256': hashlib.sha256(args.adapter.read_bytes()).hexdigest(),
              'starter_sha256': hashlib.sha256((args.referee.parent / 'uniform_random.py').read_bytes()).hexdigest(),
              'counts': dict(stats), 'first_20_cases': cases,
              'scope': 'Executes only view_board helper extracted with AST, then the adapter own_legal_moves expression. Uses true own castling rights (optimistic for adapter). Also checks proposed course ObservationTracker using each side\'s observations and own moves only. No engine/Stockfish/native execution. All nonterminal turns in frozen corpus. Legal-list conformance, not proof a spurious move is selected.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
