"""Describe all audited continuation branches; never select actions or fit a model.

The shared taxonomy is unchanged. Pre-decision queen visibility and en passant
are explicit supplements, and only moves after the intervention enter totals.
This analysis was added while the frozen batch was running, after interim
outcomes had been observed. It is descriptive, not a preregistered strength test.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import chess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT))
from learning import move_taxonomy as mt


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def annotate(game):
    branch = game['continuation']['branch_ply']
    frames = game['frames']
    assert all(f['ply'] == i for i, f in enumerate(frames))
    actor = branch % 2
    first = frames[branch + 1]
    assert first['move']
    labelled = mt.label_game(game)
    events = [m for m in labelled['moves'] if m['ply'] > branch]
    assert len(events) == len(frames) - branch - 1
    counts = {role: Counter() for role in ('actor', 'opponent')}
    supplements = []
    for event in events:
        ply = event['ply']
        mover = (ply - 1) % 2
        assert mover == event['side']
        role = 'actor' if mover == actor else 'opponent'
        counts[role]['moves'] += 1
        counts[role].update(set(event['tags']))
        before = frames[ply - 1]
        src = chess.parse_square(event['move'][:2])
        dst = chess.parse_square(event['move'][2:4])
        victim_view = ('black', 'white')[mover]
        moving = before['board'][src]
        victim = before['board'][dst]
        assert moving != '-'
        if moving.lower() == 'p' and src % 8 != dst % 8 and victim == '-':
            # The audited referee guarantees legality. Preserve the original
            # tag definition instead of silently rewriting EP as a legacy capture.
            supplements.append(dict(ply=ply, role=role, en_passant_capture=True,
                capturer_hidden_before_capture=before[victim_view][src] == '?'))
        if victim.lower() == 'q':
            choice = frames[ply - 2] if ply >= 2 else None
            supplements.append(dict(ply=ply, role=role, queen_capture=True,
                capturer_hidden_before_capture=before[victim_view][src] == '?',
                capturer_square_hidden_at_victim_decision=(
                    choice[victim_view][src] == '?' if choice is not None else None),
                victim_decision_is_continuation=ply - 1 > branch,
                scope='Visibility only; a queen capture need not be a losing exchange.'))
    terminal = []
    if not game['censored'] and game['reason'] == 'King capturable':
        assert game['result'] in ('1-0', '0-1')
        end, previous = frames[-1], frames[-2]
        board = chess.Board(mt.fen(end['board']))
        loser = chess.WHITE if game['result'] == '0-1' else chess.BLACK
        king = board.king(loser)
        assert king is not None
        view = 'white' if loser else 'black'
        for square in board.attackers(not loser, king):
            terminal.append(dict(piece=board.piece_at(square).symbol(),
                square=chess.square_name(square), visible_after=end[view][square] != '?',
                square_visible_before=previous[view][square] != '?'))
        assert terminal
    destination = chess.parse_square(first['move'][2:4])
    return dict(root_move=first['move'],
                root_piece_hidden=first[('black', 'white')[actor]][destination] == '?',
                continuation_events=events,
                counts={role: dict(c) for role, c in counts.items()},
                supplements=supplements, terminal_attackers=terminal)


def main():
    dataset = json.loads((OUT / 'dataset.json').read_text())
    for name, digest in dataset['artifacts'].items():
        assert sha(OUT / name) == digest, name
    review = json.loads((OUT / 'review.json').read_text())
    assert review['passed']
    targets = {r['id']: r for r in map(json.loads, (OUT / 'root-targets.jsonl').read_text().splitlines())}
    assert len(targets) == dataset['root_rows'] == len(review['rows'])
    rows = []
    panels = defaultdict(Counter)
    for receipt in review['rows']:
        job = receipt['job']
        target = targets[job['id']]
        path = OUT / job['id'] / 'replay.json'
        assert sha(path) == receipt['replay_sha256'] == target['replay_sha256']
        game = json.loads(path.read_text())
        assert game['continuation']['source_game'] == target['source_group']
        assert game['censored'] == target['censored']
        row = dict(job=job['id'], source_group=target['source_group'], arm=job['arm'],
                   repeat=job['repeat'], actor_side=target['side'], phase=target['phase'],
                   terminal_return=target['terminal_return'], censored=target['censored'],
                   replay_sha256=target['replay_sha256'], **annotate(game))
        assert row['root_move'] == target['action']
        for role, counts in row['counts'].items():
            group = panels[(job['arm'], role)]
            group.update(counts)
            group['branches'] += 1
            group['censored_branches'] += int(row['censored'])
        rows.append(row)
    assert len({r['job'] for r in rows}) == len(targets)
    assert sum(len(r['continuation_events']) for r in rows) == sum(t['new_plies'] for t in targets.values())
    summaries = []
    for (arm, role), counts in sorted(panels.items()):
        summaries.append(dict(arm=arm, role=role, moves=counts['moves'],
            branches=counts['branches'], censored_branches=counts['censored_branches'],
            counts={tag: counts[tag] for tag in mt.KEYS},
            per_100_moves={tag: 100 * counts[tag] / counts['moves'] if counts['moves'] else None for tag in mt.KEYS}))
    result = dict(at=datetime.now(timezone.utc).isoformat(), post_hoc=True, rows=rows,
        panels=summaries, source_sha256=sha(Path(__file__)),
        taxonomy_source_sha256=sha(ROOT / 'learning/move_taxonomy.py'),
        dataset_sha256=sha(OUT / 'dataset.json'),
        scope='All audited branches, only moves after the intervention; shared prefixes are not counted. '
              'Offline labels may use full boards, both views and future moves. Not critic inputs, '
              'independent samples, guard calibration, causal mechanism proof or strength evidence.')
    with (OUT / 'taxonomy.json').open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(dict(branches=len(rows), panels=summaries,
        queen_supplements=sum(bool(s.get('queen_capture')) for r in rows for s in r['supplements']),
        ep_supplements=sum(bool(s.get('en_passant_capture')) for r in rows for s in r['supplements']))))


if __name__ == '__main__':
    main()
