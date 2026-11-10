"""Independent rules and chance-mass audit; replay truth is never actor input."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'astra-submissions/analysis/root-strata-20261110'
PRIOR = ROOT/'astra-submissions/analysis/root-population-20261110'
sys.path[:0] = [str(ROOT), str(ROOT.parent/'fow-starter')]
import referee as ref
from learning.move_taxonomy import fen


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = json.loads((OUT/'plan.json').read_text())
    done = json.loads((OUT/'completion.json').read_text())
    assert done['error'] is None and done['completed'] == len(plan['seeds']) == 4
    for path, digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    pop = json.loads((PRIOR/'case/population.json').read_text())
    assert sha(PRIOR/'case/population.json') == plan['source_census_sha256']
    moves = [ref.chess.Move.from_uci(a['uci']) for a in pop['moves']]
    loss, win, signatures, weights = [], [], [], []
    for world in pop['worlds']:
        b = ref.FowBoard(fen(world['board']))
        b.turn = world['side'] == 0; b.castling_rights = int(world['castle'], 16)
        b.ep_square = None if world['ep'] < 0 else world['ep']; b.halfmove_clock = world['halfmove']
        assert set(ref.fow_moves(b)) == set(moves)
        assert not (b.queens & b.occupied_co[b.turn])
        ls, ws = [], []
        for m in moves:
            mover = b.turn
            b.push(m)
            captured = b.king(not mover) is None
            king = b.king(mover)
            fatal = not captured and (king is None or bool(b.attackers(not mover, king)))
            b.pop(); ls.append(int(fatal)); ws.append(int(captured))
        loss.append(ls); win.append(ws); signatures.append((tuple(ls), tuple(ws)))
        weights.append(math.exp(struct.unpack('f', struct.pack('f', world['logw']))[0]))
    total = math.fsum(weights)
    exact_loss = [math.fsum(w*ls[a] for w, ls in zip(weights, loss))/total for a in range(len(moves))]
    exact_win = [math.fsum(w*ws[a] for w, ws in zip(weights, win))/total for a in range(len(moves))]
    lower = [p-2*r-(1-r-p) for r, p in zip(exact_loss, exact_win)]
    upper = [p-2*r+(1-r-p) for r, p in zip(exact_loss, exact_win)]
    bounded = {m.uci() for m, hi in zip(moves, upper) if hi < max(lower)-1e-12}
    old = {m['uci'] for m in pop['moves'] if not m['base_kept']}
    matrix = []
    for record in done['rows']:
        seed = record['seed']; folder = OUT/f'seed-{seed}'
        assert not record['timed_out'] and not record['live_members'] and record['exit_code'] == 0
        assert json.loads((folder/'result.json').read_text()) == record
        for name, digest in record['files'].items():
            assert sha(folder/name) == digest, name
        row = json.loads((folder/'stdout.json').read_text())
        assert row['seed'] == seed and row['eligible'] and row['belief_unchanged']
        assert set(row['old_avoid']) == old and set(row['bounded_avoid']) == bounded
        assert row['groups'] == len(set(signatures)) == 6
        for a, values in enumerate(row['actions']):
            assert abs(values['loss']-exact_loss[a]) < 1e-11
            assert abs(values['win']-exact_win[a]) < 1e-11
        targets = [json.loads(line) for line in (folder/'targets.jsonl').read_text().splitlines()]
        assert len(targets) == len(row['searches']) == 4
        sample_sets = {}
        for result, target in zip(row['searches'], targets):
            arm = result['arm']; stratified = arm.startswith('stratified')
            expected_sample = row['stratified_samples' if stratified else 'ordinary_samples']
            expected_mask = bounded if arm.endswith('bounded') else old
            assert set(target['avoid_moves']) == expected_mask
            assert {a['uci'] for a in target['actions']} == {m.uci() for m in moves}-expected_mask
            samples = target['samples']
            assert len(samples) == len(expected_sample)
            for s, expected in zip(samples, expected_sample):
                assert s['belief_index'] == expected['index'] and abs(s['weight']-expected['weight']) < 1e-13
                assert s['hypothesis_board'] == pop['worlds'][s['belief_index']]['board']
            assert abs(math.fsum(s['weight'] for s in samples)-1) < 1e-12
            sample_sets[arm] = samples
            sampled_loss = [math.fsum(s['weight']*loss[s['belief_index']][a] for s in samples) for a in range(len(moves))]
            sampled_win = [math.fsum(s['weight']*win[s['belief_index']][a] for s in samples) for a in range(len(moves))]
            error = max(abs(a-b) for a, b in zip(sampled_loss, exact_loss))
            if stratified:
                assert error < 1e-12 and max(abs(a-b) for a, b in zip(sampled_win, exact_win)) < 1e-12
            assert target['own_reach_consistent'] and abs(target['cf_mass']-1) < 1e-12
            assert abs(math.fsum(a['probability'] for a in target['actions'])-1) < 1e-12
            assert abs(math.fsum(a['q']*a['probability'] for a in target['actions'])-target['root_value']) < 1e-10
            assert result['move'] == target['solver_move'] == max(target['actions'], key=lambda a: a['probability'])['uci']
            assert abs(result['value']-target['root_value']) < 1e-10
            matrix.append(dict(seed=seed, **result, max_tactical_probability_error=error,
                               actions=[dict(uci=a['uci'], probability=a['probability'], q=a['q']) for a in target['actions']]))
        assert sample_sets['ordinary-old'] == sample_sets['ordinary-bounded']
        assert sample_sets['stratified-old'] == sample_sets['stratified-bounded']
    # Retrospective truth labels join after all native processes have exited.
    prior_audit = json.loads((PRIOR/'audit.json').read_text())
    truth = {r['move']: r['true_fatal'] for r in prior_audit['risks']}
    for r in matrix:
        r['recorded_truth_fatal'] = truth[r['move']]
    report = dict(at=datetime.now(timezone.utc).isoformat(), passed=True, seeds=plan['seeds'],
                  worlds=len(weights), verified_move_world_pairs=len(weights)*len(moves),
                  risk_signatures=len(set(signatures)), matrix=matrix, plan_sha256=sha(OUT/'plan.json'),
                  auditor_sha256=sha(Path(__file__)), scope=plan['scope'])
    with (OUT/'audit.json').open('x') as handle:
        json.dump(report, handle, indent=2); handle.write('\n')
    print(json.dumps(dict(passed=True, decisions=len(matrix), changes=sum(r['move'] != 'g7g8' for r in matrix))), flush=True)


if __name__ == '__main__':
    main()
