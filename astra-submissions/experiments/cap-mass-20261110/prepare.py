"""Observer-only cap snapshots on the already-frozen eight historical prefixes."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/cap-mass-20261110'
BUILD=HERE/'build'
PRIOR=ROOT/'astra-submissions/analysis/belief-sort-cost-20261110'
CORRECTION=HERE.parent/'cap-weight-20261110/correction.h'
STORE=Path('/media/henrytan/seagate/iamavirus/astra/cap-mass-20261110')
SOURCES=['board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval','main']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def patched(source):
    anchor='typedef struct { double key; uint32_t index; } Ranked;'
    assert source.count(anchor)==1
    source=source.replace(anchor,anchor+'\n#include "observe.h"')
    anchor='        for (size_t i = 0; i < keep; ++i) chosen[i] = r[i].index;'
    assert source.count(anchor)==1
    source=source.replace(anchor,anchor+'\n        astra_cap_observe(0,m,keep,r,cand,sizeof(Candidate),offsetof(Candidate,logw));')
    anchor='    qsort(r, b->count, sizeof(Ranked), by_rank);'
    assert source.count(anchor)==1
    source=source.replace(anchor,anchor+'\n    astra_cap_observe(1,b->count,target,r,b->logw,sizeof(float),0);')
    return source


def main():
    OUT.mkdir(exist_ok=False);BUILD.mkdir(exist_ok=False)
    plan=json.loads((PRIOR/'plan.json').read_text());parent=Path(plan['parent'])
    shutil.copytree(parent/'src',BUILD/'src')
    p=BUILD/'src/belief.c';p.write_text(patched(p.read_text()))
    flags=['gcc','-std=c11','-pthread','-D_POSIX_C_SOURCE=199309L','-I',str(HERE),'-I',str(CORRECTION.parent)]
    cmd=[*flags,'-O2',*[str(BUILD/'src'/f'{s}.c') for s in SOURCES],'-lm','-o',str(BUILD/'mist')]
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=90);assert result.returncode==0,result.stderr
    unitcmd=[*flags,'-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer',str(HERE/'unit.c'),'-lm','-o',str(BUILD/'unit')]
    u=subprocess.run(unitcmd,capture_output=True,text=True,timeout=30);assert u.returncode==0,u.stderr
    pre=OUT/'preflight';pre.mkdir()
    env=dict(os.environ,ASTRA_CAP_DUMP_DIR=str(pre))
    u=subprocess.run([str(BUILD/'unit')],capture_output=True,text=True,env=env,timeout=15)
    assert u.returncode==0,u.stderr
    logs=[json.loads(s) for s in re.findall(r'^astra-cap-mass: (.*)$',u.stderr,re.M)]
    assert len(logs)==2
    for row in logs:
        raw=(pre/f"{row['stage']}.bin").read_bytes();n,k,t,top=struct.unpack_from('<QQdd',raw)
        lw=np.frombuffer(raw,dtype='<f4',offset=32,count=n).astype(float)
        keys=np.frombuffer(raw,dtype='<f8',offset=32+4*n,count=n)
        idx=np.frombuffer(raw,dtype='<u4',offset=32+12*n,count=k)
        w=np.exp(lw-top)
        assert n==3 and k==2 and len(raw)==row['bytes']
        assert t==np.sort(keys)[k] and set(idx)==set(np.argsort(keys)[:k])
        assert abs(row['discarded_fraction']-(1-w[idx].sum()/w.sum()))<1e-14
    from run import feed,environment
    openings=[]
    for side in ('white','black'):
        c=dict(next(c for c in plan['cases'] if c['side']==side));c['ply']=0 if side=='white' else 1
        text,moves=feed(c);dump=pre/side;dump.mkdir()
        opening=subprocess.run([str(BUILD/'mist')],input=text,capture_output=True,text=True,
                               env=environment(parent,moves,dump),timeout=10)
        assert opening.returncode==0 and re.findall(r'^move (\S+)$',opening.stdout,re.M)==moves
        assert 'nodes=' not in opening.stderr and not list(dump.iterdir())
        openings.append(dict(side=side,move=moves[0]))
    write(OUT/'preflight.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,commands=[cmd,unitcmd],openings=openings,
          compile_stderr=result.stderr,sanitizer_stderr=u.stderr,tests=['strided candidate float access','uniform NULL weights',
          'cutoff and subset identity','duplicate suppression','input immutability','address/undefined sanitizers']))
    deps=[Path(__file__),HERE/'run.py',HERE/'audit.py',HERE/'observe.h',HERE/'unit.c',CORRECTION,BUILD/'mist',
          PRIOR/'plan.json',parent/'data/history.bin',ROOT.parent/'fow-starter/referee.py']
    deps+=list((BUILD/'src').glob('*'))+list((parent/'src').glob('*'))
    deps += [Path(c['replay_path']) for c in plan['cases']]
    write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),parent=str(parent),cases=plan['cases'],
          cores=[0,1],per_case_seconds=120,total_seconds=1020,bulk_store=str(STORE),max_snapshot_bytes=64*1024*1024,
          dependencies={str(p):sha(p) for p in deps},
          scope='Eight reused historical controls selected by previous population size, no outcome selection. '
                'Observe first opponent-cap and first paid-thinning event per case. Raw weights/keys/indices are output '
                'only. No weight, RNG or selection rule changes. Observer cost and real-clock thinning can alter later '
                'populations: this is a reconstructed diagnostic, not exact arena states or frequency/strength.',
          criteria='All first attempts preserved, no fault or unexpected search; course input/forced-move audit and '
                   'independent raw binary ranking/cutoff/mass recomputation. At least four snapshots across three games '
                   'and a snapshot dropping >=1% mass make a sequential-measure design worth review, not automatic play.',
          limitations='First event of each kind only; large-population enriched development set. Single-step TV equals '
                      'discarded mass for normalized truncation, not a cumulative/filter bound. Corrected fraction is '
                      'an estimator, not true-board calibration. No correction applied or candidate/arena action.'))
    print(json.dumps(dict(prepared=True,cases=len(plan['cases']),pins=len(set(map(str,deps))))),flush=True)


if __name__=='__main__':main()
