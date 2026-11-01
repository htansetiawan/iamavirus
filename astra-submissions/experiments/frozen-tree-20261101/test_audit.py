#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
src = HERE / 'build/src'
sources = [str(p) for p in src.glob('*.c') if p.name not in ('gtcfr.c', 'main.c')]
receipts = []
for mode, flags in [('optimized', ['-O2']), ('sanitized', ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-no-pie'])]:
    exe = HERE / 'build' / ('test-audit-' + mode)
    cmd = ['gcc', '-std=c11', '-D_POSIX_C_SOURCE=200809L', '-pthread', *flags,
           str(HERE / 'test_audit.c'), *sources, '-lm', '-o', str(exe)]
    built = subprocess.run(cmd, capture_output=True, text=True)
    assert built.returncode == 0, built.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True, env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=1:abort_on_error=1'}, timeout=30)
    assert result.returncode == 0, result.stderr
    row = json.loads(result.stdout)
    assert row['selected'] == 'e2e4' and row['greedy'] == 'd2d4'
    assert abs(row['root_value'] + .125) < 1e-12
    assert abs(row['root_deviation_gain'] - .675) < 1e-12
    assert abs(row['selected_value_gap'] - .675) < 1e-12
    assert row['actions'][0]['expanded_mass'] == 0 and row['actions'][1]['expanded_mass'] == .25
    assert row['root_total_variation'] == 0
    receipts.append({'mode': mode, 'exit': result.returncode, 'stderr': result.stderr, 'root_oracle': row})
(HERE / 'correctness.json').write_text(json.dumps(receipts, indent=2) + '\n')
print(json.dumps({'passes': len(receipts), 'checks': 'weighted root values, zero support action, opponent sign, frozen tree, solver, initial leaves, JSON'}))
