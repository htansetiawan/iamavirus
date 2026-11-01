#!/usr/bin/env python3
import hashlib,json,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PARENT=HERE.parent/'response-causal-audit-20261101'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins=json.loads((PARENT/'provenance.json').read_text())
for p,h in pins['source_sha256'].items():assert sha(ROOT/p)==h,p
build=HERE/'build';build.mkdir(exist_ok=False);shutil.copytree(PARENT/'build/src',build/'src')
for name in ['br.h','br_audit.h']:shutil.copyfile(HERE/name,build/'src'/name)
p=build/'src/trace.h';s=p.read_text();needle='    free(values);free(marks);free(initial);';assert s.count(needle)==1
s=s.replace('#include "audit.h"','#include "audit.h"\n#include "br_audit.h"')
s=s.replace(needle,'    br_audit(t,b,indices,shares,count,root_I,moves,result,x);\n'+needle);p.write_text(s)
cmd=['gcc','-O2','-pthread','-D_POSIX_C_SOURCE=199309L','-std=c11',*[str(p.relative_to(build)) for p in sorted((build/'src').glob('*.c'))],'-lm','-o','mist']
r=subprocess.run(cmd,cwd=build,capture_output=True,text=True);(HERE/'build.log').write_text(r.stdout+r.stderr);r.check_returncode()
out=dict(parent_provenance_sha256=sha(PARENT/'provenance.json'),binary_sha256=sha(build/'mist'),command=cmd,
         source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'br.h',HERE/'br_audit.h',*sorted((build/'src').glob('*'))]},
         scope='Read-only best responses after original move choice; no continuation-policy optimization, tree growth, extra CFR iteration or truth input.')
(HERE/'provenance.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'binary':out['binary_sha256']}))
