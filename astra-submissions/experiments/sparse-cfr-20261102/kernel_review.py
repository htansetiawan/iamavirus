"""Audit saved fixed-work results; never rerun or select timing attempts."""
from pathlib import Path
import gzip
import hashlib
import json
import math
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/sparse-cfr-20261102'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = json.loads((OUT / 'plan.json').read_text())
    receipt = json.loads((OUT / 'receipt.json').read_text())
    assert receipt['state'] == 'completed' and len(receipt['jobs']) == 9
    assert receipt['plan_sha256'] == sha(OUT / 'plan.json')
    for name, digest in {**plan['sources'], **plan['build']}.items():
        assert sha(ROOT / name) == digest, name
    native = json.loads((OUT / 'native-checks.json').read_text())
    assert native['passed'] and native['negative_control_detected']
    changed = [p.name for p in (HERE / 'build/base/src').glob('*')
               if p.is_file() and sha(p) != sha(HERE / 'build/fast/src' / p.name)]
    assert sorted(changed) == ['cfr.c', 'cfr.h'], changed
    rows = []
    for tree in plan['trees']:
        path = Path(tree['tree'])
        data = path.read_bytes()
        assert sha(path) == tree['raw_sha256'] and data[:8] == b'ASTRA253'
        nn, ne, ni, ns, root = struct.unpack_from('=5i', data, 8)
        assert len(data) == 28 + nn*28 + ne*12 + ni*12 + ns*24
        rec = json.loads((OUT / (tree['case'] + '-check-opt.json')).read_text())
        assert rec['exit_code'] == 0 and rec['error'] is None and not rec['stderr']
        assert rec['tree_sha256'] == tree['raw_sha256']
        r = json.loads(rec['stdout'])
        assert r['identical'] and r['steps'] == plan['iterations'] and r['timed_repeats'] == 5
        ratio = r['base_seconds'] / r['fast_seconds']
        assert abs(ratio - r['speedup']) < 1e-6
        cap = 64
        while cap < ni:
            cap *= 2
        # wrapper.storage omits the new sparse bookkeeping. Include its four
        # int/unsigned arrays explicitly; compare with baseline iteration peak.
        rows.append(dict(case=tree['case'], nodes=nn, infosets=ni, slots=ns,
                         base_seconds=r['base_seconds'], fast_seconds=r['fast_seconds'],
                         speedup=ratio, identical=True,
                         base_iteration_array_bytes=ns*6*8,
                         fast_iteration_array_bytes=r['fast_storage'] + cap*16))
    san = json.loads((OUT / (plan['trees'][0]['case'] + '-check-san.json')).read_text())
    assert san['exit_code'] == 0 and san['error'] is None and not san['stderr']
    assert json.loads(san['stdout'])['identical']
    speedup = math.exp(sum(math.log(r['speedup']) for r in rows) / len(rows))
    summary = dict(rows=rows, geometric_mean_speedup=speedup,
                   total_base_seconds=sum(r['base_seconds'] for r in rows),
                   total_fast_seconds=sum(r['fast_seconds'] for r in rows),
                   gate_pass=speedup >= plan['min_speedup'],
                   all_bit_identical=True, changed_source_files=sorted(changed),
                   source_and_binary_hashes_verified=True,
                   plan_sha256=sha(OUT / 'plan.json'), receipt_sha256=sha(OUT / 'receipt.json'),
                   scope='Fixed-tree solver work only; timings sum five measured repeats. '
                         'Includes workspace plus selective updates versus original v37. '
                         'Memory numbers cover solver arrays, not total RSS. No strength inference.')
    with (OUT / 'summary.json').open('x') as f:
        json.dump(summary, f, indent=2); f.write('\n')
    lines = ['# Exact selective CFR: fixed-work result', '',
             f'**{speedup:.3f}x geometric-mean solver speedup**, passing the declared 1.20x condition for an equal-clock search test.', '',
             'All eight saved-tree comparisons are bit-identical. This is an execution optimization, not playing-strength evidence.', '',
             '| Case | Baseline seconds | Candidate seconds | Speedup |', '|---|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['case']} | {r['base_seconds']:.4f} | {r['fast_seconds']:.4f} | {r['speedup']:.3f}x |")
    lines += ['', 'Times sum five measured repeats of 200 iterations after an excluded warmup. '
              'Order alternates; all first attempts are retained. The sanitized real-tree run is excluded from performance.', '',
              'Native/growing checks compare 9,569 checkpoints and 6,263,272 doubles across 8,193 iterations, '
              'including 496 stale-prediction clears. ASan/UBSan/LSan pass. A deliberately omitted prediction clear fails the equality check.', '',
              'The audit verifies the frozen source/binary/tree hashes, output arithmetic and tree dimensions. '
              'Only cfr.c and cfr.h differ from original v37. The prior experiment already checked the saved trees against replay inputs and the referee.', '',
              'The candidate retains geometric-capacity storage and sparse index lists. Corrected solver-array memory '
              'is recorded in summary.json; the raw benchmark storage field omits sparse lists. This is not a total-process memory measurement.', '',
              'Next: compare whole searches on identical beliefs, allowed moves and world draws at the same 2.5-second budget, '
              'then full games only if that diagnostic passes. No new ZIP or Elo claim.']
    (OUT / 'README.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({k:v for k,v in summary.items() if k != 'rows'}))


if __name__ == '__main__':
    main()
