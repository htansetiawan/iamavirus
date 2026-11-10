"""Locate the earlier decision and audit responses to the recorded hidden capture."""
from collections import Counter
import argparse
import json

from measure import OUT, STORE, VALIDATOR, _native, digest, material, ref, write
from learning import rules
from learning.api_client import ApiClient, atomic_write


def retain_sources(expected):
    """Materialize the exact responses referenced by the original result."""
    existing = {}
    for path in STORE.parent.rglob('replay.json'):
        if path.parent.name in expected:
            existing.setdefault(path.parent.name, []).append(path)
    client = ApiClient(min_interval=1.5, timeout=20)
    reused = 0
    for game, checksum in expected.items():
        target = STORE/'source/games'/game/'replay.json'
        if target.exists():
            assert digest(target) == checksum
            continue
        cached = next((p for p in existing.get(game, []) if digest(p) == checksum), None)
        if cached is not None:
            data = cached.read_bytes()
            reused += 1
        else:
            data, receipt = client.get_bytes(f'/api/games/{game}')
            assert receipt.sha256 == checksum, game
        assert atomic_write(target, data) == checksum
    write(OUT/'source-retention.json', dict(games=len(expected), cached_reused=reused,
        new_requests=client.requests_made, original_response_hashes_verified=True))


def threatens_material(board, action, ours):
    if action not in board.legal_moves():
        return False
    target = rules.square_index(action[2:4])
    source = rules.square_index(action[:2])
    victim = board.piece_at(target)
    ep = board.piece_at(source)%6 == 0 and target == board.en_passant and source%8 != target%8
    if victim < 0 and not ep:
        return False
    child = board.copy()
    child.push(action)
    return not child.mover_lost() and material(child.board_string(), ours) <= -3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--retain-sources', action='store_true')
    args = parser.parse_args()
    _native.ensure_built = lambda verbose=True: VALIDATOR
    original = json.loads((OUT/'result.json').read_text())
    if args.retain_sources:
        retain_sources(original['source_replay_sha256'])
    rows = json.loads((STORE/'matchup-rows.json').read_text())
    selected = []
    for row in rows:
        onset = row['onset']
        if row['score'] != 0 or not onset or not (onset['mover']=='duck' and onset['capture']
                                                and onset['hidden_before_previous_own_move']):
            continue
        game = row['game']
        path = STORE/'source/games'/game/'replay.json'
        assert digest(path) == original['source_replay_sha256'][game]
        frames = json.loads(path.read_text())['frames']
        ply = onset['ply']
        prior = ply-2
        action = frames[ply]['move']
        played = frames[ply-1]['move']
        assert prior >= 0
        ours = row['side']
        board = rules.Board()
        for frame in frames[1:prior+1]:
            board.push(frame['move'])
        assert board.board_string() == frames[prior]['board']
        assert board.side == (0 if ours=='white' else 1)
        assert board.observation(board.side) == frames[prior][ours]
        assert frames[prior][ours][rules.square_index(action[:2])]=='?'
        safe = []
        prevent = []
        for move in board.legal_moves():
            child = board.copy()
            child.push(move)
            if child.mover_lost():
                continue
            safe.append(move)
            if not threatens_material(child, action, ours):
                prevent.append(move)
        assert played in safe and played not in prevent
        after = board.copy()
        after.push(played)
        target = rules.square_index(action[2:4])
        if target == after.en_passant and after.piece_at(target) < 0:
            target += -8 if after.side == rules.WHITE else 8
        from_square = rules.square_index(action[:2])
        played_from = rules.square_index(played[:2])
        if rules.square_index(played[2:4]) == target:
            geometry = 'moved_piece_was_captured'
        elif onset['piece'] in 'brq' and (ref.chess.between(from_square,target) >> played_from) & 1:
            geometry = 'vacated_square_on_capture_ray'
        else:
            geometry = 'other_piece_was_captured'
        selected.append(dict(game=game, decision_ply=prior, captured_piece_move=played,
            duck_capture=action, attacking_piece=onset['piece'], geometry=geometry,
            true_board_safe_count=len(safe), prevents_recorded_capture=prevent))
    assert len(selected) == original['metrics']['losses']['hidden_capture_onset']
    write(STORE/'prior-material-options.json', selected)
    result = dict(hidden_capture_cases=len(selected),
        cases_with_specific_capture_prevention=sum(bool(row['prevents_recorded_capture']) for row in selected),
        attacking_pieces=dict(Counter(row['attacking_piece'] for row in selected)),
        geometry=dict(Counter(row['geometry'] for row in selected)),
        own_actions_checked=sum(row['true_board_safe_count'] for row in selected),
        analysis_rows_sha256=digest(STORE/'prior-material-options.json'),
        scope='Counterfactual legal moves use the true board and test the single recorded reply. Other opponent replies and subsequent play are outside this comparison.')
    write(OUT/'earlier-options.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
