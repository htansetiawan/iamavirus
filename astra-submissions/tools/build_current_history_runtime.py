#!/usr/bin/env python3
"""Freeze a pinned root revision and overlay the rebased Astra belief patch.

The root checkout is read only. New binaries and a complete source receipt go
into a fresh Astra build directory. This creates no arena archive.
"""
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
    parser.add_argument('--source', type=Path, default=ASTRA / 'candidates/history-current')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--control', action='store_true')
    parser.add_argument('--ort', type=Path, default=Path.home() / 'git/onnxruntime-sdk/onnxruntime-linux-x64-1.24.2')
    args = parser.parse_args()
    basis = json.loads((args.source / 'basis.json').read_text())
    revision = basis['basis_revision']
    if not re.fullmatch('[a-f0-9]{40}', revision):
        parser.error('basis must pin a full Git commit hash')
    output = args.output.resolve()
    if not output.is_relative_to(ASTRA):
        parser.error('research builds must stay under astra-submissions')
    output.mkdir(parents=True, exist_ok=False)
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', revision], cwd=ROOT, text=True).splitlines()
    originals = {}
    for name in names:
        p = Path(name)
        if p.suffix not in ('.cc', '.h') or (len(p.parts) > 1 and p.parts[0] != 'tests'):
            continue
        if p.is_absolute() or '..' in p.parts:
            raise ValueError('unsafe tracked source path')
        target = output / p
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(subprocess.check_output(['git', 'show', revision + ':' + name], cwd=ROOT))
        originals[name] = sha(target)
    for name, digest in basis['basis_files'].items():
        if originals.get(name) != digest:
            raise ValueError('basis hash mismatch: ' + name)
    overlays = {}
    if not args.control:
        for name in ('belief.h', 'belief.cc', 'engine.h', 'engine.cc', 'history_test.cc'):
            (output / name).write_bytes((args.source / name).read_bytes())
            overlays[name] = sha(output / name)
    benchmark = ASTRA / 'implementation/tools/benchmark_corpus.cc'
    (output / 'benchmark.cc').write_text(re.sub(r'#include "\.\./([^"\n]+)"', r'#include "\1"', benchmark.read_text()))
    (output / 'probe.cc').write_bytes((ASTRA / 'tools/probe_belief.cc').read_bytes())
    common = ['g++', '-O2', '-std=c++20', '-Wall', '-Wextra', '-Werror', '-pthread', '-mpopcnt', '-I' + str(output)]
    belief = ['belief', 'opponent_model', 'observation', 'position', 'move', 'bitboard']
    engine = ['engine', 'search', 'evaluation', 'transposition', 'regret', 'neural_observation', 'neural_inference', *belief]
    tasks = [('probe', ['probe', *belief], False),
             ('belief_test', ['tests/belief_test', *belief], False),
             ('engine_test', ['tests/engine_test', *engine], False),
             ('benchmark', ['benchmark', *engine], True)]
    if not args.control:
        tasks.append(('history_test', ['history_test', *belief], False))
    commands = []
    with (output / 'build.log').open('w') as log:
        for name, sources, neural in tasks:
            command = list(common)
            if neural:
                command += ['-DFOW_WITH_ONNX', '-I' + str(args.ort / 'include')]
            command += [str(output / (source + '.cc')) for source in sources]
            if neural:
                command += ['-L' + str(args.ort / 'lib'), '-Wl,-rpath,' + str(args.ort / 'lib'), '-lonnxruntime']
            command += ['-o', str(output / name)]
            commands.append(command)
            subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    receipt = {'basis_revision': revision, 'basis_source_sha256': originals,
               'control': args.control, 'overlays': overlays,
               'files_sha256': {str(p.relative_to(output)): sha(p) for p in sorted(output.rglob('*'))
                                if p.is_file() and p.suffix in ('.cc', '.h')},
               'binaries': {name: sha(output / name) for name, _, _ in tasks},
               'commands': commands, 'builder_sha256': sha(Path(__file__)),
               'status': 'research runtime only; no submission archive'}
    (output / 'integration-manifest.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'binaries': receipt['binaries']}))


if __name__ == '__main__':
    main()
