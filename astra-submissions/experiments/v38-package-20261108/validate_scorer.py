"""Verify portable scorer equivalence and throughput on the frozen panels."""
from collections import defaultdict
from datetime import datetime, timezone
import gzip
import importlib.util
import json
import os
from pathlib import Path
import re
import statistics
import shutil
import subprocess
import sys
import time

from prepare import HERE, ROOT, OLD, OUT, sha

sys.path.insert(0, str(OLD))
spec = importlib.util.spec_from_file_location('v38_scorer_protocol', OLD / 'run.py')
protocol = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protocol)
BUILT = HERE / 'build/stockfish/src/stockfish'
PORTABLE = HERE / 'build/standalone/bin/stockfish'
MEASURED = OLD / 'build/candidate/src/stockfish'
SHIPPED = OLD.parent / 'queen-terminal-backport-20261102/build-r2/base/bin/stockfish'
PANELS = ROOT / 'astra-submissions/analysis/sf-allchildren-20261102'

def engine(binary, flag=True, pv=256):
    protocol.binaries = lambda: {'on': binary, 'off': binary}
    return protocol.UCI('on' if flag else 'off', pv)

def main():
    os.sched_setaffinity(0, {4, 5})
    assert json.loads((OUT / 'container-build.json').read_text())['exit_code'] == 0
    source = json.loads((OUT / 'source.json').read_text())
    PORTABLE.parent.mkdir(parents=True, exist_ok=False)
    shutil.copy2(BUILT, PORTABLE)
    assert sha(PORTABLE) == sha(BUILT) and PORTABLE.stat().st_size > 98000000
    assert list(PORTABLE.parent.iterdir()) == [PORTABLE]
    # Verify the network from the binary alone, with neither an adjacent nor
    # current-directory NNUE to hide a missing embedding.
    exported = HERE / 'build/exported-embedded.nnue'
    assert not exported.exists()
    output = subprocess.run([str(PORTABLE)], input=f'export_net {exported}\nquit\n',
                            cwd=PORTABLE.parent, capture_output=True, text=True, timeout=30)
    assert output.returncode == 0 and exported.exists(), output.stdout + output.stderr
    assert sha(exported) == source['network_sha256']
    with (OUT / 'embedded-network.json').open('x') as f:
        json.dump(dict(passed=True, binary_sha256=sha(PORTABLE), exported_sha256=sha(exported),
                       cwd=str(PORTABLE.parent), stdout=output.stdout, stderr=output.stderr), f, indent=2)
    for p, h in source['source_files'].items():
        assert sha(HERE / 'build/stockfish' / p) == h, p
    assert sha(MEASURED) == source['measured_binary_sha256']
    symbols = subprocess.check_output(['objdump', '-T', str(PORTABLE)], text=True)
    versions = {}
    for prefix in ('GLIBC', 'GLIBCXX', 'CXXABI'):
        found = set(re.findall(r'\b' + prefix + r'_(\d+(?:\.\d+)+)', symbols))
        versions[prefix] = max(found, key=lambda x: tuple(map(int, x.split('.')))) if found else None
    assert versions['GLIBCXX'] is None and versions['CXXABI'] is None
    assert tuple(map(int, versions['GLIBC'].split('.'))) <= (2, 35)
    record = dict(at=datetime.now(timezone.utc).isoformat(), state='running',
                  portable_sha256=sha(PORTABLE), measured_sha256=sha(MEASURED),
                  embedded_network_sha256=sha(exported),
                  shipped_sha256=sha(SHIPPED), abi_requirements=versions,
                  script_sha256=sha(__file__), pairs=0, special_calls=0, regimes={})
    path = OUT / 'scorer-validation.json'
    with path.open('x') as f:
        json.dump(record, f, indent=2)
    try:
        # The build must preserve both the patch and its activation boundaries.
        with gzip.open(OUT / 'scorer-special.jsonl.gz', 'xt') as log:
            for depth, pv, flag in ((1, 256, True), (1, 256, False), (2, 256, True), (1, 1, True)):
                reference = MEASURED if flag and depth == 1 and pv == 256 else SHIPPED
                a, b = engine(PORTABLE, flag, pv), engine(reference, flag, pv)
                try:
                    for name, fen in protocol.SPECIAL.items():
                        a.reset(); b.reset()
                        x, y = a.query(fen, depth), b.query(fen, depth)
                        log.write(json.dumps(dict(name=name, depth=depth, pv=pv, flag=flag, portable=x, reference=y)) + '\n')
                        assert all(x[k] == y[k] for k in ('scores', 'nodes', 'best')), (name, depth, pv, flag)
                        record['special_calls'] += 2
                finally:
                    a.close(); b.close()
        for label, relative in (('played', 'plan.json'), ('frontier', 'frontier/plan.json')):
            p = PANELS / relative
            plan = json.loads(p.read_text())
            assert len(plan['cases']) == 256
            for regime in ('cold', 'warm'):
                key = label + '-' + regime
                totals = defaultdict(float)
                per_pass = []
                with gzip.open(OUT / (key + '.jsonl.gz'), 'xt') as log:
                    for repeat in range(3):
                        engines = {'portable': engine(PORTABLE), 'measured': engine(MEASURED), 'shipped': engine(SHIPPED, False)}
                        batch = defaultdict(float)
                        try:
                            for e in engines.values():
                                e.query(protocol.SPECIAL['start']); e.reset()
                            for i, case in enumerate(plan['cases']):
                                arms = list(engines)
                                shift = (i + repeat) % 3
                                arms = arms[shift:] + arms[:shift]
                                results = {}
                                for arm in arms:
                                    e = engines[arm]
                                    if regime == 'cold':
                                        e.reset()
                                    r = e.query(case['fen'])
                                    assert set(r['scores']) == set(case['legal']), (key, case['id'], arm)
                                    results[arm] = r
                                    totals[arm] += r['seconds']
                                    batch[arm] += r['seconds']
                                log.write(json.dumps(dict(repeat=repeat, id=case['id'], results=results)) + '\n')
                                assert all(results['portable'][k] == results['measured'][k] for k in ('scores', 'nodes', 'best')), (key, case['id'], repeat)
                                record['pairs'] += 1
                        finally:
                            for e in engines.values():
                                e.close()
                        per_pass.append(dict(batch))
                speed = statistics.median(x['shipped'] / x['portable'] for x in per_pass)
                record['regimes'][key] = dict(panel_sha256=sha(p), queries_per_arm=768,
                                              timing_seconds=dict(totals), per_pass=per_pass,
                                              median_speedup_shipped=speed, speed_gate=speed >= 1.2)
                print(json.dumps(dict(regime=key, speedup=speed, parity=True)), flush=True)
        record['passed'] = all(x['speed_gate'] for x in record['regimes'].values())
        record['state'] = 'completed'
        assert record['pairs'] == 3072 and record['special_calls'] == 64
    except BaseException as exc:
        record.update(state='failed', error=repr(exc), passed=False)
        raise
    finally:
        record['ended_at'] = datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record), flush=True)

if __name__ == '__main__':
    main()
