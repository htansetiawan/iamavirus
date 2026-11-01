#!/usr/bin/env python3
"""Separate observable-survival variant; frozen running candidate untouched."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PRIOR=HERE.parent/'learned-response-search-20261101'
PROOF=HERE.parent/'observable-response-audit-20261101'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(s,a,b):
    assert s.count(a)==1,(a[:80],s.count(a));return s.replace(a,b)

def main():
    pinned=json.loads((PRIOR/'provenance.json').read_text())
    for name,h in pinned['source_sha256'].items():assert sha(ROOT/name)==h,name
    proof_plan=json.loads((ROOT/'astra-submissions/analysis/observable-response-audit-20261101/plan.json').read_text())
    for n in ['proof.c','proof.h']:
        assert sha(PROOF/n)==proof_plan['source_sha256'][str((PROOF/n).relative_to(ROOT))]
    build=HERE/'build';build.mkdir(exist_ok=False);shutil.copytree(PRIOR/'build/src',build/'src')
    originals={p.name:p.read_text() for p in (build/'src').glob('*')}
    for n in ['proof.c','proof.h']:shutil.copyfile(PROOF/n,build/'src'/n)
    shutil.copyfile(HERE/'projection.h',build/'src/projection.h')
    p=build/'src/gtcfr.c';s=p.read_text()
    s=replace(s,'    double response_seconds;','    double response_seconds, response_dominated_mass;\n    unsigned long response_projected_sets, response_projected_actions, response_all_proven;');p.write_text(s)
    p=build/'src/dbr.h';s=p.read_text()
    s=replace(s,'#include "response.h"','#include "response.h"\n#include "proof.h"\n#include "projection.h"')
    s=replace(s,'static double visible_confidence;','static int visible_project;\nstatic double visible_confidence;')
    s=replace(s,'    visible_initialized = 1;','    visible_initialized = 1;\n    visible_project = getenv("ASTRA_VISIBLE_PROJECT") && atoi(getenv("ASTRA_VISIBLE_PROJECT")) == 1;')
    s=replace(s,'    game_restrict(&t->g, I, visible_confidence, q);','''    if (visible_project) {
        uint8_t fatal[256], witness[256];
        if (!observable_fatal(tokens, encoded, moves.count, fatal, witness)) {
            ++t->response_failures; goto done;
        }
        double mass;int removed=project_response(q,fatal,moves.count,&mass);
        if (removed<0) ++t->response_all_proven;
        else if (removed>0) {
            ++t->response_projected_sets;
            t->response_projected_actions += (unsigned long)removed;
            t->response_dominated_mass += mass;
        }
    }
    game_restrict(&t->g, I, visible_confidence, q);''')
    s=replace(s,'seconds %.9g load_failed %d\\n",','seconds %.9g load_failed %d projected_sets %lu projected_actions %lu dominated_mass %.9g all_proven %lu\\n",')
    s=replace(s,'            t->response_seconds, visible_load_failed);','            t->response_seconds, visible_load_failed, t->response_projected_sets, t->response_projected_actions, t->response_dominated_mass, t->response_all_proven);');p.write_text(s)
    sources=sorted(str(p.relative_to(build)) for p in (build/'src').glob('*.c'))
    cmd=['gcc','-O2','-pthread','-D_POSIX_C_SOURCE=199309L','-std=c11',*sources,'-lm','-o','mist']
    r=subprocess.run(cmd,cwd=build,text=True,capture_output=True);(HERE/'build.log').write_text(r.stdout+r.stderr);r.check_returncode()
    patch=[]
    for name,before in originals.items():
        after=(build/'src'/name).read_text()
        if before!=after:patch.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/'+name,tofile='b/src/'+name))
    (HERE/'patch.diff').write_text(''.join(patch))
    for name in ['cfr.c','cfr.h','belief.c','main.c','board.c','movemodel.c','response.c','adapter.c']:
        assert sha(build/'src'/name)==sha(PRIOR/'build/src'/name),name
    result=dict(parent_provenance_sha256=sha(PRIOR/'provenance.json'),parent_binary_sha256=sha(PRIOR/'build/mist'),
                binary_sha256=sha(build/'mist'),model_sha256=pinned['model_sha256'],compiler=cmd,
                source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'projection.h',HERE/'patch.diff',*sorted((build/'src').glob('*'))]})
    (HERE/'provenance.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'binary':result['binary_sha256'],'unchanged_parent':result['parent_binary_sha256']}))

if __name__=='__main__':main()
