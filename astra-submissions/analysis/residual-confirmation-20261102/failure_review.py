"""Post-result replay audit, with no fitting or changed acceptance rule."""
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
WORK = ROOT / 'astra-submissions/experiments/residual-confirmation-20261102/work'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert json.loads((OUT / 'review.json').read_text())['passed']
    diagnosis = json.loads((OUT / 'cohort-diagnosis.json').read_text())
    games = json.loads((OUT / 'games.json').read_text())
    with np.load(WORK / 'holdout/data.npz') as z:
        data = {k: z[k] for k in z.files}
    with np.load(WORK / 'predictions.npz') as z:
        pred = {k: z[k] for k in z.files}
    with gzip.open(WORK / 'holdout/rows.jsonl.gz', 'rt') as f:
        rows = [json.loads(line) for line in f]
    refpath = ROOT.parent / 'fow-starter/referee.py'
    spec = importlib.util.spec_from_file_location('failure_referee', refpath)
    ref = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ref)
    values = dict(zip('pnbrqk', (1, 3, 3, 5, 9, 0)))

    def material(board, side):
        return sum(values[p.lower()] for p in board if p != '-' and p.isupper() == (side == 0))

    cases, frames = [], 0
    # Fixed post-hoc selection: the five largest game-level increases in NLL.
    for item in diagnosis['individual_games'][:5]:
        gi = next(i for i, g in enumerate(games) if g['row']['id'] == item['game'])
        game = games[gi]
        assert sha(ROOT / game['path']) == game['sha256']
        replay = json.loads((ROOT / game['path']).read_text())
        board = ref.FowBoard()
        history = Counter({ref.position_key(board): 1})
        sample = {rows[i]['ply']: int(i) for i in np.flatnonzero(data['game'] == gi)}
        positions = []
        for ply, frame in enumerate(replay['frames']):
            if ply:
                assert frame['move'] in {m.uci() for m in ref.fow_moves(board)}
                board.push_uci(frame['move'])
                history[ref.position_key(board)] += 1
            actual = ref.make_frame(board, [0, 0])
            assert all(actual[k] == frame[k] for k in ('board', 'white', 'black'))
            frames += 1
            if ply not in sample:
                continue
            i = sample[ply]
            side = 0 if board.turn else 1
            result = replay['result']
            y = .5 if result == '1/2-1/2' else float((result == '1-0') == (side == 0))
            assert y == data['y'][i] == rows[i]['label']
            positions.append(dict(ply=ply, perspective=('white', 'black')[side],
                label=y, calibrated_sf=float(pred['calibrated_sf'][i]),
                flat=float(pred['flat'][i]), remaining_plies=len(replay['frames'])-1-ply,
                own_material=material(frame['board'], side),
                opponent_material=material(frame['board'], 1-side)))
        assert ref.outcome(board, history) == (replay['result'], replay['reason'])
        assert replay['reason'] == 'King capturable'
        final, before = replay['frames'][-1], replay['frames'][-2]
        mover_white = (final['ply'] % 2 == 1)
        key = 'white' if mover_white else 'black'
        king = board.king(mover_white)
        attackers = list(board.attackers(not mover_white, king))
        assert attackers
        square = lambda sq: chr(97 + sq % 8) + str(1 + sq // 8)
        cases.append(dict(**item, replay_sha256=game['sha256'], result=replay['result'],
            reason=replay['reason'], plies=final['ply'], positions=positions,
            final_moves=[f['move'] for f in replay['frames'][-8:]],
            losing_king=square(king), attackers=[dict(square=square(sq), piece=final['board'][sq],
                hidden_before_final_move=before[key][sq] == '?', hidden_after_final_move=final[key][sq] == '?')
                for sq in attackers],
            final_white_material=material(final['board'], 0),
            final_black_material=material(final['board'], 1)))

    # An uncertainty description after the test; never overrides its point-estimate safeguard.
    deltas = np.array([r['logloss_difference'] for r in diagnosis['individual_games']])
    rng = np.random.default_rng(2401104)
    means = np.array([rng.choice(deltas, len(deltas), replace=True).mean() for _ in range(10000)])
    report = dict(at=datetime.now(timezone.utc).isoformat(), post_hoc=True, passed=True,
        verified_games=len(cases), verified_frames=frames, cases=cases,
        newer_game_bootstrap=dict(seed=2401104, replicates=10000, games=len(deltas),
            mean=float(deltas.mean()), interval_95=np.quantile(means, [.025, .975]).tolist()),
        source_sha256=sha(__file__), referee_sha256=sha(refpath),
        scope='Five largest newer-game NLL regressions selected after results. Replay rules/outcomes and perspective labels checked independently. Bootstrap is descriptive; original gate remains failed. No refit, exclusions or candidate substitution.')
    with (OUT / 'failure-review.json').open('x') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    lines = ['# Newer-game failure audit', '',
        'These five cases were selected after results by largest increase in game-average log loss. They cannot be excluded or used to change the frozen gate.', '',
        f'Independent referee: {len(cases)} complete games / {frames} frames; recorded outcomes and selected-position label perspectives agree.', '',
        '| Game | Result | Plies | Increase in log loss | Final losing king | Attacker(s) |',
        '|---|---|---:|---:|---|---|']
    for c in cases:
        attack = ', '.join(f"{a['piece']} {a['square']} (hidden after: {a['hidden_after_final_move']})" for a in c['attackers'])
        lines.append(f"| {c['game']} | {c['result']} | {c['plies']} | {c['logloss_difference']:+.5f} | {c['losing_king']} | {attack} |")
    ci = report['newer_game_bootstrap']['interval_95']
    lines += ['', f'Post-hoc whole-game bootstrap of the newer cohort: mean {deltas.mean():+.5f}, 95% [{ci[0]:+.5f}, {ci[1]:+.5f}], 126 games. The failed point-estimate safeguard remains failed.', '',
        'The largest error, updro1eg, is a real reversal, not a label-sign error. At ply 94 the White-to-move outcome probability rises from 0.984 to 0.997 under the residual; White ultimately loses. Late in the game White loses its remaining rook, and its bare king steps onto a hidden rook line at ply 149. The selected positions are far enough before the terminal event that the final trap alone is not a supervised explanation of their values.', '',
        'Game outcomes depend on both continuation policies and their observation histories. These predictors see a board, current visibility masks, metadata, and the SF parent-child score; they do not see the players’ beliefs or continuation policies. This is a limitation of the target/input pair. The cases motivate investigating continuation-conditioned targets; they do not prove that doing so will improve play. No new fit or policy test follows this audit.']
    (OUT / 'failure-review.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({k: report[k] for k in ('passed', 'verified_games', 'verified_frames', 'newer_game_bootstrap')}))


if __name__ == '__main__':
    main()
