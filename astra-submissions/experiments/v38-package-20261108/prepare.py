"""Copy pinned upstream source and the measured patch for a portable build."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = HERE.parent / 'sf-allchildren-20261102'
OUT = ROOT / 'astra-submissions/analysis/v38-package-20261108'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    provenance = json.loads((ROOT / 'astra-submissions/analysis/sf-allchildren-20261102/provenance.json').read_text())
    archive = OLD / 'build/upstream.tar.gz'
    patch = OLD / 'stockfish19-allchildren.patch'
    assert sha(archive) == provenance['archive_sha256']
    assert sha(patch) == provenance['patch_sha256']
    target = HERE / 'build/stockfish'
    target.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive) as t:
        for member in t.getmembers():
            if not member.isfile():
                continue
            rel = Path(*Path(member.name).parts[1:])
            if str(rel) not in provenance['upstream_files']:
                continue
            assert not rel.is_absolute() and '..' not in rel.parts
            p = target / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(t.extractfile(member).read())
            p.chmod(member.mode & 0o777)
            assert sha(p) == provenance['upstream_files'][str(rel)]
    subprocess.run(['patch', '-p1', '-i', str(patch)], cwd=target, check=True)
    pins = {}
    for rel in provenance['upstream_files']:
        p = target / rel
        assert sha(p) == sha(OLD / 'build/candidate' / rel), rel
        pins[rel] = sha(p)
    network = OLD / 'build/candidate/src/nn-1a298aa575a0.nnue'
    assert sha(network) == provenance['network_sha256']
    shutil.copyfile(network, target / 'src' / network.name)
    record = dict(at=datetime.now(timezone.utc).isoformat(), source_files=pins,
                  source_archive_sha256=sha(archive), patch_sha256=sha(patch),
                  network_sha256=sha(network), measured_binary_sha256=sha(OLD / 'build/candidate/src/stockfish'),
                  base_image='nvidia/cuda@sha256:80d4d9ac041242f6ae5d05f9be262b3374e0e0b8bb5a49c6c3e94e192cde4a44',
                  cores=[4, 5], gpu=False, architecture='x86-64-universal', pgo=False,
                  reason='Ubuntu 22.04 libc and static C++ runtime; official eight-slice CPU dispatch.')
    with (OUT / 'source.json').open('x') as f:
        json.dump(record, f, indent=2)
        f.write('\n')
    print(json.dumps(dict(prepared=True, files=len(pins), network_bytes=network.stat().st_size)))

if __name__ == '__main__':
    main()
