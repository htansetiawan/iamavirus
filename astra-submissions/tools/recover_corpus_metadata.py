"""Recover historical metadata alongside, never over, accepted corpus replays.

The first three fixed IDs are a coverage pilot. Every accepted supplement
requires the exact recorded position/view sequence as well as moves/result.
Only documented public GET requests are used; no current-version substitution.
"""
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning.api_client import ApiClient, ApiError

NAME = 'corpus-metadata-recovery-20261111'
OUT = ROOT / 'astra-submissions/analysis' / NAME
STORE = ROOT / 'data/astra-spool' / NAME
SNAPSHOT = ROOT / 'data/astra-spool/training-artifact-readiness-20261111/journal.jsonl'
CORE_FIELDS = ('ply', 'move', 'board', 'white', 'black')
HISTORICAL_FIELDS = ('createdAt', 'whiteVersion', 'blackVersion',
                     'whitePlayerId', 'blackPlayerId', 'white', 'black',
                     'rulesVersion', 'timeControl')


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def update(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(row, original, replay):
    require(replay['id'] == row['id'] == original['id'], 'game ID mismatch')
    require(replay['result'] == row['result'] == original['result'], 'result mismatch')
    frames = replay['frames']
    require(len(frames) == len(original['frames']) == row['plies'] + 1, 'frame count mismatch')
    require(frames[0]['move'] is None, 'initial move is not null')
    moves = ' '.join(frame['move'] for frame in frames[1:])
    require(hashlib.sha256(moves.encode()).hexdigest() == row['moves_sha256'], 'move sequence mismatch')
    for i, (old, new) in enumerate(zip(original['frames'], frames)):
        require(old['ply'] == new['ply'] == i, 'ply index mismatch')
        require(all(old[key] == new[key] for key in CORE_FIELDS), 'recorded frame mismatch at ' + str(i))
    stamp = replay.get('createdAt')
    require(isinstance(stamp, str) and re.fullmatch(
        r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,9})?(?:Z|[+-]\d\d:\d\d)', stamp), 'missing/invalid date')
    parsed = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    require(parsed.utcoffset() is not None, 'date is not timezone-aware')
    for side in ('white', 'black'):
        version = replay.get(side + 'Version')
        require(version is None or (type(version) is int and version >= 0), 'invalid played version')
        player = replay.get(side + 'PlayerId')
        require(player is None or (isinstance(player, str) and bool(player)), 'invalid player ID')
    return {key: replay.get(key) for key in HISTORICAL_FIELDS}


def prepare():
    OUT.mkdir(exist_ok=False)
    STORE.mkdir(exist_ok=False)
    (STORE / 'originals').mkdir()
    (STORE / 'responses').mkdir()
    rows = [r for line in SNAPSHOT.open() if not (r := json.loads(line)).get('createdAt')]
    require(len(rows) == 164 and len({r['id'] for r in rows}) == 164, 'source cohort changed')
    originals = []
    for row in sorted(rows, key=lambda r: r['id']):
        game = row['id']
        require(re.fullmatch('[a-z0-9]{8}', game), 'invalid API ID')
        raw_path = ROOT / 'data/raw/games' / game / 'replay.json'
        data = raw_path.read_bytes()
        obj = json.loads(data)
        require(obj.get('source') == 'corpus' and not obj.get('createdAt'), 'not an undated corpus source')
        local = STORE / 'originals' / (game + '.json')
        local.write_bytes(data)
        originals.append(dict(row=row, original_path=str(local), canonical_path=str(raw_path), sha256=sha(local)))
    save(STORE / 'sources.json', originals)
    plan = dict(at=now(), expected_games=164, pilot_games=3, wall_seconds=900,
                min_request_interval_seconds=1.2, timeout_seconds=15, max_http_attempts=200,
                max_response_bytes=5 * 1024**2, max_total_response_bytes=50 * 1024**2,
                dependencies={str(p): sha(p) for p in (Path(__file__), ROOT / 'learning/api_client.py',
                                                       SNAPSHOT, STORE / 'sources.json')},
                antecedents='155/156 documented 164 undated corpus imports; 328 recovered recent move-list metadata, with no hits for these IDs. 379 verified the old episode split fallback.',
                scope='A separate provenance supplement. Preserve canonical raw bytes, journal, old generations and splits. No rules revalidation, label rebuilding, fit, GPU, matches, model changes, release, commit, push or deployment.')
    save(OUT / 'plan.json', plan)
    # Guard against accepting the wrong source or borrowing a current version.
    source = originals[0]
    original = read(source['original_path'])
    sample = copy.deepcopy(original)
    sample.update(createdAt='2026-10-01T12:00:00Z', whiteCurrentVersion=999)
    require(identity(source['row'], original, sample)['whiteVersion'] is None, 'current version used')
    for key, value in [('id', 'zzzzzzzz'), ('createdAt', '2026-10-01'), ('whiteVersion', True)]:
        bad = copy.deepcopy(sample)
        bad[key] = value
        try:
            identity(source['row'], original, bad)
        except ValueError:
            continue
        raise ValueError('invalid metadata accepted: ' + key)
    bad = copy.deepcopy(sample)
    board = bad['frames'][0]['board']
    bad['frames'][0]['board'] = ('-' if board[0] != '-' else 'P') + board[1:]
    try:
        identity(source['row'], original, bad)
    except ValueError:
        pass
    else:
        raise ValueError('changed frame accepted')
    save(OUT / 'preflight.json', dict(at=now(), checks=6, current_versions_excluded=True,
                                     plan_sha256=sha(OUT / 'plan.json')))
    print(json.dumps(dict(plan_sha256=sha(OUT / 'plan.json'), games=len(originals))), flush=True)


@contextmanager
def lease():
    owner = 'astra-' + NAME
    path = ROOT / 'chatroom/cores.json'
    def change(take):
        with open('/tmp/iamavirus-cores-json.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = read(path)
            if take:
                require(not any(6 in r['cores'] for r in state['allocation']), 'core 6 reserved')
                state['allocation'].append(dict(owner=owner, cores=[6], pid=os.getpid(), at=now(),
                                                purpose='bounded metadata retrieval and JSON comparison'))
            else:
                state['allocation'] = [r for r in state['allocation'] if not (r['owner'] == owner and r.get('pid') == os.getpid())]
            state['updated'] = now()
            update(path, state)
    change(True)
    try:
        yield
    finally:
        change(False)


def run():
    plan = read(OUT / 'plan.json')
    for path, expected in plan['dependencies'].items():
        require(sha(path) == expected, 'dependency changed: ' + path)
    sources = read(STORE / 'sources.json')
    for source in sources:
        require(sha(source['original_path']) == source['sha256'], 'frozen replay changed')
    client = ApiClient(min_interval=plan['min_request_interval_seconds'], timeout=plan['timeout_seconds'])
    started = time.monotonic()
    state = dict(at=now(), status='running', pid=os.getpid(), completed=0, accepted=0,
                 requests=0, plan_sha256=sha(OUT / 'plan.json'))
    save(OUT / 'execution.json', state)
    def timeout(*_):
        raise TimeoutError('metadata collection reached original wall cap')
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(plan['wall_seconds'])
    receipts, supplemental, total_bytes = [], [], 0
    reason = 'all planned IDs processed'
    try:
        with lease(), (STORE / 'receipts.jsonl').open('x') as journal:
            for source in sources:
                game = source['row']['id']
                receipt = dict(id=game, original_sha256=source['sha256'])
                try:
                    require(client.requests_made + 5 <= plan['max_http_attempts'], 'HTTP request budget exhausted')
                    data, fetch = client.get_bytes('/api/games/' + game)
                    require(len(data) <= plan['max_response_bytes'], 'response byte cap')
                    total_bytes += len(data)
                    require(total_bytes <= plan['max_total_response_bytes'], 'total response byte cap')
                    response = STORE / 'responses' / (game + '.json')
                    with response.open('xb') as stream:
                        stream.write(data)
                    receipt.update(fetch=fetch.__dict__, response_path=str(response), response_bytes=len(data))
                    replay = json.loads(data)
                    metadata = identity(source['row'], read(source['original_path']), replay)
                    item = dict(id=game, original_sha256=source['sha256'], moves_sha256=source['row']['moves_sha256'],
                                response_sha256=fetch.sha256, metadata=metadata)
                    supplemental.append(item)
                    receipt.update(status='accepted', metadata=metadata,
                                   name_matches={s: replay[s] == source['row'][s] for s in ('white', 'black')})
                except ApiError as error:
                    receipt.update(status='unavailable', http_status=error.status, error=str(error))
                except (ValueError, KeyError, TypeError) as error:
                    receipt.update(status='rejected', error=repr(error))
                receipts.append(receipt)
                journal.write(json.dumps(receipt, allow_nan=False) + '\n')
                journal.flush()
                state.update(completed=len(receipts), accepted=len(supplemental), requests=client.requests_made)
                update(OUT / 'execution.json', state)
                if len(receipts) <= 3 or len(receipts) % 20 == 0:
                    print(json.dumps(dict(game=game, **{k: state[k] for k in ('completed', 'accepted', 'requests')})), flush=True)
                if len(receipts) == plan['pilot_games'] and not supplemental:
                    reason = 'no verified coverage in the fixed first-three pilot'
                    break
                if len(receipts) >= 3 and all(r['status'] != 'accepted' for r in receipts[-3:]):
                    reason = 'three consecutive unavailable or rejected sources'
                    break
            for source in sources:
                require(sha(source['canonical_path']) == source['sha256'], 'canonical source changed during run')
            require(sha(SNAPSHOT) == plan['dependencies'][str(SNAPSHOT)], 'source snapshot changed')
            save(STORE / 'supplement.json', supplemental)
            result = dict(at=now(), planned=len(sources), processed=len(receipts), recovered=len(supplemental),
                          remaining=len(sources) - len(supplemental), stop_reason=reason,
                          counts=dict(Counter(r['status'] for r in receipts)), requests=client.requests_made,
                          response_bytes=total_bytes, elapsed_seconds=time.monotonic() - started,
                          recovered_date_min=min((r['metadata']['createdAt'] for r in supplemental), default=None),
                          recovered_date_max=max((r['metadata']['createdAt'] for r in supplemental), default=None),
                          hashes={str(p): sha(p) for p in (OUT / 'plan.json', STORE / 'sources.json',
                                                           STORE / 'receipts.jsonl', STORE / 'supplement.json')},
                          scope=plan['scope'])
            save(OUT / 'result.json', result)
            state.update(status='completed', ended_at=now(), elapsed_seconds=result['elapsed_seconds'])
            update(OUT / 'execution.json', state)
            print(json.dumps(result), flush=True)
    except BaseException as error:
        state.update(status='failed', ended_at=now(), error=repr(error), elapsed_seconds=time.monotonic() - started)
        update(OUT / 'execution.json', state)
        raise
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    {'prepare': prepare, 'run': run}[sys.argv[1]]()
