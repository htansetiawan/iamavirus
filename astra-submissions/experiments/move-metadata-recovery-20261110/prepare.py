"""Consistent read-only source-cache backup and syntax/hash inventory; no API."""
from collections import Counter
from datetime import datetime,timezone
import fcntl
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'astra-submissions/analysis/move-metadata-recovery-20261110'
STORE=ROOT/'data/astra-spool/move-metadata-recovery-20261110'
SOURCE=ROOT/'data/cache/move-export.sqlite'
sys.path.insert(0,str(ROOT/'astra-submissions/tools'))
from export_move_cache import checked_moves


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def write(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def main():
    started=time.monotonic();assert not STORE.exists();STORE.mkdir(parents=True)
    # The source connection is read-only. Backup captures a complete logical
    # snapshot even in WAL mode; neither source rows nor exporter state change.
    with SOURCE.with_name(SOURCE.name+'.lock').open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
        source=sqlite3.connect(SOURCE.resolve().as_uri()+'?mode=ro',uri=True)
        snapshot=sqlite3.connect(STORE/'source.sqlite')
        source.backup(snapshot,pages=512);snapshot.close();source.close()
    db=sqlite3.connect((STORE/'source.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    assert db.execute('pragma user_version').fetchone()[0]==1
    assert db.execute('pragma integrity_check').fetchone()[0]=='ok'
    rows=plies=encoded_bytes=0;unique=set();ids=set();split_groups={};split_counts=Counter()
    for game,digest,text in db.execute('select game_id,moves_sha256,moves from moves order by game_id'):
        assert re.fullmatch('[a-z0-9]{8}',game) and game not in ids
        assert re.fullmatch('[0-9a-f]{64}',digest)
        canonical=checked_moves(text);assert canonical==text and hashlib.sha256(text.encode()).hexdigest()==digest
        ids.add(game);unique.add(digest);rows+=1;plies+=len(text.split());encoded_bytes+=len(text.encode())
        # Replicate the existing exporter partition for contamination diagnostics,
        # never claim it is an untouched holdout for a new model.
        test=int(hashlib.sha1(game.encode()).hexdigest(),16)%1000<150
        split_counts['test' if test else 'train']+=1;split_groups[digest]=split_groups.get(digest,0)|(2 if test else 1)
    assert rows==len(ids)==96210
    report=dict(at=datetime.now(timezone.utc).isoformat(),source=str(SOURCE),snapshot=str(STORE/'source.sqlite'),
        snapshot_sha256=sha(STORE/'source.sqlite'),snapshot_bytes=(STORE/'source.sqlite').stat().st_size,
        rows=rows,unique_trajectories=len(unique),conflicting_game_ids=0,plies=plies,raw_move_text_bytes=encoded_bytes,
        legacy_id_hash_partition=dict(split_counts),trajectory_groups_spanning_legacy_partitions=sum(v==3 for v in split_groups.values()),
        seconds=time.monotonic()-started,source_opened_read_only=True,source_data_modified=False,
        outcome_metadata_recovered=False,clocks_available=False,recorded_views_available=False,
        scope='Infrastructure inventory of all cached moves. Row hashes, UCI syntax, uniqueness and SQLite integrity checked; no new FOW legality proof, metadata or model inference. Metadata/results/clocks are absent from this source table. Snapshot private, no accepted-store mutation or training.')
    write(OUT/'snapshot-inventory.json',report);print(json.dumps(report,indent=2))


if __name__=='__main__':main()
