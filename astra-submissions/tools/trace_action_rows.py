#!/usr/bin/env python3
"""Reproduce selected benchmark decisions with the existing matrix-row trace.

This diagnoses already-inspected cases. It does not change the engine, score a
new evaluation set, or interpret the rounded cell values as exact payoffs.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaign', type=Path, required=True)
    p.add_argument('--arm', required=True)
    p.add_argument('--targets', nargs='+', required=True, help='game:w or game:b')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    root = args.campaign.resolve()
    state = json.loads((root / 'campaign.json').read_text())
    arm = state['arms'][args.arm]
    if state['state'] != 'complete' or arm['state'] != 'complete':
        p.error('a completed campaign is required')
    targets = []
    for target in args.targets:
        if not re.fullmatch(r'[a-z0-9]{8}:[wb]', target):
            p.error('targets must have eight-character IDs and w/b sides')
        targets.append(tuple(target.split(':')))
    if len(set(targets)) != len(targets):
        p.error('duplicate targets')
    for name, digest in state['inputs'].items():
        if sha(Path(name)) != digest:
            raise ValueError('changed input: ' + name)
    original = [json.loads(line.removeprefix('DECISION '))
                for line in (root / (args.arm + '.log')).read_text().splitlines()
                if line.startswith('DECISION ')]
    seat_lines = {}
    for line in (root / 'seats.txt').read_text().splitlines():
        fields = line.split()
        key = tuple(fields[:2])
        if key in seat_lines:
            raise ValueError('duplicate seat: ' + str(key))
        seat_lines[key] = line
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('FOW_', 'ASTRA_'))}
    env.update(arm['settings'], FOW_DEBUG_ROWS='1')
    report = {'recorded_at': datetime.now(timezone.utc).isoformat(),
              'campaign': str(root), 'arm': args.arm,
              'campaign_sha256': sha(root / 'campaign.json'),
              'inputs': state['inputs'], 'settings': arm['settings'],
              'runner_sha256': sha(Path(__file__)), 'seats': [],
              'limitations': ['Selected diagnostic cases, not new validation.',
                              'Existing debug output rounds risks and cells to integers.',
                              'Risk is the combined evaluation charge, not a probability.']}
    for game, side in targets:
        corpus = out / f'{game}-{side}.txt'
        corpus.write_text(seat_lines[(game, side)] + '\n')
        log = out / f'{game}-{side}.log'
        command = list(arm['command'])
        command[1] = str(corpus)
        # Match stderr rows with the following stdout decision before buffering
        # can move all decision records to the end of the file.
        command = ['stdbuf', '-oL', *command]
        with log.open('w') as f:
            subprocess.run(command, env=env, stdout=f,
                           stderr=subprocess.STDOUT, check=True, timeout=180)
        decisions, pending_rows = [], []
        for line in log.read_text().splitlines():
            match = re.fullmatch(r'row (\S+) risk=(-?\d+) cells:(.*)', line)
            if match:
                pending_rows.append({'move': match[1], 'risk_charge_rounded': int(match[2]),
                                     'payoffs_rounded': [int(x) for x in match[3].split()]})
            elif line.startswith('DECISION '):
                decisions.append({'decision': json.loads(line.removeprefix('DECISION ')),
                                  'rows': pending_rows})
                pending_rows = []
        expected = [r for r in original if r['game'] == game and r['side'] == (side == 'b')]
        if [r['decision'] for r in decisions] != expected or pending_rows:
            raise ValueError('traced decisions differ from original: ' + game + ':' + side)
        record = {'game': game, 'side': side, 'command': command,
                  'corpus_sha256': sha(corpus), 'log_sha256': sha(log),
                  'all_decisions_match_original': True, 'decisions': decisions}
        report['seats'].append(record)
        print(json.dumps({'game': game, 'side': side, 'decision_parity': True,
                          'terminal': [r for r in decisions if r['decision']['terminal']]}), flush=True)
    if any(sha(Path(name)) != digest for name, digest in state['inputs'].items()):
        raise ValueError('input changed during tracing')
    report['inputs_unchanged'] = True
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
