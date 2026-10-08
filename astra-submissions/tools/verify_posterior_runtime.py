#!/usr/bin/env python3
"""Verify unchanged control decisions and exact shared-search inputs to selectors."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse(path):
    decisions, matrices = {}, {}
    rows, sample = [], None
    for line in path.read_text().splitlines():
        if line.startswith('root_sample '):
            fields, indices = line.split(' indices:')
            fields = dict(part.split('=') for part in fields.split()[1:])
            sample = {'indices': list(map(int, indices.split())),
                      'nodes': int(fields['nodes']), 'skipped': int(fields['skipped'])}
        elif line.startswith('root_row '):
            rows.append(line)
        elif line.startswith('DECISION '):
            decision = json.loads(line[9:])
            key = (decision['game'], decision['side'], decision['ply'])
            if key in decisions:
                raise ValueError('duplicate decision')
            decisions[key] = decision
            matrices[key] = {'sample': sample, 'rows': rows}
            rows, sample = [], None
    return decisions, matrices


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--reference-campaign', type=Path, required=True)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    reference = json.loads((args.reference_campaign / 'campaign.json').read_text())
    case_manifest = json.loads((args.cases / 'manifest.json').read_text())
    for name, digest in reference['inputs'].items():
        if sha(Path(name)) != digest:
            raise ValueError('reference input changed: ' + name)
    reference_log = args.cases / 'prediction0.log'
    if sha(reference_log) != case_manifest['arms']['0']['log_sha256']:
        raise ValueError('reference case log changed')
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    binary = out / 'benchmark'; binary.write_bytes(args.binary.read_bytes()); binary.chmod(0o755)
    seats = out / 'seats.txt'; seats.write_bytes((args.cases / 'seats.txt').read_bytes())
    report = {'started_at': datetime.now(timezone.utc).isoformat(), 'state': 'running',
              'binary_sha256': sha(binary), 'seats_sha256': sha(seats),
              'reference_inputs': reference['inputs'], 'reference_log_sha256': sha(reference_log),
              'runner_sha256': sha(Path(__file__)), 'runs': {}}
    def save():
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    save()
    try:
        outputs = {}
        for mode in (0, 1, 2):
            env = {k: v for k, v in os.environ.items() if not k.startswith(('FOW_', 'ASTRA_'))}
            env.update(reference['arms']['prediction0-prior1']['settings'])
            env.update(FOW_ROOT_MODE=str(mode), FOW_DEBUG_ROOT='1')
            command = ['stdbuf', '-oL', '-eL', str(binary), str(seats),
                       str(reference['stride']), str(reference['nodes']), 'verbose']
            log = out / f'root{mode}.log'
            with log.open('w') as handle:
                result = subprocess.run(command, env=env, stdout=handle,
                                        stderr=subprocess.STDOUT, timeout=600)
            if result.returncode:
                raise RuntimeError('case benchmark failed')
            outputs[mode] = parse(log)
            report['runs'][str(mode)] = {'command': command, 'settings': {k:v for k,v in env.items() if k.startswith('FOW_')},
                                        'log_sha256': sha(log), 'decisions': len(outputs[mode][0])}
            save()
        original, _ = parse(reference_log)
        if not original or outputs[0][0] != original:
            raise ValueError('root0 does not reproduce the original control decisions')
        if outputs[1][0].keys() != outputs[2][0].keys():
            raise ValueError('selector arms evaluated different decisions')
        if outputs[1][1] != outputs[2][1]:
            raise ValueError('sampled indices, node counts or full-precision payoffs differ')
        matrices = [v for v in outputs[1][1].values() if v['sample'] is not None]
        if not matrices or any(v['sample']['skipped'] for v in matrices):
            raise ValueError('no compared matrices or some cells used clock fallback')
        report.update(state='complete', control_decisions_equal=len(original),
                      exact_matched_matrices=len(matrices),
                      exact_matched_payoff_cells=sum(len(line.split(' cells:')[1].split())
                                                    for v in matrices for line in v['rows']),
                      terminal=[{'game':k[0], 'side':k[1], 'ply':k[2],
                                 'choices':{str(mode):outputs[mode][0][k] for mode in outputs}}
                                for k,v in original.items() if v['terminal']],
                      completed_at=datetime.now(timezone.utc).isoformat(),
                      limitations=['Three selected diagnostic histories; correctness, not a strength sample.'])
    except BaseException as error:
        report.update(state='failed', error=repr(error)); raise
    finally:
        save()
    print(json.dumps({k:report[k] for k in ('state','control_decisions_equal','exact_matched_matrices','exact_matched_payoff_cells')}))


if __name__ == '__main__':
    main()
