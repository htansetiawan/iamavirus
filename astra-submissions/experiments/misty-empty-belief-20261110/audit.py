"""Verify redaction, dependency hashes and the capped/uncapped component outcomes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'astra-submissions/analysis/misty-empty-belief-20261110'
PANEL = ROOT/'astra-submissions/analysis/guard-opponent-bounded-20261110'
sys.path.insert(0, str(ROOT.parent/'fow-starter'))
import referee as ref


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = json.loads((OUT/'plan.json').read_text())
    done = json.loads((OUT/'completion.json').read_text())
    for path, digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    payload = json.loads((OUT/'redacted-input.json').read_text())
    assert set(payload) == {'side', 'seed', 'observations'}
    assert payload['side'] == 'white' and payload['seed'] == plan['seed'] == 2802007
    game = json.loads((PANEL/'jobs/p3-black-candidate/replay.json').read_text())
    assert len(payload['observations']) == 24
    board = ref.FowBoard()
    for i, item in enumerate(payload['observations']):
        assert set(item) == {'ply', 'view', 'own_move_after'}
        if i:
            move = ref.chess.Move.from_uci(game['frames'][i]['move'])
            assert move in ref.fow_moves(board)
            board.push(move)
        assert item['ply'] == i and item['view'] == ref.observation(board, True)
        own = game['frames'][i+1]['move'] if i % 2 == 0 else None
        assert item['own_move_after'] == own
        if own is not None:
            assert ref.chess.Move.from_uci(own) in ref.fow_moves(board)
    rows = {}
    for cap in plan['cases']:
        folder = OUT/cap
        result = json.loads((folder/'result.json').read_text())
        assert result == next(r for r in done['rows'] if r['cap'] == cap)
        for name, digest in result['files'].items():
            assert sha(folder/name) == digest
        events = [json.loads(line) for line in (folder/'events.jsonl').read_text().splitlines()]
        assert events[0]['kind'] == 'start' and events[0]['seed'] == plan['seed']
        assert events[-1] == result['last_event']
        assert not result['timed_out'] and not result['unverified_cleanup']
        rows[cap] = dict(result_sha256=sha(folder/'result.json'), exit_code=result['exit_code'],
                         seconds=result['seconds'], completed=result['completed'], max_positions=result['max_positions'],
                         peak_rss_kib=result['peak_rss_kib'], last_event=events[-1])
    assert rows['200000']['exit_code'] == 1 and not rows['200000']['completed']
    assert rows['200000']['last_event']['ply'] == 23
    assert 'P became empty after own move d1a4' in rows['200000']['last_event']['error']
    assert rows['none']['exit_code'] == 0 and rows['none']['completed']
    assert rows['none']['last_event']['frames'] == 24 and rows['none']['last_event']['positions'] > 0
    report = dict(at=datetime.now(timezone.utc).isoformat(), redacted_input_verified=True,
                  referee_frames=24, capped_failure_reproduced=True, uncapped_completed=True,
                  rows=rows, plan_sha256=sha(OUT/'plan.json'), auditor_sha256=sha(Path(__file__)),
                  scope='Supports cap-loss explanation for this belief-update component. '
                        'Historical searches skipped; not exact live set/carryover/timing or universal library reliability. '
                        'No candidate scoring, model change or next game batch.')
    with (OUT/'audit.json').open('x') as handle:
        json.dump(report, handle, indent=2)
        handle.write('\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
