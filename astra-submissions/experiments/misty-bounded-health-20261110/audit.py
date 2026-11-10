"""Independent course-referee audit; a health pass says nothing about strength."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'astra-submissions/analysis/misty-bounded-health-20261110'
sys.path.insert(0, str(ROOT.parent/'fow-starter'))
import referee as ref


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = json.loads((OUT/'plan.json').read_text())
    completion = json.loads((OUT/'completion.json').read_text())
    assert completion['completed'] == 2
    for path, value in plan['dependencies'].items():
        assert sha(path) == value, path
    rows = []
    frame_count = 0
    for job in plan['jobs']:
        folder = OUT/'jobs'/job['id']
        result = json.loads((folder/'result.json').read_text())
        assert result['job'] == job
        for name, value in result['files'].items():
            assert sha(folder/name) == value, (job['id'], name)
        game = json.loads((folder/'replay.json').read_text())
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
            assert all(math.isfinite(t) and t >= 0 for t in frame['clocks'])
            assert ref.observation(board, True) == frame['white']
            assert ref.observation(board, False) == frame['black']
            assert ''.join(board.piece_at(i).symbol() if board.piece_at(i) else '-' for i in range(64)) == frame['board']
            if index < len(game['frames'])-1:
                assert ref.outcome(board, repetitions) is None
            previous = frame['clocks']
            frame_count += 1
        assert result['plies']+1 == len(game['frames'])
        assert result['result'] == game['result'] and result['reason'] == game['reason']
        native = job['side']
        misty = 'black' if native == 'white' else 'white'
        assert 'mist: stockfish ready' in game['privateDiagnostics'][native]
        diag = game['privateDiagnostics'][misty]
        deployment_asserted = ('misty-clock: enabled=1 fixed=none budget180=5.000' in diag
                               and 'misty-cap: states=200000' in diag)
        controls = game['localTurnControl']['controls']
        assert len(controls) == 2
        for control in controls:
            events = control['events']
            assert events and events[0]['op'] == 'freeze'
            assert all(e['op'] in ('freeze', 'resume') for e in events)
            assert all(e['op'] != events[i-1]['op'] for i, e in enumerate(events) if i)
        pid = controls[1 if native == 'white' else 0]['pid']
        path = OUT/f'misty-{pid}.jsonl'
        telemetry = [json.loads(line) for line in path.read_text().splitlines()]
        assert telemetry and sha(path) == result['telemetry']['sha256']
        maximum = max(e['p_post'] for e in telemetry)
        assert maximum == result['telemetry']['max_post_positions']
        cap_ok = maximum <= plan['cap']
        if result['passed']:
            assert not result['faults'] and not game.get('failedSide') and not game['warnings']
            assert deployment_asserted and cap_ok and 'inadmissible engine move' not in diag
            assert ref.outcome(board, repetitions) == (game['result'], game['reason'])
        rows.append(dict(id=job['id'], passed=result['passed'], result=game['result'], reason=game['reason'],
                         frames=len(game['frames']), max_post_population=maximum,
                         capped_updates=sum(bool(e.get('downsampled')) for e in telemetry),
                         max_raw_population=max((e.get('p_raw', 0) or 0 for e in telemetry), default=0),
                         max_update_ms=max((e['wall_ms'] for e in telemetry if e['kind'] != 'pick_move'), default=0),
                         max_search_ms=max((e['wall_ms'] for e in telemetry if e['kind'] == 'pick_move'), default=0),
                         telemetry_sha256=sha(path), result_sha256=sha(folder/'result.json')))
    qualified = all(r['passed'] for r in rows)
    assert qualified == completion['qualified']
    result = dict(at=datetime.now(timezone.utc).isoformat(), qualified=qualified, completed=2,
                  referee_frames=frame_count, rows=rows, plan_sha256=sha(OUT/'plan.json'),
                  auditor_sha256=sha(Path(__file__)), referee_sha256=sha(ref.__file__),
                  scope='Score-independent qualification of this bounded local comparator only. '
                        'No candidate promotion or current arena opponent equivalence. Host cleanup checked separately.')
    with (OUT/'audit.json').open('x') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
