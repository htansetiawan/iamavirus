"""Force both handshake failures and verify the real startup code reports them."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from prepare import HERE, ROOT, OUT, sha
sys.path.insert(0, str(ROOT/'astra-submissions/tools'))
from local_turn_control import group_members

PREFIX = 'astra-sf-startup '

def clean_env():
    return {k:v for k,v in os.environ.items()
            if not k.startswith(('MIST_','ASTRA_','FOW_','FAKE_UCI_'))}

def trace_rows(text):
    return [json.loads(line[len(PREFIX):]) for line in text.splitlines() if line.startswith(PREFIX)]

def main():
    build=HERE/'build'
    receipt=json.loads((OUT/'build.json').read_text())
    for path,digest in receipt['dependencies'].items(): assert sha(path)==digest,path
    raw=ROOT/'data/astra-spool/sf-startup-diagnosis-20261110-mocks'
    raw.mkdir(parents=True,exist_ok=False)
    rows=[]
    cases=[('ready','diagnostic',True),('delayed','diagnostic',True),
        ('bad-exec','diagnostic',True),('uci-eof','diagnostic',True),
        ('ready-eof','diagnostic',True),('uci-stall','diagnostic',True),
        ('ready-stall','diagnostic',True),('ready','diagnostic',False),
        ('ready','reference',False),('uci-eof','reference',False),
        ('ready-eof','reference',False)]
    for i,(mode,arm,trace) in enumerate(cases):
        env=clean_env()|{'MIST_SF_WORKERS':'2','FAKE_UCI_MODE':mode}
        if trace: env['ASTRA_SF_STARTUP_TRACE']='1'
        path=build/'not-a-real-executable' if mode=='bad-exec' else HERE/'fake_engine.py'
        start=time.monotonic()
        proc=subprocess.Popen([build/(arm+'-driver'),path],env=env,stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,text=True,start_new_session=True)
        try:
            stdout,stderr=proc.communicate(timeout=12)
        except subprocess.TimeoutExpired:
            # This is the session just created by our unreaped Popen child.
            try: os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            stdout,stderr=proc.communicate(timeout=3)
            (raw/f'{i:02d}-timeout.txt').write_text(stdout+stderr)
            raise
        elapsed=time.monotonic()-start
        captured=raw/f'{i:02d}.json'
        captured.write_text(json.dumps(dict(mode=mode,arm=arm,trace=trace,stdout=stdout,
            stderr=stderr,code=proc.returncode,seconds=elapsed),indent=2)+'\n')
        assert not [p for p in group_members(proc.pid) if p['state'] not in ('Z','X')],mode
        good=mode in ('ready','delayed')
        assert (proc.returncode,stdout)==((0,'start=1 workers=2\n') if good else (1,'start=0 workers=0\n')),mode
        events=trace_rows(stderr)
        assert bool(events)==trace and len(events)<=2*(64+8),mode
        phase=None
        if trace and good:
            assert [(r['worker'],r['phase'],bytes.fromhex(r['line_hex'])) for r in events if r['event']=='matched']==[
                (0,'uci',b'uciok'),(0,'ready',b'readyok'),(1,'uci',b'uciok'),(1,'ready',b'readyok')],mode
            assert [r['worker'] for r in events if r['event']=='success']==[0,1],mode
            if mode=='delayed': assert elapsed>.28
        elif trace:
            phase='ready' if mode.startswith('ready-') else 'uci'
            failed=[r for r in events if r['event']=='failed']
            assert len(failed)==1 and failed[0]['phase']==phase and failed[0]['worker']==0,mode
            assert not any(r['event']=='success' for r in events),mode
            if mode.endswith('stall'):
                assert 4.5<=elapsed<7 and any(r['event'] in ('poll-timeout','read-deadline') for r in events),mode
            elif mode.endswith('eof'):
                assert any(r['event']=='read-eof' for r in events),mode
            exit_observed={r['exit_status'] for r in events if r['exited_pid']}
            expected={'bad-exec':127,'uci-eof':3,'ready-eof':4}.get(mode)
            if expected is not None: assert exit_observed in (set(),{expected}),mode
        rows.append(dict(case=i,mode=mode,arm=arm,trace=trace,seconds=elapsed,phase=phase,
            events=len(events),sha256=sha(captured),passed=True))
    result=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,calls=len(rows),rows=rows,
        scope='Owned mock transport contracts only. Two-worker success, both wait phases, EOF/exec failure, bounded stalls and disabled trace parity; no real startup prevalence or strength evidence.')
    (OUT/'mock-contracts.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True)

if __name__=='__main__': main()
