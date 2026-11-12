"""Finish a timed-out local replay audit without repeating completed checks.

The first attempt and its 30-minute limit stay recorded. This tool can only
prepare after that attempt is terminal with its exact timeout. It uses the
same pinned per-game verifier and a separate bounded continuation.
"""
from argparse import ArgumentParser
from collections import Counter
import json
import os
from pathlib import Path
import signal
import time

import verify_field_replays as original

OUT, STORE = original.OUT, original.STORE
JOURNAL = STORE / 'review-rows.jsonl'


def prefix_rows(raw, listing, validation, accepted):
    rows, tail = [], 0
    lines = raw.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if not line.endswith(b'\n'):
            assert i == len(lines) - 1
            tail = len(line)
            break
        row = json.loads(line)
        assert i < len(listing) and row['game'] == listing[i]['id']
        assert row['frames'] == validation[i]['frames_checked']
        assert row['sequence_sha256'] == validation[i]['moves_sha256'] == accepted[i]['moves_sha256']
        assert row['termination'] == accepted[i]['termination']
        assert isinstance(row['clocks'], dict) and isinstance(row['time_control_present'], bool)
        rows.append(row)
    return rows, tail


def inputs():
    listing = original.read(STORE / 'listing.json')
    validation = [json.loads(s) for s in (STORE / 'validation.jsonl').read_text().splitlines()]
    accepted = [json.loads(s) for s in (STORE / 'raw/accepted.jsonl').read_text().splitlines()]
    assert [r['id'] for r in listing] == [r['id'] for r in validation] == [r['id'] for r in accepted]
    assert len(listing) == 6000
    return listing, validation, accepted


def preflight():
    listing = [dict(id=f'a000000{i}') for i in range(3)]
    validation = [dict(frames_checked=i + 1, moves_sha256=str(i) * 64) for i in range(3)]
    accepted = [dict(moves_sha256=str(i) * 64, termination='normal') for i in range(3)]
    rows = [dict(game=listing[i]['id'], frames=i+1, sequence_sha256=str(i)*64,
                 termination='normal', clocks={}, time_control_present=False) for i in range(3)]
    encoded = lambda values: b''.join((json.dumps(r) + '\n').encode() for r in values)
    complete = encoded(rows[:2])
    assert prefix_rows(complete, listing, validation, accepted) == (rows[:2], 0)
    partial = complete + b'{"game":'
    assert prefix_rows(partial, listing, validation, accepted) == (rows[:2], 8)
    bad = [encoded([rows[1], rows[0]]), encoded([rows[0], rows[0]]), encoded(rows + [rows[0]])]
    wrong_hash = dict(rows[0], sequence_sha256='x' * 64)
    bad.append(encoded([wrong_hash]))
    for raw in bad:
        try:
            prefix_rows(raw, listing, validation, accepted)
        except AssertionError:
            continue
        raise AssertionError('Bad completed prefix accepted')
    original.save(OUT / 'completion-preflight.json', dict(at=original.now(), checks=6,
                  source_sha256=original.sha(Path(__file__)),
                  scope='Synthetic prefix-accounting checks only. No original replay or running audit changed.'))
    print(json.dumps(dict(prefix_contract_checks=6)))


def prepare():
    previous = original.read(OUT / 'review-execution.json')
    assert previous['status'] == 'failed' and previous.get('ended_at')
    assert previous.get('error') == "TimeoutError('field review reached its wall limit')", previous.get('error')
    first_plan = original.read(OUT / 'review-plan.json')
    for path, expected in first_plan['dependencies'].items():
        assert original.sha(path) == expected, path
    listing, validation, accepted = inputs()
    rows, tail = prefix_rows(JOURNAL.read_bytes(), listing, validation, accepted)
    assert 0 < len(rows) < len(listing)
    dependencies = dict(first_plan['dependencies'])
    paths = [Path(__file__), OUT / 'review-plan.json', OUT / 'review-execution.json', JOURNAL,
             OUT / 'result.json', STORE / 'validation.jsonl', STORE / 'raw/accepted.jsonl',
             OUT / 'completion-preflight.json']
    dependencies.update({str(p): original.sha(p) for p in paths})
    plan = dict(at=original.now(), original_status=previous['status'], original_error=previous['error'],
                initial_limit_seconds=first_plan['wall_seconds'], initial_completed_rows=len(rows),
                incomplete_trailing_bytes=tail, remaining_games=len(listing)-len(rows),
                total_games=6000, wall_seconds=900, cores=[6], dependencies=dependencies,
                scope='Separate local continuation using identical pinned per-game rules/provenance checks. '
                      'Reuse the certified prefix, verify only remaining games, and reduce all6000 rows. '
                      'The original30-minute incomplete attempt is not reclassified as passed. No model, game, network, Git or deployment.')
    original.save(OUT / 'completion-plan.json', plan)
    print(json.dumps({k: plan[k] for k in ['initial_completed_rows', 'remaining_games', 'wall_seconds', 'original_error']}), flush=True)


