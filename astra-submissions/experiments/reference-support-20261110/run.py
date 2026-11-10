"""Bounded private-prefix support probe, one preceding search per case."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import time
from prepare import OUT,BUILD,STORE,environment,feed,sha,write

def main():
    plan=json.loads((OUT/'plan.json').read_text())
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    assert os.path.ismount('/media/henrytan/seagate') and shutil.disk_usage(STORE.parent).free>2*1024**3
    STORE.mkdir(exist_ok=False);os.sched_setaffinity(0,set(plan['cores']));os.nice(10)
    start=time.monotonic();results=[];failure=None
    write(OUT/'started.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),
          start_ticks=Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()[19],plan_sha256=sha(OUT/'plan.json')))
    def limits():
        resource.setrlimit(resource.RLIMIT_AS,(3*1024**3,3*1024**3))
        resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
    try:
        for c in plan['cases']:
            assert time.monotonic()-start<plan['total_seconds']-plan['per_case_seconds']
            d=STORE/f"context-{c['context']:02d}";d.mkdir();text,moves=feed(c);(d/'input.txt').write_text(text)
            before=time.monotonic()
            with (d/'input.txt').open('rb') as inp,(d/'stdout.txt').open('xb') as out,(d/'stderr.txt').open('xb') as err:
                p=subprocess.Popen([str(BUILD/'probe')],stdin=inp,stdout=out,stderr=err,
                     env=environment(c,moves,plan['search_seconds']),preexec_fn=limits,start_new_session=True)
                ident=dict(pid=p.pid,pgid=p.pid,start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19])
                write(d/'process.json',ident)
                try:p.wait(timeout=plan['per_case_seconds']);timeout=False
                except subprocess.TimeoutExpired:timeout=True;os.killpg(p.pid,signal.SIGKILL);p.wait()
            r=dict(context=c['context'],exit_code=p.returncode,timed_out=timeout,seconds=time.monotonic()-before,
                   input_sha256=sha(d/'input.txt'),stdout_sha256=sha(d/'stdout.txt'),stderr_sha256=sha(d/'stderr.txt'),folder=str(d),**ident)
            write(d/'result.json',r);results.append(r);print(json.dumps(r),flush=True)
            assert p.returncode==0 and not timeout,r
    except Exception as exc:failure=repr(exc)
    write(OUT/'completion.json',dict(at=datetime.now(timezone.utc).isoformat(),results=results,attempted=len(results),
          seconds=time.monotonic()-start,failure=failure,status='complete' if failure is None else 'stopped-first-failure'))
    assert failure is None,failure
if __name__=='__main__':main()
