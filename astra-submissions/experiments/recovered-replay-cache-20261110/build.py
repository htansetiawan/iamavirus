"""Reconstruct one packed, rules-checked trajectory per recovered move sequence."""
from collections import Counter
from datetime import datetime, timezone
import argparse
import fcntl
import hashlib
import importlib.util
from itertools import groupby
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis'/HERE.name
SOURCE = ROOT/'data/astra-spool/move-metadata-recovery-20261110'
RECOVERY = OUT.parent/'move-metadata-recovery-20261110'
CODEC_SOURCE = HERE.parent/'reconstructed-train-20261110/build.py'
METADATA_SOURCE = HERE.parent/'move-metadata-recovery-20261110/collect.py'
NATIVE = HERE.parent/'observed-class-20261110/build/producer.so'
VALIDATOR = HERE.parent/'last-only-pilot-20261110/build/native-validator.so'
REF = ROOT.parent/'fow-starter/referee.py'
OWNER = 'astra-'+HERE.name
NORMAL_REASONS = {'King capturable', 'Threefold repetition', '50-move rule', 'No legal moves', 'Move limit reached'}

spec = importlib.util.spec_from_file_location('reconstruction_316', CODEC_SOURCE)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
codec, ref = old.codec, old.ref
spec = importlib.util.spec_from_file_location('metadata_328', METADATA_SOURCE)
metadata = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metadata)


