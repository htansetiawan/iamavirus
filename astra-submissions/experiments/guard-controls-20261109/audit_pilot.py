"""Check frozen full-game receipts with the independent course referee."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import zipfile

from prepare import ROOT, OUT, sha, write
sys.path[:0] = [str(ROOT), '/home/henrytan/git/fow-starter']
import referee as ref

PILOT = OUT/'full-games'


def main():
    plan = json.loads((PILOT/'plan.json').read_text())
    completion = json.loads((PILOT/'completion.json').read_text())
    assert not (PILOT/'failure.json').exists()
    for path, digest in plan['dependencies'].items():
        assert sha(Path(path)) == digest, path
    assert sha(Path(plan['parent'])) == plan['parent_sha256']
    assert sha(Path(plan['candidate'])) == plan['candidate_sha256']
    with zipfile.ZipFile(plan['parent']) as a, zipfile.ZipFile(plan['candidate']) as b:
        left = {n: a.read(n) for n in a.namelist() if not n.endswith('/')}
        right = {n: b.read(n) for n in b.namelist() if not n.endswith('/')}
    changed = {n for n in left if left[n] != right[n]}
    assert changed == {'src/main.c', 'run.sh'}
    assert set(right)-set(left) == {'src/guard_envelope.h', 'ASTRA-GUARD-EXPERIMENT.md'}
    assert right['run.sh'].count(b'export ASTRA_GUARD_EITHER=1\n') == 1
    counts, frames, rows = Counter(), 0, []
    pairs = {i: [] for i in range(8)}
    expected_ids = {j['id'] for j in plan['jobs']}
    actual_ids = {p.parent.name for p in (PILOT/'jobs').glob('*/result.json')}
    assert actual_ids <= expected_ids
    for job in plan['jobs']:
        folder = PILOT/'jobs'/job['id']
        if not (folder/'result.json').exists():
            continue
        result = json.loads((folder/'result.json').read_text())
        assert result['job'] == job
        for name, digest in result['files'].items():
            assert sha(folder/name) == digest, (job['id'], name)
        replay = json.loads((folder/'replay.json').read_text())
        board = ref.FowBoard()
        repetitions = Counter({ref.position_key(board): 1})
        prior_clocks = [180, 180]
        for index, frame in enumerate(replay['frames']):
            if frame['move']:
                move = ref.chess.Move.from_uci(frame['move'])
                assert move in ref.fow_moves(board)
                mover = 0 if board.turn else 1
                board.push(move)
                repetitions[ref.position_key(board)] += 1
                assert frame['clocks'][1-mover] == prior_clocks[1-mover]
                assert 0 <= frame['clocks'][mover] <= prior_clocks[mover]+2
            else:
                assert index == 0 and frame['clocks'] == [180, 180]
            text = ''.join(board.piece_at(i).symbol() if board.piece_at(i) else '-' for i in range(64))
            assert text == frame['board']
            assert ref.observation(board, True) == frame['white']
            assert ref.observation(board, False) == frame['black']
            if index < len(replay['frames'])-1:
                assert ref.outcome(board, repetitions) is None
            prior_clocks = frame['clocks']
            frames += 1
        assert result['plies'] + 1 == result['validated_frames'] == len(replay['frames'])
        assert result['result'] == replay['result'] and result['reason'] == replay['reason']
        if result['technical_failure'] is None:
            terminal = ref.outcome(board, repetitions)
            if terminal is None and result['plies'] == 1000:
                terminal = ('1/2-1/2', 'Move limit reached')
            assert terminal == (replay['result'], replay['reason'])
        score = {'1-0': 1, '0-1': 0, '1/2-1/2': .5}[replay['result']]
        if job['side'] == 'black':
            score = 1-score
        assert result['score'] == score
        counts[{1: 'wins', .5: 'draws', 0: 'losses'}[score]] += 1
        counts['faults'] += result['technical_failure'] is not None
        counts[job['side']+'_points'] += score
        counts[job['side']+'_games'] += 1
        pairs[job['pair']].append(score)
        rows.append(dict(id=job['id'], score=score, plies=result['plies'],
                         technical_failure=result['technical_failure'], result_sha256=sha(folder/'result.json')))
    points = counts['wins']+.5*counts['draws']
    assert completion['completed'] == len(rows)
    assert completion['points'] == points
    passed = len(rows) == 16 and counts['faults'] == 0 and points >= plan['min_points']
    assert completion['gate_pass'] == passed
    result = dict(at=datetime.now(timezone.utc).isoformat(), gate_pass=passed, completed=len(rows),
                  points=points, counts=dict(counts), referee_frames=frames,
                  pair_points={str(i): sum(v) for i, v in pairs.items()},
                  missing=sorted(expected_ids-actual_ids), rows=rows,
                  plan_sha256=sha(PILOT/'plan.json'), auditor_sha256=sha(Path(__file__)),
                  referee_sha256=sha(Path(ref.__file__)),
                  scope='All attempted first games count. Passing earns a further opponent panel; '
                  'small development duel, no Elo claim or release authorization. Process cleanup checked separately.')
    write(PILOT/'audit.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}), flush=True)


if __name__ == '__main__':
    main()
