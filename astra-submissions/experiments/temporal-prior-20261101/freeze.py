#!/usr/bin/env python3
"""Deterministic outcome-blind chronological manifest and fully auditable inputs."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

TEAMS=['Greek Gift','Knight Vision','Strongly Invisible','Decent Chess Bot',
       'Crimson Fog','Instructors','Mist Opportunities','duck','HYPOTHERMIA']
WINDOWS={'train':('2026-10-20','2026-10-28',1200),
         'validation':('2026-10-28','2026-10-30',300),
         'test':('2026-10-30','2026-11-01',600)}
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--raw',type=Path,default=Path('data/raw'))
    ap.add_argument('--exclude-plan',type=Path,required=True);args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    prior=json.loads(args.exclude_plan.read_text())
    excluded_ids={r['game'] for r in prior['games']}
    excluded_sequences={r['sequence_sha256'] for r in prior['games']}
    rows={}
    for line in (args.raw/'accepted.jsonl').open():
        r=json.loads(line);at=r.get('createdAt') or ''
        if '2026-10-20'<=at<'2026-11-01':rows[r['id']]=r
    ids=sorted(rows,key=lambda k:sha(('temporal-prior-1101:'+k).encode()))
    all_games=[];seen=set();counts={};versions=Counter();skips=Counter()
    for split,(lo,hi,n) in WINDOWS.items():
        selected=[];text=[]
        for gid in ids:
            if len(selected)==n:break
            if not lo<=(rows[gid].get('createdAt') or '')<hi:continue
            if gid in excluded_ids:skips['prior_experiment_game']+=1;continue
            path=args.raw/'games'/gid/'replay.json';payload=path.read_bytes();r=json.loads(payload)
            if r.get('rulesVersion')!='fow-v1':skips['rules']+=1;continue
            names=[r['white'],r['black']]
            if not any(name in TEAMS for name in names):continue
            frames=r['frames'];moves=[f['move'] for f in frames[1:]]
            assert all(f['ply']==i for i,f in enumerate(frames)) and all(moves)
            sequence=sha(' '.join(moves).encode())
            if sequence in seen or sequence in excluded_sequences:skips['duplicate_sequence']+=1;continue
            seen.add(sequence);index=len(all_games)+len(selected)
            used=[TEAMS.index(name) if name in TEAMS else -1 for name in names]
            text.append(f'game {index} {used[0]} {used[1]}\n')
            for i,f in enumerate(frames):
                text.append(f"{f['move'] if i else 'initial'} {f['board']} {f['white']} {f['black']}\n")
            item={'index':index,'id':gid,'split':split,'createdAt':r['createdAt'],
                  'white':r['white'],'black':r['black'],'whiteVersion':r.get('whiteVersion'),
                  'blackVersion':r.get('blackVersion'),'replay_path':str(path),'replay_sha256':sha(payload),
                  'sequence_sha256':sequence,'plies':len(moves)}
            selected.append(item)
            for side,name in zip(['white','black'],names):
                if name in TEAMS:versions[f"{split}:{name}:v{r.get(side+'Version')}:{side}"]+=1
        assert len(selected)==n,(split,len(selected),n)
        data=''.join(text).encode();dest=args.out/f'{split}.txt.gz'
        with dest.open('wb') as f:
            with gzip.GzipFile(filename='',fileobj=f,mode='wb',mtime=0) as z:z.write(data)
        counts[split]={'games':len(selected),'input_sha256':sha(data),'gzip_sha256':sha(dest.read_bytes())}
        all_games+=selected
    manifest={'teams':TEAMS,'windows':WINDOWS,'splits':counts,'games':all_games,'versions':dict(versions),
              'skips':dict(skips),'selection':'outcome-blind fixed ID hash; chronological, sequence-deduplicated',
              'exclusion_plan':str(args.exclude_plan),'exclusion_plan_sha256':sha(args.exclude_plan.read_bytes()),
              'script_sha256':sha(Path(__file__).read_bytes())}
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'splits':counts,'skips':dict(skips)},indent=2))
if __name__=='__main__':main()