def sha(path):
    with Path(path).open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    tmp = path.with_name(path.name+'.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def load():
    plan = json.loads((OUT/'plan.json').read_text())
    for path, digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    return plan


def connect():
    # The two sealed recovery artifacts are immutable inputs.
    db = sqlite3.connect((SOURCE/'source.sqlite').as_uri()+'?mode=ro&immutable=1', uri=True)
    db.execute('attach database ? as listings', ((SOURCE/'metadata.sqlite').as_uri()+'?mode=ro&immutable=1',))
    db.execute('pragma query_only=on')
    db.execute('pragma temp_store=memory')
    return db


def source_groups(db):
    query = '''select m.moves_sha256, m.game_id, m.moves, d.json
               from moves m join listings.metadata d on m.game_id=d.game_id
               order by m.moves_sha256,m.game_id'''
    for digest, group in groupby(db.execute(query), key=lambda row: row[0]):
        text = None
        members = []
        for _, game_id, raw, metadata in group:
            if text is None:
                text = raw
            assert raw == text and hashlib.sha256(raw.encode()).hexdigest() == digest
            row = json.loads(metadata)
            assert row['id'] == game_id and row['plies'] == len(raw.split())
            members.append(row)
        yield digest, text.split(), members


def completion(row):
    return metadata.stamp(row['createdAt']), row['id']


def split(row, plan):
    date = completion(row)[0]
    if date < metadata.stamp(plan['validation_start']):
        return 'train'
    if date < metadata.stamp(plan['test_start']):
        return 'validation'
    return 'test'


def freeze():
    receipt = json.loads((RECOVERY/'terminal-verification.json').read_text())
    assert receipt['independent_review_passed'] and receipt['unmatched'] == 0
    assert sha(SOURCE/'source.sqlite') == receipt['source_moves_sha256']
    assert sha(SOURCE/'metadata.sqlite') == receipt['metadata_sha256']
    assert Path(ref.__file__).resolve() == REF.resolve()
    dependencies = [*sorted(HERE.glob('*.py')), CODEC_SOURCE, METADATA_SOURCE, REF, NATIVE, VALIDATOR,
        SOURCE/'source.sqlite', SOURCE/'metadata.sqlite', RECOVERY/'terminal-verification.json',
        ROOT/'astra-submissions/tools/reconstructed_cache.py', ROOT/'astra-submissions/tools/experience_index.py',
        ROOT/'learning/rules.py', ROOT/'learning/_native.py',
        OUT.parent/'capture-fixed-prior-20261110/plan.json',
        OUT.parent/'prospective-quiet-teacher-20261110/plan.json']
    plan = dict(at=now(), input_games=receipt['metadata_rows'], input_groups=receipt['whole_trajectories'],
        input_plies=receipt['move_plies'], record_size=codec.ROW.size,
        output=str(ROOT/'data/astra-spool'/HERE.name), cpu=6,
        validation_start='2026-11-07T00:00:00Z', test_start='2026-11-09T00:00:00Z',
        build_cap_seconds=3600, audit_cap_seconds=1800, byte_cap=768*1024**2,
        dependencies={str(path):sha(path) for path in dependencies})
    OUT.mkdir(exist_ok=False)
    save(OUT/'plan.json', plan)
    print(json.dumps(dict(pins=len(dependencies), input_games=plan['input_games'],
        input_groups=plan['input_groups'], plan_sha256=sha(OUT/'plan.json'))), flush=True)


class InvalidTrajectory(ValueError):
    """The course rules and C agree that a source path cannot be played."""


def reconstruct(moves, native):
    board = ref.FowBoard()
    native.start()
    repetitions = Counter({ref.position_key(board): 1})
    records = bytearray()
    for ply, text in enumerate([*moves, None]):
        views = [ref.observation(board, True), ref.observation(board, False)]
        native.check(board, views)
        full = native.buffers[0].value.decode()
        side = 0 if board.turn else 1
        castle, ep, halfmove = native.castle.value, native.ep.value, native.half.value
        outcome = ref.outcome(board, repetitions)
        flags = 0
        if text is not None:
            if outcome is not None or ply >= 1000:
                raise InvalidTrajectory('continued_after_terminal')
            move = ref.chess.Move.from_uci(text)
            step = native.lib.astra_test_step(old.native_move(text))
            if move not in ref.fow_moves(board):
                assert step == -1, 'C accepted an illegal course move'
                raise InvalidTrajectory('illegal_move')
            flags |= codec.CAPTURE if board.is_capture(move) else 0
            flags |= codec.EN_PASSANT if board.is_en_passant(move) else 0
            flags |= codec.CASTLE if board.is_castling(move) else 0
            flags |= codec.PROMOTION if move.promotion else 0
            mover = board.turn
            board.push(move)
            repetitions[ref.position_key(board)] += 1
            king = board.king(mover)
            fatal = king is None or board.is_attacked_by(not mover, king)
            assert step == int(fatal), 'native/course king-risk disagreement'
            flags |= codec.FATAL if fatal else 0
        elif outcome is None and ply == 1000:
            outcome = ('1/2-1/2', 'Move limit reached')
        selection = codec.AFTER_EIGHT if ply//2 >= 8 else 0
        records.extend(codec.encode(full, *views, castle, ep, halfmove, side, text, selection, flags))
    return records, outcome


def lease(take, cpu):
    path = ROOT/'chatroom/cores.json'
    with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads(path.read_text())
        if take:
            assert all(cpu not in row['cores'] for row in state['allocation'])
            state['allocation'].append(dict(owner=OWNER, cores=[cpu], pid=os.getpid(),
                at=now(), purpose='rules replay and independent packed cache audit'))
        else:
            state['allocation'] = [row for row in state['allocation'] if row['owner'] != OWNER]
        state['updated'] = now()
        save(path, state)


def build(plan, output):
    games = []
    counts = Counter()
    splits = Counter()
    native = old.Native(NATIVE)
    with connect() as db, (output/'records.bin').open('xb') as data, \
            (output/'excluded.jsonl').open('x') as excluded:
        for digest, moves, members in source_groups(db):
            counts['source_groups'] += 1
            counts['source_games'] += len(members)
            counts['source_plies'] += len(moves)*len(members)
            normal = [row for row in members if row['reason'] in NORMAL_REASONS]
            rejected = {row['id']: 'technical_outcome' for row in members if row not in normal}
            eligible = []
            if normal:
                try:
                    records, outcome = reconstruct(moves, native)
                except InvalidTrajectory as error:
                    rejected.update({row['id']: str(error) for row in normal})
                else:
                    for row in normal:
                        if outcome == (row['result'], row['reason']):
                            eligible.append(row)
                        else:
                            rejected[row['id']] = 'outcome_mismatch'
            if eligible:
                chosen = min(eligible, key=completion)
                partition = split(chosen, plan)
                rejected.update({row['id']: 'duplicate_trajectory' for row in eligible if row is not chosen})
                games.append(dict(game=chosen['id'], sequence_sha256=digest,
                    start=data.tell()//codec.ROW.size, records=len(moves)+1,
                    moves=len(moves), split=partition, metadata=chosen,
                    clocks_available=False, original_recorded_views_available=False))
                data.write(records)
                counts['accepted_groups'] += 1
                counts['packed_records'] += len(moves)+1
                splits[partition] += 1
            for game_id, reason in rejected.items():
                excluded.write(json.dumps(dict(game=game_id, sequence_sha256=digest, reason=reason))+'\n')
                counts[reason] += 1
            assert len(rejected)+bool(eligible) == len(members)
            assert data.tell()+excluded.tell() <= plan['byte_cap']
            if counts['source_groups'] % 1000 == 0:
                save(OUT/'progress.json', dict(at=now(), status='building', counts=dict(counts), splits=dict(splits)))
        data.flush()
        os.fsync(data.fileno())
    assert (counts['source_games'], counts['source_groups'], counts['source_plies']) == (
        plan['input_games'], plan['input_groups'], plan['input_plies'])
    save(output/'games.json', games)
    assert sum(path.stat().st_size for path in output.iterdir()) <= plan['byte_cap']
    save(OUT/'built.json', dict(at=now(), counts=dict(counts), splits=dict(splits)))


def run():
    plan = load()
    output = Path(plan['output'])
    output.mkdir(parents=True, exist_ok=False)
    os.sched_setaffinity(0, {plan['cpu']})
    lease(True, plan['cpu'])
    start = time.monotonic()
    state = dict(status='running', phase='build', started_at=now(), pid=os.getpid(), plan_sha256=sha(OUT/'plan.json'))
    save(OUT/'execution.json', state)
    try:
        def deadline(*_):
            raise TimeoutError('replay build wall cap')
        signal.signal(signal.SIGALRM, deadline)
        signal.alarm(plan['build_cap_seconds'])
        build(plan, output)
        signal.alarm(0)
        state['phase'] = 'audit'
        save(OUT/'execution.json', state)
        subprocess.run([sys.executable, str(HERE/'verify.py')], check=True, timeout=plan['audit_cap_seconds'])
        state['status'] = 'complete'
    except BaseException as error:
        state.update(status='failed', error=repr(error))
        raise
    finally:
        signal.alarm(0)
        state.update(ended_at=now(), seconds=time.monotonic()-start)
        save(OUT/'execution.json', state)
        lease(False, plan['cpu'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('freeze','run'))
    args = parser.parse_args()
    (freeze if args.action == 'freeze' else run)()
