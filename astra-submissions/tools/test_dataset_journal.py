"""Dataset generations count distinct accepted games and preserve old readers."""
import gzip
import fcntl
import hashlib
import json
from pathlib import Path

import pytest

from learning import dataset, histories, ingest


def source(tmp_path, duplicate=False):
    raw=tmp_path/'raw'
    for game,moves in [('test0001',['e2e4','f7f6','d1h5','g7g5']),
                       ('test0002',['e2e4','f7f5','d1h5','a7a6'])]:
        folder=raw/'games'/game;folder.mkdir(parents=True)
        replay=histories.replay_from_moves(game,moves,'1-0','King capturable')
        assert not ingest.validate_replay(replay)[1], 'fixture must finish under course rules'
        (folder/'replay.json').write_text(json.dumps(replay))
    rows=[dict(id='test0001',moves_sha256='first',createdAt='2026-10-25T12:00:00Z'),
          dict(id='test0002',moves_sha256='second',createdAt='2026-10-25T13:00:00Z')]
    entries=[rows[0],dict(rows[0],ignored_new_field='forward compatible'),rows[1]] if duplicate else rows
    (raw/'accepted.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in entries))
    return raw,rows


def episode_rows(manifest):
    rows=[]
    for path in manifest['shards'].values():
        with gzip.open(path,'rt') as handle: rows.extend(json.loads(line) for line in handle)
    return rows


def test_legacy_duplicate_has_same_examples_and_weight_as_unique_journal(tmp_path):
    raw,rows=source(tmp_path)
    clean=dataset.build_dataset(raw,tmp_path/'published/latest.json','latest')
    with (raw/'accepted.jsonl').open('a') as handle: handle.write(json.dumps(rows[0])+'\n')
    duplicated=dataset.build_dataset(raw,tmp_path/'published/latest.json','latest')
    assert duplicated['source_games']==2
    assert sum(s.get('episodes',0) for s in duplicated['counts'].values())==4
    assert episode_rows(duplicated)==episode_rows(clean)
    assert duplicated['content_sha256']==clean['content_sha256']
    journal=duplicated['source_journal']
    assert journal['accepted_lines']==3 and journal['duplicate_lines']==1
    assert journal['unique_games']==journal['selected_games']==2
    assert journal['sha256']==hashlib.sha256((raw/'accepted.jsonl').read_bytes()).hexdigest()


def test_limit_applies_after_distinct_ids_and_ignores_unconsumed_fields(tmp_path):
    raw,_=source(tmp_path,duplicate=True)
    rows,receipt=dataset.dataset_source_rows(raw/'accepted.jsonl',limit=2)
    assert [r['id'] for r in rows]==['test0001','test0002']
    assert receipt['duplicate_lines']==1


@pytest.mark.parametrize('field,value',[('moves_sha256','changed'),('createdAt','2026-10-27T12:00:00Z')])
def test_conflicting_source_identity_preserves_manifest_and_shards(tmp_path,field,value):
    raw,rows=source(tmp_path)
    path=tmp_path/'published/latest.json'
    before=dataset.build_dataset(raw,path,'latest')
    manifest_bytes=path.read_bytes()
    shards={p:Path(p).read_bytes() for p in before['shards'].values()}
    generations=set(path.parent.joinpath('latest').iterdir())
    with (raw/'accepted.jsonl').open('a') as handle:handle.write(json.dumps(dict(rows[0],**{field:value}))+'\n')
    with pytest.raises(ValueError,match=f'conflicting accepted game test0001: {field}'):
        dataset.build_dataset(raw,path,'latest')
    assert path.read_bytes()==manifest_bytes
    assert all(Path(p).read_bytes()==data for p,data in shards.items())
    assert set(path.parent.joinpath('latest').iterdir())==generations


def test_partial_journal_tail_is_not_published(tmp_path):
    raw,_=source(tmp_path);path=tmp_path/'published/latest.json'
    before=dataset.build_dataset(raw,path,'latest');manifest_bytes=path.read_bytes()
    with (raw/'accepted.jsonl').open('ab') as handle:handle.write(b'{"id":"uncommitted"}')
    with pytest.raises(ValueError,match='incomplete final row'):
        dataset.build_dataset(raw,path,'latest')
    assert path.read_bytes()==manifest_bytes
    assert all(Path(p).is_file() for p in before['shards'].values())


def test_snapshot_owns_writer_lock_and_replay_build_releases_it(tmp_path,monkeypatch):
    raw,_=source(tmp_path)
    original_snapshot=dataset.dataset_source_rows
    original_episode=histories.build_episode
    calls=[]

    def snapshot(*args,**kwargs):
        with (raw/'.writer.lock').open('a') as other:
            with pytest.raises(BlockingIOError):
                fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
        calls.append('snapshot')
        return original_snapshot(*args,**kwargs)

    def episode(*args,**kwargs):
        with (raw/'.writer.lock').open('a') as other:
            fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
        calls.append('episode')
        return original_episode(*args,**kwargs)

    monkeypatch.setattr(dataset,'dataset_source_rows',snapshot)
    monkeypatch.setattr(histories,'build_episode',episode)
    dataset.build_dataset(raw,tmp_path/'published/latest.json','latest')
    assert calls==['snapshot']+['episode']*4


def test_invalid_accepted_replay_preserves_complete_generation(tmp_path):
    raw,_=source(tmp_path);path=tmp_path/'published/latest.json'
    before=dataset.build_dataset(raw,path,'latest');manifest_bytes=path.read_bytes()
    shards={p:Path(p).read_bytes() for p in before['shards'].values()}
    replay_path=raw/'games/test0002/replay.json'
    replay=json.loads(replay_path.read_text())
    replay['frames'][1]['board']='-'*64
    replay_path.write_text(json.dumps(replay))
    with pytest.raises(ValueError,match='accepted replay test0002 failed validation'):
        dataset.build_dataset(raw,path,'latest')
    assert path.read_bytes()==manifest_bytes
    assert all(Path(p).read_bytes()==data for p,data in shards.items())
