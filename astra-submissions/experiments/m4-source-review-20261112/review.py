"""Review frozen source/fixture receipts without rerunning any native test."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/m4-source-review-20261112'
ENGINE=ROOT.parent/'fowsearch-c'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    plan=json.loads((OUT/'plan.json').read_text());result=json.loads((OUT/'result.json').read_text());inventory=json.loads((OUT/'inventory.json').read_text())
    assert sha(HERE/'check.py')==plan['source_sha256']==result['source_sha256']
    for path,v in plan['m4_sources'].items():
        blob=subprocess.check_output(['git','-C',str(ENGINE),'show',plan['m4_commit']+':'+path])
        assert hashlib.sha256(blob).hexdigest()==v
        if path.startswith('tests/') or path in ('src/gadget.c','src/gadget.h','src/kluss.c','src/kluss.h'):
            assert (HERE/'build'/path).read_bytes()==blob
    archive=ROOT/'astra-submissions/iamavirus-v38-mist-c-allchildren.zip'
    assert sha(archive)==plan['archive_sha256']
    with zipfile.ZipFile(archive) as z:
        for name,v in plan['v38_core_sha256'].items():
            blob=z.read('src/'+name);assert hashlib.sha256(blob).hexdigest()==v
            assert (HERE/'build/src'/name).read_bytes()==blob
    commands=[json.loads(l) for l in (OUT/'commands.jsonl').read_text().splitlines()]
    assert len(commands)==12 and all(c['exit_code']==0 for c in commands)
    expected=['test_gadget','test_kluss','test_gadget_controller','test_gadget_kuhn','test_kluss_carry','test_kluss_prepare']
    assert [c['test'] for c in commands if c['kind']=='fixture']==expected
    assertion_sites=0
    for name in expected:
        compile=next(c for c in commands if c['test']==name and c['kind']=='compile')
        assert '-O2' in compile['argv'] and not any('NDEBUG' in a for a in compile['argv'])
        source=(HERE/'build/tests'/f'{name}.c').read_text()
        assert '#include <assert.h>' in source and '#define NDEBUG' not in source
        assertion_sites+=source.count('assert(')
        actual=next(c for c in commands if c['test']==name and c['kind']=='fixture')
        saved=next(c for c in result['fixtures'] if c['test']==name)
        for key in ('exit_code','stdout','stderr','binary_sha256'):assert actual[key]==saved[key]
        assert sha(HERE/'build'/name)==actual['binary_sha256']
    assert result['all_six_generic_fixtures_pass']
    assert len(inventory['sources'])==len(plan['m4_sources'])==22
    r=dict(passed=True,source_files_pinned=22,exact_archive_core_files=2,original_fixture_sources_unchanged=True,
           compile_and_fixture_receipts=12,fixture_passes=6,source_assertion_sites=assertion_sites,
           native_fixture_reruns=0,chess_policy_or_backend_runs=0,
           limitations=result['not_tested'],source_sha256=sha(Path(__file__)),result_sha256=sha(OUT/'result.json'))
    with (OUT/'review.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
    print(json.dumps(r))


if __name__=='__main__':main()
