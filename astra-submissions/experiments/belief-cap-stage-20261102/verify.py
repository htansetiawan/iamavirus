#!/usr/bin/env python3
"""Independently check snapshot truth matches and pre-cap candidate transitions."""
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from run import OUT, ROOT, REPLAY, sha

REF = ROOT.parent / 'fow-starter/referee.py'
assert sha(REF) == '2f82ac292bfad29bcb2d701b73c060d1ca8281378b4598f08a620fe5c97255be'
spec = importlib.util.spec_from_file_location('cap_stage_referee', REF)
ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)


def inspect(path, expected, truth, indices=()):
    assert sha(path) == expected['gzip_sha256']
    digest = hashlib.sha256(); weights = []; matched = []; selected = {}; count = 0
    with gzip.open(path, 'rb') as f:
        header = f.readline(); digest.update(header); h = header.decode().split()
        assert h[0] == 'ASTRA_BELIEF1'
        for i, line in enumerate(f):
            digest.update(line); fields = line.decode().split()
            assert len(fields) == 7 and len(fields[0]) == 64
            row = dict(board=fields[0], side=int(fields[1]), castle=int(fields[2], 16),
                ep=int(fields[3]), halfmove=int(fields[4]), logw=float.fromhex(fields[5]), history=int(fields[6], 16))
            weight = math.exp(row['logw']); weights.append(weight)
            if row['board'] == truth: matched.append(weight)
            if i in indices: selected[i] = row
            count += 1
    assert count == int(h[1]) and digest.hexdigest() == expected['raw_sha256']
    return dict(count=count, truth_placements=len(matched),
        truth_mass=math.fsum(matched) / math.fsum(weights), selected=selected)


def board(row):
    b = ref.FowBoard(None)
    b.set_piece_map({i: ref.chess.Piece.from_symbol(c) for i, c in enumerate(row['board']) if c != '-'})
    b.turn = row['side'] == 0; b.castling_rights = row['castle']
    b.ep_square = row['ep'] if row['ep'] >= 0 else None
    b.halfmove_clock = row['halfmove']
    return b


def main():
    assert json.loads((OUT / 'execution.json').read_text())['status'] == 'complete'
    plan = json.loads((OUT / 'plan.json').read_text()); assert sha(REPLAY) == plan['replay_sha256']
    replay = json.loads(REPLAY.read_text()); summary = json.loads((OUT / 'summary.json').read_text())
    records = []; candidates = snapshots = 0
    for attempt in summary['attempts']:
        directory = OUT / f"attempt-{attempt['attempt']}"
        events = attempt['events']; matches = [r for r in events if r['phase'] == 'before_cap_match']
        stats = {}
        for name, truth in [('pre_clock', replay['frames'][27]['board']), ('pre_expand', replay['frames'][27]['board']), ('post_expand', replay['frames'][28]['board'])]:
            filename = name + '.txt'
            stats[name] = inspect(directory / (filename + '.gz'), attempt['snapshots'][filename], truth,
                                  {r['parent'] for r in matches} if name == 'pre_expand' else ())
            snapshots += 1
        for name, phase in [('pre_expand', 'parent'), ('post_expand', 'child')]:
            native = next(e for e in events if e['phase'] == phase)
            for key in ('count', 'truth_placements'): assert stats[name][key] == native[key]
            assert abs(stats[name]['truth_mass'] - native['truth_mass']) < 1e-12
        transitions = []
        for event in matches:
            parent = board(stats['pre_expand']['selected'][event['parent']])
            assert ref.make_frame(parent, [0, 0])['white'] == replay['frames'][27]['white']
            move = ref.chess.Move.from_uci(event['move'])
            assert move in ref.fow_moves(parent)
            parent.push(move)
            frame = ref.make_frame(parent, [0, 0])
            assert frame['board'] == replay['frames'][28]['board'] and frame['white'] == replay['frames'][28]['white']
            king = parent.king(not parent.turn)
            assert king is not None and not parent.is_attacked_by(parent.turn, king)
            transitions.append(dict(move=event['move'], child_ep=parent.ep_square,
                                    child_castling=parent.castling_rights))
            candidates += 1
        pre = next(e for e in events if e['phase'] == 'before_cap')
        assert pre['truth_placements'] == len(matches)
        records.append(dict(attempt=attempt['attempt'], snapshots={k: {a: b for a, b in v.items() if a != 'selected'} for k, v in stats.items()},
                            independently_verified_candidates=transitions))
    report = dict(snapshots_checked=snapshots, candidate_transitions_checked=candidates,
        referee_sha256=sha(REF), script_sha256=sha(Path(__file__)), records=records,
        scope='Independent placement/mass checks and candidate legality, not full posterior calibration or playing strength.')
    with (OUT / 'independent-review.json').open('x') as f: json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
