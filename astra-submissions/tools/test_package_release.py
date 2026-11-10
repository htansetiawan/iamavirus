"""Packaging regression fixtures; never create a numbered real archive."""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import package_release as package


class ReleaseNumbering(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.astra=self.root/'astra-submissions';self.fable=self.root/'fable-submissions'
        self.source=self.astra/'fixture';self.source.mkdir(parents=True);self.fable.mkdir()
        (self.fable/'iamavirus-v37-fixture.zip').write_bytes(b'fixture parent')
        (self.source/'run.sh').write_bytes(b'FOW_MODE:-hybrid')
        (self.source/'RELEASE.md').write_text('synthetic fixture')
        (self.source/'model').mkdir();(self.source/'model/weights').write_bytes(b'unchanged synthetic weights')
        self.origin=self.astra/'origin.json'
        self.origin.write_text(json.dumps(dict(archive_sha256='synthetic',initial_files_sha256={name:hashlib.sha256((self.source/name).read_bytes()).hexdigest() for name in ('run.sh','model/weights')})))
        for name,value in [('ROOT',self.root),('ASTRA',self.astra)]:
            patcher=patch.object(package,name,value);patcher.start();self.addCleanup(patcher.stop)
    def invoke(self):
        with patch('sys.argv',['package_release','--source',str(self.source),'--origin',str(self.origin),'--expected-version','38']),redirect_stdout(io.StringIO()):package.main()
    def test_other_suffix_cannot_reuse_major_or_replace_manifest(self):
        existing=self.astra/'iamavirus-v38-mist-c-allchildren.zip';existing.write_bytes(b'published')
        manifest=self.astra/'v38-manifest.json';manifest.write_text('published manifest')
        with self.assertRaises(FileExistsError):self.invoke()
        self.assertEqual(existing.read_bytes(),b'published');self.assertEqual(manifest.read_text(),'published manifest')
        self.assertFalse((self.astra/'iamavirus-v38-hybrid.zip').exists())
    def test_archive_alone_reserves_major(self):
        (self.astra/'iamavirus-v38.zip').write_bytes(b'published')
        with self.assertRaises(FileExistsError):self.invoke()
        self.assertFalse((self.astra/'v38-manifest.json').exists())
    def test_manifest_alone_reserves_major(self):
        (self.astra/'v38-manifest.json').write_text('preserved')
        with self.assertRaises(FileExistsError):self.invoke()
        self.assertEqual((self.astra/'v38-manifest.json').read_text(),'preserved')
    def test_minor_alias_reserves_major(self):
        (self.astra/'iamavirus-v38.1-candidate.zip').write_bytes(b'published')
        with self.assertRaises(FileExistsError):self.invoke()
    def test_neighbor_major_does_not_false_match(self):
        (self.astra/'iamavirus-v380-fixture.zip').write_bytes(b'other major')
        self.invoke();self.assertTrue((self.astra/'iamavirus-v38-hybrid.zip').is_file())
    def test_success_has_exact_content_and_second_call_preserves_it(self):
        self.invoke();path=self.astra/'iamavirus-v38-hybrid.zip';before=path.read_bytes();manifest=(self.astra/'v38-manifest.json').read_bytes()
        with zipfile.ZipFile(path) as archive:
            self.assertEqual(archive.read('model/weights'),b'unchanged synthetic weights')
            self.assertEqual(json.loads(archive.read('astra-release.json'))['fable_version'],37)
        self.assertEqual(json.loads(manifest)['archive_sha256'],hashlib.sha256(before).hexdigest())
        with self.assertRaises(FileExistsError):self.invoke()
        self.assertEqual(path.read_bytes(),before);self.assertEqual((self.astra/'v38-manifest.json').read_bytes(),manifest)
    def test_fable_drift_fails_before_publication(self):
        with patch.object(package,'next_version',side_effect=[38,39]):
            with self.assertRaises(RuntimeError):self.invoke()
        self.assertFalse((self.astra/'iamavirus-v38-hybrid.zip').exists());self.assertFalse(list(self.astra.glob('astra-package-*')))
    def test_plain_fable_name_and_candidates_count(self):
        (self.fable/'iamavirus-v39.zip').write_bytes(b'parent');(self.fable/'iamavirus-v40.1-candidate-hybrid.zip').write_bytes(b'parent')
        self.assertEqual(package.next_version(),41)

if __name__=='__main__':unittest.main()
