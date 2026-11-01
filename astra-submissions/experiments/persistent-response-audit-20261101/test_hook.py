#!/usr/bin/env python3
import hashlib,json,os,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/persistent-response-audit-20261101'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sources=[str(p) for p in sorted((HERE/'build/src').glob('*.c')) if p.name not in ('gtcfr.c','main.c')]
records=[]
for name,flags in [('optimized',['-O2']),('sanitized',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
    binary=HERE/'build'/('hook-'+name)
    cmd=['gcc',*flags,'-pthread','-D_POSIX_C_SOURCE=199309L','-std=c11','-I'+str(HERE/'build/src'),str(HERE/'test_hook.c'),*sources,'-lm','-o',str(binary)]
    r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
    for kind in range(4):
        directory=Path(tempfile.mkdtemp(prefix='astra215-hook-'));path=directory/'br.json'
        env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))};env['ASTRA_BEST_REPLY_TRACE']=str(path);env['ASTRA_BEST_REPLY_FOCUS']='d1d2'
        r=subprocess.run([str(binary),str(path),str(kind)],env=env,capture_output=True,text=True,timeout=60)
        assert r.returncode==0,dict(kind=kind,stderr=r.stderr)
        d=json.loads(path.read_text());assert d['state_unchanged']
        for profile in d['profiles']:
            v=profile['values'];assert all(a>=b-1e-10 for a,b in zip(v,v[1:]));assert abs(v[1]-v[2])<1e-12
            if kind==0:assert abs(v[1]-v[3])<1e-12
            if not profile['worlds']:continue
            worlds=profile['worlds'];assert len(worlds)==(4 if kind==2 else 2)
            assert abs(sum(w['weight'] for w in worlds)-1)<1e-12
            for j in range(4):assert abs(sum(w['weight']*w['values'][j] for w in worlds)-v[j])<1e-12
            assert {w['mode'] for w in worlds}==({-1} if kind<2 else {0,1} if kind==2 else {1})
            for w in worlds:
                if w['mode']==0:assert max(w['values'][1:])-min(w['values'][1:])<1e-12
            if profile['profile']=='d1d2':
                count=len(worlds[0]['replies']);loss=(.5-1.5/count)-(-1)
                expected=0 if kind==0 else .25*loss*(1 if kind==3 else .25)
                assert abs((v[1]-v[3])-expected)<1e-12,(kind,v,expected)
        records.append(dict(build=name,kind=kind,returncode=r.returncode,output=d,stderr=r.stderr))
out=dict(tests=records,source_sha256={str(p):sha(p) for p in [Path(__file__),HERE/'test_hook.c',HERE/'provenance.json']},scope='Four mode/export cases, optimized and ASan/UBSan; analytic restricted gap and branch-weight identities. BR solver is unchanged from the exhaustive 213 checks.')
(OUT/'hook-correctness.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'cases':len(records),'all_passed':True}))
