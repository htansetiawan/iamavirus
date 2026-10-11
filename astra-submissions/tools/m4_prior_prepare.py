#!/usr/bin/env python3
"""Freeze an opponent-only, game-separated move-prior corpus from cached replays."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess

EXCLUDED={'Uniform','Baseline','baseline.py','IAmAVirus'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cache',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--extractor',type=Path,required=True)
    ap.add_argument('--games',type=int,default=2400);args=ap.parse_args()
    args.out.mkdir(exist_ok=False);shutil.copyfile(args.extractor,args.out/'extractor');(args.out/'extractor').chmod(0o755)
    ids=sorted(p.name for p in args.cache.iterdir() if p.is_dir());random.Random(43).shuffle(ids)
    writers={s:(args.out/(s+'.txt')).open('w') for s in ('train','validation','test')}
    games={s:[] for s in writers};skipped=Counter();n=0
    for gid in ids:
        if n>=args.games:break
        path=args.cache/gid/'replay.json'
        try:
            raw=path.read_bytes();g=json.loads(raw)
        except (OSError,ValueError):skipped['missing_or_invalid']+=1;continue
        if g.get('rulesVersion')!='fow-v1':skipped['rules']+=1;continue
        if not '2026-09-30'<=g.get('createdAt','')[:10]<'2026-10-11':skipped['date']+=1;continue
        if g['white'] in EXCLUDED and g['black'] in EXCLUDED:skipped['movers']+=1;continue
        if len(g['frames'])<5 or len(g['frames'])>513:skipped['length']+=1;continue
        assert g['id']==gid
        for ply,f in enumerate(g['frames']):
            assert f['ply']==ply and len(f['board'])==64
        bucket=int(hashlib.sha256(gid.encode()).hexdigest(),16)%1000
        split='train' if bucket<700 else 'validation' if bucket<850 else 'test'
        tags=[g[color] not in EXCLUDED for color in ['white','black']]
        writers[split].write(f"game {gid} {'white' if tags[0] else '-'} {'black' if tags[1] else '-'}\n")
        writers[split].write(' '.join(f["move"]+':'+f['board'] for f in g['frames'][1:])+'\n')
        games[split].append({k:g.get(k) for k in ['id','createdAt','white','black','whitePlayerId','blackPlayerId','whiteVersion','blackVersion','reason','result']} |
            {'source':str(path.resolve()),'sha256':hashlib.sha256(raw).hexdigest(),'used_sides':tags,'plies':len(g['frames'])-1})
        n+=1
    for f in writers.values():f.close()
    manifest={'created_at':datetime.now(timezone.utc).isoformat(),'games':games,'skipped':dict(skipped),
        'split':'SHA256(game_id) mod1000: train<700, validation<850, test otherwise; selection shuffle seed43',
        'exclusions':sorted(EXCLUDED),'range':'2026-09-30 <= completion date < 2026-10-11',
        'extractor_sha256':sha(args.out/'extractor'),'tool_sha256':sha(Path(__file__)),
        'text_sha256':{s:sha(args.out/(s+'.txt')) for s in writers},
        'classification':'Offline true-state-conditioned move prediction; no Elo inference; no GPU'}
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'selected':n,'split_games':{s:len(g) for s,g in games.items()},'skipped':dict(skipped)}),flush=True)
    for split in writers:
        with (args.out/(split+'-extract.txt')).open('w') as log:
            result=subprocess.run([str((args.out/'extractor').resolve()),str(args.out/(split+'.txt')),str(args.out/(split+'.bin'))],stdout=log,stderr=log)
        if result.returncode:raise RuntimeError('Extraction failed; preserve directory for audit: '+split)
        print(split,(args.out/(split+'-extract.txt')).read_text().strip(),flush=True)
    (args.out/'features.json').write_text(json.dumps({s:{'sha256':sha(args.out/(s+'.bin')),'bytes':(args.out/(s+'.bin')).stat().st_size} for s in writers},indent=2)+'\n')

if __name__=='__main__':main()
