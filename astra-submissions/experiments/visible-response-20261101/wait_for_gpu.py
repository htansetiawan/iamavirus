#!/usr/bin/env python3
"""Bounded availability wait; never signals another process or re-runs a fit."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time

import data


def now(): return datetime.now(timezone.utc).isoformat()


def main():
    path=data.OUT/'gpu-wait.json'; assert not path.exists()
    assert not (data.OUT/'training-execution.json').exists()
    status=dict(status='waiting',pid=os.getpid(),started_at=now(),checks=[])
    start=time.monotonic(); consecutive=0
    while time.monotonic()-start<600:
        raw=subprocess.check_output(['nvidia-smi','--query-gpu=utilization.gpu,memory.used','--format=csv,noheader,nounits'],text=True).strip()
        util,memory=map(int,raw.split(','))
        pids=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True).strip().splitlines()
        cp=data.ROOT/'chatroom/cores.json'; cores=json.loads(cp.read_text())
        conflict=any(a.get('owner')!='astra' and set(a.get('cores',[])) & {0,1} for a in cores['allocation'])
        free=util<10 and memory<2048 and not pids and not conflict
        consecutive=consecutive+1 if free else 0
        record=dict(at_utc=now(),utilization=util,memory_mib=memory,compute_pids=pids,core_conflict=conflict,consecutive_free=consecutive)
        status['checks'].append(record);path.write_text(json.dumps(status,indent=2)+'\n')
        print(json.dumps(record),flush=True)
        if consecutive>=2:
            for a in cores['allocation']:
                if a.get('owner')=='astra' and a.get('task','').startswith('208 '):
                    a.update(cores=[0,1],gpu=0,gpu_waiting=False)
            cores['updated']=now();cp.write_text(json.dumps(cores,indent=2)+'\n')
            status.update(status='launched',launched_at=now());path.write_text(json.dumps(status,indent=2)+'\n')
            env=os.environ.copy();env.update(OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
            os.execvpe('taskset',['taskset','-c','0,1',str(data.ROOT/'.venv/bin/python'),str(data.HERE/'train.py')],env)
        time.sleep(15)
    status.update(status='wait_expired_without_launch',ended_at=now());path.write_text(json.dumps(status,indent=2)+'\n')
    print(status['status'],flush=True)


if __name__=='__main__':main()
