"""Host-only GPU availability check immediately followed by the one fit."""
import json
import os
import subprocess
import sys
from common import HERE, ROOT, OUT, now, sha, write_new


def main():
    assert not (HERE/'work/training').exists()
    probe=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],
        capture_output=True,text=True,check=True)
    status=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv,noheader'],
        capture_output=True,text=True,check=True)
    assert not probe.stdout.strip(), 'GPU occupied; leave current service running and wait.'
    cores=ROOT/'chatroom/cores.json';d=json.loads(cores.read_text())
    for a in d['allocation']:
        assert a.get('agent')=='astra' or not {2,3}&set(a['cores']),a
    d['allocation']=[a for a in d['allocation'] if a.get('agent')!='astra']
    d['updated']=now();d['allocation'].append(dict(agent='astra',cores=[2,3],gpu=True,
        purpose='238 single bounded matched-budget student fit',since=d['updated']))
    cores.write_text(json.dumps(d,indent=2)+'\n')
    os.sched_setaffinity(0,{2,3})
    write_new(OUT/'gpu-start.json',dict(at=now(),pid=os.getpid(),free_compute_device=True,
        compute_apps=probe.stdout,gpu=status.stdout,plan_sha256=sha(OUT/'plan.json')))
    os.environ.update(OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    os.execv(sys.executable,[sys.executable,'-u',str(HERE/'train.py')])


if __name__=='__main__':main()
