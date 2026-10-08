#!/usr/bin/env python3
"""Recover actual next-ply queen capturers for Fable's diagnostic loss seats.

Synthetic terminal/result fields are never copied as outcome targets. These
events were selected because a queen was lost; they are not calibration data.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


def sha(data):
    return hashlib.sha256(data).hexdigest()


def square(name):
    if not re.fullmatch('[a-h][1-8]', name):
        raise ValueError('invalid coordinate')
    return 8 * (int(name[1]) - 1) + ord(name[0]) - ord('a')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.corpus.read_bytes()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    (out / 'source-seats.txt').write_bytes(source)
    records, rejected, seen = [], [], set()
    counts = defaultdict(Counter)
    for line in source.decode().splitlines():
        if not line or line.startswith('#'):
            continue
        fields = line.split(); game = fields[0]
        try:
            game, color, _, _, label, *moves = fields
            if game in seen or not re.fullmatch('[a-z0-9]{8}', game):
                raise ValueError('duplicate or malformed game ID')
            seen.add(game)
            if color not in ('w', 'b') or not moves:
                raise ValueError('invalid side or empty prefix')
            side = 'white' if color == 'w' else 'black'
            ply = len(moves) - 1
            if ply % 2 != int(color == 'b'):
                raise ValueError('prefix does not end on actor move')
            raw = (args.cache / game / 'replay.json').read_bytes()
            replay = json.loads(raw); frames = replay['frames']
            if replay['id'] != game or len(frames) <= ply + 2:
                raise ValueError('missing next-ply replay frame')
            if moves != [f['move'] for f in frames[1:ply + 2]]:
                raise ValueError('synthetic prefix differs from recorded game')
            before, after, captured = frames[ply:ply + 3]
            for index, frame in enumerate((before, after, captured), ply):
                if frame['ply'] != index or len(frame['board']) != 64 or len(frame[side]) != 64:
                    raise ValueError('invalid frame encoding')
            capture = captured['move']
            attacker, target = square(capture[:2]), square(capture[2:4])
            queen = 'Q' if color == 'w' else 'q'
            piece = after['board'][attacker]
            if after['board'][target] != queen or piece not in ('pnbrqk' if color == 'w' else 'PNBRQK'):
                raise ValueError('next recorded move does not capture actor queen')
            expected = capture[4:] or piece
            expected = expected.lower() if color == 'w' else expected.upper()
            if captured['board'][target] != expected or captured['board'][attacker] != '-':
                raise ValueError('capture does not match resulting board')
            version = replay.get(side + 'Version')
            if version is not None and label.split(':')[0] != f'v{version}':
                raise ValueError('corpus version differs from played version')
            record = {'game': game, 'side': int(color == 'b'), 'ply': ply,
                      'actor': replay[side], 'arena_version': version,
                      'actual_move': moves[-1], 'actual_capture': capture,
                      'queen_square': capture[2:4], 'capturer_square': capture[:2],
                      'capturer_piece': piece, 'capturer_visible_before': before[side][attacker] != '?',
                      'capturer_visible_after': after[side][attacker] != '?',
                      'queen_moved': before['board'][square(moves[-1][:2])] == queen,
                      'replay_sha256': sha(raw)}
            records.append(record)
            tally = counts[str(version)]
            tally.update(events=1, unseen_before=int(not record['capturer_visible_before']),
                         newly_visible=int(not record['capturer_visible_before'] and record['capturer_visible_after']),
                         queen_moved=int(record['queen_moved']), early=int(ply < 30))
        except (KeyError, ValueError, OSError, IndexError) as error:
            rejected.append({'game': game, 'error': str(error)})
    targets = out / 'targets.jsonl'
    targets.write_text(''.join(json.dumps(r) + '\n' for r in records))
    report = {'recorded_at': datetime.now(timezone.utc).isoformat(),
              'state': 'complete' if not rejected else 'needs-review',
              'corpus_sha256': sha(source), 'tool_sha256': sha(Path(__file__).read_bytes()),
              'targets': str(targets), 'targets_sha256': sha(targets.read_bytes()),
              'events': len(records), 'rejected': rejected,
              'by_arena_version': {k: dict(v) for k,v in counts.items()},
              'validation': 'Recorded move-prefix, ply/encoding, queen capture, resulting occupancy and played-version consistency; not an independent native referee validation.',
              'use': 'Selected-loss diagnostic only; no synthetic result/reason labels are emitted; not natural-frequency calibration data.'}
    (out / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if rejected:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
