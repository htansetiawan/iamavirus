"""Recheck the frozen local Misty protocol adapter, without running its engine.

This is an audit of our wrapper on already played games, not an Obscuro duel,
another v38 promotion attempt, or an inspection of Misty's implementation.
"""
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import chess

ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT/'astra-submissions/analysis/sf-opponent-20261108'
ADAPTER = ROOT/'astra-submissions/experiments/stable-mix-20261101/build/misty/misty_bot.py'
COURSE = Path('/home/henrytan/git/fow-starter')
OUT = ROOT/'astra-submissions/analysis/obscuro-fidelity-20261108/adapter-audit.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan = json.loads((GATE/'plan.json').read_text())
    assert sha(ADAPTER) == plan['dependencies'][str(ADAPTER)]
    source = ADAPTER.read_text()
    assert 'legal = list(board.pseudo_legal_moves)' in source
    helper = [node for node in ast.parse(source).body
              if isinstance(node, ast.FunctionDef) and node.name == 'view_board']
    assert len(helper) == 1
    namespace = {'chess': chess}
    exec(compile(ast.Module(body=helper, type_ignores=[]), str(ADAPTER), 'exec'), namespace)
    sys.path.insert(0, str(COURSE))
    import referee as ref
    import uniform_random as starter
    counts = Counter(); by_arm = {}; examples = []; files = {}
    for job in plan['jobs']:
        directory = GATE/'jobs'/job['id']
        if not (directory/'result.json').exists():
            continue
        receipt = json.loads((directory/'result.json').read_text())
        replay_path = directory/'replay.json'
        assert sha(replay_path) == receipt['replay_sha256']
        data = json.loads(replay_path.read_text())
        files[job['id']] = sha(replay_path)
        counts['games'] += 1
        misty_side = 'black' if job['side'] == 'white' else 'white'
        arm = by_arm.setdefault(job['arm'], Counter())
        arm['games'] += 1
        board = ref.FowBoard()
        trackers = {side: starter.ObservationTracker(side) for side in (chess.WHITE, chess.BLACK)}
        for index, frame in enumerate(data['frames']):
            if frame['move']:
                move = chess.Move.from_uci(frame['move'])
                assert move in ref.fow_moves(board), (job['id'],index)
                trackers[board.turn].record_move(move)
                board.push(move)
            for side, key in [(chess.WHITE,'white'),(chess.BLACK,'black')]:
                trackers[side].observe(frame[key])
            if index == len(data['frames'])-1 and 'failedSide' not in data:
                continue
            side = 'white' if board.turn else 'black'
            if side != misty_side:
                continue
            rights = dict(K=board.has_kingside_castling_rights(board.turn),
                          Q=board.has_queenside_castling_rights(board.turn))
            visible = namespace['view_board'](frame[side], board.turn, rights)
            actual = {move.uci() for move in visible.pseudo_legal_moves}
            expected = {move.uci() for move in ref.fow_moves(board)}
            repaired = {move.uci() for move in trackers[board.turn].legal_moves()}
            extras, missing = actual-expected, expected-actual
            for counter in (counts,arm):
                counter['misty_turns'] += 1
                counter['mismatch'] += bool(extras or missing)
                counter['extra_moves'] += bool(extras)
                counter['missing_moves'] += bool(missing)
                counter['course_tracker_mismatch'] += repaired != expected
            if (extras or missing or repaired != expected) and len(examples)<20:
                examples.append(dict(job=job['id'],ply=index,side=side,
                                     extra=sorted(extras),missing=sorted(missing),
                                     tracker_extra=sorted(repaired-expected),
                                     tracker_missing=sorted(expected-repaired)))
    assert counts['games'] == 29
    native = Path('/home/henrytan/fable-persist/scratchpad/misty/venv/lib/python3.13/site-packages/fow_rust/fow_rust.cpython-313-x86_64-linux-gnu.so')
    result = dict(at=datetime.now(timezone.utc).isoformat(),counts=dict(counts),
                  by_arm={k:dict(v) for k,v in by_arm.items()},examples=examples,
                  files=files,adapter_sha256=sha(ADAPTER),
                  referee_sha256=sha(COURSE/'referee.py'),
                  tracker_sha256=sha(COURSE/'uniform_random.py'),
                  native_extension_current=dict(path=str(native),sha256=sha(native),
                      bytes=native.stat().st_size,was_pinned_in_gate=str(native) in plan['dependencies']),
                  scope='Only our wrapper helper is executed. Correct own castling rights '
                  'make this an optimistic audit of the old helper. Course tracker uses '
                  'each side observation and own moves only. All 29 recorded first '
                  'attempts are retained, including the unanswered final timeout turn. '
                  'Wrong supplied move lists do not prove those moves were selected. '
                  'No game is replayed by an actor; no score or prior gate is changed.')
    with OUT.open('x') as handle:
        json.dump(result,handle,indent=2);handle.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('files','examples')}))


if __name__ == '__main__':
    main()
