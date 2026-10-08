#!/usr/bin/env python3
"""Trace exact recorded queen capturers without supplying truth to the belief.

Runs sequentially, preserves raw traces, and uses only frozen cached replays.
This selected-loss corpus is developmental diagnosis, not calibration or Elo.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def square(s):
    if len(s) != 2 or s[0] not in 'abcdefgh' or s[1] not in '12345678':
        raise ValueError('invalid square')
    return (int(s[1]) - 1) * 8 + ord(s[0]) - ord('a')


def capturer_trajectory(frames, target):
    """Follow one physical piece backward, including castling and promotion.

    The resulting future-informed labels are consumed only by offline scoring.
    Native replay validation checks both colours' observations independently.
    """
    end = target['ply'] + 1
    sq = square(target['capturer_square'])
    enemy = 'pnbrqk' if target['side'] == 0 else 'PNBRQK'
    trajectory = [None] * (end + 1)
    for i in range(end, -1, -1):
        current = frames[i]
        piece = current['board'][sq]
        if piece not in enemy:
            raise ValueError('lost physical capturer identity')
        trajectory[i] = (sq, piece)
        if i == 0:
            break
        previous = frames[i - 1]['board']
        move = current['move']; src, dst = square(move[:2]), square(move[2:4])
        moving = previous[src]
        if moving in enemy:
            if dst == sq:
                sq = src
            elif moving.lower() == 'k' and abs(dst - src) == 2:
                # Standard castling relocates the rook without naming it in UCI.
                rook_to = dst - 1 if dst > src else dst + 1
                if sq == rook_to:
                    if piece.lower() != 'r':
                        raise ValueError('castle displaced a non-rook')
                    sq = src + 3 if dst > src else src - 4
        prior_piece = previous[sq]
        expected = moving if dst == trajectory[i][0] and moving in enemy else piece
        if prior_piece != expected:
            raise ValueError('capturer identity transition disagrees with replay')
    return trajectory


def prepare(target, cache, destination):
    path = cache / target['game'] / 'replay.json'
    if sha(path) != target['replay_sha256']:
        raise ValueError('cached replay changed: ' + target['game'])
    replay = json.loads(path.read_text())
    frames = replay['frames'][:target['ply'] + 3]
    if len(frames) != target['ply'] + 3 or replay['id'] != target['game']:
        raise ValueError('replay identity/length mismatch')
    trajectory = capturer_trajectory(frames, target)
    rows = []
    for i, frame in enumerate(frames):
        if frame['ply'] != i:
            raise ValueError('replay frame index mismatch')
        for field in ['board', 'white', 'black']:
            if len(frame[field]) != 64:
                raise ValueError('invalid replay encoding')
        sq, piece = trajectory[i] if i < len(trajectory) else (-1, '-')
        rows.append(f"{i} {frame['move'] or '-'} {frame['board']} {frame['white']} {frame['black']} {sq} {piece}\n")
    if frames[-2]['move'] != target['actual_move'] or frames[-1]['move'] != target['actual_capture']:
        raise ValueError('recorded target moves changed')
    destination.write_text(''.join(rows))
    return trajectory


def summarize(rows, target):
    if len(rows) != target['ply'] + 1 or [r['ply'] for r in rows] != list(range(len(rows))):
        raise ValueError('incomplete trace')
    final = rows[-1]
    if 'queen' not in final:
        raise ValueError('missing final queen diagnosis')
    seen = [r['ply'] for r in rows if r['tracked_visible']]
    last_seen = max(seen, default=-1)
    collapses = [r['ply'] for r in rows if r['collapsed']]
    to_zero = [r['ply'] for prev, r in zip(rows, rows[1:]) if prev['tracked_held'] > 0 and r['tracked_held'] == 0]
    to_low = [r['ply'] for prev, r in zip(rows, rows[1:])
              if prev['tracked_held']/prev['particles'] >= .05 and r['tracked_held']/r['particles'] < .05]
    last_low = max(to_low, default=None)
    moves = [r['ply'] for prev, r in zip(rows, rows[1:])
             if (prev['tracked_square'], prev['tracked_piece']) != (r['tracked_square'], r['tracked_piece'])]
    return {'final': final, 'collapses': collapses, 'last_seen_ply': last_seen,
            'collapses_after_last_seen': [p for p in collapses if p > last_seen],
            'last_capturer_move_ply': max(moves, default=0),
            'support_to_zero': to_zero, 'support_below_five_percent': to_low,
            'last_low_crossing': None if last_low is None else rows[last_low],
            'total_observe_ms': sum(r['observe_ms'] for r in rows),
            'prefix_capped_updates': sum(r['successor_prefix_capped'] for r in rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', type=Path, required=True)
    parser.add_argument('--targets', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prediction-modes', nargs='+', type=int, choices=[0, 1, 2], default=[0, 1])
    parser.add_argument('--history', type=int, choices=[0, 1, 2], default=0)
    parser.add_argument('--prior', type=int, choices=[0, 1, 2], default=1)
    parser.add_argument('--particles', type=int, default=2048)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    if args.particles < 1 or (args.limit is not None and args.limit < 1):
        parser.error('positive particle count and limit required')
    probe = args.probe.resolve(); out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / 'inputs').mkdir()
    source_bytes = args.targets.read_bytes()
    (out / 'source-targets.jsonl').write_bytes(source_bytes)
    targets = [json.loads(s) for s in source_bytes.decode().splitlines()]
    if len({(t['game'], t['side'], t['ply']) for t in targets}) != len(targets):
        raise ValueError('duplicate target')
    if args.limit:
        targets = targets[:args.limit]
    for target in targets:
        path = out / 'inputs' / (target['game'] + '.txt')
        prepare(target, args.cache, path)
        target['input_path'] = str(path)
        target['input_sha256'] = sha(path)
    state = {'started_at': datetime.now(timezone.utc).isoformat(), 'state': 'running',
             'pid': os.getpid(), 'probe': str(probe), 'probe_sha256': sha(probe),
             'runner_sha256': sha(Path(__file__)), 'targets_sha256': sha(args.targets),
             'seats': len(targets), 'prediction_modes': args.prediction_modes,
             'history': args.history, 'prior': args.prior, 'particles': args.particles,
             'seed': args.seed, 'limit': args.limit, 'completed_runs': 0, 'failed_runs': 0,
             'interpretation': 'Forced-history selected-loss belief diagnosis; not calibration, move selection or strength.'}
    def save():
        tmp = out / 'state.tmp'; tmp.write_text(json.dumps(state, indent=2)+'\n'); tmp.replace(out / 'state.json')
    save()
    for mode in args.prediction_modes:
        for target in targets:
            stem = f"{target['game']}-{target['side']}-p{mode}"
            trace, errors = out / (stem + '.jsonl'), out / (stem + '.stderr')
            command = [str(probe), target['input_path'], str(target['side']), str(args.seed),
                       str(args.particles), str(args.prior), str(args.history), str(mode)]
            env = {k:v for k,v in os.environ.items() if not k.startswith(('ASTRA_', 'FOW_'))}
            started = time.monotonic()
            result = {'target': target, 'prediction': mode, 'trace': str(trace)}
            try:
                with trace.open('w') as stdout, errors.open('w') as stderr:
                    process = subprocess.run(command, stdout=stdout, stderr=stderr, env=env, timeout=180)
                if process.returncode:
                    raise RuntimeError(errors.read_text()[-2000:])
                rows = [json.loads(s) for s in trace.read_text().splitlines()]
                result.update(summarize(rows, target), complete=True)
            except (ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
                result.update(complete=False, error=str(error)); state['failed_runs'] += 1
            result.update(elapsed_seconds=time.monotonic()-started, trace_sha256=sha(trace))
            with (out / 'runs.jsonl').open('a') as journal:
                journal.write(json.dumps(result)+'\n')
            state['completed_runs'] += 1; save()
            if state['completed_runs'] % 20 == 0 or not result['complete']:
                print(json.dumps({k:state[k] for k in ['completed_runs','failed_runs']}),flush=True)
    state['inputs_unchanged'] = sha(probe) == state['probe_sha256'] and sha(args.targets) == state['targets_sha256']
    state['state'] = 'complete' if not state['failed_runs'] and state['inputs_unchanged'] else 'failed'
    state['completed_at'] = datetime.now(timezone.utc).isoformat(); save()
    print(json.dumps(state),flush=True)
    if state['state'] != 'complete':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
