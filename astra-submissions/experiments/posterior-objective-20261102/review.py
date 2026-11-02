"""Verify exported action sets and transitions against the separate C++ rules."""
from datetime import datetime, timezone
import gzip
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import numpy as np
from common import HERE, ROOT, OUT, array, encode, library, position_tuple, sha, StateKey
sys.path.insert(0, str(ROOT))
from learning import rules


def uci(move):
    square = lambda i: 'abcdefgh'[i % 8] + str(i // 8 + 1)
    text = square(move & 63) + square((move >> 6) & 63)
    promo = (move >> 12) & 7
    return text + ('pnbrqk'[promo] if promo != 6 else '')


def main():
    os.sched_setaffinity(0, {2, 3})
    plan = json.loads((OUT / 'plan.json').read_text())
    reference = json.loads((OUT / 'reference-pins.json').read_text())
    for path, digest in {**plan['dependencies'], **reference}.items():
        assert sha(Path(path)) == digest, path
    cases = json.loads((OUT / 'cases.json').read_text())
    by_key = {(r['game'], r['ply']): r for r in cases}
    assert len(by_key) == len(cases)
    lib = library(); key_of = StateKey()
    actions = states = parents = bytes_total = positive_edges = 0
    checked = set(); payloads = []
    for game in plan['games']:
        path = ROOT / 'data/raw/games' / game['game'] / 'replay.json'
        assert sha(path) == game['replay_sha256']
        replay = json.loads(path.read_text())
        feed = json.loads((OUT / 'inputs' / (game['game'] + '.json')).read_text())
        assert feed['us'] == game['us']; lib.pl_start(game['us'])
        for ply, command in enumerate(feed['inputs'], 1):
            expected_view = replay['frames'][ply][('white', 'black')[game['us']]]
            ours = (ply - 1) % 2 == game['us']
            assert command['view'] == expected_view
            assert set(command) == ({'kind', 'move', 'view'} if ours else {'kind', 'view'})
            if ours:
                assert command['kind'] == 'own' and command['move'] == replay['frames'][ply]['move']
                lib.pl_own(encode(command['move']), expected_view.encode())
                continue
            assert command['kind'] == 'opponent'
            row = by_key.get((game['game'], ply))
            if row:
                checked.add((game['game'], ply)); file = Path(row['data_path'])
                assert sha(file) == row['sha256']; payloads.append(file)
                with np.load(file, allow_pickle=False) as packed:
                    data = {k: packed[k] for k in packed.files}
                assert lib.pl_count() == row['parents'] == len(data['parent_weights'])
                assert sum(v.nbytes for v in data.values()) == row['raw_bytes']
                bytes_total += row['raw_bytes']
                for i, (lo, hi) in enumerate(zip(data['offsets'][:-1], data['offsets'][1:])):
                    current = array(lib.pl_position(i), 1)[0]
                    assert current['key'] == data['parent_keys'][i]
                    assert current['base'] == data['parent_weights'][i]
                    board, side, castle, ep = position_tuple(current)
                    position = rules.Board.from_board_string(board, side, castle, ep)
                    position.halfmove_clock = int(current['halfmove'])
                    exported = data['actions'][lo:hi]
                    assert len(exported) == len({int(a['move']) for a in exported})
                    assert set(position.legal_moves()) == {uci(int(a['move'])) for a in exported}
                    parents += 1
                    for action in exported:
                        move = uci(int(action['move'])); next_board = position.copy(); next_board.push(move)
                        compatible = not next_board.mover_lost() and next_board.observation(game['us']) == expected_view
                        assert compatible == bool(action['key']), (game['game'], ply, i, move)
                        if compatible:
                            target = (next_board.board_string(), next_board.side, next_board.castling, next_board.en_passant)
                            assert position_tuple(action) == target
                            assert key_of(*target) == int(action['key'])
                            assert next_board.halfmove_clock == int(action['halfmove'])
                            states += 1
                        actions += 1
                assert np.array_equal(data['positive'], data['actions']['key'] == data['truth_key'])
                positive_edges += int(data['positive'].sum())
            lib.pl_opponent(expected_view.encode())
    lib.pl_free(); assert checked == set(by_key)
    for path, digest in reference.items():
        assert sha(Path(path)) == digest, path
    # The actual archive is small enough to retain for review. Original arrays
    # remain ignored; this deterministic compressed snapshot pins every case.
    archive = OUT / 'feasibility-data.tar.gz'
    with archive.open('xb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode='w|') as tar:
                for file in sorted(payloads):
                    data = file.read_bytes(); item = tarfile.TarInfo(file.name)
                    item.size = len(data); item.mode = 0o644; item.mtime = 0
                    tar.addfile(item, io.BytesIO(data))
    with tarfile.open(archive, 'r:gz') as tar:
        for item in tar:
            import hashlib
            content = tar.extractfile(item).read()
            assert hashlib.sha256(content).hexdigest() == sha(HERE / 'build/data' / item.name)
    result = dict(at=datetime.now(timezone.utc).isoformat(), cases=len(cases), parents=parents,
        independent_legal_actions=actions, independent_consistent_successors=states,
        natural_positive_edges=positive_edges, uncompressed_bytes=bytes_total,
        permitted_input_fields_verified=True, all_source_and_data_hashes_verified=True,
        archive_bytes=archive.stat().st_size, archive_sha256=sha(archive),
        sources={str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), ROOT / 'learning/rules.py']},
        scope='Transition and artifact correctness only. No fitting, policy comparison or strength estimate.')
    with (OUT / 'independent-review.json').open('x') as f:
        json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
