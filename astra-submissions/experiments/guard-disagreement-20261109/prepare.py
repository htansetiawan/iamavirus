"""Build an opt-in v38 guard-disagreement prototype and test its actual C rule."""
import ctypes
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/guard-disagreement-20261109';BUILD=HERE/'build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
    with p.open('x') as f:json.dump(d,f,indent=2);f.write('\n')


def main():
    OUT.mkdir(exist_ok=False);BUILD.mkdir(exist_ok=False)
    archive=ROOT/'astra-submissions/iamavirus-v38-mist-c-allchildren.zip'
    assert sha(archive)=='ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f'
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if not name.startswith(('src/','bin/','data/')) or name.endswith('/'):continue
            p=BUILD/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
    shutil.copyfile(HERE/'guard_envelope.h',BUILD/'src/guard_envelope.h')
    p=BUILD/'src/main.c';s=p.read_text();s=s.replace('#include "gtcfr.h"','#include "gtcfr.h"\n#include "guard_envelope.h"')
    anchor='    const double guard = getenv("MIST_KING_GUARD") ? atof(getenv("MIST_KING_GUARD")) : 0.02;'
    assert s.count(anchor)==1
    s=s.replace(anchor,anchor+'\n    const int guard_either = getenv("ASTRA_GUARD_EITHER") && atoi(getenv("ASTRA_GUARD_EITHER")) != 0;')
    old='out[i] = riskt[i] > leastt + guard || (pass == 0 && risk[i] > least + guard);'
    assert s.count(old)==1
    s=s.replace(old,'out[i] = astra_guard_excluded(risk[i],riskt[i],least,leastt,guard,pass,guard_either);');p.write_text(s)
    sources=['board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval','main']
    cmd=['gcc','-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=199309L',*[str(BUILD/'src'/f'{s}.c') for s in sources],'-lm','-o',str(BUILD/'mist')]
    built=subprocess.run(cmd,capture_output=True,text=True,timeout=120);assert built.returncode==0,built.stderr
    # Call the SAME compiled predicate used by the native frontend.
    stub=BUILD/'predicate.c';stub.write_text('#include "src/guard_envelope.h"\nint mask(double a,double b,double c,double d,double e,int p,int h){return astra_guard_excluded(a,b,c,d,e,p,h);}\n')
    testcmd=['gcc','-std=c11','-O2','-shared','-fPIC',str(stub),'-o',str(BUILD/'predicate.so')]
    done=subprocess.run(testcmd,capture_output=True,text=True,timeout=30);assert done.returncode==0,done.stderr
    lib=ctypes.CDLL(str(BUILD/'predicate.so'));f=lib.mask;f.argtypes=[ctypes.c_double]*5+[ctypes.c_int]*2;f.restype=ctypes.c_int
    def cmask(r,s,mode):
        low,ls=min(r),min(s)
        for p in (0,1):
            keep={i for i in range(len(r)) if not f(r[i],s[i],low,ls,.02,p,mode)}
            if keep:return keep
        raise AssertionError('Empty mask')
    rng=random.Random(2691110);n=0
    for _ in range(10000):
        count=rng.randrange(1,65);r=[rng.random()*1.9 for _ in range(count)];s=[rng.random()*1.9 for _ in range(count)]
        if n%7==0:s=list(r)
        low,ls=min(r),min(s);raw={i for i,v in enumerate(r) if v<=low+.02};sharp={i for i,v in enumerate(s) if v<=ls+.02}
        off,on=cmask(r,s,0),cmask(r,s,1)
        assert off==(raw&sharp or sharp) and on==raw|sharp and off<=on
        if r==s:assert off==on
        n+=1
    evidence=ROOT/'astra-submissions/analysis/priority-diagnosis-20261109/review.json'
    rows=json.loads(evidence.read_text())['rows'];additions=0
    for row in rows:
        aa=row['actions'];r=[a['king']+.9*max(0,a['queen']) for a in aa];s=[a['king_sharp']+.9*max(0,a['queen_sharp']) for a in aa]
        off,on=cmask(r,s,0),cmask(r,s,1);additions+=len(on-off)
        assert all(not aa[i]['excluded'] for i in off if aa[i]['move'] in row['safe_kept'])
    write(OUT/'correctness.json',dict(passed=True,synthetic_vectors=n,real_vectors=len(rows),added_actions=additions,
           scope='Actual C predicate versus independent set formulas; superset/nonempty/identical-weighting properties. No actor choice or strength test.',
           test_command=testcmd,source_sha256=sha(HERE/'guard_envelope.h'),evidence_sha256=sha(evidence)))
    write(OUT/'build.json',dict(at=datetime.now(timezone.utc).isoformat(),command=cmd,stdout=built.stdout,stderr=built.stderr,
          archive_sha256=sha(archive),binary_sha256=sha(BUILD/'mist'),header_sha256=sha(HERE/'guard_envelope.h'),
          source_sha256={p.name:sha(p) for p in (BUILD/'src').iterdir() if p.is_file()},
          status='Opt-in prototype; actor/paired/strength gates not yet run',flag='ASTRA_GUARD_EITHER=1',default_enabled=False))
    print(json.dumps(dict(built=True,synthetic_vectors=n,real_vectors=len(rows),added_actions=additions,playing_strength_tested=False)))


if __name__=='__main__':main()
