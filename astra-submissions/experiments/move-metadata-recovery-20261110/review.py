"""Independent source-page -> metadata-store verification; never scores a model."""
from collections import Counter
from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
from urllib.parse import parse_qs,urlsplit

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'astra-submissions/analysis/move-metadata-recovery-20261110'
KEYS=('id','createdAt','white','black','whitePlayerId','blackPlayerId','whiteVersion','blackVersion','result','reason','plies')


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def instant(value):
    # Independent integer nanoseconds parser, not collector stamp().
    match=re.fullmatch(r'(.{19})(?:\.(\d{1,9}))?([Zz]|[+-]\d\d:\d\d)',value)
    assert match
    main,fraction,zone=match.groups()
    moment=datetime.fromisoformat(main+('+00:00' if zone.upper()=='Z' else zone))
    delta=moment.astimezone(timezone.utc)-datetime(1970,1,1,tzinfo=timezone.utc)
    return (delta.days*86400+delta.seconds)*1_000_000_000+int((fraction or '0').ljust(9,'0'))


def main():
    plan=json.loads((OUT/'plan.json').read_text());result=json.loads((OUT/'result.json').read_text())
    assert result['status'] in ('complete_all_targets','complete_listing_window','partial_page_bound')
    for path,value in plan['dependencies'].items():assert digest(path)==value,path
    store=Path(plan['store']);source=sqlite3.connect(Path(plan['snapshot']).resolve().as_uri()+'?mode=ro',uri=True)
    assert source.execute('pragma integrity_check').fetchone()[0]=='ok'
    targets={}
    for gid,movehash,text in source.execute('select game_id,moves_sha256,moves from moves'):
        assert gid not in targets and re.fullmatch('[a-z0-9]{8}',gid)
        assert hashlib.sha256(text.encode()).hexdigest()==movehash
        moves=text.split();assert ' '.join(moves)==text
        assert all(re.fullmatch('[a-h][1-8][a-h][1-8][qrbn]?',m) for m in moves)
        targets[gid]=(len(moves),movehash)
    assert len(targets)==plan['target_rows']
    known={row['game']:row for row in json.loads(Path(plan['known_plan']).read_text())['games']}
    receipts=json.loads((store/'page-receipts.json').read_text());attempts=json.loads((store/'attempts.json').read_text())
    assert len(receipts)<=plan['page_cap'] and len(attempts)==result['requests']<=plan['request_cap']
    gaps=[b['monotonic']-a['monotonic'] for a,b in zip(attempts,attempts[1:])]
    assert all(gap>=5.99 for gap in gaps),'pacing contract'
    cursor=None;pass_no=0;previous=None;seen=set();expected={};source_indices={};page_count=0;earliest=None;latest=None;overlap=0
    low,high=instant(plan['since']),instant(plan['before'])
    for position,receipt in enumerate(receipts):
        assert receipt['index']==position
        if receipt.get('cursor_restart'):
            assert pass_no==0 and cursor is not None and receipt['pass_no']==1
            assert 'HTTP 400' in receipt['error'];pass_no=1;cursor=None;previous=None;seen=set();continue
        assert receipt['pass_no']==pass_no and receipt['cursor_in']==cursor
        path=store/'pages'/receipt['file'];assert path.name==f'page-{position:04d}.json.gz'
        assert digest(path)==receipt['gzip_sha256']
        raw=gzip.decompress(path.read_bytes());assert len(raw)<=plan['response_bytes_cap']
        assert hashlib.sha256(raw).hexdigest()==receipt['raw_sha256']==receipt['fetch']['sha256']
        fetch=receipt['fetch'];url=urlsplit(fetch['url'])
        assert url.scheme=='https' and url.netloc=='6s890.lids.mit.edu' and url.path=='/api/games'
        query={'sort':['played'],'order':['desc'],'limit':['100']}
        if cursor is not None:query['cursor']=[cursor]
        assert parse_qs(url.query)==query and fetch['status']==200 and 1<=fetch['attempts']<=5
        data=json.loads(raw);assert data['sort']=='played' and data['order']=='desc' and len(data['games'])<=100
        for item in data['games']:
            at=instant(item['createdAt']);assert previous is None or at<=previous
            assert item['id'] not in seen;seen.add(item['id']);previous=at
            if item['id'] not in targets or not low<=at<high:continue
            row={key:item[key] for key in KEYS};gid=row['id']
            assert type(row['plies']) is int and row['plies']==targets[gid][0]
            assert row['result'] in ('1-0','0-1','1/2-1/2') and isinstance(row['reason'],str)
            for side in ('white','black'):
                assert isinstance(row[side],str) and row[side]
                assert row[side+'PlayerId'] is None or isinstance(row[side+'PlayerId'],str)
                version=row[side+'Version'];assert version is None or type(version) is int and version>=0
            if gid in expected:assert expected[gid]==row
            else:
                expected[gid]=row;source_indices[gid]=position
                earliest=at if earliest is None else min(earliest,at);latest=at if latest is None else max(latest,at)
                if gid in known:
                    before=known[gid];assert at==instant(before['created_at']) and row['plies']==before['frames']-1
                    assert targets[gid][1]==before['sequence_sha256']
                    for side in ('white','black'):assert row[side]==before[side] and row[side+'Version']==before[side+'_version']
                    overlap+=1
        cursor=data['nextCursor'];page_count+=1
    db=sqlite3.connect((store/'metadata.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    assert db.execute('pragma integrity_check').fetchone()[0]=='ok'
    actual={gid:(json.loads(text),index) for gid,text,index in db.execute('select game_id,json,source_page from metadata')}
    assert actual=={gid:(row,source_indices[gid]) for gid,row in expected.items()}
    assert result['matched']==len(actual) and result['unmatched']==len(targets)-len(actual)
    assert result['known_metadata_overlaps']==overlap and result['pages']==page_count and result['cursor_restarts']==pass_no
    for path,key in [(plan['snapshot'],'snapshot_sha256'),(store/'metadata.sqlite','metadata_sha256'),(store/'page-receipts.json','page_receipts_sha256')]:assert digest(path)==result[key]
    assert sum(p.stat().st_size for p in store.rglob('*') if p.is_file())<=plan['max_bytes']
    if result['status']=='complete_all_targets':assert len(actual)==len(targets)
    elif result['status']=='complete_listing_window':assert cursor is None or previous<low
    else:assert len(receipts)==plan['page_cap']
    assert result['training_ready'] is result['clocks_recovered'] is result['recorded_views_recovered'] is result['original_replay_hash_attestation'] is False
    dates=Counter(row['createdAt'][:10] for row in expected.values())
    panels=Counter((row[side],row[side+'Version']) for row in expected.values() for side in ('white','black'))
    report=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,dependencies=len(plan['dependencies']),source_move_hashes=len(targets),matched=len(actual),unmatched=len(targets)-len(actual),raw_pages=page_count,requests=len(attempts),cursor_restarts=pass_no,minimum_attempt_spacing_seconds=min(gaps) if gaps else None,known_metadata_overlaps=overlap,date_counts=dict(sorted(dates.items())),team_version_seats=[dict(team=name,version=version,seats=count) for (name,version),count in panels.most_common()],training_ready=False,limitations='Listing identity and exact ply count, plus known metadata/hash overlap verified. No original raw replay checksum, recorded observations/clocks, newly replayed legality, untouched holdout, model update or strength evidence.')
    (OUT/'independent-review.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('date_counts','team_version_seats')},indent=2))

if __name__=='__main__':main()
