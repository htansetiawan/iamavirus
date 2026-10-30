#!/usr/bin/env python3
"""Closed-loop v35 calibration against explicitly labelled learned proxies.

Uses the frozen hybrid-era wrapper and refreshed ONNX models. These are not
the opponents' executable bots. No candidate strength claim is authorized by
this pilot; calibration against real reference records comes first.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning.compare_archives import build, play  # noqa: E402


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(base, mode):
    out = base / ('calibration-' + mode)
    if (out / 'pins.json').exists():
        raise FileExistsError('Existing pilot: use --run-only, or a new base directory')
    out.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'data/zoo/replica-duck-hybrid.zip'
    control = ROOT / 'fable-submissions/iamavirus-v35-mist-c-v14.zip'
    pins = {'mode': mode, 'clock': '180+2', 'wrapper_sha256': digest(source),
            'v35_zip_sha256': digest(control), 'classification': 'uncalibrated learned proxies',
            'proxies': {}, 'games': []}
    control_dir = build(control, out / 'builds')
    pins['v35_directory'] = str(control_dir)
    pins['v35_binary_sha256'] = digest(control_dir / 'mist')
    for index, team in enumerate(('instructors', 'duck')):
        release = base / 'models' / team / 'release'
        manifest = json.loads((release / 'model_manifest.json').read_text())
        assert manifest['parity']['failure_count'] == 0, 'ONNX parity must pass'
        archive = out / f'proxy-{team}-{mode}.zip'
        with zipfile.ZipFile(source) as src, zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as dst:
            for member in src.infolist():
                if not member.filename.startswith('model/') and member.filename != 'run.sh':
                    dst.writestr(member, src.read(member))
            for name in ('observe.onnx', 'score.onnx', 'model_manifest.json'):
                dst.write(release / name, 'model/' + name)
            # Frozen mode and no opening book: the model supplies the learned
            # opponent tendencies; hybrid additionally uses our old search.
            dst.writestr('run.sh', '#!/bin/bash\nset -euo pipefail\ncd "$(dirname "$0")"\n'
                         f'export FOW_MODE={mode}\nexport FOW_BOOK=off\nexec ./bot\n')
        directory = build(archive, out / 'builds')
        # Missing ONNX support silently falls back in this legacy wrapper.
        # Refuse to benchmark such a fallback as a learned opponent.
        check = subprocess.run(['bash', str(directory / 'run.sh')], input='fow\nw 180 2\n',
                               text=True, capture_output=True, timeout=30)
        (out / f'{team}-initialization.log').write_text(check.stdout + check.stderr)
        assert check.returncode == 0 and 'model loaded in' in check.stderr, check.stderr
        assert f'mode={mode}' in check.stderr, check.stderr
        pins['proxies'][team] = {'archive': str(archive), 'archive_sha256': digest(archive),
                                'directory': str(directory), 'binary_sha256': digest(directory / 'bot'),
                                'model_manifest_sha256': digest(release / 'model_manifest.json')}
        for pair in range(2):
            for colour in ('white', 'black'):
                pins['games'].append({'team': team, 'pair': pair, 'v35_colour': colour,
                                     'seed': 730000 + index * 1000 + pair * 2})
    (out / 'pins.json').write_text(json.dumps(pins, indent=2) + '\n')
    print('prepared', out, flush=True)
    return out


def lane(pins, team, cores, out):
    # No inherited experimental evaluator, forced line, oracle or clock knobs.
    for name in list(os.environ):
        if name.startswith(('FOW_', 'MIST_')):
            del os.environ[name]
    control = Path(pins['v35_directory'])
    proxy = Path(pins['proxies'][team]['directory'])
    assert digest(control / 'mist') == pins['v35_binary_sha256']
    assert digest(proxy / 'bot') == pins['proxies'][team]['binary_sha256']
    rows = []
    with (out / f'{team}-results.jsonl').open('x') as log:
        for case in (g for g in pins['games'] if g['team'] == team):
            white, black = (control, proxy) if case['v35_colour'] == 'white' else (proxy, control)
            replay = out / f"{team}-pair{case['pair']}-{case['v35_colour']}.json"
            try:
                result = play(white, black, case['seed'], Path.home() / 'git/fow-starter',
                              replay, cores, timeout=900)
                score = {'1-0': 1., '1/2-1/2': .5, '0-1': 0.}[result['result']]
                if case['v35_colour'] == 'black':
                    score = 1. - score
                row = dict(case, **result, v35_score=score, replay=str(replay),
                           replay_sha256=digest(replay), cores=cores)
            except Exception as exc:
                row = dict(case, error=str(exc), cores=cores)
            log.write(json.dumps(row) + '\n'); log.flush()
            rows.append(row)
            print(json.dumps(row), flush=True)
            if 'error' in row:
                break  # preserve and investigate; never count a failed attempt as a loss
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base', type=Path, required=True)
    ap.add_argument('--mode', choices=('hybrid', 'neural'), default='hybrid')
    ap.add_argument('--prepare-only', action='store_true')
    ap.add_argument('--run-only', action='store_true')
    args = ap.parse_args()
    if args.prepare_only and args.run_only:
        ap.error('choose one phase')
    out = args.base / ('calibration-' + args.mode)
    if not args.run_only:
        out = prepare(args.base, args.mode)
    if args.prepare_only:
        return
    pins = json.loads((out / 'pins.json').read_text())
    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(lane, pins, team, cores, out)
                   for team, cores in (('instructors', '2,3'), ('duck', '4,5'))]
        for future in concurrent.futures.as_completed(futures):
            rows.extend(future.result())
    summary = {'classification': 'calibration pilot, not real-opponent win rates', 'teams': {}}
    for team in pins['proxies']:
        games = [r for r in rows if r['team'] == team and 'error' not in r]
        summary['teams'][team] = {'games': len(games), 'v35_score': sum(r['v35_score'] for r in games),
                                 'errors': sum('error' in r for r in rows if r['team'] == team),
                                 'wins': sum(r['v35_score'] == 1 for r in games),
                                 'draws': sum(r['v35_score'] == .5 for r in games)}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
