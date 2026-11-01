#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
HERE=Path(__file__).resolve().parent;OUT=HERE.parents[2]/'astra-submissions/analysis/response-causal-audit-20261101'
sources=[str(p) for p in sorted((HERE/'build/src').glob('*.c')) if p.name not in ('gtcfr.c','main.c')];records=[]
for name,flags in [('optimized',['-O2']),('sanitized',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
    binary=HERE/'build'/('test-'+name)
    cmd=['gcc',*flags,'-pthread','-D_POSIX_C_SOURCE=199309L','-std=c11','-I'+str(HERE/'build/src'),str(HERE/'test_trace.c'),*sources,'-lm','-o',str(binary)]
    b=subprocess.run(cmd,capture_output=True,text=True);assert b.returncode==0,b.stderr
    out=Path(tempfile.mkdtemp(prefix='astra212-'))/'trace.json';env=os.environ.copy();env['ASTRA_RESPONSE_TRACE']=str(out)
    r=subprocess.run([str(binary),str(out)],env=env,capture_output=True,text=True);assert r.returncode==0,r.stderr
    d=json.loads(out.read_text());reply=d['worlds'][0]['actions'][0]['replies'];n=len(reply);q0=.25*(-.625-.375/n)-.15
    assert abs(d['value']-(.25*q0+.75*.7))<1e-12
    assert abs(d['root_actions'][0]['q']-q0)<1e-12 and abs(d['root_actions'][1]['q']-.7)<1e-12
    assert abs(d['root_actions'][0]['initial_q']-(.25*.3-.75*.2))<1e-12
    capture=next(x for x in reply if x['move']=='d8d2');assert abs(capture['free']-1)<1e-12
    assert all(abs(x['free'])<1e-12 for x in reply if x['move']!='d8d2')
    assert d['chosen']=='d1d3' and len(d['belief'])==2 and len(d['worlds'])==2
    records.append(dict(mode=name,command=cmd,returncode=r.returncode,stderr=r.stderr,output=d))
result=dict(tests=records,test_source_sha256=hashlib.sha256((HERE/'test_trace.c').read_bytes()).hexdigest(),
            driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            oracle='Independent unequal-world numeric calculation, fixed/free opponent mixture and legal reply action labels.',
            prior_fixture_build_error='First ad-hoc fixture command also linked engine main.c, causing duplicate main; corrected source list. No diagnostic or match candidate was changed.')
(OUT/'correctness.json').write_text(json.dumps(result,indent=2)+'\n');print('Optimized and ASan/UBSan trace-export checks passed')
