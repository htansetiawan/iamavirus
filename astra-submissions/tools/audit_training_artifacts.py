"""Read-only integrity, coverage and split audit of existing training exports.

No regeneration, repair, fitting or replay-rule execution is performed.
"""
from collections import Counter,defaultdict
from contextlib import contextmanager
from datetime import datetime,timezone
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from learning.dataset import dataset_source_rows
from learning import features,ingest

NAME='training-artifact-readiness-20261111'
OUT=ROOT/'astra-submissions/analysis'/NAME
PRIVATE=ROOT/'data/astra-spool'/NAME
RAW=ROOT/'data/raw'
EPISODES=ROOT/'data/manifests/arena-latest.json'
MOVE_POINTER=ROOT/'data/derived/moves/arena-latest-current.json'

def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(p,d):
    with p.open('x') as stream:stream.write(json.dumps(d,indent=2,allow_nan=False)+'\n')
def update(p,d):
    temporary=p.with_suffix(p.suffix+'.tmp');temporary.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');temporary.replace(p)

@contextmanager
def lease():
    owner='astra-'+NAME;path=ROOT/'chatroom/cores.json'
    def change(take):
        with open('/tmp/iamavirus-cores-json.lock','a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);state=read(path)
            if take:
                assert not any(6 in r['cores'] for r in state['allocation'])
                state['allocation'].append(dict(owner=owner,cores=[6],pid=os.getpid(),at=now(),purpose='read-only training-artifact audit'))
            else:state['allocation']=[r for r in state['allocation'] if not(r['owner']==owner and r.get('pid')==os.getpid())]
            state['updated']=now();update(path,state)
    change(True)
    try:yield
    finally:change(False)

def prepare():
    OUT.mkdir(exist_ok=False);PRIVATE.mkdir(exist_ok=False)
    with (RAW/'.writer.lock').open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_SH);rows,journal=dataset_source_rows(RAW/'accepted.jsonl')
    with (PRIVATE/'journal.jsonl').open('x') as stream:
        for row in rows:stream.write(json.dumps(row,separators=(',',':'))+'\n')
    for name,path in [('episodes.json',EPISODES),('move-pointer.json',MOVE_POINTER)]:
        with (PRIVATE/name).open('xb') as stream:stream.write(path.read_bytes())
    episodes=read(PRIVATE/'episodes.json');pointer=read(PRIVATE/'move-pointer.json')
    generation=(MOVE_POINTER.parent/pointer['generation']).resolve(strict=True)
    assert generation.is_relative_to(MOVE_POINTER.parent.resolve())
    assert sha(generation/'manifest.json')==pointer['manifest_sha256']
    with (PRIVATE/'moves.json').open('xb') as stream:stream.write((generation/'manifest.json').read_bytes())
    moves=read(PRIVATE/'moves.json');assert moves['complete']
    files=[]
    for split,path in episodes['shards'].items():
        p=Path(path);stat=p.stat();files.append(dict(kind='episodes',split=split,path=str(p),bytes=stat.st_size,sha256=episodes['shard_sha256'][split],device=stat.st_dev,inode=stat.st_ino))
    for name,meta in moves['files'].items():
        p=generation/name;stat=p.stat();assert stat.st_size==meta['bytes'];files.append(dict(kind='moves',name=name,path=str(p),**meta,device=stat.st_dev,inode=stat.st_ino))
    dependencies=[Path(__file__),ROOT/'learning/dataset.py',ROOT/'learning/histories.py',ROOT/'learning/features.py',ROOT/'learning/ingest.py',ROOT/'astra-submissions/tools/export_move_cache.py',*PRIVATE.glob('*.json'),PRIVATE/'journal.jsonl']
    plan=dict(at=now(),core=6,wall_seconds=900,max_compressed_read_bytes=2*1024**3,max_decompressed_bytes=64*1024**3,max_line_bytes=64*1024**2,max_episode_rows=1000000,
        journal=journal,current_unique_games=len(rows),undated_current_games=sum(not r.get('createdAt') for r in rows),files=files,
        current_versions=dict(feature_version=features.FEATURE_VERSION,action_version=features.ACTION_VERSION,rules_fingerprint=ingest.RULES_FINGERPRINT),
        dependencies={str(p):sha(p) for p in dependencies},
        antecedents='314 episode journal deduplication; 281/328 known ID-based move-export trajectory overlap; 336 independently grouped reconstructed cache. Not a new split design or candidate.',
        scope='Read existing immutable exports completely for hashes, gzip/JSON, metadata/count/ID coverage and whole-trajectory split overlap. No full rules/feature/actor-target-semantic recertification, new export, split reassignment, fit, GPU, game, package, commit, push or deployment.')
    save(OUT/'plan.json',plan);print(json.dumps(dict(plan_sha256=sha(OUT/'plan.json'),current_unique_games=len(rows),source_bytes=sum(f['bytes'] for f in files),episode_created_at=episodes['created_at'],move_created_at=moves['at'])),flush=True)

