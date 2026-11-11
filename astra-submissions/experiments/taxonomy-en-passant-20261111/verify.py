"""Rules-based tests for the isolated EP reporting correction.

No model or bot is executed. The constructed prefix is a test fixture, not
an arena replay or training example. Root labeler and old outputs stay intact.
"""
from collections import Counter
from datetime import datetime, timezone
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/taxonomy-en-passant-20261111'
sys.path.insert(0, str(ROOT / 'astra-submissions/tools'))
import verify_field_replays as data_review


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic(referee):
    board = referee.FowBoard()
    repetitions = Counter({referee.position_key(board): 1})
    frames = [referee.make_frame(board, [180., 180.], None)]
    for uci in ['a2a3', 'e7e5', 'b2b3', 'e5e4', 'd2d4', 'e4d3', 'c2d3', 'f8a3']:
        assert referee.outcome(board, repetitions) is None
        move = board.parse_uci(uci)
        assert move in referee.fow_moves(board)
        board.push(move)
        repetitions[referee.position_key(board)] += 1
        frames.append(referee.make_frame(board, [180., 180.], uci))
    assert referee.outcome(board, repetitions) is None
    return dict(id='epblack0', white='Synthetic White', black='Synthetic Black',
                result='*', reason='', rulesVersion='fow-v1', frames=frames,
                fixture_only=True)


def oracle(replay, referee):
    board, result = referee.FowBoard(), []
    for frame in replay['frames'][1:]:
        move = board.parse_uci(frame['move'])
        assert move in referee.fow_moves(board)
        ep = board.is_en_passant(move)
        capture = board.is_capture(move)
        captured_square = move.to_square + (-8 if board.turn else 8) if ep else move.to_square if capture else None
        result.append(dict(capture=capture, ep=ep, captured_square=captured_square, source=move.from_square,
                           side=0 if board.turn else 1))
        board.push(move)
        actual = ''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64))
        assert actual == frame['board']
    return result


