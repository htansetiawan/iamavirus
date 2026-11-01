#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent/'stable-mix-20261101/build/base'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

build = HERE/'build'; build.mkdir(exist_ok=False)
shutil.copytree(BASE/'src', build/'src')
shutil.copyfile(BASE/'build.sh', build/'build.sh')
for name in ['data','bin']: (build/name).symlink_to(BASE/name, target_is_directory=True)
# Reuse only the previously independently tested value/hash primitives.
prior = HERE.parent/'frozen-tree-20261101/src/audit.h'
numeric = prior.read_text().split('static AuditInitial *audit_initial')[0]
(build/'src/numeric_audit.h').write_text(numeric)
shutil.copyfile(HERE/'exchange_audit.h',build/'src/exchange_audit.h')
p=build/'src/gtcfr.c'; before=p.read_text()
after=before.replace('int gtcfr_decide(', '#include "exchange_audit.h"\n\nint gtcfr_decide(')
anchor='    free(x); free(idx); free(share); free(chance_kids); free(chance_p);'
assert after.count(anchor)==1
after=after.replace(anchor,'    exchange_audit(&t,b,idx,share,K,root_I,&ours,out,x);\n'+anchor)
p.write_text(after)
r=subprocess.run(['bash','build.sh'],cwd=build,capture_output=True,text=True)
(HERE/'build.log').write_text(r.stdout+r.stderr);r.check_returncode()
pins={'archive_sha256':'41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c',
      'base_gtcfr_sha256':hashlib.sha256(before.encode()).hexdigest(),
      'files':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'build.py',HERE/'exchange_audit.h',build/'src/gtcfr.c',build/'src/numeric_audit.h',build/'mist',BASE/'bin/stockfish',BASE/'data/history.bin']}}
archive=ROOT/'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
assert sha(archive)==pins['archive_sha256']
(HERE/'provenance.json').write_text(json.dumps(pins,indent=2)+'\n')
print('Built isolated post-choice exchange instrumentation')