class Reader:
    """Hash the compressed bytes consumed by gzip in the same read pass."""
    def __init__(self,stream,budget,cap):self.stream=stream;self.digest=hashlib.sha256();self.bytes=0;self.budget=budget;self.cap=cap
    def read(self,size=-1):
        data=self.stream.read(size);self.digest.update(data);self.bytes+=len(data);self.budget[0]+=len(data)
        assert self.budget[0]<=self.cap,'compressed read budget exceeded'
        return data
    def tell(self):return self.bytes
    def seekable(self):return False

def run():
    plan=read(OUT/'plan.json')
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    state=dict(at=now(),status='running',completed_files=0,episode_rows=0,plan_sha256=sha(OUT/'plan.json'),pid=os.getpid());save(OUT/'execution.json',state)
    def timeout(*_):raise TimeoutError('training-artifact audit reached original wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds']);started=time.monotonic()
    raw={r['id']:r['moves_sha256'] for r in (json.loads(line) for line in (PRIVATE/'journal.jsonl').open())}
    episodes=read(PRIVATE/'episodes.json');moves=read(PRIVATE/'moves.json')
    seen={};sequence_splits=defaultdict(set);episode_stats={};receipts=[];budget=[0];decoded=0
    try:
        with (PRIVATE/'episode-index.jsonl').open('x') as index:
            for spec in sorted([s for s in plan['files'] if s['kind']=='episodes'],key=lambda r:r['bytes']):
                split=spec['split'];counts=Counter();missing_versions=Counter()
                with Path(spec['path']).open('rb') as stream:
                    tracked=Reader(stream,budget,plan['max_compressed_read_bytes'])
                    with gzip.GzipFile(fileobj=tracked,mode='rb') as zipped:
                        while True:
                            line=zipped.readline(plan['max_line_bytes']+1)
                            if not line:break
                            assert len(line)<=plan['max_line_bytes'] and line.endswith(b'\n')
                            decoded+=len(line);assert decoded<=plan['max_decompressed_bytes']
                            obj=json.loads(line);meta=obj['metadata'];actor=obj['actor'];targets=obj['targets'];game=meta['game_id'];side=actor['side']
                            assert meta['split']==split and side in (0,1) and game in raw
                            for key in ('feature_version','action_version','rules_fingerprint'):assert meta[key]==episodes[key]
                            n=len(actor['decision_event_indices'])
                            for key in ('own_actions','legal_actions','inferred_en_passant','castling_rights'):assert len(actor[key])==n
                            for key in ('boards','king_loss_by_action','demonstrated_actions','policy_valid','value_valid','belief_valid','danger_valid'):assert len(targets[key])==n
                            old=seen.get(game)
                            if old:
                                assert old[0]==split and not(old[1] & (1<<side)) and old[2]==meta['source_hash']
                                seen[game]=(split,old[1]|(1<<side),old[2])
                            else:seen[game]=(split,1<<side,meta['source_hash'])
                            sequence_splits[raw[game]].add(split)
                            counts['episodes']+=1;counts['decisions']+=n;counts['events']+=len(actor['observations']);counts['color_white' if side==0 else 'color_black']+=1
                            counts['outcome_'+meta['result']]+=1;counts['termination_'+meta['termination']]+=1
                            counts['value_valid_'+meta['termination']]+=sum(targets['value_valid'])
                            for key in ('played_version','opponent_version'):
                                if meta.get(key) is None:missing_versions[key]+=1
                            index.write(json.dumps(dict(id=game,split=split,side=side,moves_sha256=raw[game],source_hash=meta['source_hash']),separators=(',',':'))+'\n')
                            state['episode_rows']+=1;assert state['episode_rows']<=plan['max_episode_rows']
                            if counts['episodes']%10000==0:
                                update(OUT/'execution.json',state);print(json.dumps(dict(split=split,rows=counts['episodes'],total=state['episode_rows'])),flush=True)
                    assert tracked.bytes==spec['bytes'] and tracked.digest.hexdigest()==spec['sha256'],spec['path']
                actual=Path(spec['path']).stat();assert (actual.st_dev,actual.st_ino,actual.st_size)==(spec['device'],spec['inode'],spec['bytes'])
                expected=episodes['counts'][split]
                for key in ('episodes','decisions','events','color_white','color_black'):assert counts[key]==expected[key],(split,key,counts[key],expected[key])
                for key,value in expected.items():
                    if key=='games':assert counts['episodes']/2==value
                    elif key.startswith(('outcome_','termination_')):assert counts[key]/2==value
                episode_stats[split]=dict(counts=counts,missing_versions=missing_versions)
                receipts.append(dict(kind='episodes',split=split,bytes=tracked.bytes,sha256=tracked.digest.hexdigest(),rows=counts['episodes']))
                state['completed_files']+=1;update(OUT/'execution.json',state);print(json.dumps(receipts[-1]),flush=True)
        assert len(seen)==episodes['source_games'] and all(r[1]==3 for r in seen.values())
        episode_cross={h:sorted(s) for h,s in sequence_splits.items() if len(s)>1}
        move_files={s['name']:s for s in plan['files'] if s['kind']=='moves'}
        for name,spec in move_files.items():
            assert sha(spec['path'])==spec['sha256'],spec['path'];budget[0]+=spec['bytes'];assert budget[0]<=plan['max_compressed_read_bytes']
            state['completed_files']+=1;update(OUT/'execution.json',state)
        move_rows=[json.loads(line) for line in Path(move_files['games.jsonl']['path']).open()]
        move_by_id={r['id']:r for r in move_rows};assert len(move_rows)==len(move_by_id)==moves['selected_games']
        move_groups=defaultdict(set);seen_moves=set();move_counts=Counter()
        for row in move_rows:
            assert row['id'] in raw and row['moves_sha256']==raw[row['id']]
            want='test' if int(hashlib.sha1(row['id'].encode()).hexdigest(),16)%1000<moves['test_share']*1000 else 'train'
            assert row['split']==want;move_groups[row['moves_sha256']].add(want);move_counts[want]+=1
        for split in ('train','test'):
            with Path(move_files[split+'.txt']['path']).open() as stream:
                while True:
                    header=stream.readline()
                    if not header:break
                    text=stream.readline();tokens=header.split();assert tokens[0]=='game' and text.endswith('\n')
                    game=tokens[1];assert game not in seen_moves and move_by_id[game]['split']==split
                    assert hashlib.sha256(text.strip().encode()).hexdigest()==raw[game]
                    seen_moves.add(game)
            assert move_counts[split]==moves['counts'][split]
        assert seen_moves==set(move_by_id)
        cross={h:sorted(s) for h,s in move_groups.items() if len(s)>1}
        save(PRIVATE/'split-overlap.json',dict(episode_groups=episode_cross,move_groups=cross))
        new_ids=sorted(set(raw)-set(seen))
        with (PRIVATE/'not-in-episodes.txt').open('x') as stream:stream.write(''.join(x+'\n' for x in new_ids))
        for p,h in plan['dependencies'].items():assert sha(p)==h,p
        result=dict(at=now(),status='complete',plan_sha256=sha(OUT/'plan.json'),raw_games=len(raw),episode_generation=episodes['created_at'],episode_source_games=len(seen),raw_games_absent_from_episode_generation=len(new_ids),episode_rows=state['episode_rows'],episode_statistics=episode_stats,
            episode_distinct_trajectories=len(sequence_splits),episode_cross_split_trajectory_groups=len(episode_cross),episode_split_method=episodes['split_method'],episode_undated_source_games=episodes['undated_source_games'],
            episode_version_labels_match_current={k:episodes[k]==v for k,v in plan['current_versions'].items()},
            move_generation=moves['at'],move_source_games=len(move_rows),move_counts=move_counts,move_distinct_trajectories=len(move_groups),move_cross_split_trajectory_groups=len(cross),move_split_method=moves['split'],
            bytes_read=budget[0],episode_decompressed_bytes=decoded,receipts=receipts,index_sha256=sha(PRIVATE/'episode-index.jsonl'),
            scope=plan['scope'],limitations=['Integrity matches each saved generation, not a current full-corpus training export.',
                'Whole-trajectory leakage in legacy ID-split moves was already documented in 281/328; do not silently rewrite that used test set.',
                'All JSON and metadata dimensions are checked; board legality, target semantics, feature values and provenance of each original replay are not rewalked.',
                'No calibration, model-quality, playing-strength, hardware-health or next-daily-job claim.'])
        save(OUT/'result.json',result);state.update(status='complete',result_sha256=sha(OUT/'result.json'));print(json.dumps({k:result[k] for k in ('status','raw_games','episode_source_games','raw_games_absent_from_episode_generation','episode_rows','episode_cross_split_trajectory_groups','move_source_games','move_cross_split_trajectory_groups')},indent=2),flush=True)
    except BaseException as exc:state.update(status='failed',error=repr(exc));raise
    finally:
        signal.alarm(0);state.update(ended_at=now(),seconds=time.monotonic()-started);update(OUT/'execution.json',state)

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('prepare','run')
    with lease():globals()[sys.argv[1]]()
