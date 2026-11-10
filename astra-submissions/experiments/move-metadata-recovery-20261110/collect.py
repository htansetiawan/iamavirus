"""Join old cached IDs to paced public listing pages; no replay/model access."""
from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import signal
import sqlite3
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'astra-submissions/analysis/move-metadata-recovery-20261110'
sys.path.insert(0,str(ROOT))
from learning.api_client import ApiClient,ApiError,atomic_write

FIELDS=('id','createdAt','white','black','whitePlayerId','blackPlayerId','whiteVersion','blackVersion','result','reason','plies')


def now():return datetime.now(timezone.utc).isoformat()
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,value):atomic_write(Path(path),(json.dumps(value,indent=2,allow_nan=False)+'\n').encode())
def stamp(text):
    match=re.fullmatch(r'(\d{4}-\d\d-\d\d[Tt]\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?([Zz]|[+-]\d\d:\d\d)',text)
    assert match,'invalid RFC3339'
    base,fraction,zone=match.groups();time0=datetime.fromisoformat(base.upper()+('+00:00' if zone.upper()=='Z' else zone))
    epoch=datetime(1970,1,1,tzinfo=timezone.utc);delta=time0.astimezone(timezone.utc)-epoch
    return (delta.days*86400+delta.seconds)*10**9+int((fraction or '').ljust(9,'0'))


def normalized(row):
    result={k:row[k] for k in FIELDS}
    assert re.fullmatch('[a-z0-9]{8}',result['id']) and result['result'] in ('1-0','0-1','1/2-1/2')
    assert type(result['plies']) is int and result['plies']>=0;stamp(result['createdAt'])
    assert isinstance(result['reason'],str)
    for side in ('white','black'):
        assert isinstance(result[side],str) and result[side]
        assert result[side+'PlayerId'] is None or isinstance(result[side+'PlayerId'],str)
        assert result[side+'Version'] is None or (type(result[side+'Version']) is int and result[side+'Version']>=0)
    return result


def validate_join(row,target,known):
    assert row['plies']==target['plies'],'stable game ID has a different move count'
    if known:
        assert stamp(row['createdAt'])==stamp(known['created_at'])
        for side in ('white','black'):
            assert row[side]==known[side] and row[side+'Version']==known[side+'_version'],'known metadata mismatch'


class BoundedClient(ApiClient):
    def __init__(self,budget):super().__init__(min_interval=6.,timeout=30);self.budget=budget;self.attempts=[]
    def _pace(self):
        assert self.requests_made<self.budget,'metadata recovery request bound'
        super()._pace()
        self.attempts.append(dict(at=now(),monotonic=time.monotonic()))


