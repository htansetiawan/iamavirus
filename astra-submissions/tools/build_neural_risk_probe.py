#!/usr/bin/env python3
"""Build actor-only risk instrumentation against a verified frozen engine."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ASTRA = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--ort', type=Path, default=Path.home() / 'git/onnxruntime-sdk/onnxruntime-linux-x64-1.24.2')
    args = p.parse_args()
    source, out = args.source.resolve(), args.output.resolve()
    if not out.is_relative_to(ASTRA):
        p.error('build must remain under Astra')
    receipt = source / 'integration-manifest.json'
    original = json.loads(receipt.read_text())
    for name, digest in original['files_sha256'].items():
        if sha(source / name) != digest:
            raise ValueError('frozen source changed: ' + name)
    out.mkdir(parents=True, exist_ok=False)
    for name in original['files_sha256']:
        dest = out / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((source / name).read_bytes())
    header = out / 'engine.h'
    text = header.read_text()
    needle = '  inline const BeliefState& belief() const { return belief_; }'
    if text.count(needle) != 1:
        raise ValueError('unknown engine diagnostic access point')
    accessor = '''
  // Offline instrumentation only; forwards to the unchanged runtime function.
  std::vector<double> DiagnosticKingLossProbabilities(const MoveList& moves,
                                                     int en_passant) const {
    return KingLossProbabilities(moves, en_passant);
  }
'''
    header.write_text(text.replace(needle, needle + accessor))
    (out / 'risk_probe.cc').write_bytes((ASTRA / 'tools/probe_neural_risk.cc').read_bytes())
    units = ['risk_probe', 'engine', 'search', 'evaluation', 'transposition', 'regret',
             'neural_observation', 'neural_inference', 'belief', 'opponent_model',
             'observation', 'position', 'move', 'bitboard']
    command = ['g++', '-O2', '-std=c++20', '-Wall', '-Wextra', '-Werror', '-pthread', '-mpopcnt',
               '-DFOW_WITH_ONNX', '-I' + str(out), '-I' + str(args.ort / 'include'),
               *(str(out / (u + '.cc')) for u in units), '-L' + str(args.ort / 'lib'),
               '-Wl,-rpath,' + str(args.ort / 'lib'), '-lonnxruntime', '-o', str(out / 'probe')]
    with (out / 'build.log').open('w') as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    result = {'source_receipt': str(receipt), 'source_receipt_sha256': sha(receipt),
              'files_sha256': {str(x.relative_to(out)): sha(x) for x in out.rglob('*')
                               if x.suffix in ('.h', '.cc')}, 'probe_sha256': sha(out / 'probe'),
              'command': command, 'builder_sha256': sha(Path(__file__)),
              'scope': 'Actor-only diagnostic; public forwarding accessor is the only engine source change.'}
    (out / 'probe-build.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'output': str(out), 'probe_sha256': result['probe_sha256']}))


if __name__ == '__main__':
    main()
