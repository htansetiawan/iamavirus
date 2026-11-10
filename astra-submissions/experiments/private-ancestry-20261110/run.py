"""First-attempt fixed-prefix screen. No games or true state enter actors."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import time
from prepare import OUT,BUILD,STORE,env,feed,sha,write


def main():
    plan=json.loads((OUT/'plan.json').read_text())
    for path,digest in plan['dependencies'].items():assert sha(path)==digest,path
    assert os.path.ismount('/media/henrytan/seagate') and shutil.disk_usage(STORE.parent).free>2*1024**3
    STORE.mkdir(exist_ok=False);os.sched_setaffinity(0,set(plan['cores']));os.nice(10)
    started=time.monotonic();done=[];current=None
    write(OUT/'started.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),
          start_ticks=Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()[19],plan_sha256=sha(OUT/'plan.json')))
    def limits():
        resource.setrlimit(resource.RLIMIT_AS,(plan['address_space_bytes'],plan['address_space_bytes']))
        resource.setrlimit(resource.RLIMIT_FSIZE,(plan['per_output_bytes'],plan['per_output_bytes']))
    failure=None
    try:
        for case in plan['cases']:
            order=['base','track'] if case['context']%2==0 else ['track','base']
            for arm in order+['pair']:
                assert time.monotonic()-started<plan['total_seconds']-plan['per_process_seconds'],'total wall bound'
                folder=STORE/f"context-{case['context']:02d}-{arm}";folder.mkdir()
                text=feed(case);(folder/'input.txt').write_text(text);before=time.monotonic()
                with (folder/'input.txt').open('rb') as inp,(folder/'stdout.jsonl').open('xb') as out,(folder/'stderr.txt').open('xb') as err:
                    process=subprocess.Popen([str(BUILD/('driver-'+arm))],stdin=inp,stdout=out,stderr=err,
                                             env=env(),preexec_fn=limits,start_new_session=True)
                    current=dict(context=case['context'],arm=arm,pid=process.pid,
                                 start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()[19])
                    write(folder/'process.json',current)
                    try:process.wait(timeout=plan['per_process_seconds']);timed_out=False
                    except subprocess.TimeoutExpired:
                        timed_out=True;os.killpg(process.pid,signal.SIGKILL);process.wait()
                result=dict(at=datetime.now(timezone.utc).isoformat(),**current,exit_code=process.returncode,
                            timed_out=timed_out,seconds=time.monotonic()-before,input_sha256=sha(folder/'input.txt'),
                            output_sha256=sha(folder/'stdout.jsonl'),output_bytes=(folder/'stdout.jsonl').stat().st_size,folder=str(folder))
                write(folder/'result.json',result);done.append(result);current=None
                print(json.dumps(dict(context=case['context'],arm=arm,exit_code=process.returncode,seconds=result['seconds'])),flush=True)
                assert process.returncode==0 and not timed_out,result
    except Exception as exc:
        failure=repr(exc)
    write(OUT/'completion.json',dict(at=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-started,
          attempted=len(done),expected=3*len(plan['cases']),results=done,failure=failure,current=current,
          status='complete' if failure is None else 'stopped-first-failure'))
    assert failure is None,failure

if __name__=='__main__':main()
