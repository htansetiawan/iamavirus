#!/usr/bin/env python3
"""Turn isolation for trusted Linux bots using the course referee's hook.

SIGSTOP/SIGCONT controls the bot's existing process group, including Stockfish.
This is clock/scheduling control, NOT a security or memory sandbox. Processes
that deliberately leave their group are outside this trusted-local contract.
The referee buffers observations and charges their processing on the next turn.
"""
import json
import inspect
import os
from pathlib import Path
import signal
import time


def process_stat(pid):
    """Read identity without misparsing spaces/parentheses in Linux comm."""
    try:
        raw = Path(f'/proc/{pid}/stat').read_text()
    except (FileNotFoundError, ProcessLookupError):
        return None
    fields = raw[raw.rfind(')')+2:].split()
    return {'pid':int(pid), 'state':fields[0], 'ppid':int(fields[1]),
            'pgid':int(fields[2]), 'sid':int(fields[3]), 'starttime':int(fields[19])}


def group_members(pgid):
    rows=[]
    for entry in Path('/proc').iterdir():
        if entry.name.isdigit():
            try:
                row=process_stat(int(entry.name))
            except PermissionError:
                continue  # Other users' processes need not be readable.
            if row and row['pgid']==pgid:
                rows.append(row)
    return rows


class ProcessGroupControl:
    def __init__(self, process, timeout=1.0, changed=None):
        self.process=process
        self.pid=process.pid
        self.identity=process_stat(self.pid)
        if not self.identity or self.identity['pgid']!=self.pid or self.identity['sid']!=self.pid:
            raise RuntimeError('Expected referee-owned session leader')
        self.timeout=timeout
        self.events=[]
        self.members=[self.identity]
        self.changed=changed

    def record(self):
        return {'leader':self.identity, 'members':self.members}

    def _signal(self, sig):
        current=process_stat(self.pid)
        # Popen owns the unreaped child identity. Refuse an unexpected identity.
        if current and (current['starttime']!=self.identity['starttime'] or current['sid']!=self.pid):
            raise RuntimeError('Process identity changed')
        members=group_members(self.pid)
        if not members:
            return False  # The referee, not the freezer, classifies bot exits.
        if current is None and not any(
                r['pid']==known['pid'] and r['starttime']==known['starttime']
                and r['sid']==self.pid for r in members for known in self.members):
            raise RuntimeError('Cannot prove ownership of leaderless process group')
        self.members=members
        if self.changed:self.changed()
        try:
            os.killpg(self.pid,sig)
        except ProcessLookupError:
            return False
        return True

    def freeze(self):
        started=time.monotonic()
        self._signal(signal.SIGSTOP)
        deadline=started+self.timeout
        previous=None
        while True:
            members=group_members(self.pid)
            live=[r for r in members if r['state'] not in ('Z','X')]
            identity=tuple(sorted((r['pid'],r['starttime']) for r in live))
            stopped=all(r['state'] in ('T','t') for r in live)
            if stopped and identity==previous:
                self.members=members
                if self.changed:self.changed()
                self.events.append({'op':'freeze','members':len(live),'seconds':time.monotonic()-started})
                return
            previous=identity if stopped else None
            if time.monotonic()>=deadline:
                raise RuntimeError('Could not confirm entire bot group stopped')
            time.sleep(.001)

    def resume(self):
        self._signal(signal.SIGCONT)
        self.events.append({'op':'resume'})


def run_controlled(referee, white, black, *, registry_path=None, retain_stderr=False, **kwargs):
    """Use the unmodified referee with a narrowly scoped Bot subclass.

    This entrypoint is intentionally sequential: temporary module replacement
    must not be shared across simultaneous games in the same Python process.
    """
    original=referee.Bot
    original_capture=referee.StderrCapture
    class CompleteBoundedCapture(original_capture):
        # The course's 16 KiB excerpt is a rolling tail, independent of its
        # 1 MiB output budget. Retain up to that existing budget for offline
        # per-decision checks. Output/line limits and warnings stay unchanged.
        RETAIN=original_capture.LIMIT
    controls=[]
    def save_registry():
        if registry_path:
            path=Path(registry_path)
            temp=path.with_suffix('.tmp')
            temp.write_text(json.dumps([c.record() for c in controls])+'\n')
            temp.replace(path)
    class ControlledBot(original):
        def __init__(self,*args,**bot_kwargs):
            def factory(_):
                control=ProcessGroupControl(self.proc,changed=save_registry)
                controls.append(control)
                save_registry()
                return control
            bound=inspect.signature(original.__init__).bind(self,*args,**bot_kwargs)
            bound.arguments['turn_control_factory']=factory
            original.__init__(*bound.args,**bound.kwargs)
    referee.Bot=ControlledBot
    if retain_stderr:referee.StderrCapture=CompleteBoundedCapture
    try:
        game=referee.run_match(white,black,**kwargs)
    finally:
        referee.Bot=original
        referee.StderrCapture=original_capture
    game['localTurnControl']={'method':'owned process-group SIGSTOP/SIGCONT; buffered observations',
        'security_sandbox':False,'stderr_retained_bytes':original_capture.LIMIT if retain_stderr else original_capture.RETAIN,
        'stderr_output_limit':original_capture.LIMIT,
        'controls':[{'pid':c.pid,'events':c.events} for c in controls]}
    return game


def cleanup_registry(path):
    """Kill a recorded group only while a recorded process identity still owns it.

    Retained child identities also authorize cleanup after a leader has exited.
    Return unverified groups so a harness cannot silently call cleanup complete.
    """
    path=Path(path)
    if not path.exists():
        return []
    unverified=[]
    for record in json.loads(path.read_text()):
        leader=record['leader']
        members=group_members(leader['pgid'])
        live=[r for r in members if r['state'] not in ('Z','X')]
        if not live:continue
        known=record['members']+[leader]
        if any(all(current[k]==expected[k] for k in ['pid','starttime','pgid','sid'])
               for current in members for expected in known):
            try:
                os.killpg(leader['pgid'],signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            unverified.append(leader['pgid'])
    return unverified
