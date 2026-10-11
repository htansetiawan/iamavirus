#!/usr/bin/env python3
"""Wait for a specific live gate process, verify completion, then run a sequel.

Linux pidfd tracks the original process identity, not a reusable PID or stale
lock file. The sequel still owns its ordinary per-run lock and immutable
configuration. This tool does not retry a failed predecessor or sequel.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import select
import subprocess


def emit(**values):
    print(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),**values)),flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pid',type=int,required=True)
    ap.add_argument('--predecessor',type=Path,required=True)
    ap.add_argument('command',nargs=argparse.REMAINDER)
    args=ap.parse_args()
    command=args.command[1:] if args.command[:1]==['--'] else args.command
    if not command:ap.error('A sequel command is required after --')
    fd=os.pidfd_open(args.pid)
    try:
        argv=[a.decode() for a in Path(f'/proc/{args.pid}/cmdline').read_bytes().split(b'\0') if a]
        if '--run' not in argv or Path(argv[argv.index('--run')+1]).resolve()!=args.predecessor.resolve():
            raise ValueError('PID does not belong to the requested predecessor gate')
        if not any(Path(s).name=='m4_gate_run.py' for s in argv):
            raise ValueError('Predecessor is not the gate runner')
        emit(state='waiting',predecessor_pid=args.pid,predecessor=str(args.predecessor),sequel=command)
        poll=select.poll();poll.register(fd,select.POLLIN)
        while not poll.poll(1000):pass
    finally:os.close(fd)
    summary=json.loads((args.predecessor/'summary.json').read_text())
    if not summary['complete'] or summary['completed']!=summary['expected_decisions']:
        raise ValueError('Predecessor exited without completing its gate')
    if any(r['status']!='ok' for r in summary['rows']):
        raise ValueError('Predecessor has failed decisions; review before a sequel')
    emit(state='predecessor_complete',decisions=summary['completed'])
    result=subprocess.run(command)
    emit(state='sequel_exited',returncode=result.returncode)
    raise SystemExit(result.returncode)


if __name__=='__main__':main()
