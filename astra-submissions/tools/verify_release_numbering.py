"""Read-only deployed-byte audit and expected-refusal packaging check."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'astra-submissions/analysis/release-numbering-20261110'

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    import zipfile
    manifest=ROOT/'astra-submissions/v38-manifest.json';archive=ROOT/'astra-submissions/iamavirus-v38-mist-c-allchildren.zip'
    metadata=json.loads(manifest.read_text());before={str(p.relative_to(ROOT)):sha(p) for p in (manifest,archive)}
    assert before[str(archive.relative_to(ROOT))]==metadata['archive_sha256']
    with zipfile.ZipFile(archive) as zipped:
        anchors=[n for n in zipped.namelist() if (n=='run.sh' or n.endswith('/run.sh')) and hashlib.sha256(zipped.read(n)).hexdigest()==metadata['source_sha256']['run.sh']]
        assert len(anchors)==1,anchors
        prefix=anchors[0][:-len('run.sh')]
        for name,expected in metadata['source_sha256'].items():
            member=prefix+name
            assert zipped.namelist().count(member)==1,member
            assert hashlib.sha256(zipped.read(member)).hexdigest()==expected,name
    source=ROOT/'astra-submissions/tools/package_release.py'
    process=subprocess.run([str(ROOT/'.venv/bin/python'),str(source),'--expected-version','38'],cwd=ROOT,capture_output=True,text=True)
    assert process.returncode==1 and 'FileExistsError' in process.stderr and 'already used' in process.stderr
    (OUT/'current-guard.stdout').write_text(process.stdout);(OUT/'current-guard.stderr').write_text(process.stderr)
    assert all(sha(ROOT/path)==value for path,value in before.items())
    for name in ('prospective-quiet-teacher-20261110','move-metadata-recovery-20261110'):
        plan=json.loads((ROOT/'astra-submissions/analysis'/name/'plan.json').read_text())
        for path,value in plan['dependencies'].items():assert sha(path)==value,path
    assert 'Ran 8 tests' in (OUT/'tests.stderr').read_text() and (OUT/'tests.stderr').read_text().rstrip().endswith('OK')
    report=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,synthetic_tests=8,synthetic_exit_code=0,current_real_tree_guard_exit_code=1,expected_refusal=True,real_files_unchanged=before,archive_member_hashes_verified=len(metadata['source_sha256']),source_sha256=sha(source),auditor_sha256=sha(__file__),numbering='Fable highest37 requires38, but Astra38 is already published; no new version is available under this rule. No auto-bump, reservation or new archive.',teacher_and_metadata_pins_unchanged=True,no_api_gpu_or_engine_changes=True)
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
