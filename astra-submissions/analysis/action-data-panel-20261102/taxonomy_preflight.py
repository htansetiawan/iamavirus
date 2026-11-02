"""Check the new analysis on the completed earlier pilot, not partial 244 results."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import analyze_taxonomy as analysis

OUT = Path(__file__).resolve().parent
OLD = OUT.parent / 'action-continuation-20261102'


def main():
    old = json.loads((OLD / 'taxonomy.json').read_text())
    checked = events = supplements = 0
    for row in old['rows']:
        path = OLD / row['job'] / 'replay.json'
        assert analysis.sha(path) == row['replay_sha256']
        game = json.loads(path.read_text())
        actual = analysis.annotate(game)
        for key in ('root_move', 'root_piece_hidden', 'continuation_events', 'terminal_attackers'):
            assert actual[key] == row[key], (row['job'], key)
        branch = game['continuation']['branch_ply']
        expected = {'actor': Counter(), 'opponent': Counter()}
        for event in row['continuation_events']:
            role = 'actor' if event['side'] == branch % 2 else 'opponent'
            expected[role]['moves'] += 1
            for tag in set(event['tags']):
                expected[role][tag] += 1
        assert {r: dict(c) for r, c in expected.items()} == actual['counts']
        assert sum(c['moves'] for c in expected.values()) == len(game['frames']) - branch - 1
        checked += 1
        events += len(actual['continuation_events'])
        supplements += len(actual['supplements'])
    receipt = dict(at=datetime.now(timezone.utc).isoformat(), passed=True,
                   old_pilot_branches=checked, continuation_events=events,
                   supplements=supplements,
                   old_taxonomy_sha256=analysis.sha(OLD / 'taxonomy.json'),
                   analysis_sha256=analysis.sha(OUT / 'analyze_taxonomy.py'),
                   preflight_sha256=analysis.sha(Path(__file__)),
                   scope='Exact comparison with all eight previously audited pilot branch annotations; '
                         'shared prefix moves excluded from arm totals. Not a new policy trial.')
    assert checked == 8
    with (OUT / 'taxonomy-preflight.json').open('x') as f:
        json.dump(receipt, f, indent=2)
        f.write('\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
