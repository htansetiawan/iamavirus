#!/usr/bin/env python3
"""Reconstruct the frozen comparison basis and build the isolated root experiment."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
ASTRA = ROOT / 'astra-submissions'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ASTRA / 'candidates/posterior-root')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ort', type=Path, default=Path.home() / 'git/onnxruntime-sdk/onnxruntime-linux-x64-1.24.2')
    args = parser.parse_args()
    basis = json.loads((args.source / 'basis.json').read_text())
    out = args.output.resolve()
    if not out.is_relative_to(ASTRA):
        parser.error('builds must stay under astra-submissions')
    for key in ('root_revision', 'overlay_revision'):
        if not re.fullmatch('[a-f0-9]{40}', basis[key]):
            parser.error('source revisions must be complete Git hashes')
    out.mkdir(parents=True, exist_ok=False)
    def gitfile(revision, name):
        return subprocess.check_output(['git', 'show', revision + ':' + name], cwd=ROOT)
    revision = basis['root_revision']
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', revision], cwd=ROOT, text=True).splitlines()
    for name in names:
        p = Path(name)
        if p.suffix not in ('.cc', '.h') or (len(p.parts) > 1 and p.parts[0] != 'tests'):
            continue
        target = out / p
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(gitfile(revision, name))
    for target, source in basis['overlay_files'].items():
        (out / target).write_bytes(gitfile(basis['overlay_revision'], source))
    benchmark = gitfile(basis['overlay_revision'], basis['benchmark_source']).decode()
    (out / 'benchmark.cc').write_text(re.sub(r'#include "\.\./([^"\n]+)"', r'#include "\1"', benchmark))
    for name, digest in basis['baseline_source_sha256'].items():
        if sha(out / name) != digest:
            raise ValueError('frozen baseline source differs: ' + name)
    for name, fixture in basis.get('fixture_files', {}).items():
        (out / name).write_bytes(gitfile(fixture['revision'], fixture['source']))
        if sha(out / name) != fixture['sha256']:
            raise ValueError('frozen fixture differs: ' + name)
    overlays = {}
    for name in ('engine.cc', 'engine.h', 'posterior_root.h', 'posterior_root_test.cc'):
        (out / name).write_bytes((args.source / name).read_bytes())
        overlays[name] = sha(out / name)
    common = ['g++', '-O2', '-std=c++20', '-Wall', '-Wextra', '-Werror', '-pthread', '-mpopcnt',
              '-DFOW_WITH_ONNX', '-I' + str(out), '-I' + str(args.ort / 'include')]
    sources = ['engine', 'search', 'evaluation', 'transposition', 'regret', 'neural_observation',
               'neural_inference', 'belief', 'opponent_model', 'observation', 'position', 'move', 'bitboard']
    commands, binaries = [], {}
    objects = out / 'objects'; objects.mkdir()
    with (out / 'build.log').open('w') as log:
        for source in sources:
            cmd = common + ['-c', str(out / (source + '.cc')), '-o', str(objects / (source + '.o'))]
            commands.append(cmd)
            subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)
        for name, source in (('benchmark', 'benchmark'), ('engine_test', 'tests/engine_test'),
                             ('posterior_root_test', 'posterior_root_test')):
            cmd = common + [str(out / (source + '.cc'))] + [str(objects / (s + '.o')) for s in sources]
            cmd += ['-L' + str(args.ort / 'lib'), '-Wl,-rpath,' + str(args.ort / 'lib'), '-lonnxruntime', '-o', str(out / name)]
            commands.append(cmd)
            subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)
            binaries[name] = sha(out / name)
    receipt = {'basis': basis, 'overlays': overlays,
               'files_sha256': {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*'))
                                if p.is_file() and p.suffix in ('.cc', '.h')},
               'binaries': binaries, 'commands': commands, 'builder_sha256': sha(Path(__file__)),
               'status': 'research runtime; root mode 0 default; no arena archive'}
    (out / 'build-manifest.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'output': str(out), 'binaries': binaries}), flush=True)


if __name__ == '__main__':
    main()
