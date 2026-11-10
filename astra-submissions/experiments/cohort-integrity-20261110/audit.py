"""Independent295 data-integrity audit. No collector helpers, models or NLL.

Uses exact RFC3339 nanoseconds to verify the existing chronological contract.
Does not modify eligibility, choose another cohort, or alter a running job.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import urllib.parse

ROOT=Path(__file__).resolve().parents[3]
DEFAULT=ROOT/'astra-submissions/analysis/prospective-full-prior-20261110'
OWN='a2c35173659545c99752376a70418438'
IMMUTABLE=('id','createdAt','result','plies','white','black','whitePlayerId','blackPlayerId','whiteVersion','blackVersion')
EPOCH=datetime(1970,1,1,tzinfo=timezone.utc)


def stamp_ns(text):
    m=re.fullmatch(r'(\d{4}-\d\d-\d\d[Tt]\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?([Zz]|[+-]\d\d:\d\d)',text)
    assert m, 'unsupported timestamp: '+repr(text)
    prefix,frac,offset=m.groups()
    base=datetime.fromisoformat(prefix.upper()+('+00:00' if offset.upper()=='Z' else offset))
    delta=base.astimezone(timezone.utc)-EPOCH
    return (delta.days*86400+delta.seconds)*10**9+int((frac or '').ljust(9,'0'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot(archive,index,count,cutoff):
    rows=[];hashes={};previous_cursor=None;previous_time=None;ids=set()
    paths=[archive/f'page-{index:03d}-{i:02d}.json' for i in range(count)]
    assert count>0
    for i,path in enumerate(paths):
        raw=path.read_bytes();record=json.loads(raw);page=record['page']
        hashes[path.name]=hashlib.sha256(raw).hexdigest()
        assert page['sort']=='played' and page['order']=='desc'
        url=urllib.parse.urlparse(record['fetch']['url']);query=urllib.parse.parse_qs(url.query)
        assert url.scheme=='https' and url.netloc=='6s890.lids.mit.edu' and url.path=='/api/games'
        assert query.get('sort')==['played'] and query.get('order')==['desc'] and query.get('limit')==['100']
        assert set(query)<= {'sort','order','limit','cursor'}
        assert query.get('cursor')==([previous_cursor] if i else None)
        for row in page['games']:
            assert re.fullmatch('[a-z0-9]{8}',row['id']) and row['id'] not in ids
            assert row['result'] in ('1-0','0-1','1/2-1/2')
            assert type(row['plies']) is int and row['plies']>=0
            instant=stamp_ns(row['createdAt'])
            assert previous_time is None or instant<=previous_time, 'snapshot not ordered at nanosecond precision'
            previous_time=instant;ids.add(row['id']);rows.append(row)
        previous_cursor=page['nextCursor']
        if i+1<count:
            assert previous_cursor is not None
    assert not previous_cursor or any(stamp_ns(r['createdAt'])<stamp_ns(cutoff) for r in page['games']), 'snapshot never reached cutoff'
    return rows,hashes


def candidates(rows,plan):
    low,high=stamp_ns(plan['cutoff']),stamp_ns(plan['data_deadline'])
    teams=set(plan['teams'])
    relevant=[r for r in rows if low<=stamp_ns(r['createdAt'])<=high
              and any(r.get(c+'PlayerId') in teams for c in ('white','black'))]
    return sorted(relevant,key=lambda r:(stamp_ns(r['createdAt']),r['id']))


def reconstruct(row,replay,digest,denied,teams):
    for key in IMMUTABLE:
        if key!='plies':assert replay.get(key)==row.get(key), 'source/listing mismatch: '+key
    frames=replay['frames'];assert len(frames)==row['plies']+1
    if replay.get('rulesVersion')!='fow-v1':return None,'not fow-v1'
    if row['plies']<4:return None,'fewer than four plies'
    moves=[frame['move'] for frame in frames[1:]]
    assert all(isinstance(m,str) and re.fullmatch('[a-h][1-8][a-h][1-8][qrbn]?',m) for m in moves)
    signature=hashlib.sha256(' '.join(moves).encode()).hexdigest()
    if signature in denied:return None,'whole-sequence duplicate'
    plies=[i for i in range(row['plies']) if replay.get(('white','black')[i%2]+'PlayerId') in teams]
    assert plies
    game=dict(game=row['id'],split='future',created_at=row['createdAt'],white=replay['white'],black=replay['black'],
              white_id=replay.get('whitePlayerId'),black_id=replay.get('blackPlayerId'),
              white_version=replay.get('whiteVersion'),black_version=replay.get('blackVersion'),
              selected_plies=plies,moves=moves,sequence_sha256=signature,replay_sha256=digest,frames=len(frames))
    return game,None


def audit(folder,*,require_sealed=False):
    plan=json.loads((folder/'plan.json').read_text());state=json.loads((folder/'execution.json').read_text())
    assert state['plan_sha256']==sha(folder/'plan.json')
    assert state['ticks']>=1,'no completed tick yet; poll the original live handle'
    archive=Path(plan['archive']);index=state['ticks']-1
    tick_path=archive/f'tick-{index:03d}.json';tick=json.loads(tick_path.read_text())
    rows,page_hashes=snapshot(archive,index,tick['pages'],plan['cutoff'])
    relevant=candidates(rows,plan)
    assert len(relevant)==tick['candidates']
    # Check precision against the frozen collector's actual datetime behavior
    # without importing its implementation or changing its choice.
    lossy=sorted(relevant,key=lambda r:(datetime.fromisoformat(r['createdAt'].replace('Z','+00:00')),r['id']))
    assert [r['id'] for r in relevant]==[r['id'] for r in lossy], 'microsecond precision changed actual candidate order; do not score'
    previous=json.loads(Path(plan['previous_plan']).read_text())
    denied={g['sequence_sha256'] for g in previous['games']};old_count=len(denied)
    accepted=[];expected_decisions=[];sources={}
    assert len(tick['decisions'])<=len(relevant)
    for row,decision in zip(relevant,tick['decisions']):
        assert decision['game']==row['id'] and decision['created_at']==row['createdAt']
        path=archive/'games'/row['id']/'replay.json';raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        fetch=json.loads(path.with_name('fetch.json').read_text());assert fetch['sha256']==digest and decision['source']==fetch
        sources[row['id']]=digest
        game,reason=reconstruct(row,json.loads(raw),digest,denied,set(plan['teams']))
        assert decision['eligible']==(game is not None) and decision['exclusion']==reason
        if game is not None:
            denied.add(game['sequence_sha256']);accepted.append(game)
        expected_decisions.append(decision)
        assert len(accepted)<=plan['games'],'collector exceeded prescribed cohort'
        if len(accepted)==plan['games']:
            assert len(expected_decisions)==len(tick['decisions']),'collector continued beyond first cohort'
    assert len(accepted)==tick['eligible']
    if tick['pending'] is not None:
        pos=len(tick['decisions']);assert pos<len(relevant)
        row=relevant[pos]
        assert tick['pending']['game']==row['id'] and any(row.get(c+'PlayerId')==OWN for c in ('white','black'))
    else:
        assert len(accepted)==plan['games'] or len(tick['decisions'])==len(relevant),'silently skipped unprocessed earlier games'
    # A cohort file can be visible briefly before its writer closes it. The
    # collector publishes terminal state only after both copies are complete.
    sealed=state['status']=='complete' and state.get('phase')=='sealed'
    if sealed:assert (folder/'cohort.json').is_file()
    if require_sealed:assert sealed and state['status']=='complete','cohort not sealed; do not score'
    if sealed:
        cohort=json.loads((folder/'cohort.json').read_text())
        assert len(accepted)==plan['games'] and cohort['games']==accepted
        assert cohort['exclusions']==expected_decisions and cohort['collection_tick']==index
        assert cohort['plan_sha256']==sha(folder/'plan.json')
        assert cohort['no_models_or_predictions_opened']
    # Historical fields may not mutate when current versions/staff labels do.
    known={r['id']:r for r in rows};overlap=0
    for older in sorted(archive.glob('page-*.json')):
        if older.name in page_hashes:continue
        older_index=int(older.name.split('-')[1])
        if older_index>=index:continue
        for row in json.loads(older.read_text())['page']['games']:
            if row['id'] in known:
                assert all(row.get(k)==known[row['id']].get(k) for k in IMMUTABLE),'completed historical row changed'
                overlap+=1
    return dict(at=datetime.now(timezone.utc).isoformat(),passed=True,scope='Independent source/chronology integrity only; no probability, NLL or playing-strength evidence.',
                plan_sha256=sha(folder/'plan.json'),tick=index,page_hashes=page_hashes,tick_sha256=sha(tick_path),
                snapshot_rows=len(rows),reference_candidates=len(relevant),verified_eligible=len(accepted),
                complete_cohort_verified=sealed,prior_sequences_excluded=old_count,
                exact_nanosecond_order_verified=True,actual_microsecond_order_agrees=True,
                historical_overlap_rows_checked=overlap,pending=tick['pending'],source_sha256=sources,
                no_models_or_predictions_read=True,production_score_absent=not(folder/'result.json').exists(),
                rules_or_board_observations_revalidated=False,
                limitation='Independent rules/observation and scalar-likelihood audits remain separate requirements. Does not certify the collector for all possible timestamp collisions.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder',type=Path,default=DEFAULT)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--require-sealed',action='store_true')
    args=parser.parse_args();result=audit(args.folder,require_sealed=args.require_sealed)
    with args.out.open('x') as handle:json.dump(result,handle,indent=2);handle.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('page_hashes','source_sha256')},indent=2))


if __name__=='__main__':main()
