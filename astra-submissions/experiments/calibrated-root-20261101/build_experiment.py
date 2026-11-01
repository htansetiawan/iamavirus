#!/usr/bin/env python3
"""Reconstruct the isolated experiment from a hash-pinned arena archive."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
origin = json.loads((HERE/'implementation-origin.json').read_text())
archive = ROOT/origin['base_archive']
assert hashlib.sha256(archive.read_bytes()).hexdigest() == origin['base_archive_sha256']
build = HERE/'build'
if not build.exists():
    with zipfile.ZipFile(archive) as z:
        z.extractall(build)
for src in (HERE/'src').iterdir():
    shutil.copyfile(src, build/'src'/src.name)
result = subprocess.run(['bash','build.sh'], cwd=build, capture_output=True, text=True)
(HERE/'build.log').write_text(result.stdout+result.stderr)
result.check_returncode()
provenance = {'origin': origin, 'modified_sources': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'src').iterdir())},
              'binary_sha256': hashlib.sha256((build/'mist').read_bytes()).hexdigest(),
              'compiler': subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],
              'default_enabled': False, 'enable_environment': {'mixture': 'MIST_ROOT_CALIB=1', 'residual': 'MIST_ROOT_CALIB=2'}}
(HERE/'build-provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
print(json.dumps(provenance, indent=2))
