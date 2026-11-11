"""Collect a bounded field snapshot on SSD while the external archive is offline."""

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis'/HERE.name
STORE = ROOT/'data/astra-spool'/HERE.name
TOOL = ROOT/'astra-submissions/tools/collect_recent.py'
VALIDATOR = HERE.parent/'last-only-pilot-20261110/build/native-validator.so'
sys.path[:0] = [str(ROOT/'astra-submissions/tools'), str(ROOT)]
from learning import api_client, _native


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path,value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value,indent=2)+'\n')


class SnapshotClient(api_client.ApiClient):
    def __init__(self, plan):
        super().__init__(min_interval=plan['min_interval'], timeout=20)
        self.request_limit = plan['request_limit']
        self.response_limit = plan['replay_bytes_cap']

    def _pace(self):
        if self.requests_made >= self.request_limit:
            raise RuntimeError('snapshot request bound reached')
        super()._pace()

    def get(self, path, params=None):
        if self.requests_made >= self.request_limit:
            raise RuntimeError('snapshot request bound reached')
        data, record = self.get_bytes(path, params)
        if len(data) > self.response_limit:
            raise RuntimeError('public response exceeds the snapshot byte bound')
        return json.loads(data), record.__dict__


def prepare():
    assert not OUT.exists() and not STORE.exists()
    OUT.mkdir()
    fresh = ROOT/'data/astra-spool/prospective-quiet-teacher-20261110'
    caches = [ROOT/'data/astra-spool/later-replay-window-20261111/games', fresh/'archive/games']
    # The sealed source archive path is authoritative.
    caches[1] = Path(read(fresh/'cohort.json')['source_archive'])/'games'
    assert all(path.is_dir() for path in caches)
    files = [Path(__file__),TOOL,VALIDATOR,ROOT/'astra-submissions/tools/monitor_arena.py',
             ROOT/'learning/ingest.py',ROOT/'learning/api_client.py',ROOT/'learning/rules.py',
             ROOT/'learning/_native.py']
    plan = dict(at=now(),limit=6000,request_limit=6500,min_interval=1.2,wall_seconds=10800,
                replay_bytes_cap=2*1024**2,raw_json_bytes_cap=4*1024**3,min_disk_free=8*1024**3,
                cores=[2,3],caches=[str(path) for path in caches],store=str(STORE),
                validator_sha256=sha(VALIDATOR),dependencies={str(path):sha(path) for path in files},
                selection='One newest-first fixed-cursor snapshot of 6000 completed games, all teams and outcomes.',
                purpose='Restore current all-team replay collection in an independent local store after the shared external raw archive failed. Original clocks and views retained; existing raw links and reports remain archival inputs.',
                scope='Public read-only collection and rules validation. No fit, test selection, history rebuild or deployment.')
    save(OUT/'plan.json',plan)
    print(json.dumps(dict(plan_sha256=sha(OUT/'plan.json'),dependencies=len(files),limit=6000)),flush=True)


@contextmanager
def lease(cores):
    path=ROOT/'chatroom/cores.json'
    owner='astra-'+HERE.name
    def update(take):
        with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            state=read(path)
            if take:
                assert all(not set(cores)&set(row['cores']) for row in state['allocation'])
                state['allocation'].append(dict(owner=owner,cores=cores,pid=os.getpid(),at=now(),purpose='bounded public field snapshot'))
            else:
                state['allocation']=[row for row in state['allocation'] if row['owner']!=owner]
            api_client.atomic_write(path,(json.dumps(dict(state,updated=now()),indent=2)+'\n').encode())
    update(True)
    try:
        yield
    finally:
        update(False)


def run():
    plan=read(OUT/'plan.json')
    assert not STORE.exists() and not (OUT/'execution.json').exists()
    assert all(sha(path)==digest for path,digest in plan['dependencies'].items())
    assert shutil.disk_usage(ROOT).free>=plan['min_disk_free']+plan['raw_json_bytes_cap']
    os.sched_setaffinity(0,set(plan['cores']))
    spec=importlib.util.spec_from_file_location('field_replay_collector',TOOL)
    collector=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    assert _native._library is None
    _native.ensure_built=lambda verbose=True: VALIDATOR
    collector.isolate_rules=lambda output: dict(library_sha256=sha(VALIDATOR),source='pinned independent C++ validator')
    client=SnapshotClient(plan)
    writes=dict(bytes=0)
    original_write=api_client.atomic_write

    def bounded_write(path,data):
        if Path(path).is_relative_to(STORE):
            old=Path(path).stat().st_size if Path(path).exists() else 0
            growth=max(0,len(data)-old)
            if writes['bytes']+growth>plan['raw_json_bytes_cap']:
                raise RuntimeError('local raw JSON byte bound reached')
            if shutil.disk_usage(ROOT).free<plan['min_disk_free']:
                raise RuntimeError('local SSD free-space bound reached')
            result=original_write(path,data)
            writes['bytes']+=growth
            return result
        return original_write(path,data)

    collector.Client=lambda: client
    api_client.atomic_write=bounded_write
    sys.argv=[str(TOOL),'--output',str(STORE),'--limit',str(plan['limit']),'--cache',plan['caches'][0]]
    for cache in plan['caches'][1:]:
        sys.argv.extend(['--extra-cache',cache])
    state=dict(at=now(),status='running',plan_sha256=sha(OUT/'plan.json'),pid=os.getpid())
    save(OUT/'execution.json',state)
    def timeout(*_):
        raise TimeoutError('field snapshot reached its wall limit')
    signal.signal(signal.SIGALRM,timeout)
    signal.signal(signal.SIGTERM,timeout)
    signal.alarm(plan['wall_seconds'])
    started=time.monotonic()
    try:
        with lease(plan['cores']):
            collector.main()
        report=read(STORE/'collection.json')
        assert report['state']=='complete' and report['completed']==plan['limit']
        result=dict(at=now(),games=report['completed'],accepted=report['accepted'],
                    quarantined=report['quarantined'],frames=report['frames_checked'],
                    unique_trajectories=report['unique_move_sequences'],outcomes=report['outcomes'],
                    sources=report['sources'],requests=client.requests_made,raw_json_bytes=writes['bytes'],
                    listing_sha256=sha(STORE/'listing.json'),validation_sha256=sha(STORE/'validation.jsonl'),
                    plan_sha256=state['plan_sha256'],collection_sha256=sha(STORE/'collection.json'),
                    scope=plan['scope'])
        save(OUT/'result.json',result)
        state.update(status='complete',result_sha256=sha(OUT/'result.json'))
        print(json.dumps(result),flush=True)
    except BaseException as exc:
        state.update(status='failed',error=repr(exc))
        raise
    finally:
        signal.alarm(0)
        api_client.atomic_write=original_write
        state.update(ended_at=now(),seconds=time.monotonic()-started,requests=client.requests_made,
                     raw_json_bytes=writes['bytes'])
        original_write(OUT/'execution.json',(json.dumps(state,indent=2)+'\n').encode())


if __name__=='__main__':
    {'prepare':prepare,'run':run}[sys.argv[1]]()
