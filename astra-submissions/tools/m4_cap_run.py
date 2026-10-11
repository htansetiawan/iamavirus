#!/usr/bin/env python3
"""Compare cap modes with frozen priors, replay inputs and RNG seed."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True)
    ap.add_argument('--previous',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seed',type=int,default=41);ap.add_argument('--modes',type=int,nargs='+',default=[0,1,2])
    args=ap.parse_args();args.out.mkdir(exist_ok=False)
    if not args.modes or not set(args.modes)<=set(range(3)):raise ValueError('mode')
    shutil.copyfile(args.build/'runner',args.out/'runner');(args.out/'runner').chmod(0o755)
    shutil.copyfile(__file__,args.out/'run.py')
    plan=dict(seed=args.seed,cap=10000,modes=args.modes,runner_sha256=sha(args.out/'runner'),
              build_manifest_sha256=sha(args.build/'manifest.json'),batches={})
    for batch in ['sequential02','sequential-fresh26']:
        dst=args.out/batch;dst.mkdir();old=args.previous/batch
        for src,dest in [('input.txt','input.txt'),('control26.txt','model.txt'),('manifest.json','input-manifest.json')]:shutil.copyfile(old/src,dst/dest)
        plan['batches'][batch]={'input_sha256':sha(dst/'input.txt'),'model_sha256':sha(dst/'model.txt')}
    (args.out/'manifest.json').write_text(json.dumps(plan,indent=2)+'\n')
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','M4SF_'))}
    env.update(MIST_MODEL='1',MIST_MODEL_TEMP='1',MIST_MODEL_FULL_BELOW='10000')
    for mode in args.modes:
        env['MIST_M4_CAP_MODE']=str(mode)
        for batch in plan['batches']:
            dst=args.out/batch;begin=time.monotonic()
            with (dst/f'mode{mode}.jsonl').open('w') as out,(dst/f'mode{mode}.stderr').open('w') as err:
                run=subprocess.run([str(args.out/'runner'),str(dst/'input.txt'),str(dst/'model.txt'),'10000',str(args.seed)],
                                   env=env,stdout=out,stderr=err,timeout=900)
            status=dict(mode=mode,batch=batch,returncode=run.returncode,elapsed_seconds=time.monotonic()-begin)
            (dst/f'mode{mode}-status.json').write_text(json.dumps(status,indent=2)+'\n')
            print(json.dumps(status),flush=True)
            if run.returncode:raise RuntimeError('probe failed; retain outputs')
            if args.seed==41 and mode in (0,1):
                def semantic(p):
                    rows=[json.loads(s) for s in p.read_text().splitlines()]
                    for r in rows:r.pop('update_cpu_seconds')
                    return rows
                original=semantic(args.previous/batch/'control26.jsonl');new=semantic(dst/f'mode{mode}.jsonl')
                if original!=new:raise RuntimeError(f'parity failed for {batch} mode{mode}; do not run correction')
                print(json.dumps(dict(parity='exact non-timing rows',batch=batch,mode=mode,rows=len(new))),flush=True)
    (args.out/'complete.json').write_text(json.dumps({'completed':True,'files':{str(p.relative_to(args.out)):sha(p) for p in sorted(args.out.rglob('*')) if p.is_file()}},indent=2)+'\n')


if __name__=='__main__':main()
