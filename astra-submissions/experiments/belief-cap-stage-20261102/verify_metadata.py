#!/usr/bin/env python3
"""Distinguish exact referee state from equal piece placement at the cap."""
import json
from pathlib import Path
from verify import OUT, REPLAY, REF, ref, inspect, board, sha

replay = json.loads(REPLAY.read_text())
actual = ref.FowBoard()
for frame in replay['frames'][1:29]:
    actual.push_uci(frame['move'])
    assert ref.make_frame(actual, frame['clocks'])['board'] == frame['board']
summary = json.loads((OUT / 'summary.json').read_text())
results = []
for attempt in summary['attempts']:
    matches = [e for e in attempt['events'] if e['phase'] == 'before_cap_match']
    parent = inspect(OUT / f"attempt-{attempt['attempt']}/pre_expand.txt.gz",
        attempt['snapshots']['pre_expand.txt'], replay['frames'][27]['board'], {e['parent'] for e in matches})
    rows = []
    for e in matches:
        candidate = board(parent['selected'][e['parent']]); candidate.push_uci(e['move'])
        same = candidate.turn == actual.turn and candidate.castling_rights == actual.castling_rights and candidate.ep_square == actual.ep_square and candidate.halfmove_clock == actual.halfmove_clock
        rows.append(dict(move=e['move'], native_key=e['key'], turn=candidate.turn,
            castling=candidate.castling_rights, ep=candidate.ep_square, halfmove=candidate.halfmove_clock,
            matches_referee_metadata=same))
    results.append(dict(attempt=attempt['attempt'], candidates=rows))
report = dict(referee_sha256=sha(REF), script_sha256=sha(Path(__file__)), frames_reconstructed=28,
    actual=dict(turn=actual.turn, castling=actual.castling_rights, ep=actual.ep_square, halfmove=actual.halfmove_clock),
    attempts=results, scope='Board, turn, castling, EP and halfmove comparison; not equality of either player\'s private history or all repetition counts.')
with (OUT / 'metadata-review.json').open('x') as f: json.dump(report, f, indent=2)
print(json.dumps(report, indent=2))
