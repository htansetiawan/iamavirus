"""Inventory M4 and check unchanged generic fixtures with archived v38 CFR."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/m4-source-review-20261112'
BUILD=HERE/'build'
ENGINE=ROOT.parent/'fowsearch-c'
TIP='a521bf8c14a1253c3effc87dae15e55de47b4e13'
ZIP=ROOT/'astra-submissions/iamavirus-v38-mist-c-allchildren.zip'
TESTS=['test_gadget','test_kluss','test_gadget_controller','test_gadget_kuhn','test_kluss_carry','test_kluss_prepare']


def sha(data):return hashlib.sha256(data).hexdigest()
def save(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def show(path):return subprocess.check_output(['git','-C',str(ENGINE),'show',TIP+':'+path])


def main():
    plan=json.loads((OUT/'plan.json').read_text())
    assert sha(Path(__file__).read_bytes())==plan['source_sha256']
    assert sha(ZIP.read_bytes())==plan['archive_sha256']
    assert subprocess.check_output(['git','-C',str(ENGINE),'rev-parse','astra/m4'],text=True).strip()==TIP
    allocation=json.loads((ROOT/'chatroom/cores.json').read_text())['allocation']
    assert any(a.get('lease')=='424-m4-core-bridge' and a.get('cores')==[2,3] for a in allocation)
    os.sched_setaffinity(0,{2,3})
    BUILD.mkdir(exist_ok=False);(BUILD/'src').mkdir();(BUILD/'tests').mkdir()
    catalog=[]
    for path,expected in plan['m4_sources'].items():
        blob=show(path);assert sha(blob)==expected,path
        catalog.append(dict(path=path,sha256=expected,bytes=len(blob)))
        if path in ['src/gadget.c','src/gadget.h','src/kluss.c','src/kluss.h'] or path.startswith('tests/'):
            (BUILD/path).write_bytes(blob)
    comparison=[]
    with zipfile.ZipFile(ZIP) as z:
        for name in ('cfr.c','cfr.h','belief.h','search.h','eval.h','fow.h','sfeval.h'):
            blob=z.read('src/'+name);old=show('src/'+name)
            comparison.append(dict(file=name,identical=old==blob,m4_sha256=sha(old),v38_sha256=sha(blob)))
            if name in ('cfr.c','cfr.h'):
                assert sha(blob)==plan['v38_core_sha256'][name]
                (BUILD/'src'/name).write_bytes(blob)
    save(OUT/'inventory.json',dict(m4_commit=TIP,archive_sha256=plan['archive_sha256'],sources=catalog,interface_comparison=comparison))
    commands=[];deadline=time.monotonic()+120
    for name in TESTS:
        argv=['gcc','-std=c11','-O2','src/cfr.c','src/gadget.c','src/kluss.c','tests/'+name+'.c','-lm','-o',name]
        p=subprocess.run(argv,cwd=BUILD,capture_output=True,text=True,timeout=min(15,deadline-time.monotonic()))
        row=dict(kind='compile',test=name,argv=argv,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr)
        commands.append(row)
        with (OUT/'commands.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
        if p.returncode!=0:continue
        run=subprocess.run([str(BUILD/name)],cwd=BUILD,capture_output=True,text=True,timeout=min(30,deadline-time.monotonic()))
        row=dict(kind='fixture',test=name,argv=[str(BUILD/name)],exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr,binary_sha256=sha((BUILD/name).read_bytes()))
        commands.append(row)
        with (OUT/'commands.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
    passed=all(any(c['test']==name and c['kind']=='fixture' and c['exit_code']==0 for c in commands) for name in TESTS)
    # The archive and named branch are read-only inputs; current checkout files are not patched.
    assert sha(ZIP.read_bytes())==plan['archive_sha256']
    result=dict(completed=True,at=datetime.now(timezone.utc).isoformat(),all_six_generic_fixtures_pass=passed,
                m4_commit=TIP,v38_core_sha256=plan['v38_core_sha256'],
                fixtures=[{k:c[k] for k in ('test','exit_code','stdout','stderr','binary_sha256')} for c in commands if c['kind']=='fixture'],
                asserts_enabled=True,old_fixture_sources_unchanged=True,
                tested='Original M4 generic gadget/knowledge/carry fixtures against exact deployed-v38 cfr.c/h, not a new algorithm.',
                not_tested=['Chess adapter, observation frontend or opponent-model integration','Current v38 pending-initializer paths not exercised by these old fixtures','Native asynchronous scorer, total budget, memory or policy quality','Whole-game exploitability, strength or reproduction of original Obscuro'],
                source_sha256=sha(Path(__file__).read_bytes()))
    save(OUT/'result.json',result)
    print(json.dumps({'completed':True,'generic_fixture_passes':sum(c['exit_code']==0 for c in result['fixtures']),'expected':6,'all_pass':passed,'chess_policy_or_backend_runs':0}))


if __name__=='__main__':main()
