"""Pre-fit revision: embed SHA-matching cached sequences, avoiding random opens."""
from datetime import datetime,timezone
import ctypes
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from prepare import ROOT,HERE,OUT,sha,library,write

def encoded(s):
    sq=lambda p:ord(p[0])-97+8*(int(p[1])-1)
    return sq(s[:2])|(sq(s[2:4])<<6)|(('pnbrqk'.index(s[4]) if len(s)==5 else 6)<<12)

def main():
    start=time.monotonic();path=OUT/'plan.json';raw=path.read_bytes();plan=json.loads(raw)
    assert 'prelaunch_revision' not in plan and not (OUT/'execution.json').exists()
    (OUT/'plan-initial.json.gz').write_bytes(gzip.compress(raw,mtime=0))
    cache=ROOT/'data/cache/move-export.sqlite';db=sqlite3.connect('file:'+str(cache)+'?mode=ro',uri=True);db.execute('BEGIN')
    for g in plan['games']:
        row=db.execute('SELECT moves FROM moves WHERE game_id=? AND moves_sha256=?',(g['game'],g['sequence_sha256'])).fetchone()
        assert row is not None,g['game'];text=row[0]
        assert hashlib.sha256(text.encode()).hexdigest()==g['sequence_sha256']
        g['moves']=text.split();assert len(g['moves'])+1==g['frames']
    db.close()
    # Nine unchanged hash-selected sources independently tie the embedded
    # sequences, reconstructed native state and stored source observations.
    lib=library();buffers=[ctypes.create_string_buffer(65) for _ in range(3)];checks=0
    for split in ('train','validation','test'):
        selected=sorted([g for g in plan['games'] if g['split']==split],key=lambda g:g['game'])[:3]
        for g in selected:
            p=ROOT/'data/raw/games'/g['game']/'replay.json';source=p.read_bytes();assert hashlib.sha256(source).hexdigest()==g['replay_sha256']
            replay=json.loads(source);assert [f['move'] for f in replay['frames'][1:]]==g['moves'];lib.prior_start()
            for ply,frame in enumerate(replay['frames']):
                lib.prior_state(*buffers)
                for key,b in zip(('board','white','black'),buffers):assert b.value.decode()==frame[key]
                checks+=1
                if ply<len(g['moves']):assert lib.prior_step(encoded(g['moves'][ply]))>=0
    plan['prelaunch_revision']=dict(at=datetime.now(timezone.utc).isoformat(),initial_plan_sha256=hashlib.sha256(raw).hexdigest(),
          reason='Cold external-drive random lookups delayed original preparation. Embed the same selected, SHA-matching immutable move sequences from the existing SSD SQLite cache. No cohort, selected plies, split, model, gate or fit result changes.',
          input_format='Self-contained recorded moves; native features are reconstructed from the standard start. Reviewer compares C states/views with the separate referee. Nine raw sources remain checked against the original stored observations.',
          raw_sample_frame_checks=checks,cache_lookups=len(plan['games']),cache=str(cache),seconds=time.monotonic()-start)
    plan['dependencies'][str(HERE/'finalize.py')]=sha(HERE/'finalize.py')
    for p in list(plan['dependencies']):plan['dependencies'][p]=sha(p)
    path.write_text(json.dumps(plan,indent=2,allow_nan=False)+'\n')
    write(OUT/'sequence-cache-receipt.json',plan['prelaunch_revision'])
    print(json.dumps(dict(embedded=len(plan['games']),raw_frame_checks=checks,seconds=time.monotonic()-start,plan_sha256=sha(path))),flush=True)
if __name__=='__main__':main()
