"""Fresh host-GPU admission and a bounded, receipt-producing single launch."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from prepare import HERE,OUT,sha,write


def main():
    plan=json.loads((OUT/'plan.json').read_text())
    probe=subprocess.run(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used,memory.total',
                          '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=20)
    assert probe.returncode==0,probe.stderr
    index,util,used,total=map(int,probe.stdout.splitlines()[0].split(','))
    assert index==0 and util<10 and used<2048,(index,util,used,total)
    write(OUT/'gpu-start.json',dict(at=datetime.now(timezone.utc).isoformat(),plan_sha256=sha(OUT/'plan.json'),
          free_compute_device=True,index=index,utilization_percent=util,memory_used_MiB=used,memory_total_MiB=total,
          query_stdout=probe.stdout,launcher_sha256=sha(Path(__file__))))
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    started=time.monotonic();proc=subprocess.Popen([sys.executable,'-u',str(HERE/'train.py')],stdout=subprocess.PIPE,
         stderr=subprocess.PIPE,text=True,env=env,start_new_session=True)
    st=Path(f'/proc/{proc.pid}/stat').read_text().rsplit(')',1)[1].split()
    write(OUT/'process.json',dict(pid=proc.pid,pgid=proc.pid,start_ticks=st[19]))
    timed_out=False
    try:stdout,stderr=proc.communicate(timeout=1860)
    except subprocess.TimeoutExpired:
        timed_out=True;os.killpg(proc.pid,signal.SIGKILL);stdout,stderr=proc.communicate()
    (OUT/'training.stdout').write_text(stdout);(OUT/'training.stderr').write_text(stderr)
    result=dict(at=datetime.now(timezone.utc).isoformat(),exit_code=proc.returncode,timed_out=timed_out,
                elapsed=time.monotonic()-started,result_exists=(OUT/'result.json').exists(),
                stdout_sha256=sha(OUT/'training.stdout'),stderr_sha256=sha(OUT/'training.stderr'))
    write(OUT/'terminal.json',result)
    print(stdout[-6000:],flush=True);print(json.dumps(result),flush=True)
    if proc.returncode:print(stderr[-3000:],file=sys.stderr)
    return proc.returncode


if __name__=='__main__':sys.exit(main())
