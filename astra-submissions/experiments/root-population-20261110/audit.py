"""Rebuild every exported world with the independent course rules; join truth last."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'astra-submissions/analysis/root-population-20261110'
sys.path[:0] = [str(ROOT), str(ROOT.parent/'fow-starter')]
import referee as ref
from learning.move_taxonomy import fen


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = json.loads((OUT/'plan.json').read_text())
    done = json.loads((OUT/'completion.json').read_text())
    for path, digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    assert sha(OUT/'case/population.json') == done['population_sha256']
    result = json.loads((OUT/'case/result.json').read_text())
    for name, digest in result['files'].items():
        assert sha(OUT/'case'/name) == digest, name
    pop = json.loads((OUT/'case/population.json').read_text())
    assert len(pop['worlds']) == pop['count'] == done['population']
    replay = json.loads(Path(plan['case']['replay_path']).read_text())
    truth = ref.FowBoard()
    for frame in replay['frames'][:plan['case']['ply']+1]:
        if frame['move']:
            move = ref.chess.Move.from_uci(frame['move'])
            assert move in ref.fow_moves(truth)
            truth.push(move)
        assert ref.observation(truth, True) == frame['white']
        assert ref.observation(truth, False) == frame['black']
        assert ''.join(truth.piece_at(i).symbol() if truth.piece_at(i) else '-' for i in range(64)) == frame['board']
    moves = [ref.chess.Move.from_uci(a['uci']) for a in pop['moves']]
    assert all(m in ref.fow_moves(truth) for m in moves)
    denom = [0., 0., 0.]
    guard_den = [0., 0.]
    sums = [[0., 0., 0.] for _ in moves]
    guard_sums = [[0., 0.] for _ in moves]
    illegal = [0]*len(moves)
    sampled = [0.]*len(moves)
    sample_weights = {s['index']: s['weight'] for s in pop['samples']}
    assert abs(sum(sample_weights.values())-1) < 1e-12
    for arm in ('base', 'candidate'):
        target = result['arms'][arm]['target']
        assert len(target['samples']) == len(pop['samples'])
        for x, y in zip(pop['samples'], target['samples']):
            assert x['index'] == y['belief_index'] and x['weight'] == y['weight']
            assert pop['worlds'][x['index']]['board'] == y['hypothesis_board']
        assert {a['uci'] for a in pop['moves'] if a[arm+'_kept']} == {a['uci'] for a in target['actions']}
    placement, rule_state, weights = [], [], []
    signatures = Counter()
    for i, world in enumerate(pop['worlds']):
        assert world['index'] == i and world['side'] == pop['us']
        lw = struct.unpack('f', struct.pack('f', world['logw']))[0]
        w = [math.exp(lw/pop['temperature']), math.exp(lw), 1.]
        weights.append(w)
        for c in range(3): denom[c] += w[c]
        if i % pop['guard_stride'] == 0:
            for c in range(2): guard_den[c] += w[c]
        board = ref.FowBoard(fen(world['board']))
        board.turn = world['side'] == 0
        board.castling_rights = int(world['castle'], 16)
        board.ep_square = None if world['ep'] < 0 else world['ep']
        board.halfmove_clock = world['halfmove']
        assert ref.observation(board, board.turn) == replay['frames'][plan['case']['ply']][plan['case']['side']]
        legal = set(ref.fow_moves(board))
        lm, fm = 0, 0
        for a, move in enumerate(moves):
            if move not in legal:
                illegal[a] += 1
                continue
            lm |= 1 << a
            mover = board.turn
            board.push(move)
            king = board.king(mover)
            fatal = king is None or bool(board.attackers(not mover, king))
            board.pop()
            if fatal:
                fm |= 1 << a
                for c in range(3): sums[a][c] += w[c]
                if i % pop['guard_stride'] == 0:
                    for c in range(2): guard_sums[a][c] += w[c]
                sampled[a] += sample_weights.get(i, 0)
        assert lm == int(world['legal'], 16) and fm == int(world['fatal'], 16), i
        signatures[fm] += 1
        if world['board'] == replay['frames'][plan['case']['ply']]['board']:
            placement.append(i)
            if (world['side'] == (0 if truth.turn else 1) and int(world['castle'],16) == truth.castling_rights
                and world['ep'] == (truth.ep_square if truth.ep_square is not None else -1)
                and world['halfmove'] == truth.halfmove_clock):
                rule_state.append(i)
    rows = []
    for a, move in enumerate(moves):
        calculated = dict(fitted=sums[a][0]/denom[0], sharpened=sums[a][1]/denom[1], uniform=sums[a][2]/denom[2],
                          guard_fitted=guard_sums[a][0]/guard_den[0], guard_sharpened=guard_sums[a][1]/guard_den[1],
                          sampled=sampled[a], illegal_worlds=illegal[a])
        for key, value in calculated.items():
            assert abs(value-pop['risks'][a][key]) < 1e-10, (move.uci(), key, value, pop['risks'][a][key])
        mover = truth.turn
        truth.push(move)
        king = truth.king(mover)
        true_fatal = king is None or bool(truth.attackers(not mover, king))
        truth.pop()
        rows.append(dict(move=move.uci(), true_fatal=true_fatal, **pop['moves'][a], **calculated))
    def mass(indices):
        return dict(fitted=sum(weights[i][0] for i in indices)/denom[0],
                    sharpened=sum(weights[i][1] for i in indices)/denom[1], uniform=len(indices)/pop['count'])
    report = dict(at=datetime.now(timezone.utc).isoformat(), verified_worlds=pop['count'],
                  verified_move_world_pairs=pop['count']*len(moves), guard_stride=pop['guard_stride'],
                  root_fatal_signatures=len(signatures), true_placement_indices=placement,
                  true_rule_state_indices=rule_state, true_placement_mass=mass(placement), true_rule_state_mass=mass(rule_state),
                  risks=rows, population_sha256=sha(OUT/'case/population.json'), auditor_sha256=sha(Path(__file__)),
                  scope='One reconstructed population. Every world and move checked independently; truth joined after actor exit. '
                        'Rule-state match includes halfmove but not repetition or complete opponent history. '
                        'Fitted means the deployed power-recovered weighting, not a universally exact posterior. '
                        'Not a calibration or playing-strength estimate, nor proof of the live population.')
    with (OUT/'audit.json').open('x') as handle:
        json.dump(report, handle, indent=2)
        handle.write('\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
