#!/usr/bin/env python3
"""Exact small-case expectation, independent of native sampling code."""
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
native = json.loads((root / 'native.json').read_text())
weights = [Fraction(6, 10), Fraction(3, 10), Fraction(1, 10)]
expected = [Fraction(0) for _ in weights]
orders = []
for i, j in itertools.permutations(range(3), 2):
    probability = weights[i] * weights[j] / (1 - weights[i])
    expected[i] += probability * weights[i] / (weights[i] + weights[j])
    expected[j] += probability * weights[j] / (weights[i] + weights[j])
    orders.append({'order': [i, j], 'probability': str(probability)})
assert sum(expected) == 1
z = [(native['estimated_mean'][i] - float(expected[i])) / native['standard_errors'][i] for i in range(3)]
assert all(abs(v) < 5 for v in z)
report = {'measurement': 'Exact/native audit of capped weighted retention; not an arena experiment',
          'ordered_selection_probabilities': orders, 'exact_expected_share_fractions': list(map(str, expected)),
          'exact_expected_share': list(map(float, expected)), 'native': native, 'native_vs_exact_z': z,
          'rare_world_input_share': .1, 'rare_world_expected_retained_normalized_share': float(expected[2]),
          'source_sha256': hashlib.sha256(Path('astra-submissions/experiments/temporal-belief-20261101/native/belief.c').read_bytes()).hexdigest(),
          'limit': 'A counterexample disproves general mass preservation. It does not establish which sampler plays stronger or quantify arena bias.'}
(root / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