def run():
    plan = original.read(OUT / 'completion-plan.json')
    for path, expected in plan['dependencies'].items():
        assert original.sha(path) == expected, path
    listing, validation, accepted = inputs()
    prefix, tail = prefix_rows(JOURNAL.read_bytes(), listing, validation, accepted)
    assert len(prefix) == plan['initial_completed_rows'] and tail == plan['incomplete_trailing_bytes']
    collection = original.read(OUT / 'result.json')
    old_split = {r['sequence_sha256']: r['split'] for r in original.read(original.OLD)}
    state = dict(at=original.now(), status='running', initial_completed_rows=len(prefix),
                 new_completed=0, plan_sha256=original.sha(OUT / 'completion-plan.json'))
    original.save(OUT / 'completion-execution.json', state)
    ingest, referee = original.load_rules()
    os.sched_setaffinity(0, set(plan['cores']))
    def timeout(*_):
        raise TimeoutError('field completion reached its separate wall limit')
    signal.signal(signal.SIGALRM, timeout)
    signal.signal(signal.SIGTERM, timeout)
    signal.alarm(plan['wall_seconds'])
    started = time.monotonic()
    totals, clocks, sequences, sources, overlap = Counter(), Counter(), Counter(), Counter(), Counter()
    output = STORE / 'review-completion-rows.jsonl'
    try:
        with original.lease(plan['cores']), output.open('x') as stream:
            for i, (row, checked) in enumerate(zip(listing, validation, strict=True)):
                directory = STORE / 'raw/games' / row['id']
                path = directory / 'replay.json'
                assert original.read(directory / 'listing.json') == row
                fetch = original.read(directory / 'fetch_metadata.json')['replay']
                assert original.sha(path) == checked['replay_sha256'] == fetch['sha256']
                if i < len(prefix):
                    record = dict(prefix[i], review_origin='initial30minute')
                else:
                    result = original.verify_game(original.read(path), row, ingest, referee)
                    assert result['frames'] == checked['frames_checked']
                    assert result['sequence_sha256'] == checked['moves_sha256'] == accepted[i]['moves_sha256']
                    assert result['termination'] == accepted[i]['termination']
                    record = dict(game=row['id'], review_origin='continuation', **result)
                    state['new_completed'] += 1
                totals['games'] += 1
                totals['frames'] += record['frames']
                totals['time_control_present'] += record['time_control_present']
                clocks.update(record['clocks'])
                sequence = record['sequence_sha256']
                sequences[sequence] += 1
                sources[checked['source']] += 1
                if sequence in old_split:
                    overlap[old_split[sequence]] += 1
                record['replay_sha256'] = checked['replay_sha256']
                stream.write(json.dumps(record) + '\n')
                if (i + 1) % 250 == 0:
                    stream.flush()
                    original.atomic(OUT / 'completion-execution.json', state)
                    print(json.dumps(dict(total_rows=i+1, reused=len(prefix), newly_checked=state['new_completed'])), flush=True)
        assert totals['games'] == 6000 and totals['frames'] == collection['frames']
        assert len(sequences) == collection['unique_trajectories'] and dict(sources) == collection['sources']
        assert state['new_completed'] == plan['remaining_games']
        for path, expected in plan['dependencies'].items():
            assert original.sha(path) == expected, path
        result = dict(at=original.now(), totals=dict(totals), sources=dict(sources), clock_flags=dict(clocks),
                      unique_trajectories=len(sequences), duplicate_extra_ids=6000-len(sequences),
                      game_ids_overlapping_old_336_split=dict(overlap),
                      unique_sequences_overlapping_old_336_split=dict(Counter(old_split[s] for s in sequences if s in old_split)),
                      reused_original_rows=len(prefix), newly_verified_rows=state['new_completed'],
                      initial_30minute_attempt_passed=False, initial_error=plan['original_error'],
                      original_journal_sha256=original.sha(JOURNAL), combined_journal_sha256=original.sha(output),
                      plan_sha256=original.sha(OUT / 'completion-plan.json'), scope=plan['scope'],
                      limitations=['Independent validation completed across bounded passes, not inside the original30-minute run.',
                                   'Overlap check covers the336cache, not every prior experiment.',
                                   'No training split, held-out-strength claim or strategic-quality label is assigned.',
                                   'Original data, original journal and original failure remain unchanged.'])
        original.save(OUT / 'completion-result.json', result)
        state.update(status='complete', result_sha256=original.sha(OUT / 'completion-result.json'))
        print(json.dumps(result, indent=2), flush=True)
    except BaseException as exc:
        state.update(status='failed', error=repr(exc))
        raise
    finally:
        signal.alarm(0)
        state.update(ended_at=original.now(), seconds=time.monotonic()-started)
        original.atomic(OUT / 'completion-execution.json', state)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('command', choices=['preflight', 'prepare', 'run'])
    args = parser.parse_args()
    {'preflight': preflight, 'prepare': prepare, 'run': run}[args.command]()
