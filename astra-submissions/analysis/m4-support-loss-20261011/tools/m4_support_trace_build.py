#!/usr/bin/env python3
"""Read-only cap attribution in a frozen replay binary; never change selection.

Generated hooks inspect candidate keys/weights after selection. They do not
consume RNG or write candidate/selection arrays. Original shared C stays intact.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HEADER = '''#ifndef M4_SUPPORT_TRACE_H
#define M4_SUPPORT_TRACE_H
#include <stddef.h>
#include <stdint.h>
extern uint64_t m4_audit_key;
extern const char *m4_audit_game;
extern int m4_audit_ply, m4_audit_parent;
#endif
'''
GLOBALS = '''uint64_t m4_audit_key;
const char *m4_audit_game;
int m4_audit_ply, m4_audit_parent;
'''
TRACE = r'''
    /* Observation-only instrumentation, AFTER the original random selection. */
    {
        double top=-INFINITY, z=0, sq=0, retained=0, truthw=0;
        int found=0, selected=0; size_t rank=0;
        float tw=-INFINITY;
        for(size_t i=0;i<m;++i) {
            if(cand[i].logw>top)top=cand[i].logw;
            if(cand[i].key==m4_audit_key){found=1;tw=cand[i].logw;}
        }
        for(size_t i=0;i<m;++i) {
            double w=exp((double)cand[i].logw-top);z+=w;sq+=w*w;
            if(cand[i].key==m4_audit_key)truthw+=w;
            if(found&&cand[i].logw>tw)++rank;
        }
        for(size_t k=0;k<keep;++k) {
            const Candidate *c=&cand[chosen[k]];
            retained+=exp((double)c->logw-top);
            if(c->key==m4_audit_key)selected=1;
        }
        fprintf(stderr,"{\"type\":\"support_cap\",\"game\":\"%s\",\"ply\":%d,\"parent_supported\":%d,\"generated\":%zu,\"unique\":%zu,\"kept\":%zu,\"cap\":%zu,\"truth_candidate\":%d,\"truth_kept\":%d,\"truth_rank\":%zu,\"truth_share_before_cap\":%.12g,\"retained_mass\":%.12g,\"ess_before_cap\":%.12g}\n",
            m4_audit_game,m4_audit_ply,m4_audit_parent,n,m,keep,b->cap,
            found,selected,found?rank+1:0,z?truthw/z:0,z?retained/z:0,sq?z*z/sq:0);
    }
'''


def once(source, old, new):
    if source.count(old) != 1:
        raise ValueError('Source anchor mismatch: ' + old[:100])
    return source.replace(old, new)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--frozen-build',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(exist_ok=False)
    before={}
    for path in sorted(args.frozen_build.iterdir()):
        if path.suffix in ('.c','.h'):
            shutil.copyfile(path,args.out/path.name);before[path.name]=sha(path)
    b=args.out/'belief.c';s=b.read_text()
    s=once(s,'#include "movemodel.h"','#include "movemodel.h"\n#include "support_trace.h"\n#include <stdio.h>')
    s=once(s,'    /* pass 2: rebuild the kept positions with their histories */',
           TRACE+'\n    /* pass 2: rebuild the kept positions with their histories */')
    b.write_text(s)
    r=args.out/'runner.c';s=r.read_text()
    s=once(s,'static float theta[M4MM_FEATURES];','#include "support_trace.h"\n'+GLOBALS+'\nstatic float theta[M4MM_FEATURES];')
    s=once(s,'        Undo undo;make_move(&truth,move,&undo);',
           '        m4_audit_parent=belief_contains(&b,&truth);\n        Undo undo;make_move(&truth,move,&undo);')
    s=once(s,'        clock_t begin=clock();size_t before=b.count;',
           '        m4_audit_key=position_key(&truth);m4_audit_game=id;m4_audit_ply=ply;\n        clock_t begin=clock();size_t before=b.count;')
    r.write_text(s);(args.out/'support_trace.h').write_text(HEADER)
    cmd=['cc','-O2','-std=c11','-Wall','-Wextra','-Wpedantic','-I',str(args.out),
         *[str(args.out/n) for n in ['board.c','belief.c','movemodel.c','eval.c','front.c','intent.c','runner.c']],
         '-Wl,--wrap=move_logits','-lm','-o',str(args.out/'runner')]
    run=subprocess.run(cmd,capture_output=True,text=True)
    (args.out/'build.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise RuntimeError('Compilation failed; inspect build.log')
    shutil.copyfile(__file__,args.out/'build.py')
    result={'base_sources':before,'command':cmd,'sources':{p.name:sha(p) for p in sorted(args.out.iterdir()) if p.is_file()},
            'classification':'Offline read-only instrumentation; not runtime profiling or a policy change.'}
    (args.out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'runner':str(args.out/'runner'),'sha256':sha(args.out/'runner')}))


if __name__=='__main__':main()