def main():
    plan=json.loads((OUT/'plan.json').read_text())
    for path,expected in plan['dependencies'].items():assert sha(path)==expected,path
    assert not (OUT/'execution.json').exists()
    store=Path(plan['store']);pages=store/'pages';pages.mkdir(exist_ok=False)
    source=sqlite3.connect(Path(plan['snapshot']).resolve().as_uri()+'?mode=ro',uri=True)
    targets={gid:dict(sha256=digest,plies=count) for gid,digest,count in source.execute("select game_id,moves_sha256,length(moves)-length(replace(moves,' ',''))+1 from moves")}
    assert len(targets)==plan['target_rows']
    known={g['game']:g for g in json.loads(Path(plan['known_plan']).read_text())['games']}
    db=sqlite3.connect(store/'metadata.sqlite');db.execute('create table metadata(game_id text primary key, json text not null, source_page integer not null) without rowid');db.commit()
    client=BoundedClient(plan['request_cap']);started=time.monotonic();cursor=None;previous=None;seen=set();pass_no=0;receipts=[];matched=set();known_count=0
    state=dict(status='running',started_at=now(),pages=0,matched=0,requests=0,cursor_restarts=0,training_ready=False)
    save(OUT/'execution.json',state);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('three-hour metadata recovery bound')));signal.alarm(plan['wall_seconds'])
    try:
        for index in range(plan['page_cap']):
            params=dict(sort='played',order='desc',limit=100)
            if cursor is not None:params['cursor']=cursor
            try:raw,fetch=client.get_bytes('/api/games',params)
            except ApiError as exc:
                if exc.status==400 and cursor is not None and pass_no==0:
                    pass_no=1;cursor=None;previous=None;seen=set();state['cursor_restarts']=1
                    receipts.append(dict(index=index,cursor_restart=True,error=str(exc),pass_no=pass_no));continue
                raise
            assert len(raw)<=plan['response_bytes_cap'];page=json.loads(raw)
            assert page['sort']=='played' and page['order']=='desc'
            assert isinstance(page['games'],list) and len(page['games'])<=100
            assert page['nextCursor'] is None or (isinstance(page['nextCursor'],str) and 0<len(page['nextCursor'])<=100)
            file=pages/f'page-{index:04d}.json.gz'
            with file.open('xb') as stream:
                with gzip.GzipFile(filename='',fileobj=stream,mode='wb',mtime=0) as zipped:zipped.write(raw)
            receipt=dict(index=index,file=file.name,raw_sha256=hashlib.sha256(raw).hexdigest(),gzip_sha256=sha(file),pass_no=pass_no,cursor_in=cursor,fetch=fetch.__dict__)
            receipts.append(receipt);oldest=None
            for item in page['games']:
                row=normalized(item);at=stamp(row['createdAt']);assert previous is None or at<=previous
                assert row['id'] not in seen,'duplicate within a fixed cursor snapshot';seen.add(row['id']);previous=oldest=at
                if row['id'] not in targets or not (stamp(plan['since'])<=at<stamp(plan['before'])):continue
                validate_join(row,targets[row['id']],known.get(row['id']))
                text=json.dumps(row,sort_keys=True,ensure_ascii=False);old=db.execute('select json from metadata where game_id=?',(row['id'],)).fetchone()
                if old:assert old[0]==text,'immutable listing changed during recovery'
                else:
                    db.execute('insert into metadata values(?,?,?)',(row['id'],text,index));matched.add(row['id']);known_count+=row['id'] in known
            db.commit();cursor=page['nextCursor']
            state.update(pages=sum('file' in r for r in receipts),matched=len(matched),requests=client.requests_made,known_overlap=known_count,updated_at=now())
            save(OUT/'execution.json',state)
            assert sum(p.stat().st_size for p in store.rglob('*') if p.is_file())<=plan['max_bytes'],'bounded private working storage'
            if index%25==0:print(json.dumps(state),flush=True)
            if len(matched)==len(targets):state['status']='complete_all_targets';break
            if not cursor or (oldest is not None and oldest<stamp(plan['since'])):
                state['status']='complete_listing_window';break
        else:state['status']='partial_page_bound'
        db.close()
        save(store/'page-receipts.json',receipts)
        save(store/'attempts.json',client.attempts)
        result=dict(at=now(),status=state['status'],matched=len(matched),targets=len(targets),unmatched=len(targets)-len(matched),
            known_metadata_overlaps=known_count,requests=client.requests_made,pages=state['pages'],cursor_restarts=state['cursor_restarts'],
            snapshot_sha256=sha(plan['snapshot']),metadata_sha256=sha(store/'metadata.sqlite'),page_receipts_sha256=sha(store/'page-receipts.json'),
            clocks_recovered=False,recorded_views_recovered=False,original_replay_hash_attestation=False,training_ready=False,
            scope='Public completed-game metadata joined by stable ID and exact ply count to a pinned old move snapshot. Per-row cache move hashes checked at preparation; original raw replay hashes/views/clocks are not reconstructed. No models, new states, canonical accepted-store writes or326changes. Partial or unmatched IDs remain explicit.')
        save(OUT/'result.json',result);print(json.dumps(result,indent=2),flush=True)
    except BaseException as exc:
        db.rollback();matched={g for (g,) in db.execute('select game_id from metadata')}
        state.update(status='failed',error=repr(exc));db.close();save(store/'page-receipts.json',receipts);save(store/'attempts.json',client.attempts);raise
    finally:
        state.update(ended_at=now(),seconds=time.monotonic()-started,requests=client.requests_made,matched=len(matched))
        save(OUT/'execution.json',state)


if __name__=='__main__':main()
