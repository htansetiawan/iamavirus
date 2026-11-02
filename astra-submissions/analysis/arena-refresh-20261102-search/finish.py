"""Pin accepted refresh data and check annotation coverage; never update models."""
import ast
from collections import Counter
from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def unique(p,value):
    with p.open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def manifest():
    execution=json.loads((OUT/'execution.json').read_text());assert execution['status']=='complete' and execution['exit']==0
    match=re.search(r'done: (\{[^\n]+\}); (\d+) requests',(OUT/'stderr.txt').read_text());assert match
    counts=ast.literal_eval(match[1]);assert counts['accepted']==len(execution['new_ids'])
    pins={gid:sha(ROOT/'data/raw/games'/gid/'replay.json') for gid in execution['new_ids']}
    unique(OUT/'manifest.json',dict(new_replays=len(pins),sha256=pins,counts=counts,requests=int(match[2]),
        execution_sha256=sha(OUT/'execution.json'),scope='Newly accepted games only. Bounded latest300 search, not complete archive synchronization.'))
    snapshots=[]
    for p in sorted((ROOT/'data/raw/snapshots').glob('*/leaderboard.json'),reverse=True)[:12]:
        j=json.loads(p.read_text());at=j.get('fetched',{}).get('fetched_at','')
        if execution['started']<=at<=execution['ended']:snapshots.append((p,j))
    assert len(snapshots)==1,[(str(p),j['fetched']) for p,j in snapshots]
    path,snapshot=snapshots[0];players=sorted((p for p in snapshot['leaderboard']['players'] if p.get('rating') is not None),key=lambda p:-p['rating'])
    rows=[dict(rank=i+1,**{k:p.get(k) for k in ('id','name','rating','games','wins','draws','losses','activeVersion','activeRecord','staff','external')}) for i,p in enumerate(players)]
    unique(OUT/'standings.json',dict(at=snapshot['fetched']['fetched_at'],url=snapshot['fetched']['url'],raw_snapshot=str(path.relative_to(ROOT)),raw_snapshot_sha256=sha(path),
        rank_definition='All visible rated teams, including staff and external teams.',players=rows))
    print(json.dumps(dict(new_replays=len(pins),counts=counts,requests=int(match[2]),ours=next(p for p in rows if p['name']=='IAmAVirus'))))


def verify():
    m=json.loads((OUT/'manifest.json').read_text());s=json.loads((OUT/'taxonomy-summary.json').read_text())
    rows=[json.loads(line) for line in gzip.open(OUT/'taxonomy.jsonl.gz','rt')]
    assert len(rows)==len(m['sha256'])==s['games'] and {r['game'] for r in rows}==set(m['sha256'])
    moves=queen=ep=0;sequences=Counter()
    for r in rows:
        assert r['replay_sha256']==m['sha256'][r['game']]
        path=ROOT/'data/raw/games'/r['game']/'replay.json';assert sha(path)==r['replay_sha256'];replay=json.loads(path.read_text())
        assert r['complete_uci_sequence_sha256']==hashlib.sha256(' '.join(f['move'] for f in replay['frames'][1:]).encode()).hexdigest()
        sequences[r['complete_uci_sequence_sha256']]+=1
        assert len(r['moves'])==len(replay['frames'])-1
        for name,side in (('white',0),('black',1)):
            assert r['counts'][name].get('moves',0)==sum(x['side']==side for x in r['moves'])
        moves+=len(r['moves']);queen+=sum(bool(x.get('queen_capture')) for x in r['supplements']);ep+=sum(bool(x.get('en_passant_capture')) for x in r['supplements'])
    assert moves==s['moves'] and s['independently_validated_frames']==moves+len(rows)
    assert queen==s['queen_capture_supplements'] and ep==s['en_passant_supplements']
    assert sum(p['games'] for p in s['panels'])==2*len(rows) and sum(p['moves'] for p in s['panels'])==moves
    for p in s['panels']:
        for tag,count in p['counts'].items():assert abs(p['per_100'][tag]-100*count/max(1,p['moves']))<1e-10
    plan=json.loads((ROOT/'astra-submissions/analysis/value-expansion-20261102/plan.json').read_text())
    overlap=sorted(set(m['sha256'])&{c['game'] for c in plan['cases']})
    assert sha(OUT/'taxonomy.jsonl.gz')==s['taxonomy_sha256']
    result=dict(at=datetime.now(timezone.utc).isoformat(),games=len(rows),moves=moves,frames=moves+len(rows),
        queen_capture_supplements=queen,en_passant_supplements=ep,distinct_complete_trajectories=len(sequences),
        duplicate_trajectory_groups=sum(n>1 for n in sequences.values()),experiment234_replay_panel_overlap=overlap,
        manifest_sha256=sha(OUT/'manifest.json'),taxonomy_sha256=sha(OUT/'taxonomy.jsonl.gz'),all_checks_pass=True,
        scope='Traceability and denominator checks; model/table/guards unchanged. These inspected labels are development data.')
    unique(OUT/'taxonomy-integrity.json',result);print(json.dumps(result))


if __name__=='__main__':
    assert sys.argv[1] in ('manifest','verify');globals()[sys.argv[1]]()
