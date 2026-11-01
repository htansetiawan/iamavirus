#!/usr/bin/env python3
"""Complete trace/BR export hook, including an unallocated disabled model."""
import hashlib,json,os,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE.parents[2]/'astra-submissions/analysis/response-best-reply-r2-20261101'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sources=[str(p) for p in sorted((HERE/'build/src').glob('*.c')) if p.name not in ('gtcfr.c','main.c')];records=[]
for name,flags in [('optimized',['-O2']),('sanitized',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
    binary=HERE/'build'/('hook-'+name)
    cmd=['gcc',*flags,'-pthread','-D_POSIX_C_SOURCE=199309L','-std=c11','-I'+str(HERE/'build/src'),str(HERE/'test_hook.c'),*sources,'-lm','-o',str(binary)]
    build=subprocess.run(cmd,capture_output=True,text=True);assert build.returncode==0,build.stderr
    for restricted in [False,True]:
        directory=Path(tempfile.mkdtemp(prefix='astra213-hook-'));env=os.environ.copy()
        env.update(ASTRA_RESPONSE_TRACE=str(directory/'trace.json'),ASTRA_BEST_REPLY_TRACE=str(directory/'br.json'))
        env.pop('FIXTURE_RESTRICT',None)
        if restricted:env['FIXTURE_RESTRICT']='1'
        r=subprocess.run([str(binary),env['ASTRA_RESPONSE_TRACE']],env=env,capture_output=True,text=True);assert r.returncode==0,r.stderr
        d=json.loads((directory/'br.json').read_text());assert d['state_unchanged']
        assert d['restricted_first_sets']==int(restricted) and d['restricted_later_sets']==0
        for profile in d['profiles']:
            v=profile['values'];assert all(a>=b-1e-12 for a,b in zip(v,v[1:]))
            assert abs(v[1]-v[2])<1e-12
            if not restricted:assert abs(v[1]-v[3])<1e-12
        records.append(dict(mode=name,restricted=restricted,returncode=r.returncode,stderr=r.stderr,output=d))
out=dict(tests=records,source_sha256={str(p):sha(p) for p in [Path(__file__),HERE/'test_hook.c',HERE/'br_audit.h']},
         regression='The first original diagnostic segfaulted hashing the unallocated fixed_policy; both full-hook variants are now exercised.')
(OUT/'hook-correctness.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'hook_cases':len(records),'passed':True}))
