"""Check every stored state and selection with the independent C++ rules."""
from collections import Counter
import json
import mmap
from pathlib import Path
import sys
import time

from build import OUT, ROOT, VALIDATOR, NORMAL_REASONS, codec, completion, connect, load, now, save, sha, source_groups, split
sys.path.insert(0, str(ROOT))
from learning import _native, rules
from experience_index import unpack_view


def use_pinned_validator():
    assert _native._library is None
    _native.ensure_built = lambda verbose=True: VALIDATOR


def replay_cpp(moves, rows=None):
    state = rules.GameState()
    board = state.board
    for ply, move in enumerate([*moves, None]):
        flags = 0
        if rows is not None:
            row = rows(ply)
            assert unpack_view(row[0]) == board.board_string()
            assert row[1:7] == (board.visible(0), board.visible(1), board.castling,
                board.en_passant, board.halfmove_clock, board.side)
            assert codec.decode_move(row[7]) == move
            assert row[8] == (codec.AFTER_EIGHT if ply//2 >= 8 else 0)
            if move is not None:
                source, target = row[7] & 63, (row[7] >> 6) & 63
                piece = board.piece_at(source) % 6
                ep = piece == 0 and target == board.en_passant and source%8 != target%8
                if ep or board.piece_at(target) >= 0:
                    flags |= codec.CAPTURE
                if ep:
                    flags |= codec.EN_PASSANT
                if piece == 5 and abs(source-target) == 2:
                    flags |= codec.CASTLE
                if len(move) == 5:
                    flags |= codec.PROMOTION
        if move is not None:
            if state.outcome() is not None:
                return None, 'continued_after_terminal'
            try:
                state.push(move)
            except ValueError:
                return None, 'illegal_move'
            if rows is not None and board.mover_lost():
                flags |= codec.FATAL
        if rows is not None:
            assert row[9] == flags
    return state.outcome(), None


def main():
    started = time.monotonic()
    plan = load()
    use_pinned_validator()
    output = Path(plan['output'])
    entries = json.loads((output/'games.json').read_text())
    index = {row['sequence_sha256']:row for row in entries}
    assert len(index) == len(entries)
    with (output/'excluded.jsonl').open() as file:
        excluded = {}
        for line in file:
            row = json.loads(line)
            assert row['game'] not in excluded
            excluded[row['game']] = row
    seen = Counter()
    splits = Counter()
    offset = 0
    with connect() as db, (output/'records.bin').open('rb') as file, mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as data:
        for digest, moves, members in source_groups(db):
            entry = index.pop(digest, None)
            normal = [row for row in members if row['reason'] in NORMAL_REASONS]
            if entry is not None:
                assert entry['start'] == offset and entry['records'] == len(moves)+1 and entry['moves'] == len(moves)
                assert not entry['clocks_available'] and not entry['original_recorded_views_available']
                def rows(ply):
                    return codec.ROW.unpack_from(data, (offset+ply)*codec.ROW.size)
                outcome, fault = replay_cpp(moves, rows)
                assert fault is None and outcome is not None
                eligible = [row for row in normal if (row['result'],row['reason']) == outcome]
                chosen = min(eligible, key=completion)
                assert entry['metadata'] == chosen and entry['game'] == chosen['id']
                assert entry['split'] == split(chosen, plan)
                splits[entry['split']] += 1
                offset += len(moves)+1
            elif normal:
                outcome, fault = replay_cpp(moves)
                assert not any((row['result'],row['reason']) == outcome for row in normal)
                chosen = None
            else:
                chosen = outcome = fault = None
            for row in members:
                if row is chosen:
                    seen['accepted_groups'] += 1
                    continue
                if row['reason'] not in NORMAL_REASONS:
                    reason = 'technical_outcome'
                elif fault is not None:
                    reason = fault
                elif (row['result'],row['reason']) == outcome:
                    reason = 'duplicate_trajectory'
                else:
                    reason = 'outcome_mismatch'
                assert excluded.pop(row['id']) == dict(game=row['id'], sequence_sha256=digest, reason=reason)
                seen[reason] += 1
            seen['source_games'] += len(members)
            seen['source_groups'] += 1
            seen['source_plies'] += len(moves)*len(members)
        assert offset*codec.ROW.size == len(data) and not index and not excluded
    seen['packed_records'] = offset
    produced = json.loads((OUT/'built.json').read_text())
    assert seen == Counter(produced['counts']) and splits == Counter(produced['splits'])
    manifest = dict(schema=codec.SCHEMA, record_size=codec.ROW.size, records=offset,
        plan_sha256=sha(OUT/'plan.json'), sha256={name:sha(output/name) for name in ('records.bin','games.json','excluded.jsonl')},
        clock_source=None, observation_source='course rules from recorded UCI moves',
        result_source='validated public listing metadata', group_key='complete move sequence SHA-256',
        splits=dict(splits), purpose='Grouped chronology for training future models from this cache')
    manifest_bytes = (json.dumps(manifest, indent=2, allow_nan=False)+'\n').encode()
    storage_bytes = sum(path.stat().st_size for path in output.iterdir())+len(manifest_bytes)
    assert storage_bytes <= plan['byte_cap']
    save(output/'manifest.json', manifest)
    summary = dict(at=now(), passed=True, counts=dict(seen), splits=dict(splits),
        frames=offset, bytes=storage_bytes,
        manifest_sha256=sha(output/'manifest.json'), source_pins=len(plan['dependencies']),
        audit_seconds=time.monotonic()-started)
    save(OUT/'independent-review.json', summary)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
