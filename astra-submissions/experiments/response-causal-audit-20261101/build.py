#!/usr/bin/env python3
import hashlib,json,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PARENT=HERE.parent/'observable-response-search-20261101'
AUDIT=HERE.parent/'frozen-tree-20261101'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(s,a,b):assert s.count(a)==1,a;return s.replace(a,b)
provenance=json.loads((PARENT/'provenance.json').read_text())
for p,h in provenance['source_sha256'].items():assert sha(ROOT/p)==h,p
assert sha(AUDIT/'src/audit.h')==json.loads((AUDIT/'provenance.json').read_text())['audit_sha256']
build=HERE/'build';build.mkdir(exist_ok=False);shutil.copytree(PARENT/'build/src',build/'src')
shutil.copyfile(AUDIT/'src/audit.h',build/'src/audit.h');shutil.copyfile(HERE/'trace.h',build/'src/trace.h')
p=build/'src/gtcfr.c';s=p.read_text();s=replace(s,'int gtcfr_decide(','#include "trace.h"\n\nint gtcfr_decide(')
s=replace(s,'    game_finalize(&t.g);','    game_finalize(&t.g);\n    double *trace_start=trace_initial(&t.g,ours.count);')
s=replace(s,'    dbr_report(&t, x);','    dbr_report(&t, x);\n    trace_final(&t,b,idx,share,K,root_I,&ours,out,x,trace_start);');p.write_text(s)
cmd=['gcc','-O2','-pthread','-D_POSIX_C_SOURCE=199309L','-std=c11',*[str(p.relative_to(build)) for p in sorted((build/'src').glob('*.c'))],'-lm','-o','mist']
r=subprocess.run(cmd,cwd=build,capture_output=True,text=True);(HERE/'build.log').write_text(r.stdout+r.stderr);r.check_returncode()
pins=dict(parent_provenance_sha256=sha(PARENT/'provenance.json'),parent_binary_sha256=sha(PARENT/'build/mist'),binary_sha256=sha(build/'mist'),command=cmd,
          source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'trace.h',*sorted((build/'src').glob('*'))]},scope='Post-decision observables-only audit; initial leaf-copy can affect wall timing; no policy candidate.')
(HERE/'provenance.json').write_text(json.dumps(pins,indent=2)+'\n');print(json.dumps({'binary':pins['binary_sha256']}))
