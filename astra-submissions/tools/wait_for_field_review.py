"""Bounded handoff from the already-live field collector to its local audit.

No collector restart, API request, training, Git operation or deployment.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'astra-submissions/analysis/field-snapshot-20261111'


def read(path):
    return json.loads(path.read_text())


def now():
    return datetime.now(timezone.utc).isoformat()


def save(state):
    path = OUT / 'review-wait.json'
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, indent=2) + '\n')
    temporary.replace(path)


def main():
    assert not (OUT / 'review-wait.json').exists()
    assert not (OUT / 'review-execution.json').exists()
    state = dict(at=now(), status='waiting_for_original_collector', original_session=32307,
                 max_wait_seconds=1500, poll_seconds=20, child_seconds=1900,
                 scope='Launch the prepared local review once the original collector is complete. No restart or new collection.')
    save(state)
    deadline = time.monotonic() + state['max_wait_seconds']
    while time.monotonic() < deadline:
        try:
            original = read(OUT / 'execution.json')
        except (OSError, json.JSONDecodeError):
            # A transient observation failure does not make the producer terminal.
            time.sleep(state['poll_seconds'])
            continue
        if original['status'] == 'complete' and original.get('ended_at'):
            assert not (OUT / 'review-execution.json').exists()
            state.update(status='review_running', review_started_at=now())
            save(state)
            print(json.dumps(dict(event='collector_complete_start_review', at=now())), flush=True)
            child = subprocess.Popen([sys.executable, str(ROOT / 'astra-submissions/tools/verify_field_replays.py'), 'run'])
            try:
                code = child.wait(timeout=state['child_seconds'])
            except subprocess.TimeoutExpired:
                child.terminate()
                try:
                    code = child.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    child.kill()
                    code = child.wait(timeout=10)
                state.update(status='review_timeout', ended_at=now(), child_code=code)
                save(state)
                raise
            state.update(status='complete' if code == 0 else 'review_failed', child_code=code, ended_at=now())
            save(state)
            raise SystemExit(code)
        if original['status'] not in ('running', 'complete'):
            state.update(status='collector_terminal_without_completion', collector_status=original['status'], ended_at=now())
            save(state)
            return
        time.sleep(state['poll_seconds'])
    state.update(status='wait_expired', ended_at=now(), collector_unchanged=True)
    save(state)
    print(json.dumps(dict(event='bounded_wait_expired', original_collector_not_restarted=True)), flush=True)


if __name__ == '__main__':
    main()
