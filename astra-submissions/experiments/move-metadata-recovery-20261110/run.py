"""One finite collection, then independent audit; never restarts a job."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'astra-submissions/analysis/move-metadata-recovery-20261110'

def main():
    started=time.monotonic();plan=json.loads((OUT/'plan.json').read_text())
    assert not (OUT/'supervision.json').exists()
    receipt=dict(started_at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),status='running',stages=[],restarted=False)
    def save():
        temporary=OUT/'supervision.tmp';temporary.write_text(json.dumps(receipt,indent=2)+'\n');temporary.replace(OUT/'supervision.json')
    save()
    try:
        for name,limit in [('collect',plan['wall_seconds']+60),('review',600)]:
            receipt['phase']=name;save()
            with (OUT/f'{name}.stdout').open('x') as stdout,(OUT/f'{name}.stderr').open('x') as stderr:
                child=subprocess.Popen(['nice','-n','15','taskset','-c','6',sys.executable,str(HERE/f'{name}.py')],cwd=ROOT,stdout=stdout,stderr=stderr,start_new_session=True)
                try:code=child.wait(timeout=limit)
                except BaseException:
                    os.killpg(child.pid,signal.SIGTERM)
                    try:child.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
                    raise
            receipt['stages'].append(dict(name=name,code=code));save()
            if code:raise RuntimeError(f'{name} exited {code}; original job preserved, no retry')
        receipt['status']='complete'
    except BaseException as exc:
        receipt.update(status='failed',error=repr(exc));raise
    finally:
        receipt.update(ended_at=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-started);save()

if __name__=='__main__':main()