def main():
    origin = read(HERE / 'origin.json')
    root_source = ROOT / origin['source']
    assert sha(root_source) == sha(HERE / 'baseline.py') == origin['sha256']
    before_root = sha(root_source)
    base = load('taxonomy_ep_baseline', HERE / 'baseline.py')
    fixed = load('taxonomy_ep_fixed', HERE / 'move_taxonomy.py')
    ingest, referee = data_review.load_rules()
    fixtures = []
    for path in sorted((ROOT / 'data/astra-spool/compact-mass-playing-20261111/jobs').glob('*/replay.json')):
        receipt = read(path.parent / 'result.json')
        assert sha(path) == receipt['replay_sha256']
        fixtures.append((str(path), read(path), sha(path)))
    known = read(ROOT / 'astra-submissions/analysis/v38-mist-positive-20261111/result.json')
    for record in known['records']:
        path = ROOT / 'data/astra-spool/v38-mist-wins-20261111' / (record['id'] + '.json')
        assert sha(path) == record['replay_sha256']
        fixtures.append((str(path), read(path), sha(path)))
    assert len(fixtures) == 11
    prefix = synthetic(referee)
    states, errors = ingest.validate_replay(prefix)
    assert not errors and len(states) == 9
    fixtures.append(('constructed rules-valid Black EP capture chain', prefix, None))
    capture_tags = {'capture', 'quiet', 'capture_unseen', 'victim_walked_in', 'long_strike', 'fog_route', 'forcing_chain'}
    checked_moves = checked_frames = untouched_games = 0
    differences, ep_cases, provenance = [], [], []
    for path, replay, digest in fixtures:
        old, new = base.label_game(replay), fixed.label_game(replay)
        assert new.pop('taxonomy_version') == 'astra-ep-v1'
        truth = oracle(replay, referee)
        assert len(old['moves']) == len(new['moves']) == len(truth)
        if not any(r['ep'] for r in truth):
            assert old == new, replay['id']
            untouched_games += 1
        for i, (a, b, state) in enumerate(zip(old['moves'], new['moves'], truth, strict=True)):
            checked_moves += 1
            assert all(a[k] == b[k] for k in ['ply', 'side', 'move', 'piece'])
            tags, prior = set(b['tags']), set(a['tags'])
            assert ('capture' in tags) == state['capture']
            assert ('quiet' in tags) == (not state['capture'])
            if state['capture']:
                opponent_view = replay['frames'][i]['black' if state['side'] == 0 else 'white']
                assert ('capture_unseen' in tags) == (opponent_view[state['source']] == '?')
                previous_to = None
                if i > 0:
                    previous = replay['frames'][i]['move']
                    previous_to = ord(previous[2]) - 97 + 8 * (int(previous[3]) - 1)
                assert ('victim_walked_in' in tags) == (previous_to == state['captured_square'])
            chain = i + 2 < len(truth) and all(row['capture'] for row in truth[i:i+3])
            assert ('forcing_chain' in tags) == chain
            assert tags - capture_tags == prior - capture_tags
            if tags != prior:
                permitted = capture_tags if state['ep'] else {'forcing_chain'}
                assert tags.symmetric_difference(prior) <= permitted
                if not state['ep']:
                    assert any(r['ep'] for r in truth[i:i+3])
                differences.append(dict(game=replay['id'], ply=b['ply'], move=b['move'], before=a['tags'], after=b['tags']))
            if state['ep']:
                ep_cases.append(dict(game=replay['id'], ply=b['ply'], move=b['move'], side=b['side'], tags=b['tags']))
        for side in ['white', 'black']:
            expected = Counter(t for row in new['moves'] if row['side'] == (0 if side == 'white' else 1) for t in row['tags'])
            for tag in set(expected) | set(base.KEYS) | {'quiet', 'king_capture'}:
                assert new['counts'][side].get(tag, 0) == expected[tag]
        checked_frames += len(replay['frames'])
        provenance.append(dict(source=path, sha256=digest, frames=len(replay['frames']), synthetic=replay.get('fixture_only', False)))
    assert {r['side'] for r in ep_cases} == {0, 1}
    black = next(r for r in ep_cases if r['side'] == 1)
    assert {'capture', 'victim_walked_in', 'forcing_chain'} <= set(black['tags'])
    assert sha(root_source) == before_root
    patch = ''.join(difflib.unified_diff((HERE / 'baseline.py').read_text().splitlines(True),
                                        (HERE / 'move_taxonomy.py').read_text().splitlines(True),
                                        fromfile='a/learning/move_taxonomy.py', tofile='b/learning/move_taxonomy.py'))
    with (HERE / 'reporting-fix.patch').open('x') as stream:
        stream.write(patch)
    OUT.mkdir(exist_ok=False)
    report = dict(at=datetime.now(timezone.utc).isoformat(), checked_moves=checked_moves, checked_frames=checked_frames,
                  real_games=11, synthetic_prefixes=1, synthetic_cpp_frames=9, untouched_no_ep_games=untouched_games,
                  ep_cases=ep_cases, differences=differences, fixtures=provenance,
                  source_sha256={str(p): sha(p) for p in [Path(__file__), HERE / 'baseline.py', HERE / 'move_taxonomy.py', HERE / 'origin.json', HERE / 'reporting-fix.patch']},
                  shared_root_source_unchanged=True,
                  scope='Isolated report-label correctness change; course capture oracle on all fixture moves and separate C++ validation of constructed prefix. No model, game, fit, deployment or strength estimate. Prior taxonomy limitations remain.')
    with (OUT / 'result.json').open('x') as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: report[k] for k in ['checked_moves', 'checked_frames', 'real_games', 'synthetic_cpp_frames', 'untouched_no_ep_games', 'ep_cases', 'differences']}, indent=2))


if __name__ == '__main__':
    main()
