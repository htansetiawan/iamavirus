#!/usr/bin/env python3
"""Build the general belief diagnostic against a verified frozen native source."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ASTRA = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, out = args.source.resolve(), args.output.resolve()
    if not out.is_relative_to(ASTRA):
        parser.error('build must stay under Astra')
    receipt = source / 'integration-manifest.json'
    manifest = json.loads(receipt.read_text())
    for name, digest in manifest['files_sha256'].items():
        if sha(source / name) != digest:
            raise ValueError('frozen source changed: ' + name)
    out.mkdir(parents=True, exist_ok=False)
    for name in manifest['files_sha256']:
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source / name).read_bytes())
    (out / 'probe.cc').write_bytes((ASTRA / 'tools/probe_belief.cc').read_bytes())
    units = ['probe', 'belief', 'opponent_model', 'observation', 'position', 'move', 'bitboard']
    command = ['g++', '-O2', '-std=c++20', '-Wall', '-Wextra', '-Werror', '-mpopcnt', '-I'+str(out),
               *(str(out/(name+'.cc')) for name in units), '-o', str(out/'probe')]
    with (out/'build.log').open('w') as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    result = {'source_receipt': str(receipt), 'source_receipt_sha256': sha(receipt),
              'files_sha256': {str(p.relative_to(out)): sha(p) for p in out.rglob('*')
                               if p.is_file() and p.suffix in ('.h', '.cc')},
              'probe_sha256': sha(out/'probe'), 'builder_sha256': sha(Path(__file__)),
              'command': command, 'scope': 'Diagnostic only; the native belief implementation is unchanged.'}
    (out/'probe-build.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'output': str(out), 'probe_sha256': result['probe_sha256']}))


if __name__ == '__main__':
    main()
