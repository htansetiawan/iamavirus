#!/usr/bin/env python3
"""Compare immutable v35, the patched feature-off control, and the raw/calibrated by loss-payoff factorial.

Uses the frozen fresh-taxonomy development cases; this is not a held-out
strength estimate. Inputs contain only the player's permitted history.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.with_name('calibrated-root-20261101')
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'astra-submissions/tools'))
from fresh_taxonomy_gate import exchange_probe, protocol
from learning import ingest, compare_archives as ca


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def event(value, field):
    if field == 'fatal_or_exchange':
        return (value.get('fatal', False) or value.get('forced_king_loss_after_capture', False)
                or (value.get('exchange_loss') or 0) >= 2)
    if field in ('exchange_loss', 'queen_exchange_loss'):
        return (value.get(field) or 0) >= (4 if field.startswith('queen') else 2)
    return bool(value.get(field))


def summarize(rows, arms):
    report = {'cases': len(rows), 'games': len({r['case']['game'] for r in rows}), 'arms': {}, 'paired': {}}
    fields = ['fatal', 'exchange_loss', 'queen_exchange_loss', 'forced_king_loss_after_capture', 'fatal_or_exchange']
    for arm in arms:
        values = [r['arms'][arm] for r in rows]
        report['arms'][arm] = {field: sum(event(v,field) for v in values) for field in fields}
        report['arms'][arm].update(errors=sum('error' in v for v in values), illegal=sum(v.get('legal') is False for v in values))
        for metric in ('elapsed', 'nodes', 'iterations', 'queen_guard_seconds'):
            valid = [v[metric] for v in values if metric in v]
            report['arms'][arm]['median_'+metric] = statistics.median(valid) if valid else None
    for old,new in (('v35','raw2'), ('v35','raw1'), ('v35','cal1'), ('raw2','cal2'), ('raw1','cal1'), ('raw2','raw1'), ('cal2','cal1')):
        pair = {}
        for field in fields:
            fixes, breaks = [], []
            for r in rows:
                a,b = r['arms'][old],r['arms'][new]
                if 'error' in a or 'error' in b:
                    continue
                key = f"{r['case']['game']}:{r['case']['ply']}"
                if event(a,field) and not event(b,field): fixes.append(key)
                if not event(a,field) and event(b,field): breaks.append(key)
            pair[field] = {'fixed': fixes, 'broken': breaks}
        pair['moves_changed'] = sum(r['arms'][old].get('move') != r['arms'][new].get('move') for r in rows)
        report['paired'][old+'->'+new] = pair
    report['scope'] = 'Development diagnostic sample, correlated cases, limited omniscient exchange probe; not Elo or overall calibration.'
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--cases', type=Path, default=ROOT/'astra-submissions/analysis/fresh-taxonomy-20261101/cases.json')
    ap.add_argument('--seconds', type=float, default=2.5)
    ap.add_argument('--seed', type=int, default=11012026)
    ap.add_argument('--cores', default='0,1')
    ap.add_argument('--wall-seconds', type=float, default=3600)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    frozen = json.loads(args.cases.read_text())
    deadline = time.monotonic() + args.wall_seconds
    provenance = json.loads((BASE/'build-provenance.json').read_text())
    assert sha(BASE/'build/mist') == provenance['binary_sha256']
    for name,digest in provenance['modified_sources'].items():
        assert sha(BASE/'src'/name) == digest == sha(BASE/'build/src'/name)
    baseline = ROOT/'astra-submissions/analysis/fresh-taxonomy-20261101/builds/iamavirus-v35-mist-c-v14'
    # Verify the baseline build remains the exact source, data, and SF from the pinned archive.
    import zipfile
    archive = ROOT/provenance['origin']['base_archive']
    assert sha(archive) == provenance['origin']['base_archive_sha256']
    with zipfile.ZipFile(archive) as z:
        for entry in z.namelist():
            if entry.startswith(('src/', 'data/', 'bin/')) and not entry.endswith('/'):
                assert sha(baseline/entry) == hashlib.sha256(z.read(entry)).hexdigest(), entry
                if not entry.startswith('src/'):
                    assert sha(BASE/'build'/entry) == sha(baseline/entry), entry
    arms = ['v35','raw2','cal2','raw1','cal1']
    settings = {'v35': {}, 'raw2': {'MIST_ROOT_CALIB':'0','MIST_KING_RISK':'2'}, 'cal2': {'MIST_ROOT_CALIB':'1','MIST_KING_RISK':'2'}, 'raw1': {'MIST_ROOT_CALIB':'0','MIST_KING_RISK':'1'}, 'cal1': {'MIST_ROOT_CALIB':'1','MIST_KING_RISK':'1'}}
    binaries = {name: baseline if name == 'v35' else BASE/'build' for name in arms}
    pins = {'started_at': datetime.now(timezone.utc).isoformat(), 'cases': str(args.cases),
            'cases_sha256': sha(args.cases), 'provenance': provenance,
            'binaries': {k:sha(v/'mist') for k,v in binaries.items()}, 'arms': arms, 'settings': settings,
            'runner_sha256': sha(Path(__file__)), 'protocol_helper_sha256': sha(ROOT/'astra-submissions/tools/fresh_taxonomy_gate.py'),
            'seed': args.seed, 'seconds': args.seconds, 'cores': args.cores,
            'runner_pid': os.getpid(), 'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'wall_seconds': args.wall_seconds,
            'timing_diagnostics': True, 'truth_to_bot': False, 'recorded_replies_after_divergence': False,
            'stop_rule': 'Stop on any protocol error or illegal move. A variant earns independent confirmation only if fatal_or_exchange fixes exceed breaks by at least 3, fatal choices decrease, and neither material nor queen-loss counts increase. For cal1 also require fewer combined adverse events and no increase in fatalities/material/queen loss versus raw1. A null closes this global-calibration integration family. No promotion from this development sample.'}
    (args.out/'pins.json').write_text(json.dumps(pins,indent=2)+'\n')
    (args.out/'logs').mkdir()
    rows = []
    with (args.out/'results.jsonl').open('x') as output:
        for i,case in enumerate(frozen['cases']):
            payload = Path(case['replay_path']).read_bytes()
            assert hashlib.sha256(payload).hexdigest() == case['replay_sha256']
            replay = json.loads(payload); states,errors = ingest.validate_replay(replay)
            assert not errors, errors
            side = ('white','black').index(case['side']); state = states[case['ply']]
            feed,forced = protocol(replay,case['ply'],side)
            row = {'case': case, 'arms': {}}
            for name in arms[i%len(arms):]+arms[:i%len(arms)]:
                if time.monotonic() >= deadline:
                    raise RuntimeError('Wall cap reached; incomplete experiment, not a policy loss.')
                env = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_'))}
                env.update(MIST_FORCE_MOVES=','.join(forced), MIST_MAX_SECONDS=str(args.seconds),
                           FOW_SEED=str(args.seed), MIST_TIMING='1')
                env.update(settings[name])
                start = time.monotonic()
                proc = subprocess.Popen(['taskset','-c',args.cores,'bash',str(binaries[name]/'run.sh')],
                                        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
                stdout,stderr = '', ''
                try:
                    stdout,stderr = proc.communicate(feed,timeout=min(180,max(1,deadline-time.monotonic())))
                    moves = [line[5:].strip() for line in stdout.splitlines() if line.startswith('move ')]
                    if proc.returncode or len(moves) != len(forced)+1 or moves[:-1] != forced:
                        raise ValueError(f'protocol exit={proc.returncode}, moves={len(moves)} expected={len(forced)+1}')
                    record = {'move':moves[-1], 'elapsed':time.monotonic()-start, **exchange_probe(state,moves[-1])}
                    search = re.findall(r'nodes=(\d+) iters=(\d+)',stderr)
                    if search: record.update(nodes=int(search[-1][0]),iterations=int(search[-1][1]))
                    guards = re.findall(r'timing queen guard ([\d.]+) s',stderr)
                    if guards: record['queen_guard_seconds'] = float(guards[-1])
                    row['arms'][name] = record
                except (subprocess.TimeoutExpired,ValueError) as exc:
                    if proc.poll() is None: ca.kill_tree(proc.pid)
                    proc.wait()
                    row['arms'][name] = {'error':str(exc),'elapsed':time.monotonic()-start}
                (args.out/'logs'/f"{case['game']}-{case['ply']}-{name}.stderr").write_text(stderr)
                if 'error' in row['arms'][name] or row['arms'][name].get('legal') is False:
                    output.write(json.dumps(row)+'\n'); output.flush()
                    raise RuntimeError(f'fail-fast: {case["game"]}:{case["ply"]} {name}')
            rows.append(row); output.write(json.dumps(row)+'\n'); output.flush()
            report = summarize(rows,arms)
            (args.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
            print(i+1,len(frozen['cases']),{k:v['move'] for k,v in row['arms'].items()},flush=True)
    report['complete'] = True
    (args.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__': main()
