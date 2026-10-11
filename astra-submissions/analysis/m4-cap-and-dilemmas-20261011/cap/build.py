#!/usr/bin/env python3
"""Build an isolated cap experiment without editing the shared belief source.

0: original cap; 1: identical weighted selection via heap, original weights;
2: same heap selection, threshold-corrected weights. Both cap sites are covered.
Exact source anchors fail closed if the upstream implementation changes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

INCLUDE = '''#include "m4resample.h"

/* Isolated generated experiment. Active belief.c remains unchanged. */
static int m4_cap_mode(void) {
    const char *s=getenv("MIST_M4_CAP_MODE");
    if(!s||!strcmp(s,"0"))return 0;
    if(!strcmp(s,"1"))return 1;
    if(!strcmp(s,"2"))return 2;
    abort();
}
typedef struct {uint32_t index;float logw;} M4Kept;
static int m4_kept_order(const void *a,const void *b) {
    const M4Kept *x=a,*y=b;return (x->index>y->index)-(x->index<y->index);
}
static size_t m4_heap_shrink(Belief *b,size_t target,int mode) {
    size_t *indices=malloc(target*sizeof(*indices));
    float *weights=malloc(target*sizeof(*weights));
    M4Kept *kept=malloc(target*sizeof(*kept));
    if(!indices||!weights||!kept||!m4_weighted_cap(b->logw,b->count,target,&b->rng,indices,weights))abort();
    for(size_t i=0;i<target;++i)kept[i]=(M4Kept){(uint32_t)indices[i],mode==2?weights[i]:(b->logw?b->logw[indices[i]]:0)};
    qsort(kept,target,sizeof(*kept),m4_kept_order);
    for(size_t i=0;i<target;++i) {
        b->items[i]=b->items[kept[i].index];
        if(b->hist)b->hist[i]=b->hist[kept[i].index];
        if(b->logw)b->logw[i]=kept[i].logw;
    }
    free(indices);free(weights);free(kept);
    b->count=target;b->overflowed=1;return target;
}
'''

OLD = '''        Ranked *r = malloc(m * sizeof(Ranked));
        for (size_t i = 0; i < m; ++i) { r[i].key = log(-log(unit_open(&b->rng))) - cand[i].logw; r[i].index = (uint32_t)i; }
        qsort(r, m, sizeof(Ranked), by_rank);
        keep = b->cap;
        for (size_t i = 0; i < keep; ++i) chosen[i] = r[i].index;
        free(r);'''
NEW = '''        int mode=m4_cap_mode();
        if(mode) {
            keep=b->cap;
            float *weights=malloc(m*sizeof(*weights));
            float *corrected=malloc(keep*sizeof(*corrected));
            size_t *indices=malloc(keep*sizeof(*indices));
            if(!weights||!corrected||!indices)abort();
            for(size_t i=0;i<m;++i)weights[i]=cand[i].logw;
            if(!m4_weighted_cap(weights,m,keep,&b->rng,indices,corrected))abort();
            for(size_t i=0;i<keep;++i){chosen[i]=(uint32_t)indices[i];if(mode==2)cand[chosen[i]].logw=corrected[i];}
            free(weights);free(corrected);free(indices);
        } else {
'''+OLD+'''
        }'''


def once(source,old,new):
    if source.count(old)!=1:raise ValueError('upstream anchor changed: '+old[:75])
    return source.replace(old,new)


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    args.out.mkdir(exist_ok=False);frozen=args.out/'sources';(frozen/'src').mkdir(parents=True);(frozen/'tools').mkdir()
    sources=['board','belief','front','eval','movemodel','m4movefeatures','m4resample']
    for path in sorted((args.source/'src').glob('*.h')):shutil.copyfile(path,frozen/'src'/path.name)
    for name in sources:shutil.copyfile(args.source/'src'/(name+'.c'),frozen/'src'/(name+'.c'))
    shutil.copyfile(args.source/'tools/m4_prior_replay.c',frozen/'tools/m4_prior_replay.c')
    original=(frozen/'src/belief.c').read_text()
    generated=once(original,'#include "movemodel.h"','#include "movemodel.h"\n'+INCLUDE)
    generated=once(generated,OLD,NEW)
    generated=once(generated,'    if (b->count <= target) return b->count;\n',
                   '    if (b->count <= target) return b->count;\n    if(m4_cap_mode())return m4_heap_shrink(b,target,m4_cap_mode());\n')
    (frozen/'src/belief-cap.c').write_text(generated)
    paths=[frozen/'src'/((s if s!='belief' else 'belief-cap')+'.c') for s in sources]
    command=['gcc','-O2','-std=c11','-Wall','-Wextra','-Wpedantic',*[str(p) for p in paths],
             str(frozen/'tools/m4_prior_replay.c'),'-Wl,--wrap=move_logits','-lm','-o',str(args.out/'runner')]
    compiled=subprocess.run(command,text=True,capture_output=True)
    (args.out/'build.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise RuntimeError('compile failed; inspect build.log')
    shutil.copyfile(__file__,args.out/'build.py')
    manifest=dict(command=command,base_commit=subprocess.check_output(['git','-C',str(args.source),'rev-parse','HEAD'],text=True).strip(),
        source_sha256={str(p.relative_to(frozen)):sha(p) for p in sorted(frozen.rglob('*')) if p.is_file()},
        runner_sha256=sha(args.out/'runner'),builder_sha256=sha(Path(__file__)),
        modes={'0':'unmodified weighted cap','1':'heap selection / original weights','2':'heap selection / threshold-corrected weights'},
        notes='Standalone generated source only; no active engine/header change.')
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'runner_sha256':manifest['runner_sha256'],'build_stderr':compiled.stderr}))


if __name__=='__main__':main()
