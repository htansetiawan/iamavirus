#!/usr/bin/env python3
"""Build a diagnostic against a hash-checked immutable belief runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ASTRA = Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


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
    # Check every native source/header, not just the compiled translation units.
    for name, expected in manifest['files_sha256'].items():
        if sha(source / name) != expected:
            raise ValueError('native source changed: ' + name)
    out.mkdir(parents=True, exist_ok=False)
    for name in manifest['files_sha256']:
        destination = out / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((source / name).read_bytes())
    overlays = ['probe_queen_belief.cc', 'queen_threats.h', 'queen_threats_test.cc']
    for name in overlays:
        (out / name).write_bytes((ASTRA / 'tools' / name).read_bytes())
    common = ['g++', '-O2', '-std=c++20', '-Wall', '-Wextra', '-Werror', '-mpopcnt', '-I' + str(out)]
    native = ['belief', 'opponent_model', 'observation', 'position', 'move', 'bitboard']
    commands = []
    with (out / 'build.log').open('w') as log:
        for name in ['probe_queen_belief', 'queen_threats_test']:
            command = common + [str(out / (x + '.cc')) for x in [name, *native]] + ['-o', str(out / name)]
            subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
            commands.append(command)
    test = subprocess.check_output([str(out / 'queen_threats_test')], text=True)
    report = {'source_receipt': str(receipt), 'source_receipt_sha256': sha(receipt),
              'basis_revision': manifest['basis_revision'], 'files_sha256':
              {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.suffix in ('.cc', '.h')},
              'binaries': {n: sha(out / n) for n in ['probe_queen_belief', 'queen_threats_test']},
              'builder_sha256': sha(Path(__file__)), 'commands': commands, 'tests': test.strip(),
              'scope': 'Offline truth-labelled diagnosis; unchanged native belief; not an arena archive'}
    (out / 'integration-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output': str(out), 'tests': test.strip(), 'binaries': report['binaries']}))


if __name__ == '__main__':
    main()
