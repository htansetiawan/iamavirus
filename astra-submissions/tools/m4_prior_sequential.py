#!/usr/bin/env python3
"""Freeze and run a paired sequential-belief diagnostic; no search or arena writes."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import time


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--audits',type=Path,required=True);ap.add_argument('--cache',type=Path,required=True)
    ap.add_argument('--fit',type=Path,required=True);ap.add_argument('--runner',type=Path,required=True)
    ap.add_argument('--games',type=int,default=16,help='0 selects all audited games')
    ap.add_argument('--skip-diagnostics',action='store_true')
    args=ap.parse_args();args.out.mkdir(exist_ok=False)
    audits=json.loads(gzip.open(args.audits,'rt').read());ids=sorted(a['id'] for a in audits)
    if args.games<0:raise ValueError('negative game count')
    random.Random(701).shuffle(ids);selected=ids[:args.games] if args.games else ids
    primary='random'+str(len(selected)) if args.games else 'fresh_all'
    # Explicitly diagnosed traps are an extra cohort, never hidden in random counts.
    cohorts={gid:primary for gid in selected}
    for gid in ([] if args.skip_diagnostics else ['gjlnku86','c4ak2ldi']):
        if gid not in cohorts:selected.append(gid);cohorts[gid]='diagnostic'
    frozen=[];by_id={a['id']:a for a in audits}
    with (args.out/'input.txt').open('w') as target:
        for gid in selected:
            path=args.cache/gid/'replay.json';g=json.loads(path.read_text());side=by_id[gid]['side']
            if g[side]!='IAmAVirus' or g.get('rulesVersion')!='fow-v1':raise ValueError('seat/rules')
            target.write(f"game {gid} {0 if side=='white' else 1}\n")
            for f in g['frames'][1:]:target.write(' '.join([f['move'],f['board'],f['white'],f['black']])+'\n')
            frozen.append(dict(id=gid,side=side,cohort=cohorts[gid],plies=len(g['frames'])-1,
                               sha256=sha(path),source=str(path),result=g['result']))
    shutil.copyfile(args.runner,args.out/'runner');(args.out/'runner').chmod(0o755)
    shutil.copyfile(__file__,args.out/'run.py')
    models=json.loads((args.fit/'models.json').read_text())['models']
    for name,theta in models.items():
        (args.out/(name+'.txt')).write_text(str(len(theta))+'\n'+' '.join(f'{x:.12g}' for x in theta)+'\n')
    manifest=dict(games=frozen,cap=10000,seed=41,primary_cohort=primary,
        selection=f'shuffle sorted fresh audited IDs with seed701; games={args.games}; skip_diagnostics={args.skip_diagnostics}',
        runner_sha256=sha(args.out/'runner'),source_sha256=sha(Path(__file__)),input_sha256=sha(args.out/'input.txt'),
        models_sha256=sha(args.fit/'models.json'),classification='Fixed-cap sequential belief, historical moves forced; no search or clock-dependent thinning; no Elo estimate')
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','M4SF_'))}
    env.update(MIST_MODEL='1',MIST_MODEL_TEMP='1',MIST_MODEL_FULL_BELOW='10000')
    for name in ['control26','visibility32']:
        begin=time.time()
        with (args.out/(name+'.jsonl')).open('w') as out,(args.out/(name+'.stderr')).open('w') as err:
            p=subprocess.run([str(args.out/'runner'),str(args.out/'input.txt'),str(args.out/(name+'.txt')),'10000','41'],
                             stdout=out,stderr=err,env=env,timeout=900)
        result=dict(model=name,returncode=p.returncode,elapsed_seconds=time.time()-begin)
        (args.out/(name+'-status.json')).write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result),flush=True)
        if p.returncode:raise RuntimeError('Sequential probe failed; retain all outputs')


if __name__=='__main__':main()
