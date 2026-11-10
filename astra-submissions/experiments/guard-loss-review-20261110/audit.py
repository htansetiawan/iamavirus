"""Independent truth/mask audit of retrospective same-belief traces."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'astra-submissions/analysis/guard-loss-review-20261110'
sys.path[:0] = [str(ROOT), str(ROOT.parent/'fow-starter')]
import referee as ref
from learning.move_taxonomy import fen


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe(board, move):
    mover = board.turn
    board.push(move)
    other_king, king = board.king(not mover), board.king(mover)
    result = other_king is None or (king is not None and not board.attackers(not mover, king))
    board.pop()
    return result


def main():
    plan = json.loads((OUT/'plan.json').read_text())
    completion = json.loads((OUT/'completion.json').read_text())
    assert completion['completed'] == 4 and completion['error'] is None
    for path, digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    rows, frames = [], 0
    for case in plan['cases']:
        folder = OUT/'jobs'/case['id']
        result = json.loads((folder/'result.json').read_text())
        for name, digest in result['files'].items():
            assert sha(folder/name) == digest
        game = json.loads(Path(case['replay_path']).read_text())
        board = ref.FowBoard()
        for frame in game['frames'][:case['ply']+1]:
            if frame['move']:
                move = ref.chess.Move.from_uci(frame['move'])
                assert move in ref.fow_moves(board)
                board.push(move)
            assert ref.observation(board, True) == frame['white']
            assert ref.observation(board, False) == frame['black']
            assert ''.join(board.piece_at(i).symbol() if board.piece_at(i) else '-' for i in range(64)) == frame['board']
            frames += 1
        legal = list(ref.fow_moves(board))
        safe_moves = {m.uci() for m in legal if safe(board, m)}
        a, b = result['arms']['base'], result['arms']['candidate']
        assert a['belief_fingerprint'] == b['belief_fingerprint']
        assert a['target']['samples'] == b['target']['samples']
        arms = {}
        for name, arm in [('base', a), ('candidate', b)]:
            target = arm['target']
            actions = {x['uci'] for x in target['actions']}
            assert actions.isdisjoint(target['avoid_moves'])
            assert abs(sum(w['weight'] for w in target['samples'])-1) < 1e-12
            assert abs(sum(x['probability'] for x in target['actions'])-1) < 1e-12
            assert abs(sum(x['probability']*x['q'] for x in target['actions'])-target['root_value']) < 1e-9
            chosen = ref.chess.Move.from_uci(arm['move'])
            assert chosen in legal and arm['fatal'] == (not safe(board, chosen))
            actual = ref.chess.Move.from_uci(case['actual'])
            # All four actual actions are ordinary non-EP/non-castle moves.
            assert not board.is_en_passant(actual) and not board.is_castling(actual)
            risk = 0
            for world in target['samples']:
                hypo = board.copy()
                hypo.set_board_fen(fen(world['hypothesis_board']).split()[0])
                assert actual in ref.fow_moves(hypo)
                risk += world['weight']*(not safe(hypo, actual))
            arms[name] = dict(move=arm['move'], fatal=arm['fatal'], actions=len(actions),
                safe_kept=sorted(actions & safe_moves), added_actions=sorted(actions-{x['uci'] for x in a['target']['actions']}),
                belief_count=target['belief_count'], sampled_worlds=len(target['samples']),
                actual_move_sampled_fatal_risk=risk, root_value=target['root_value'])
        rows.append(dict(id=case['id'], actual=case['actual'], true_safe_moves=sorted(safe_moves),
                         arms=arms, result_sha256=sha(folder/'result.json')))
    report = dict(at=datetime.now(timezone.utc).isoformat(), completed=4, referee_frames=frames, rows=rows,
                  plan_sha256=sha(OUT/'plan.json'), auditor_sha256=sha(Path(__file__)),
                  scope='Four outcome-selected diagnostic roots. Both arms share reconstructed belief and sample worlds. '
                        'Truth labels join after actor exit. No full-population support or probability-calibration claim. '
                        'No strength or causal attribution to the live game from one-core reconstruction.')
    with (OUT/'audit.json').open('x') as handle:
        json.dump(report, handle, indent=2)
        handle.write('\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
