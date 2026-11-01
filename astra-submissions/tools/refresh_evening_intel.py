#!/usr/bin/env python3
"""Bounded public refresh plus traceable offline taxonomy for newly indexed games."""
from contextlib import redirect_stderr
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'astra-submissions/analysis/arena-intel-20261101-evening'
RAW=ROOT/'data/raw'
sys.path.insert(0,str(ROOT))
from learning import ingest,move_taxonomy

def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows():
    return {r['id']:r for r in map(json.loads,(RAW/'accepted.jsonl').read_text().splitlines())}
def save(path,data):
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');temp.replace(path)

def main():
    before=rows();snapshots=set((RAW/'snapshots').glob('*/leaderboard.json'))
    status=dict(status='running',pid=os.getpid(),starttime=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],
                started=now(),limit=600,scope='All teams, newest completed games, public GET only',pause_seconds=1.2,
                raw_path=str(RAW.resolve()),known_before=len(before),source_sha256=sha(Path(__file__)))
    with (OUT/'refresh.json').open('x') as f:json.dump(status,f,indent=2)
    try:
        with (OUT/'refresh.log').open('x') as log,redirect_stderr(log):
            counts=ingest.ingest_from_api(RAW,None,None,600,None,False,1.2)
        after=rows();new=sorted(set(after)-set(before));records=[]
        for game in new:
            path=RAW/'games'/game/'replay.json';replay=json.loads(path.read_text())
            labelled=move_taxonomy.label_game(replay)
            records.append(dict(game=game,created_at=after[game]['createdAt'],
                white=after[game]['white'],black=after[game]['black'],white_version=after[game]['whiteVersion'],black_version=after[game]['blackVersion'],
                result=after[game]['result'],replay_sha256=sha(path),counts=labelled['counts'],moves=labelled['moves']))
        with (OUT/'new-game-taxonomy.jsonl').open('x') as f:
            for record in records:f.write(json.dumps(record,sort_keys=True)+'\n')
        new_snapshots=sorted(set((RAW/'snapshots').glob('*/leaderboard.json'))-snapshots)
        status.update(status='complete',counts=counts,known_after=len(after),newly_observed_index_entries=len(records),
            no_concurrent_index_discrepancy=len(records)==counts['accepted'],
            taxonomy_sha256=sha(OUT/'new-game-taxonomy.jsonl'),
            snapshots=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in new_snapshots],
            training_boundary='These are offline annotations only. No fitting, history-table rebuild, threshold update, benchmark replacement or deployed-model update.',
            coverage='A bounded newest-600 refresh is not a claim of complete archive synchronization. Index differences may include a concurrent writer; compare with accepted count.')
    except BaseException as error:
        status.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        status['finished']=now();save(OUT/'refresh.json',status)
    print(json.dumps(status,indent=2))

if __name__=='__main__':main()
