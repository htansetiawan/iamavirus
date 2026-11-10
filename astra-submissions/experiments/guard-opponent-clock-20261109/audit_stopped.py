"""Audit all first attempts in the stopped clock-aware comparison."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'astra-submissions/analysis/guard-opponent-clock-20261109'
sys.path.insert(0, str(ROOT.parent/'fow-starter'))
import referee as ref


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = json.loads((OUT/'plan.json').read_text())
    terminal = json.loads((OUT/'completion.json').read_text())
    assert terminal['completed'] == 5 and not terminal['clean'] and not terminal['gate_pass']
    for path, value in plan['dependencies'].items():
        assert sha(path) == value, path
    rows, frames, cells = [], 0, {}
    for job in plan['jobs']:
        directory = OUT/'jobs'/job['id']
        if not (directory/'result.json').exists():
            continue
        result = json.loads((directory/'result.json').read_text())
        assert result['job'] == job
        for name, value in result['files'].items():
            assert sha(directory/name) == value
        game = json.loads((directory/'replay.json').read_text())
        board = ref.FowBoard()
        repetitions = Counter({ref.position_key(board): 1})
        previous = [180, 180]
        for index, frame in enumerate(game['frames']):
            if frame['move']:
                side = 0 if board.turn else 1
                move = ref.chess.Move.from_uci(frame['move'])
                assert move in ref.fow_moves(board)
                board.push(move)
                repetitions[ref.position_key(board)] += 1
                assert frame['clocks'][1-side] == previous[1-side]
                assert 0 <= frame['clocks'][side] <= previous[side]+2
            assert ref.observation(board, True) == frame['white']
            assert ref.observation(board, False) == frame['black']
            assert ''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64)) == frame['board']
            if index < len(game['frames'])-1:
                assert ref.outcome(board, repetitions) is None
            previous = frame['clocks']
            frames += 1
        clean = not result['faults']
        if clean:
            assert ref.outcome(board, repetitions) == (game['result'], game['reason'])
            cells.setdefault((job['pair'], job['side']), {})[job['arm']] = result['score']
        else:
            assert game['reason'] == 'Time forfeit' and game['failedSide'] != job['side']
            assert 'misty-clock: enabled=1 fixed=none budget180=5.000' in game['privateDiagnostics'][game['failedSide']]
        rows.append(dict(id=job['id'], arm=job['arm'], score=result['score'], clean=clean,
                         reason=game['reason'], plies=result['plies'], result_sha256=sha(directory/'result.json')))
    assert len(rows) == 5
    matched = [dict(pair=key[0], side=key[1], **value) for key, value in cells.items() if set(value) == {'base', 'candidate'}]
    result = dict(at=datetime.now(timezone.utc).isoformat(), gate_pass=False, decision='technical_stop_inconclusive',
                  attempted=5, clean_games=sum(r['clean'] for r in rows), technical_games=sum(not r['clean'] for r in rows),
                  own_technical_failures=0, unstarted=len(terminal['unstarted']), referee_frames=frames,
                  matched_clean_cells=matched, matched_control_points=sum(r['base'] for r in matched),
                  matched_candidate_points=sum(r['candidate'] for r in matched), rows=rows,
                  auditor_sha256=sha(Path(__file__)), plan_sha256=sha(OUT/'plan.json'),
                  scope='No promotion or Elo conclusion. Two matched White cells only; no Black games. '
                        'Timeout win stays in original receipt but is excluded from clean matched scores.')
    with (OUT/'audit-stopped.json').open('x') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}), flush=True)


if __name__ == '__main__':
    main()
