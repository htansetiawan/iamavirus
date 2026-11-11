"""Second-pass rules/provenance review of the complete field snapshot.

Prepare can run while the collector is active. Run refuses an incomplete
collector. All artifacts stay local; this tool has no network/deployment path.
"""
from argparse import ArgumentParser
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'astra-submissions/analysis/field-snapshot-20261111'
STORE = ROOT / 'data/astra-spool/field-snapshot-20261111'
OLD = ROOT / 'data/astra-spool/recovered-replay-cache-20261110/games.json'
VALIDATOR = ROOT / 'astra-submissions/experiments/last-only-pilot-20261110/build/native-validator.so'
REFEREE = ROOT.parent / 'fow-starter/referee.py'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def atomic(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def load_rules():
    sys.path.insert(0, str(ROOT))
    from learning import _native, ingest
    assert _native._library is None
    _native.ensure_built = lambda verbose=True: VALIDATOR
    spec = importlib.util.spec_from_file_location('field_audit_course_referee', REFEREE)
    referee = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(referee)
    return ingest, referee


def verify_game(replay, listing, ingest, referee):
    for key in ('id', 'white', 'black', 'whitePlayerId', 'blackPlayerId', 'whiteVersion', 'blackVersion', 'result', 'reason'):
        assert replay[key] == listing[key], (listing['id'], key)
    # Mutable current versions and staff classifications are deliberately not
    # required to match a previously cached replay.
    states, errors = ingest.validate_replay(replay)
    assert not errors, (listing['id'], errors)
    frames = replay['frames']
    assert len(states) == len(frames) == listing['plies'] + 1
    board = referee.FowBoard()
    repetitions = Counter({referee.position_key(board): 1})
    clock_flags = Counter()
    control = replay.get('timeControl')
    for i, frame in enumerate(frames):
        if i:
            assert referee.outcome(board, repetitions) is None, (listing['id'], i, 'continued after course terminal')
            move = board.parse_uci(frame['move'])
            assert move in referee.fow_moves(board), (listing['id'], i, 'course move')
            board.push(move)
            repetitions[referee.position_key(board)] += 1
        actual = ''.join(board.piece_at(sq).symbol() if board.piece_at(sq) else '-' for sq in range(64))
        assert actual == frame['board'], (listing['id'], i, 'course board')
        assert referee.observation(board, True) == frame['white'], (listing['id'], i, 'white view')
        assert referee.observation(board, False) == frame['black'], (listing['id'], i, 'black view')
        clocks = frame['clocks']
        assert len(clocks) == 2 and all(isinstance(t, (float, int)) and not isinstance(t, bool) and math.isfinite(t) for t in clocks)
        clock_flags['negative_clock_values'] += sum(t < 0 for t in clocks)
        if i:
            mover = (i - 1) % 2
            previous = frames[i - 1]['clocks']
            clock_flags['nonmoving_clock_changes'] += clocks[1 - mover] != previous[1 - mover]
            if control is not None:
                elapsed = previous[mover] + control['incrementSeconds'] - clocks[mover]
                clock_flags['elapsed_below_minus_two_ms'] += elapsed < -.002
    verdict = referee.outcome(board, repetitions)
    if verdict is not None:
        assert verdict == (replay['result'], replay['reason']), (listing['id'], 'course result', verdict)
    elif replay['reason'] == 'Move limit reached':
        assert listing['plies'] == 1000 and replay['result'] == '1/2-1/2'
    else:
        assert ingest.classify_termination(replay['result'], replay['reason']) != 'normal'
    moves = ' '.join(f['move'] for f in frames[1:])
    digest = hashlib.sha256(moves.encode()).hexdigest()
    assert digest == ingest.replay_hash(replay)
    return dict(frames=len(frames), sequence_sha256=digest, clocks=dict(clock_flags),
                time_control_present=control is not None,
                termination=ingest.classify_termination(replay['result'], replay['reason']))


def prepare():
    metadata = read(OUT / 'listing-review.json')
    for name, digest in metadata['source_hashes'].items():
        assert sha(name) == digest, name
    listing = read(STORE / 'listing.json')
    ingest, referee = load_rules()
    checked = []
    for row in listing[:2]:
        path = STORE / 'raw/games' / row['id'] / 'replay.json'
        replay = read(path)
        result = verify_game(replay, row, ingest, referee)
        checked.append(dict(game=row['id'], replay_sha256=sha(path), **result))
    dependencies = [Path(__file__), OUT / 'listing-review.json', STORE / 'listing.json', OLD, VALIDATOR, REFEREE,
                    ROOT / 'learning/ingest.py', ROOT / 'learning/rules.py', ROOT / 'learning/_native.py', ROOT / 'learning/histories.py']
    plan = dict(at=now(), games=6000, selection='Every accepted replay in the unchanged frozen 359 listing; no team/outcome selection.',
                cores=[6], wall_seconds=1800, dependencies={str(p): sha(p) for p in dependencies},
                require_original_collector_complete=True, require_accepted=6000, require_quarantined=0,
                checks=['source pages/cursor/listing already reviewed', 'saved raw and journal byte hashes',
                        'played metadata, both private views and true board', 'C++ plus separate full course-rule walk',
                        'clock schema and descriptive timing flags', 'whole-sequence duplicate and prior-cache split overlaps'],
                scope='Local data correctness/provenance review. No model fitting, inference, new game, split assignment, benchmark, network or deployment.')
    save(OUT / 'review-plan.json', plan)
    save(OUT / 'review-preflight.json', dict(at=now(), records=checked, frames=sum(r['frames'] for r in checked), scope=plan['scope']))
    print(json.dumps(dict(plan_sha256=sha(OUT / 'review-plan.json'), preflight_games=len(checked), frames=sum(r['frames'] for r in checked))), flush=True)


@contextmanager
def lease(cores):
    path = ROOT / 'chatroom/cores.json'
    owner = 'astra-field-review-20261111'
    def change(take):
        with open('/tmp/iamavirus-cores-json.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = read(path)
            if take:
                assert not any(set(row['cores']) & set(cores) for row in state['allocation'])
                state['allocation'].append(dict(owner=owner, cores=cores, pid=os.getpid(), at=now(), purpose='bounded second-pass field data review'))
            else:
                state['allocation'] = [r for r in state['allocation'] if not (r['owner'] == owner and r.get('pid') == os.getpid())]
            state['updated'] = now()
            atomic(path, state)
    change(True)
    try:
        yield
    finally:
        change(False)


def run():
    plan = read(OUT / 'review-plan.json')
    for path, expected in plan['dependencies'].items():
        assert sha(path) == expected, path
    original = read(OUT / 'execution.json')
    collection = read(OUT / 'result.json')
    assert original['status'] == 'complete' and original['result_sha256'] == sha(OUT / 'result.json')
    assert collection['games'] == collection['accepted'] == 6000 and collection['quarantined'] == 0
    assert collection['listing_sha256'] == sha(STORE / 'listing.json')
    assert collection['validation_sha256'] == sha(STORE / 'validation.jsonl')
    assert collection['collection_sha256'] == sha(STORE / 'collection.json')
    validation = [json.loads(line) for line in (STORE / 'validation.jsonl').read_text().splitlines()]
    accepted = [json.loads(line) for line in (STORE / 'raw/accepted.jsonl').read_text().splitlines()]
    listing = read(STORE / 'listing.json')
    assert [r['id'] for r in validation] == [r['id'] for r in accepted] == [r['id'] for r in listing]
    assert all(r['accepted'] and not r['problems'] for r in validation)
    old = {r['sequence_sha256']: r['split'] for r in read(OLD)}
    state = dict(at=now(), status='running', completed=0, original_result_sha256=sha(OUT / 'result.json'), plan_sha256=sha(OUT / 'review-plan.json'))
    save(OUT / 'review-execution.json', state)
    ingest, referee = load_rules()
    os.sched_setaffinity(0, set(plan['cores']))
    def timeout(*_):
        raise TimeoutError('field review reached its wall limit')
    signal.signal(signal.SIGALRM, timeout)
    signal.signal(signal.SIGTERM, timeout)
    signal.alarm(plan['wall_seconds'])
    started = time.monotonic()
    totals, sources, overlap, clocks, sequences = Counter(), Counter(), Counter(), Counter(), Counter()
    try:
        with lease(plan['cores']), (STORE / 'review-rows.jsonl').open('x') as journal:
            for row, checked, journal_row in zip(listing, validation, accepted, strict=True):
                directory = STORE / 'raw/games' / row['id']
                replay_path = directory / 'replay.json'
                assert read(directory / 'listing.json') == row
                fetch = read(directory / 'fetch_metadata.json')['replay']
                assert sha(replay_path) == checked['replay_sha256'] == fetch['sha256']
                replay = read(replay_path)
                result = verify_game(replay, row, ingest, referee)
                assert result['frames'] == checked['frames_checked']
                assert result['sequence_sha256'] == checked['moves_sha256'] == journal_row['moves_sha256']
                assert journal_row['termination'] == result['termination']
                totals['games'] += 1
                totals['frames'] += result['frames']
                totals['time_control_present'] += result['time_control_present']
                sources[checked['source']] += 1
                clocks.update(result['clocks'])
                sequences[result['sequence_sha256']] += 1
                if result['sequence_sha256'] in old:
                    overlap[old[result['sequence_sha256']]] += 1
                journal.write(json.dumps(dict(game=row['id'], **result)) + '\n')
                if totals['games'] % 250 == 0:
                    journal.flush()
                    state['completed'] = totals['games']
                    atomic(OUT / 'review-execution.json', state)
                    print(json.dumps(dict(completed=totals['games'], frames=totals['frames'])), flush=True)
        assert totals['frames'] == collection['frames']
        assert len(sequences) == collection['unique_trajectories']
        assert dict(sources) == collection['sources']
        for path, expected in plan['dependencies'].items():
            assert sha(path) == expected, path
        result = dict(at=now(), source_result_sha256=sha(OUT / 'result.json'), plan_sha256=sha(OUT / 'review-plan.json'),
                      totals=dict(totals), sources=dict(sources), clock_flags=dict(clocks), unique_trajectories=len(sequences),
                      duplicate_trajectory_extra_ids=sum(n - 1 for n in sequences.values()),
                      game_ids_overlapping_old_336_split=dict(overlap),
                      unique_sequences_overlapping_old_336_split=dict(Counter(old[s] for s in sequences if s in old)),
                      journal_sha256=sha(STORE / 'review-rows.jsonl'), scope=plan['scope'],
                      limitations=['Raw replay validity does not certify move quality or learning targets.',
                                   'Overlap is against the specific reconstructed 336 cache, not every old experiment.',
                                   'This audit assigns no train/dev/test split and makes no held-out-strength claim.',
                                   'Timing flags are descriptive; original reported clocks were not changed.',
                                   'The shared external archive and daily pipeline are not repaired by this local cache.'])
        save(OUT / 'review-result.json', result)
        state.update(status='complete', completed=6000, result_sha256=sha(OUT / 'review-result.json'))
        print(json.dumps(result, indent=2), flush=True)
    except BaseException as exc:
        state.update(status='failed', error=repr(exc))
        raise
    finally:
        signal.alarm(0)
        state.update(ended_at=now(), seconds=time.monotonic() - started)
        atomic(OUT / 'review-execution.json', state)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'run'])
    args = parser.parse_args()
    {'prepare': prepare, 'run': run}[args.command]()
