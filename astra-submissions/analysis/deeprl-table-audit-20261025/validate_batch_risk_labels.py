"""Independently validate native PPO candidate labels along real replay prefixes.

Builds a pinned native source snapshot outside Fable's build directory. No model,
training, protocol mutation or deployment is involved. Full replay truth is used
only for this offline simulator/referee conformance check.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def native_snapshot(folder):
    from learning import _native
    folder.mkdir(parents=True, exist_ok=True)
    files = _native.SOURCES + _native.HEADERS
    hashes = {name: sha(ROOT / name) for name in files}
    marker = folder / 'sources.json'
    if marker.exists():
        if json.loads(marker.read_text()) != hashes:
            raise RuntimeError('Native sources changed; use a fresh build directory')
    else:
        for name in files:
            (folder / name).write_bytes((ROOT / name).read_bytes())
        marker.write_text(json.dumps(hashes, indent=2) + '\n')
    if any(sha(folder / name) != digest or sha(ROOT / name) != digest
           for name, digest in hashes.items()):
        raise RuntimeError('Snapshot differs or sources changed during copy')
    _native.ROOT = folder
    _native.BUILD_DIR = folder / 'build'
    _native.LIBRARY = _native.BUILD_DIR / 'librules.so'
    start = time.monotonic()
    library = _native.ensure_built()
    return {'sources': hashes, 'library_sha256': sha(library),
            'prepare_seconds': time.monotonic() - start,
            'compiler': subprocess.check_output(['g++', '--version'], text=True).splitlines()[0],
            'build_directory': str(folder)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--panel', type=Path, default=ROOT / 'astra-submissions/analysis/hidden-slider-zone-20261025/independent-audit-512/teacher-readiness-panel.json')
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'astra-submissions/build/native-risk-labels-20261025')
    parser.add_argument('--referee-dir', type=Path, default=Path('/home/henrytan/git/fow-starter'))
    parser.add_argument('--wall-cap', type=float, default=180.)
    args = parser.parse_args()
    started = time.monotonic()
    native = native_snapshot(args.build_dir)
    from learning.batch_env import BatchEnv
    from learning.action_codec import decode_action
    sys.path.insert(0, str(args.referee_dir))
    import chess
    from referee import FowBoard, observation, outcome, position_key
    panel = json.loads(args.panel.read_bytes())
    totals = Counter()
    records = []
    failures = []
    query_seconds = 0.
    env = BatchEnv(1, max_plies=10000)
    for case in panel['cases']:
        if time.monotonic() - started >= args.wall_cap:
            failures.append({'error': 'wall cap reached', 'next_game': case['game']})
            break
        replay_path = ROOT / case['replay']
        if sha(replay_path) != case['replay_sha256']:
            raise RuntimeError('Pinned replay changed')
        replay = json.loads(replay_path.read_bytes())
        env.reset(0)
        board = FowBoard()
        repetitions = Counter({position_key(board): 1})
        count = Counter()
        special = Counter()
        target_labels = None
        try:
            for ply, frame in enumerate(replay['frames'][:case['frame'] + 1]):
                if time.monotonic() - started >= args.wall_cap:
                    raise RuntimeError('wall cap reached')
                assert frame['ply'] == ply
                raw_board = ''.join(board.piece_at(sq).symbol() if board.piece_at(sq) else '-' for sq in range(64))
                assert env.board(0) == frame['board'] == raw_board, 'board mismatch'
                assert outcome(board, repetitions) is None and env.status(0) == 0, 'early terminal'
                side = 0 if board.turn == chess.WHITE else 1
                assert env.side_to_move(0) == side, 'side mismatch'
                for color, name in enumerate(('white', 'black')):
                    assert env.view(0, color) == frame[name] == observation(board, color == 0), 'observation mismatch'
                    env.take_events(0, color)  # Drain; no actor/model input is constructed here.
                f, t, promo = env.candidates(0)
                moves = [decode_action((int(a) * 64 + int(b)) * 5 + int(p), side)
                         for a, b, p in zip(f, t, promo)]
                assert len(set(moves)) == len(moves), 'duplicate native candidates'
                true_moves = list(board.generate_pseudo_legal_moves())
                assert set(moves) == {m.uci() for m in true_moves}, 'candidate set mismatch'
                before = time.perf_counter()
                labels = env.danger(0)
                query_seconds += time.perf_counter() - before
                assert len(labels) == len(moves), 'danger/candidate length mismatch'
                labelled = []
                for uci, got in zip(moves, labels):
                    move = board.parse_uci(uci)
                    if board.is_castling(move): special['castling_candidates'] += 1
                    if board.is_en_passant(move): special['en_passant_candidates'] += 1
                    if move.promotion: special['promotion_candidates'] += 1
                    copy = board.copy(stack=False)
                    copy.push(move)
                    king = copy.king(board.turn)
                    fatal = king is None or copy.is_attacked_by(copy.turn, king)
                    assert int(got) == int(fatal), f'danger mismatch: {uci}, native={got}, referee={fatal}'
                    count['candidate_labels'] += 1
                    count['fatal_candidate_labels'] += int(fatal)
                    labelled.append({'move': uci, 'fatal': bool(fatal)})
                # Queries are pure: verify neither truth nor candidate identities changed.
                assert env.board(0) == raw_board
                after = env.candidates(0)
                assert all(np.array_equal(a, b) for a, b in zip((f, t, promo), after))
                count['decisions'] += 1
                count['white_decisions' if side == 0 else 'black_decisions'] += 1
                if ply == case['frame']:
                    target_labels = labelled
                    break
                uci = replay['frames'][ply + 1]['move']
                index = moves.index(uci)
                status = int(env.step_all(np.array([index], dtype=np.int32))[0])
                board.push(board.parse_uci(uci))
                repetitions[position_key(board)] += 1
                expected = outcome(board, repetitions)
                expected_status = 0 if expected is None else {'1-0': 1, '0-1': 2, '1/2-1/2': 3}[expected[0]]
                assert status == expected_status, 'termination mismatch'
            records.append({'game': case['game'], 'frame': case['frame'], 'slice': case['slice'],
                            'replay_sha256': case['replay_sha256'], 'counts': dict(count),
                            'special_candidates': dict(special), 'target_labels': target_labels})
            totals.update(count)
            totals.update(special)
        except (AssertionError, RuntimeError, ValueError) as error:
            failures.append({'game': case['game'], 'frame': ply, 'error': str(error)})
            break
        print(f'validated {len(records)}/{len(panel["cases"])} games, {totals["candidate_labels"]} labels', file=sys.stderr, flush=True)
    report = {'classification': 'native simulator / independent referee conformance; no model training or strength estimate',
              'completed_at': datetime.now(timezone.utc).isoformat(), 'panel_sha256': sha(args.panel),
              'validator_sha256': sha(Path(__file__)), 'referee_sha256': sha(args.referee_dir / 'referee.py'),
              'batch_env_wrapper_sha256': sha(ROOT / 'learning/batch_env.py'),
              'action_codec_sha256': sha(ROOT / 'learning/action_codec.py'), 'native': native,
              'requested_cases': len(panel['cases']), 'completed_cases': len(records),
              'counts': dict(totals), 'failures': failures, 'native_danger_query_seconds': query_seconds,
              'wall_seconds': time.monotonic() - started, 'wall_cap_seconds': args.wall_cap,
              'cases': records,
              'limits': ['Replay-prefix conformance does not prove all legal histories or training convergence.',
                         'Case wall time includes independent Python referee work and is not simulator throughput.',
                         'Terminal-history replay frames beyond the selected decision are not tested.']}
    print(json.dumps(report, indent=2))
    return 1 if failures or len(records) != len(panel['cases']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
