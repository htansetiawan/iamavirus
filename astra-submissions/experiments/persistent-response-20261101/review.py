#!/usr/bin/env python3
"""Post-run label audit using the course referee, independently of exchange_probe."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/persistent-response-20261101'
REFPATH = ROOT.parent / 'fow-starter/referee.py'
sys.path[:0] = [str(ROOT), str(REFPATH.parent)]
from learning import ingest

spec = importlib.util.spec_from_file_location('persistent_review_ref', REFPATH)
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)
VALUES = dict(p=1, n=3, b=3, r=5, q=9, k=0)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(board):
    return ''.join(board.piece_at(i).symbol() if board.piece_at(i) else '-' for i in range(64))


def material(board, side):
    return sum(VALUES[c.lower()] * (1 if c.isupper() == (side == 0) else -1)
               for c in text(board) if c != '-')


def push(board, history, move):
    board = board.copy()
    history = history.copy()
    board.push_uci(move)
    history[ref.position_key(board)] += 1
    return board, history, ref.outcome(board, history)


def probe(board, history, move, side):
    legal = {m.uci() for m in ref.fow_moves(board)}
    assert move in legal
    losing = ('0-1', '1-0')[side]
    child, hc, terminal = push(board, history, move)
    result = dict(legal=True, fatal=bool(terminal and terminal[0] == losing),
                  terminal=list(terminal) if terminal else None, exchange_loss=None,
                  queen_exchange_loss=None, forced_king_loss_after_capture=False)
    checks = 1
    if terminal:
        return result, checks
    chars = 'PNBRQK' if side == 0 else 'pnbrqk'
    queen = 'Q' if side == 0 else 'q'
    before = text(child)
    count = sum(c in chars for c in before)
    initial = material(board, side)
    worst = worst_queen = 0
    for reply in ref.fow_moves(child):
        after, ha, terminal = push(child, hc, reply.uci())
        checks += 1
        after_text = text(after)
        if terminal or sum(c in chars for c in after_text) >= count:
            continue
        losses = []
        for response in ref.fow_moves(after):
            end, he, terminal = push(after, ha, response.uci())
            checks += 1
            if terminal and terminal[0] == losing:
                continue
            losses.append((0 if terminal else initial-material(end, side), response.uci()))
        if not losses:
            result['forced_king_loss_after_capture'] = True
            continue
        loss, answer = min(losses)
        loss = max(0, loss)
        if loss > worst:
            worst = loss
            result['worst_capture'] = reply.uci()
            result['best_response'] = answer
        if after_text.count(queen) < before.count(queen):
            worst_queen = max(worst_queen, loss)
    result.update(exchange_loss=worst, queen_exchange_loss=worst_queen)
    return result, checks


def main():
    assert json.loads((OUT/'execution.json').read_text())['status'] == 'complete'
    plan = json.loads((OUT/'plan.json').read_text())
    labelled = json.loads((OUT/'labelled.json').read_text())
    cache = {}
    frames_checked = transitions = 0
    for game in plan['games']:
        path = ROOT/'data/raw/games'/game['game']/'replay.json'
        assert sha(path) == game['replay_sha256']
        replay = json.loads(path.read_text())
        states, errors = ingest.validate_replay(replay)
        assert not errors
        rb = ref.FowBoard()
        history = Counter({ref.position_key(rb): 1})
        sequence = []
        for ply, frame in enumerate(replay['frames']):
            if ply:
                rb.push_uci(frame['move'])
                history[ref.position_key(rb)] += 1
            rf = ref.make_frame(rb, frame['clocks'])
            for key in ['board', 'white', 'black']:
                assert rf[key] == frame[key], (game['game'], ply, key)
            assert states[ply].outcome() == ref.outcome(rb, history)
            if not states[ply].outcome():
                assert set(states[ply].board.legal_moves()) == {m.uci() for m in ref.fow_moves(rb)}
            sequence.append((rb.copy(), history.copy()))
            frames_checked += 1
        cache[game['game']] = sequence
    records = []
    fields = ['legal', 'fatal', 'terminal', 'exchange_loss', 'queen_exchange_loss',
              'forced_king_loss_after_capture']
    unique_moves = 0
    for row in labelled:
        rb, history = cache[row['game']][row['ply']]
        side = 0 if rb.turn else 1
        results = {}
        for arm, record in row['arms'].items():
            move = record['move']
            if move not in results:
                results[move], count = probe(rb, history, move, side)
                transitions += count
                unique_moves += 1
            actual = results[move]
            for key in fields:
                assert actual[key] == record['label'][key], (row['name'], arm, key, actual, record['label'])
        if len(results) > 1:
            records.append(dict(case=row['name'], opponent=row['opponent'],
                                recorded_tags=row['recorded_move_tags'],
                                choices={arm:r['move'] for arm,r in row['arms'].items()},
                                independent_labels=results))
    result = dict(referee_sha256=sha(REFPATH), script_sha256=sha(Path(__file__)),
                  plan_sha256=sha(OUT/'plan.json'), labelled_sha256=sha(OUT/'labelled.json'),
                  frames_checked=frames_checked, transitions_checked=transitions,
                  unique_choices=unique_moves, changed_cases=records,
                  scope='Independent referee verifies replay states, legal moves and all bounded tactical labels. No long-horizon optimality or Elo claim.')
    with (OUT/'referee-review.json').open('x') as f:
        json.dump(result, f, indent=2)
    print(json.dumps({k:v for k,v in result.items() if k != 'changed_cases'}, indent=2))


if __name__ == '__main__':
    main()
