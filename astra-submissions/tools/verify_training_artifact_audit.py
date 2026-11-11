"""Independent sorted reductions of the completed export audit's saved index."""
from collections import Counter
from datetime import datetime,timezone
from itertools import groupby
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'astra-submissions/analysis/training-artifact-readiness-20261111'
PRIVATE=ROOT/'data/astra-spool/training-artifact-readiness-20261111'

def read(p):return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    plan=read(OUT/'plan.json');result=read(OUT/'result.json');execution=read(OUT/'execution.json')
    assert execution['status']==result['status']=='complete' and execution['completed_files']==6
    assert execution['result_sha256']==sha(OUT/'result.json')
    assert execution['plan_sha256']==result['plan_sha256']==sha(OUT/'plan.json')
    assert execution['seconds']<=plan['wall_seconds']
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    assert sha(PRIVATE/'episode-index.jsonl')==result['index_sha256']
    raw={r['id']:r['moves_sha256'] for r in (json.loads(line) for line in (PRIVATE/'journal.jsonl').open())}
    rows=sorted((r['id'],r['side'],r['split'],r['moves_sha256'],r['source_hash']) for r in (json.loads(line) for line in (PRIVATE/'episode-index.jsonl').open()))
    seen=set();counts=Counter()
    for game,items in groupby(rows,key=lambda r:r[0]):
        items=list(items);assert len(items)==2 and [r[1] for r in items]==[0,1]
        assert items[0][2:]==items[1][2:] and items[0][3]==raw[game]
        seen.add(game);counts[items[0][2]]+=2
    manifest=read(PRIVATE/'episodes.json')
    assert len(seen)==manifest['source_games']==result['episode_source_games']
    for split,count in counts.items():assert count==manifest['counts'][split]['episodes']
    cross={}
    for sequence,items in groupby(sorted((r[3],r[2]) for r in rows),key=lambda r:r[0]):
        splits=sorted({r[1] for r in items})
        if len(splits)>1:cross[sequence]=splits
    assert cross==read(PRIVATE/'split-overlap.json')['episode_groups']
    assert len(rows)==result['episode_rows'] and len(cross)==result['episode_cross_split_trajectory_groups']
    assert set((PRIVATE/'not-in-episodes.txt').read_text().splitlines())==set(raw)-seen
    assert len(set(raw)-seen)==result['raw_games_absent_from_episode_generation']
    for spec in plan['files']:
        stat=Path(spec['path']).stat()
        assert (stat.st_dev,stat.st_ino,stat.st_size)==(spec['device'],spec['inode'],spec['bytes'])
        if spec['kind']=='episodes':
            assert next(r['sha256'] for r in result['receipts'] if r['split']==spec['split'])==spec['sha256']
        else:assert sha(spec['path'])==spec['sha256']
    games=next(Path(r['path']) for r in plan['files'] if r.get('name')=='games.jsonl')
    moves=sorted((r['moves_sha256'],r['split'],r['id']) for r in (json.loads(line) for line in games.open()))
    move_cross={}
    for sequence,items in groupby(moves,key=lambda r:r[0]):
        items=list(items);assert all(raw[r[2]]==sequence for r in items)
        splits=sorted({r[1] for r in items})
        if len(splits)>1:move_cross[sequence]=splits
    assert move_cross==read(PRIVATE/'split-overlap.json')['move_groups']
    assert len(moves)==result['move_source_games'] and len(move_cross)==result['move_cross_split_trajectory_groups']
    assert not any(r['owner']=='astra-training-artifact-readiness-20261111' for r in read(ROOT/'chatroom/cores.json')['allocation'])
    review=dict(at=datetime.now(timezone.utc).isoformat(),status='complete',episode_rows=len(rows),episode_games=len(seen),episode_split_overlap=len(cross),move_games=len(moves),move_split_overlap=len(move_cross),
        result_sha256=sha(OUT/'result.json'),review_source_sha256=sha(Path(__file__)),
        checks=['Original six-file audit ended within original cap; inputs/source and index hashes match.',
                'Independent sorting checks both color records and shared source identity for every episode game.',
                'All split counts, raw-ID coverage and the absence list reconcile.',
                'Independent sorted full-sequence grouping matches both exports overlap maps.',
                'Source generations retain their inode/size; move-file hashes checked independently again.',
                'Original core lease released.'],
        scope='Saved-index and generation reconciliation, not a second gzip scan, rule/target walk, new export, fit, calibration or playing test.')
    with (OUT/'review.json').open('x') as stream:stream.write(json.dumps(review,indent=2)+'\n')
    print(json.dumps(review,indent=2))

if __name__=='__main__':main()
