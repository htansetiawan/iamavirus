#!/usr/bin/env python3
"""Reuse the verified DBR solver; add the frozen observable student only."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PRIOR=HERE.parent/'data-biased-search-20261101'
NEURAL=HERE.parent/'visible-response-20261101'
MODEL=ROOT/'astra-submissions/analysis/visible-response-20261101/models/response.bin'
BUILD=HERE/'build'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(s,a,b):
    assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b)

def main():
    old=json.loads((PRIOR/'provenance.json').read_text())
    assert sha(MODEL)=='45a41cf4ecaae9324472ae93a81b349d597cec20364a7c73ef66e513df077c97'
    for rel,h in old['source_sha256'].items():assert sha(ROOT/rel)==h,rel
    BUILD.mkdir(exist_ok=False);shutil.copytree(PRIOR/'build/src',BUILD/'src')
    originals={p.name:p.read_text() for p in (BUILD/'src').glob('*')}
    for name in ('response.c','response.h'):shutil.copyfile(NEURAL/name,BUILD/'src'/name)
    for name in ('adapter.c','adapter.h','dbr.h'):shutil.copyfile(HERE/name,BUILD/'src'/name)
    p=BUILD/'src/gtcfr.c';s=p.read_text()
    s=replace(s,'    Game g;','    Game g;\n    uint64_t *response_keys; int response_key_cap;\n    unsigned long response_calls, response_reuses, response_failures, response_mismatches;\n    double response_seconds;')
    s=replace(s,'    if (t->g.n_infosets > before) dbr_install(t, I, &leaf);','    dbr_install(t, I, &leaf);')
    s=replace(s,'    free(t.leaves);','    free(t.response_keys);\n    free(t.leaves);');p.write_text(s)
    sources=sorted(str(p.relative_to(BUILD)) for p in (BUILD/'src').glob('*.c'))
    cmd=['gcc','-O2','-pthread','-D_POSIX_C_SOURCE=199309L','-std=c11',*sources,'-lm','-o','mist']
    r=subprocess.run(cmd,cwd=BUILD,capture_output=True,text=True)
    (HERE/'build.log').write_text(r.stdout+r.stderr);r.check_returncode()
    patch=[]
    for name,before in originals.items():
        after=(BUILD/'src'/name).read_text()
        if before!=after:patch.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/'+name,tofile='b/src/'+name))
    (HERE/'patch.diff').write_text(''.join(patch))
    for name in ('cfr.c','cfr.h','belief.c','belief.h','main.c','sfeval.c','board.c','movemodel.c'):
        assert sha(BUILD/'src'/name)==sha(PRIOR/'build/src'/name),name
    record=dict(prior_provenance_sha256=sha(PRIOR/'provenance.json'),model_sha256=sha(MODEL),
                binary_sha256=sha(BUILD/'mist'),compiler=cmd,
                source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [HERE/'build.py',HERE/'adapter.c',HERE/'adapter.h',HERE/'dbr.h',HERE/'patch.diff',*sorted((BUILD/'src').glob('*'))]},
                inherited_solver_evidence={str((ROOT/'astra-submissions/analysis/data-biased-search-20261101'/n).relative_to(ROOT)):sha(ROOT/'astra-submissions/analysis/data-biased-search-20261101'/n) for n in ['numeric-tests.json','extensive-tests.json','sanitizer-tests.json']})
    (HERE/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'binary_sha256':record['binary_sha256'],'model_sha256':record['model_sha256'],'unchanged_solver':True}))

if __name__=='__main__':main()
