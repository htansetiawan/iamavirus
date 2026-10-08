#!/usr/bin/env python3
"""Audit default-off parity and runtime for a frozen weighted-frontier run."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path, mode):
    state = json.loads((path / 'state.json').read_text())
    if state['state'] != 'complete' or state['failed_runs'] or not state['inputs_unchanged']:
        raise ValueError('run is incomplete or changed')
    rows = [json.loads(line) for line in (path / 'runs.jsonl').read_text().splitlines()]
    rows = [r for r in rows if r['prediction'] == mode]
    if len(rows) != state['seats'] or not all(r['complete'] for r in rows):
        raise ValueError('run rows missing')
    out = {}
    for row in rows:
        key = tuple(row['target'][k] for k in ('game', 'side', 'ply'))
        if key in out:
            raise ValueError('duplicate target')
        trace = Path(row['trace'])
        if sha(trace) != row['trace_sha256']:
            raise ValueError('trace changed: ' + str(trace))
        frames = [json.loads(line) for line in trace.read_text().splitlines()]
        out[key] = row, frames
    return state, out


def runtime(rows):
    frames = [frame for _, trace in rows.values() for frame in trace]
    times = sorted(f['observe_ms'] for f in frames)
    states = [f['frontier_states'] for f in frames]
    effective = [f['frontier_effective_states'] for f in frames]
    return {'events': len(rows), 'updates': len(frames),
            'process_seconds': sum(row['elapsed_seconds'] for row, _ in rows.values()),
            'observe_ms': {'median': statistics.median(times),
                           'p95': times[min(len(times)-1, int(.95*len(times)))],
                           'maximum': max(times), 'sum': sum(times)},
            'frontier_states': {'median': statistics.median(states), 'maximum': max(states)},
            'effective_states': {'median': statistics.median(effective), 'maximum': max(effective)},
            'capacity_reductions': sum(f['frontier_reduced'] for f in frames),
            'collapses': sum(f['collapsed'] for f in frames),
            'updates_with_true_board_in_engine_samples': sum(f['truth_board_held'] > 0 for f in frames),
            'target_zero_support': sum(row['final']['tracked_held'] == 0 for row, _ in rows.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control-run', type=Path, required=True)
    parser.add_argument('--frontier-run', type=Path, required=True)
    parser.add_argument('--reference-run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    control_state, control = load(args.control_run, 1)
    candidate_state, candidate = load(args.frontier_run, 1)
    reference_state, reference = load(args.reference_run, 1)
    for key in ('targets_sha256', 'particles', 'seed', 'history', 'prior'):
        if len({s[key] for s in (control_state, candidate_state, reference_state)}) != 1:
            raise ValueError('mismatched ' + key)
    if control_state['frontier_capacity'] != 0 or candidate_state['frontier_capacity'] <= 0:
        raise ValueError('invalid frontier arms')
    if control_state['probe_sha256'] != candidate_state['probe_sha256']:
        raise ValueError('candidate and control must use the same binary')
    if set(control) != set(candidate) or not set(control).issubset(reference):
        raise ValueError('mismatched seats')
    fields = frames = 0
    for key, (_, trace) in control.items():
        old_trace = reference[key][1]
        if len(trace) != len(old_trace):
            raise ValueError('mismatched trace length')
        for old, new in zip(old_trace, trace):
            frames += 1
            for name, value in old.items():
                if name == 'observe_ms':
                    continue
                if new[name] != value:
                    raise ValueError(f'default-off mismatch {key}: {old["ply"]} {name}')
                fields += 1
    report = {'control': runtime(control), 'frontier': runtime(candidate),
              'parity': {'status': 'passed', 'games': len(control), 'frames': frames,
                         'field_checks': fields, 'excluded': ['observe_ms'],
                         'reference_probe_sha256': reference_state['probe_sha256']},
              'states': [control_state, candidate_state, reference_state],
              'runs_sha256': {str(p): sha(p / 'runs.jsonl') for p in
                              (args.control_run, args.frontier_run, args.reference_run)},
              'interpretation': 'Support and shared-host timings over forced replay prefixes, not decisions or Elo. Observe timing excludes ApplyOurMove; process time includes it.'}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('control', 'frontier', 'parity')}))


if __name__ == '__main__':
    main()
