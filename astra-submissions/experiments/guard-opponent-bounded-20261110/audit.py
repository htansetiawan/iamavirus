"""Audit first attempts independently; incomplete checkpoints never pass a gate."""
from collections import Counter
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'astra-submissions/analysis/guard-opponent-bounded-20261110'
sys.path.insert(0, str(ROOT.parent/'fow-starter'))
import referee as ref


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(partial=False):
    plan = json.loads((OUT/'plan.json').read_text())
    for path, digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    expected = {j['id'] for j in plan['jobs']}
    assert len(expected) == 32
    assert len({(j['pair'], j['side'], j['arm']) for j in plan['jobs']}) == 32
    assert {j['arm'] for j in plan['jobs']} == {'base', 'candidate'}
    for pair in range(8):
        block = [j for j in plan['jobs'] if j['pair'] == pair]
        assert {(j['side'], j['arm']) for j in block} == {
            (side, arm) for side in ('white', 'black') for arm in ('base', 'candidate')}
        assert {j['engine_seed'] for j in block} == {2802000+2*pair}
        assert {j['opponent_seed'] for j in block} == {2802001+2*pair}
    actual = {p.parent.name for p in OUT.glob('jobs/*/result.json')}
    assert actual <= expected
    rows, cells, frames, known_own_faults, unknown_faults = [], {}, 0, 0, 0
    for job in plan['jobs']:
        folder = OUT/'jobs'/job['id']
        if not (folder/'result.json').exists():
            continue
        result = json.loads((folder/'result.json').read_text())
        assert result['job'] == job
        for name, value in result['files'].items():
            assert sha(folder/name) == value, (job['id'], name)
        clean = not result['faults']
        game = json.loads((folder/'replay.json').read_text()) if (folder/'replay.json').exists() else None
        if game is not None:
            board = ref.FowBoard()
            repetitions = Counter({ref.position_key(board): 1})
            previous = [180, 180]
            for index, frame in enumerate(game['frames']):
                assert frame['ply'] == index
                if index == 0:
                    assert frame['move'] is None and frame['clocks'] == previous
                else:
                    mover = 0 if board.turn else 1
                    move = ref.chess.Move.from_uci(frame['move'])
                    assert move in ref.fow_moves(board)
                    board.push(move)
                    repetitions[ref.position_key(board)] += 1
                    assert frame['clocks'][1-mover] == previous[1-mover]
                    assert 0 <= frame['clocks'][mover] <= previous[mover]+2
                assert ref.observation(board, True) == frame['white']
                assert ref.observation(board, False) == frame['black']
                assert ''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64)) == frame['board']
                if index < len(game['frames'])-1:
                    assert ref.outcome(board, repetitions) is None
                previous = frame['clocks']
                frames += 1
            if clean:
                terminal = ref.outcome(board, repetitions)
                if terminal is None and len(game['frames']) == 1001:
                    terminal = ('1/2-1/2', 'Move limit reached')
                assert terminal == (game['result'], game['reason'])
                assert result['validated_frames'] == len(game['frames'])
                assert result['replay_sha256'] == sha(folder/'replay.json')
                assert not game.get('failedSide') and not game['warnings']
                assert result['result'] == game['result'] and result['reason'] == game['reason']
                score = {'1-0': 1.0, '0-1': 0.0, '1/2-1/2': .5}[game['result']]
                if job['side'] == 'black':
                    score = 1-score
                assert score == result['score']
                controls = game['localTurnControl']['controls']
                assert len(controls) == 2
                for control in controls:
                    events = control['events']
                    assert events and events[0]['op'] == 'freeze'
                    assert all(e['op'] in ('freeze', 'resume') for e in events)
                    assert all(e['op'] != events[i-1]['op'] for i, e in enumerate(events) if i)
                pid = controls[1 if job['side'] == 'white' else 0]['pid']
                path = OUT/'telemetry'/f'misty-{pid}.jsonl'
                events = [json.loads(line) for line in path.read_text().splitlines()]
                assert events and max(e['p_post'] for e in events) <= 200000
                assert sha(path) == result['telemetry']['sha256']
                cells.setdefault((job['pair'], job['side']), {})[job['arm']] = score
            elif game.get('failedSide') == job['side']:
                known_own_faults += 1
            elif not game.get('failedSide'):
                unknown_faults += 1
        else:
            assert not clean
            unknown_faults += 1
        rows.append(dict(id=job['id'], pair=job['pair'], side=job['side'], arm=job['arm'],
                         clean=clean, score=result.get('score'), faults=result['faults'],
                         result_sha256=sha(folder/'result.json')))
    stats = {}
    for arm in ('base', 'candidate'):
        scores = [r['score'] for r in rows if r['arm'] == arm and r['score'] is not None]
        stats[arm] = dict(games=len(scores), wins=scores.count(1), draws=scores.count(.5),
                          losses=scores.count(0), points=sum(scores))
    matched = [dict(pair=key[0], side=key[1], **value) for key, value in cells.items()
               if set(value) == {'base', 'candidate'}]
    g = plan['gate']
    clean = all(r['clean'] for r in rows)
    passed = (len(rows) == 32 and clean and stats['candidate']['points'] >= g['candidate_min_points']
              and stats['candidate']['points']-stats['base']['points'] >= g['candidate_min_advantage_points'])
    if not partial:
        completion = json.loads((OUT/'completion.json').read_text())
        assert completion['completed'] == len(rows) and completion['clean'] == clean
        assert completion['stats'] == stats and completion['gate_pass'] == passed
    return dict(at=datetime.now(timezone.utc).isoformat(), final=not partial, completed=len(rows),
                clean_games=sum(r['clean'] for r in rows), technical_games=sum(not r['clean'] for r in rows),
                known_own_faults=known_own_faults, unknown_faults=unknown_faults,
                stats=stats, gate_pass=passed if not partial else False, referee_frames=frames,
                clean_matched_cells=matched, rows=rows,
                matched_control_points=sum(c['base'] for c in matched),
                matched_candidate_points=sum(c['candidate'] for c in matched),
                plan_sha256=sha(OUT/'plan.json'), auditor_sha256=sha(Path(__file__)),
                referee_sha256=sha(ref.__file__),
                scope='First-attempt bounded local proxy comparison. Incomplete checkpoints never pass. '
                      'Technical attempts retained, clean matched points reported separately. '
                      'A final gate pass earns review, not an Elo claim or automatic promotion.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--partial', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit(args.partial)
    target = args.output or OUT/'audit.json'
    with target.open('x') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}), flush=True)
