#!/usr/bin/env python3
"""Resume only Astra's paused index after timed matches release its CPU cores.

Bounded CPU coordination helper. Never changes another job or uses a GPU.
Recheck the complete command and process start time before signalling. Run on
the host where the original index lives, not a separate PID namespace.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import time


def arguments(pid):
    return [p.decode() for p in Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0") if p]


def start_time(pid):
    # /proc stat field 22; the parenthesized process name can contain spaces.
    return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]


def match_drivers(cores):
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            args = arguments(entry.name)
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if "learning.compare_archives" not in args:
            continue
        if "--cores" not in args:
            found.append(int(entry.name))  # Unknown allocation: conservatively wait.
            continue
        allocated = {int(n) for n in args[args.index("--cores") + 1].split(",")}
        if cores & allocated:
            found.append(int(entry.name))
    return sorted(found)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--max-minutes", type=int, default=120)
    args = parser.parse_args()
    command = arguments(args.pid)
    if (len(command) < 3 or command[1:3] !=
            ["astra-submissions/tools/experience_index.py", "build"]):
        raise ValueError("PID is not Astra's experience-index build")
    cores = os.sched_getaffinity(args.pid)
    if cores != {4, 5}:
        raise ValueError(f"unexpected CPU allocation: {cores}")
    started = start_time(args.pid)
    deadline = time.monotonic() + max(1, min(120, args.max_minutes)) * 60
    while time.monotonic() < deadline:
        blockers = match_drivers(cores)
        state = dict(at=datetime.now(timezone.utc).isoformat(), pid=args.pid,
                     cores=sorted(cores), blockers=blockers, status="waiting_for_timed_matches")
        if not blockers:
            if arguments(args.pid) != command or start_time(args.pid) != started:
                raise ValueError("target process identity changed; refusing to signal")
            os.kill(args.pid, signal.SIGCONT)
            state["status"] = "resumed"
        temporary = args.state.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, indent=2) + "\n")
        temporary.replace(args.state)
        if state["status"] == "resumed":
            print(json.dumps(state), flush=True)
            return
        time.sleep(30)
    raise TimeoutError("index remains paused; CPU allocation needs review")


if __name__ == "__main__":
    main()
