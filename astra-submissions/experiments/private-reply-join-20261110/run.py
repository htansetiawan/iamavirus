"""Single bounded offline C mining run on true completed replay ancestors."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import time
from prepare import OUT,BUILD,sha,write


def main():
    plan=json.loads((OUT/'plan.json').read_text())
    for path,digest in plan['dependencies'].items():assert sha(path)==digest,path
    assert os.path.ismount('/media/henrytan/seagate') and shutil.disk_usage('/media/henrytan/seagate').free>2*1024**3
    bulk=Path(plan['bulk_store']);bulk.mkdir(parents=True,exist_ok=False)
    os.sched_setaffinity(0,{plan['core']});os.nice(10)
    def limits():resource.setrlimit(resource.RLIMIT_FSIZE,(plan['output_limit'],plan['output_limit']))
    started=time.monotonic();timeout=False
    with (OUT/'input.txt').open('rb') as source,(bulk/'raw.jsonl').open('xb') as output,(OUT/'stderr.txt').open('x') as errors:
        p=subprocess.Popen([str(BUILD/'mine')],stdin=source,stdout=output,stderr=errors,preexec_fn=limits,start_new_session=True)
        write(OUT/'started.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=p.pid,pgid=p.pid,
             start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],plan_sha256=sha(OUT/'plan.json')))
        try:p.wait(timeout=plan['process_seconds'])
        except subprocess.TimeoutExpired:timeout=True;os.killpg(p.pid,signal.SIGKILL);p.wait()
    path=bulk/'raw.jsonl'
    write(OUT/'completion.json',dict(at=datetime.now(timezone.utc).isoformat(),exit_code=p.returncode,timed_out=timeout,
          seconds=time.monotonic()-started,raw_path=str(path),raw_sha256=sha(path),raw_bytes=path.stat().st_size,
          scope='Oracle feasibility corpus. No runtime input, search, model or playing change.'))
    assert p.returncode==0 and not timeout,p.returncode
    print((OUT/'completion.json').read_text(),flush=True)


if __name__=='__main__':main()
