#!/usr/bin/env python3
import hashlib,json,os,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/persistent-response-20261101';PARENT=HERE.parent/'observable-response-search-20261101'
MODEL=ROOT/'astra-submissions/analysis/visible-response-20261101/models/response.bin'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compile(name,source,flags):
    binary=HERE/'build'/name
    cmd=['gcc',*flags,'-pthread','-D_POSIX_C_SOURCE=199309L','-std=c11','-I'+str(source),str(HERE/'test_native.c'),*[str(p) for p in sorted(source.glob('*.c')) if p.name not in ('main.c','gtcfr.c')],'-lm','-o',str(binary)]
    r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
    return binary,cmd
def run(binary,persistent,confidence,fixture=False,missing=False):
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))};env.update(ASTRA_VISIBLE_MODEL='missing' if missing else str(MODEL),ASTRA_VISIBLE_CONFIDENCE=str(confidence),ASTRA_VISIBLE_PROJECT='1',ASTRA_PERSISTENT=str(persistent))
    r=subprocess.run([str(binary)]+(['fixture'] if fixture else []),env=env,capture_output=True,text=True,timeout=60)
    record=dict(binary=str(binary),persistent=persistent,confidence=confidence,fixture=fixture,missing=missing,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
    assert r.returncode==0,record
    record['output']=json.loads(r.stdout);return record
def main():
    base,base_cmd=compile('native-base',PARENT/'build/src',['-O2']);records=[];commands=[base_cmd];oracle={}
    for c in [0,.25,1]:
        row=run(base,0,c);records.append(row);oracle[c]=row['output']
    missing_base=run(base,0,.25,missing=True);records.append(missing_base)
    for name,flags in [('optimized',['-O2']),('sanitized',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
        binary,cmd=compile('native-'+name,HERE/'build/src',[*flags,'-DHAS_MODE']);commands.append(cmd)
        for c in [0,.25,1]:
            row=run(binary,0,c);assert row['output']==oracle[c],(name,c,row,oracle[c]);records.append(row)
        row=run(binary,1,0);assert row['output']==oracle[0];records.append(row)
        row=run(binary,1,.25,missing=True);assert row['output']==missing_base['output'];records.append(row)
        for c,branches in [(.25,2),(1,1)]:
            row=run(binary,1,c);assert f'branches {branches} ' in row['stderr'];assert 'failures 0 mismatches 0' in row['stderr'];records.append(row)
        row=run(binary,1,.25,fixture=True);assert row['output']['own_infosets_shared'];records.append(row)
    result=dict(runs=records,commands=commands,source_sha256={str(p):sha(p) for p in [Path(__file__),HERE/'test_native.c',HERE/'provenance.json']},model_sha256=sha(MODEL),
                scope='Deterministic zero-budget two-ply search parity, mode endpoints/fallback and three-ply mode persistence. Optimized plus full-engine ASan/UBSan. No playing-strength claim.')
    (OUT/'native-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'runs':len(records),'all_passed':True}))
if __name__=='__main__':main()
