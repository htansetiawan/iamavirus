#!/usr/bin/env python3
"""Read-only post-choice audit on a copy of the frozen persistent candidate."""
import hashlib,json,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PARENT=HERE.parent/'persistent-response-20261101'
BR=HERE.parent/'response-best-reply-r2-20261101'
AUDIT=HERE.parent/'frozen-tree-20261101/src/audit.h'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
pins=json.loads((PARENT/'provenance.json').read_text())
for p,h in pins['source_sha256'].items():assert sha(ROOT/p)==h,p
brpins=json.loads((BR/'provenance.json').read_text())
for name in ['br.h','br_audit.h']:
    assert sha(BR/name)==brpins['source_sha256'][str((BR/name).relative_to(ROOT))]
assert sha(AUDIT)==json.loads((HERE.parent/'frozen-tree-20261101/provenance.json').read_text())['audit_sha256']
build=HERE/'build';build.mkdir(exist_ok=False);shutil.copytree(PARENT/'build/src',build/'src')
shutil.copyfile(AUDIT,build/'src/audit.h');shutil.copyfile(BR/'br.h',build/'src/br.h')
s=(BR/'br_audit.h').read_text()
s=replace(s,'            const Position *position=&b->items[indices[k]];char board[65];pos_to_board_string(position,board);',
'''            const Position *position=&b->items[indices[k]];char board[65];pos_to_board_string(position,board);
            int mode=t->persistent?persistent_mode(t->model_prior,k%persistent_count(t->model_prior)):-1;''')
s=replace(s,'\\"index\\":%d,\\"board\\":\\"%s\\",\\"weight\\":%.17g',
            '\\"index\\":%d,\\"board\\":\\"%s\\",\\"weight\\":%.17g,\\"branch\\":%d,\\"mode\\":%d,\\"castle\\":%" PRIu64 ",\\"ep\\":%d')
s=replace(s,'indices[k],board,shares[k],v[0][id]', 'indices[k],board,shares[k],k,mode,position->castle_rooks,position->ep,v[0][id]')
(build/'src/br_audit.h').write_text(s)
p=build/'src/gtcfr.c';s=p.read_text()
s=replace(s,'int gtcfr_decide(', '#include "audit.h"\n#include "br_audit.h"\n\nint gtcfr_decide(')
s=replace(s,'    dbr_report(&t, x);','''    dbr_report(&t, x);
    if(getenv("ASTRA_BEST_REPLY_TRACE")) {
        int *bi=malloc((size_t)branches*sizeof(int));double *bw=malloc((size_t)branches*sizeof(double));assert(bi&&bw);
        const GameNode *rn=&t.g.nodes[t.g.root];assert(rn->count==branches);
        for(int j=0;j<branches;++j){bi[j]=idx[j/modes];bw[j]=t.g.prob[rn->first+j];}
        br_audit(&t,b,bi,bw,branches,root_I,&ours,out,x);free(bi);free(bw);
    }''');p.write_text(s)
cmd=['gcc','-O2','-pthread','-D_POSIX_C_SOURCE=199309L','-std=c11',*[str(p.relative_to(build)) for p in sorted((build/'src').glob('*.c'))],'-lm','-o','mist']
r=subprocess.run(cmd,cwd=build,text=True,capture_output=True);(HERE/'build.log').write_text(r.stdout+r.stderr);r.check_returncode()
result=dict(parent_provenance_sha256=sha(PARENT/'provenance.json'),parent_binary_sha256=sha(PARENT/'build/mist'),binary_sha256=sha(build/'mist'),command=cmd,
            source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),*sorted((build/'src').glob('*'))]},
            scope='Read-only post-choice BR audit; duplicated physical index mapping, exact root chance weights, shared own policy. No playing-policy change.')
(HERE/'provenance.json').write_text(json.dumps(result,indent=2)+'\n');print(result['binary_sha256'])
