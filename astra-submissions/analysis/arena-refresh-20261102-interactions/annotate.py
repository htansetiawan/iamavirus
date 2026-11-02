"""Annotate this immutable refresh only after experiment 228 freezes selection."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT))
from learning import ingest, move_taxonomy as mt


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    os.sched_setaffinity(0, {2, 3})
    experiment = OUT.parent / 'interaction-prior-20261102'
    lock = json.loads((experiment / 'selection-lock.json').read_text())
    assert lock['sha256'] == sha(experiment / 'selection.json')
    assert json.loads((experiment / 'execution.json').read_text())['status'] == 'complete'
    manifest = json.loads((OUT / 'manifest.json').read_text())
    assert len(manifest['sha256']) == manifest['new_replays']
    panels = defaultdict(Counter)
    total_moves = total_frames = queen_captures = en_passant = 0
    with (OUT / 'taxonomy.jsonl.gz').open('xb') as stream:
        with gzip.GzipFile(filename='', fileobj=stream, mode='wb', mtime=0) as gz:
            for gid, digest in sorted(manifest['sha256'].items()):
                path = ROOT / 'data/raw/games' / gid / 'replay.json'
                assert sha(path) == digest
                replay = json.loads(path.read_text())
                states, errors = ingest.validate_replay(replay)
                assert not errors, (gid, errors)
                labelled = mt.label_game(replay)
                assert len(labelled['moves']) == len(states) - 1
                supplemental = []
                for k, frame in enumerate(replay['frames'][1:], 1):
                    move = frame['move']
                    square = lambda s: ord(s[0]) - 97 + 8 * (int(s[1]) - 1)
                    src, dst = square(move[:2]), square(move[2:4])
                    before = replay['frames'][k - 1]
                    actor = (k - 1) % 2
                    victim_side = ('black', 'white')[actor]
                    # An EP supplement preserves, rather than silently rewrites,
                    # the legacy taxonomy's destination-occupied capture label.
                    ep = (before['board'][src].lower() == 'p'
                          and src % 8 != dst % 8 and before['board'][dst] == '-')
                    if ep:
                        en_passant += 1
                        supplemental.append({'ply': k, 'en_passant_capture': True,
                            'capturer_hidden_before_capture': before[victim_side][src] == '?'})
                    if before['board'][dst].lower() == 'q':
                        queen_captures += 1
                        # Before the victim's immediately preceding move, not
                        # just the frame immediately before the capture.
                        choice = replay['frames'][k - 2] if k >= 2 else None
                        supplemental.append({'ply': k, 'queen_capture': True,
                            'capturer_square_hidden_at_victim_decision':
                                choice[victim_side][src] == '?' if choice else None,
                            'capturer_hidden_before_capture': before[victim_side][src] == '?',
                            'scope': 'Visibility labels; no net-loss or bad-move claim.'})
                for side in ('white', 'black'):
                    opposite = 'black' if side == 'white' else 'white'
                    key = (replay[side], replay.get(side + 'Version'), side,
                           replay[opposite], replay.get(opposite + 'Version'))
                    panels[key].update(labelled['counts'][side])
                    panels[key]['games'] += 1
                record = dict(game=gid, replay_sha256=digest,
                    created_at=replay['createdAt'], white=replay['white'], black=replay['black'],
                    white_version=replay.get('whiteVersion'), black_version=replay.get('blackVersion'),
                    result=replay['result'], counts=labelled['counts'], moves=labelled['moves'],
                    supplements=supplemental)
                gz.write((json.dumps(record, sort_keys=True) + '\n').encode())
                total_moves += len(labelled['moves'])
                total_frames += len(states)
    rates = []
    for key, counts in sorted(panels.items(), key=lambda kv: str(kv[0])):
        team, version, colour, opponent, opponent_version = key
        rates.append(dict(team=team, version=version, colour=colour, opponent=opponent,
            opponent_version=opponent_version, games=counts['games'], moves=counts['moves'],
            counts={tag: counts[tag] for tag in mt.KEYS},
            per_100={tag: 100 * counts[tag] / max(1, counts['moves']) for tag in mt.KEYS}))
    result = dict(at=datetime.now(timezone.utc).isoformat(), games=manifest['new_replays'],
        moves=total_moves, independently_validated_frames=total_frames,
        queen_capture_supplements=queen_captures, en_passant_supplements=en_passant,
        selection_lock_sha256=sha(experiment / 'selection-lock.json'),
        taxonomy_sha256=sha(OUT / 'taxonomy.jsonl.gz'), manifest_sha256=sha(OUT / 'manifest.json'),
        sources={str(p.relative_to(ROOT)): sha(p) for p in
                 [Path(__file__), ROOT / 'learning/move_taxonomy.py', ROOT / 'learning/ingest.py']},
        panels=rates, scope='Post-selection offline curation. All new games retained, including controls. '
            'No training input, model change, guard threshold, causal effect or strength estimate.')
    with (OUT / 'taxonomy-summary.json').open('x') as f:
        json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'panels'}, indent=2))


if __name__ == '__main__':
    main()
