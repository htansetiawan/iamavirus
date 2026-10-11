#!/usr/bin/env python3
"""Build an isolated finite-resampling replay arm from immutable native source."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def once(s,a,b):
    if s.count(a)!=1:raise ValueError('Frozen source anchor mismatch: '+a[:70])
    return s.replace(a,b)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(exist_ok=False)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    before={}
    for p in sorted(a.source.iterdir()):
        if p.suffix in ['.c','.h']:shutil.copyfile(p,a.out/p.name);before[p.name]=sha(p)
    for name in ['m4_finite_resample.c','m4_finite_resample.h']:
        shutil.copyfile(Path(__file__).with_name(name),a.out/name)
    p=a.out/'belief.c';s=p.read_text()
    if 'm4_audit_key' in s:raise ValueError('Use the non-instrumented baseline')
    s=once(s,'#include "movemodel.h"','#include "movemodel.h"\n#include "m4_finite_resample.h"\n#include <stdio.h>')
    s=once(s,'    /* past the cap: weighted sampling without replacement (exponential keys) */',
           '    float *selected_logw = NULL;\n    /* past the cap: weighted sampling without replacement (exponential keys) */')
    s=once(s,'        Ranked *r = malloc(m * sizeof(Ranked));','''        const char *method = getenv("M4_CAP_MODE");
        if(method && (!strcmp(method,"finite") || !strcmp(method,"raw"))) {
            float *input = malloc(m*sizeof(float));
            selected_logw = malloc(b->cap*sizeof(float));
            if(!input || !selected_logw)exit(6);
            for(size_t i=0;i<m;++i)input[i]=cand[i].logw;
            if(m4_finite_resample(input,m,b->cap,unit_open(&b->rng),chosen,selected_logw)) {
                fprintf(stderr,"finite cap failed: n=%zu k=%zu\\n",m,b->cap);exit(6);
            }
            free(input);keep=b->cap;
            if(!strcmp(method,"raw")){free(selected_logw);selected_logw=NULL;}
        } else {
        Ranked *r = malloc(m * sizeof(Ranked));''')
    s=once(s,'        free(r);\n    } else {','        free(r);\n        }\n    } else {')
    s=once(s,'        vec_push(&next, &p, h, c->logw);',
           '        vec_push(&next, &p, h, selected_logw ? selected_logw[k] : c->logw);')
    s=once(s,'    free(chosen);','    free(selected_logw);\n    free(chosen);');p.write_text(s)
    cmd=['cc','-O2','-std=c11','-Wall','-Wextra','-Wpedantic','-I',str(a.out),
         *[str(a.out/n) for n in ['board.c','belief.c','movemodel.c','eval.c','front.c','intent.c','runner.c','m4_finite_resample.c']],
         '-Wl,--wrap=move_logits','-lm','-o',str(a.out/'runner')]
    run=subprocess.run(cmd,capture_output=True,text=True);(a.out/'build.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise RuntimeError('Compilation failed')
    shutil.copyfile(__file__,a.out/'build.py')
    d={'base_sources':before,'command':cmd,'files':{p.name:sha(p) for p in sorted(a.out.iterdir()) if p.is_file()}}
    (a.out/'manifest.json').write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps({'binary':str(a.out/'runner'),'sha256':sha(a.out/'runner')}))


if __name__=='__main__':main()
