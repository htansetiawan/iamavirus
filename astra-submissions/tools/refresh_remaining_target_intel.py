"""Separate bounded continuation after the first collector's request-limit stop."""
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = HERE/'refresh_target_intel.py'
PRIOR = ROOT/'astra-submissions/analysis/target-intel-20261110'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', type=Path, default=ROOT/'data/raw')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    receipt = json.loads((PRIOR/'receipt.json').read_text())
    audit = json.loads((PRIOR/'audit.json').read_text())
    assert not receipt['completed'] and receipt['error'] == "RuntimeError('Target refresh request bound')"
    assert receipt['counts']['accepted'] == audit['new_games'] == 451
    assert audit['taxonomy_recomputed'] and audit['initial_prefix_verified']
    assert set(audit['completed_targets']) == {'duck', 'Instructors', 'HYPOTHERMIA'}
    assert sha(SOURCE) == receipt['source_sha256']
    spec = importlib.util.spec_from_file_location('remaining_intel_base', SOURCE)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    base.TARGETS = ['Greek Gift', 'Mist Opportunities']
    try:
        base.run(args)
    finally:
        if args.out.exists():
            base.write(args.out/'continuation-receipt.json', dict(
                at=datetime.now(timezone.utc).isoformat(), targets=base.TARGETS,
                wrapper_sha256=sha(Path(__file__)), base_source_sha256=sha(SOURCE),
                prior_receipt_sha256=sha(PRIOR/'receipt.json'), prior_audit_sha256=sha(PRIOR/'audit.json'),
                scope='New bounded metadata snapshot for the remaining two targets. '
                      'Original partial batch remains unchanged; immutable completed-game caches reused. '
                      'Same 900-second and 500-request limits. No model or playing-policy changes.'))
