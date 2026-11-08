"""Wait for the original backfill, audit its coverage, then stage fresh reports.

No retries, second ingestion, model fit, publication, release or arena action.
If the collector fails or is incomplete, retain current published warnings.
"""
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import time

import audit_backfill
import refresh

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT/'astra-submissions/analysis/report-repair-20261108'
BACKFILL = EVIDENCE/'backfill'
OUT = EVIDENCE/'closure'


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2); handle.write('\n')


def original_alive(plan):
    try:
        fields = Path(f"/proc/{plan['pid']}/stat").read_text().rsplit(')', 1)[1].split()
    except FileNotFoundError:
        return False
    return fields[19] == str(plan['proc_starttime']) and fields[0] != 'Z'


def main():
    os.chdir(ROOT); os.sched_setaffinity(0, {4, 5}); os.nice(10)
    plan = json.loads((BACKFILL/'plan.json').read_text())
    deadline = audit_backfill.instant(plan['started']).timestamp()+plan['wall_cap_seconds']+300
    OUT.mkdir(exist_ok=False)
    write(OUT/'plan.json', dict(at=now(), pid=os.getpid(),
          proc_starttime=Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19],
          pid_namespace=os.readlink('/proc/self/ns/pid'), original_pid=plan['pid'],
          original_starttime=plan['proc_starttime'], deadline_utc=datetime.fromtimestamp(deadline, timezone.utc).isoformat(),
          source_sha256={p.name:audit_backfill.digest(p) for p in (
              Path(__file__),Path(audit_backfill.__file__),Path(refresh.__file__))},
          scope='Wait for original collector only; audit then stage reports; no publication or training.'))
    status = dict(started=now(), passed=False, published=False)
    try:
        if not original_alive(plan) and not (BACKFILL/'receipt.json').exists():
            raise RuntimeError('original process absent without a completion receipt')
        while original_alive(plan):
            if time.time() >= deadline:
                raise TimeoutError('original collector did not close within its bounded deadline')
            time.sleep(min(30, max(0.1, deadline-time.time())))
        status['collector_closed_at'] = now()
        # The original collector owned this lock until termination. Do not
        # race a scheduled refresh if one acquired it in the intervening gap.
        with (ROOT/'data/logs/daily/.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = audit_backfill.audit(BACKFILL, ROOT/'data/raw')
            write(OUT/'coverage-audit.json', result)
            print(json.dumps(dict(at=now(), event='coverage_audit_passed',
                                 other_team_games=result['other_team_games'])), flush=True)
            refresh.OUT = OUT
            refresh.STAGE = OUT/'reports'
            refresh.main()
            receipt = json.loads((OUT/'refresh-receipt.json').read_text())
            if not receipt['passed']:
                raise RuntimeError('report refresh failed; prior published reports retained')
        status.update(passed=True, coverage_audit_passed=True, reports_staged=True)
    except BaseException as exc:
        status['error'] = repr(exc)
        raise
    finally:
        status['finished'] = now()
        write(OUT/'receipt.json', status)
        print(json.dumps(status), flush=True)


if __name__ == '__main__':
    main()
