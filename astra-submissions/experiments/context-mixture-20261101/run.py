#!/usr/bin/env python3
"""Single frozen panel; every child result and exit is retained."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REFERENCE = HERE.parent / 'temporal-belief-20261101/build/libtemporal.so'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('directory', type=Path)
    ap.add_argument('--pilot', action='store_true')
    args = ap.parse_args()
    root = args.directory
    plan = json.loads((root / 'plan.json').read_text())
    name = 'pilot' if args.pilot else 'runs'
    runs = root / name
    runs.mkdir(exist_ok=False)
    if not args.pilot:
        pilot = json.loads((root / 'pilot-receipt.json').read_text())
        assert pilot['state'] == 'complete' and pilot['redaction_parity']
        assert all(r['update_seconds'] < 5 for r in pilot['completed'])
    dependencies = json.loads((HERE / 'origin.json').read_text())['dependencies']
    for path, digest in dependencies.items():
        assert sha(Path(path)) == digest
    sources = {str(p): sha(p) for p in HERE.iterdir() if p.suffix in ('.c', '.h', '.py', '.json')}
    libraries = {'static_merged': REFERENCE, 'static_mixture': HERE / 'build/libmixture.so', 'temporal_mixture': HERE / 'build/libmixture.so'}
    pins = {'state': 'running', 'startedAt': datetime.now(timezone.utc).isoformat(),
            'plan_sha256': sha(root / 'plan.json'), 'sources': sources,
            'dependencies': dependencies, 'libraries': {k: {'path': str(v), 'sha256': sha(v)} for k, v in libraries.items()},
            'completed': [], 'redaction_parity': None}
    receipt = root / f'{name}-receipt.json'
    receipt.write_text(json.dumps(pins, indent=2) + '\n')
    env = {k: v for k, v in os.environ.items() if not k.startswith(('MIST_', 'ASTRA_', 'FOW_'))}
    env.update(MIST_MODEL_TEMP=str(plan['model_temperature']), MIST_THREADS='2', MIST_MODEL_FULL_BELOW='1000000000', PYTHONFAULTHANDLER='1')
    deadline = time.monotonic() + plan['wall_cap_seconds']
    try:
        for i, case in enumerate(plan['cases'][:1] if args.pilot else plan['cases']):
            for suffix in ('input', 'truth'):
                assert sha(root / f"{case['id']}.{suffix}.json") == case[suffix + '_sha256']
            names = list(plan['arms']); names = names[i % 3:] + names[:i % 3]
            for arm in names:
                for redact in (False, True) if args.pilot else (False,):
                    path = runs / f"{case['id']}-{arm}{'-redacted' if redact else ''}.json"
                    command = [sys.executable, str(HERE / 'trace.py'), '--library', str(libraries[arm]),
                               '--input', str(root / f"{case['id']}.input.json"), '--truth', str(root / f"{case['id']}.truth.json"),
                               '--out', str(path), '--cap', str(plan['cap']), '--seed', str(plan['seed']),
                               '--max-ply', '16' if args.pilot else str(plan['max_ply']), '--memory-mib', str(plan['memory_mib'])]
                    if redact:
                        command.append('--redact-truth')
                    left = deadline - time.monotonic()
                    if left <= 0:
                        raise TimeoutError('panel wall cap')
                    start = time.monotonic()
                    result = subprocess.run(command, env=env | plan['arms'][arm], capture_output=True, text=True,
                                            timeout=min(plan['per_arm_cap_seconds'], left))
                    path.with_suffix('.stderr').write_text(result.stderr)
                    item = {'game': case['id'], 'arm': arm, 'redacted': redact, 'exit_code': result.returncode,
                            'wall_seconds': time.monotonic() - start, 'path': str(path)}
                    if path.exists():
                        data = json.loads(path.read_text())
                        item.update(sha256=sha(path), update_seconds=data['total_update_seconds'], max_rss_kib=data['max_rss_kib'])
                        if not args.pilot:
                            assert len(data['decisions']) == case['decisions']
                    pins['completed'].append(item)
                    receipt.write_text(json.dumps(pins, indent=2) + '\n')
                    if result.returncode:
                        raise RuntimeError((case['id'], arm, result.returncode, result.stderr))
                    assert item['max_rss_kib'] <= plan['memory_mib'] * 1024
                if args.pilot:
                    a = json.loads((runs / f"{case['id']}-{arm}.json").read_text())
                    b = json.loads((runs / f"{case['id']}-{arm}-redacted.json").read_text())
                    assert [r['checksum'] for r in a['updates']] == [r['checksum'] for r in b['updates']]
                    assert [r['king_risk'] for r in a['decisions']] == [r['king_risk'] for r in b['decisions']]
            print(json.dumps({'case': i + 1, 'game': case['id'], 'opponent': case['opponent'], 'cells': len(pins['completed'])}), flush=True)
        pins['state'] = 'complete'
        if args.pilot:
            pins['redaction_parity'] = True
    except BaseException as exc:
        pins['state'] = 'failed'; pins['error'] = repr(exc)
        raise
    finally:
        pins['finishedAt'] = datetime.now(timezone.utc).isoformat()
        receipt.write_text(json.dumps(pins, indent=2) + '\n')


if __name__ == '__main__':
    main()
